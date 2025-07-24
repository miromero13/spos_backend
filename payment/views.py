from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import authenticate
import json
import base64
import os
from datetime import datetime, timedelta

from .models import PaymentTransaction
from .serializers import (
    PaymentTransactionSerializer, 
    GenerateQRSerializer, 
    VerifyPaymentSerializer,
    PaymentStatusSerializer
)
from .veripagos_service import VeripagosService
from config.response import response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_qr_payment(request):
    """
    Genera un código QR para pago usando Veripagos
    """
    try:
        serializer = GenerateQRSerializer(data=request.data)
        if not serializer.is_valid():
            return response(400, "Datos inválidos", serializer.errors)

        data = serializer.validated_data
        amount = data['amount']
        extra_data = data.get('extra_data', {})
        validity = data.get('validity', "1/00:00")
        detail = data.get('detail')

        # Agregar información del usuario a extra_data
        extra_data.update({
            'user_id': str(request.user.id),  # Convertir UUID a string
            'user_email': request.user.email,
            'timestamp': timezone.now().isoformat()
        })

        # Inicializar servicio de Veripagos
        veripagos = VeripagosService()
        
        # Generar QR
        result = veripagos.generate_qr(
            amount=amount,
            extra_information=extra_data,
            validity=validity,
            detail=detail
        )

        if result['status'] != 200:
            return response(result['status'], result['message'], None)

        qr_data = result['data']
        movement_id = qr_data.get('movimiento_id')
        qr_code = qr_data.get('qr')

        # Crear registro de transacción en la base de datos
        payment_transaction = PaymentTransaction.objects.create(
            user=request.user,
            movement_id=str(movement_id),
            amount=amount,
            payment_method='qr',
            status='pending',
            qr_code=qr_code,
            qr_validity=validity,
            extra_data=extra_data,
            expires_at=_calculate_expiry_date(validity)
        )

        # Construir respuesta manualmente para evitar problemas de serialización
        response_data = {
            'transaction_id': str(payment_transaction.id),
            'payment_id': str(payment_transaction.id),
            'movement_id': movement_id,
            'qr_data': qr_code,  # QR code string sin formatear
            'qr_code': veripagos.format_qr_image(qr_code),  # QR formateado para mostrar
            'amount': float(amount),
            'validity': validity,
            'status': 'pending',
            'expires_at': payment_transaction.expires_at.isoformat() if payment_transaction.expires_at else None,
            'created_at': payment_transaction.created_at.isoformat(),
            'user_id': str(request.user.id),
            'user_email': request.user.email
        }

        return response(200, "QR generado exitosamente", response_data)

    except Exception as e:
        return response(500, f"Error interno: {str(e)}", None)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment_status(request):
    """
    Verifica el estado de un pago por su ID
    """
    try:
        serializer = VerifyPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return response(400, "Datos inválidos", serializer.errors)

        payment_id = serializer.validated_data['payment_id']
        
        try:
            print(f"Verificando estado del pago con ID: {payment_id}")
            print(
              json.dumps(request.data, default=str)
            )
            print(
              json.dumps(request.user, default=str)
            )
            payment = PaymentTransaction.objects.get(
                id=payment_id,
                user=request.user  # Verificar que pertenece al usuario
            )
        except PaymentTransaction.DoesNotExist:
            return response(404, "Transacción no encontrada", None)

        # Si ya está completado, retornar el estado actual
        print(
          payment.status
        )
        if payment.status == 'completed':
            transaction_serializer = PaymentTransactionSerializer(payment)
            return response(200, "Pago ya completado", transaction_serializer.data)

        # Verificar estado en Veripagos usando movement_id
        veripagos = VeripagosService()
        result = veripagos.verify_qr_status(payment.movement_id)
        print(f"Resultado de Veripagos: {result}")

        if result['status'] != 200:
            return response(result['data']['estado'], result['message'], None)

        payment_data = result['data']
        payment_status = payment_data.get('estado', '').lower()
        # Actualizar estado del pago
        if payment_status == 'completado':
            payment.status = 'completed'
            payment.completed_at = timezone.now()
            
            # Actualizar información del remitente
            remitente = payment_data.get('remitente', {})
            payment.sender_name = remitente.get('nombre')
            payment.sender_bank = remitente.get('banco')
            payment.sender_document = remitente.get('documento')
            payment.sender_account = remitente.get('cuenta')
            
            payment.save()

        # Serializar respuesta
        transaction_serializer = PaymentTransactionSerializer(payment)
        
        response_data = {
            'payment_status': payment.status,
            'is_completed': payment.status == 'completed',
            'veripagos_data': payment_data,
            'transaction': transaction_serializer.data
        }

        return response(200, "Estado verificado exitosamente", response_data)

    except Exception as e:
        return response(500, f"Error interno: {str(e)}", None)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_transactions(request):
    """
    Obtiene las transacciones de pago del usuario
    """
    try:
        transactions = PaymentTransaction.objects.filter(user=request.user)
        serializer = PaymentTransactionSerializer(transactions, many=True)
        return response(200, "Transacciones obtenidas exitosamente", serializer.data)
    except Exception as e:
        return response(500, f"Error interno: {str(e)}", None)

@csrf_exempt
def veripagos_webhook(request):
    """
    Webhook para recibir notificaciones de Veripagos
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        # Verificar autenticación Basic Auth
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Basic '):
            return JsonResponse({'error': 'Autenticación requerida'}, status=401)

        # Decodificar credenciales
        encoded_credentials = auth_header[6:]  # Remover 'Basic '
        decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
        username, password = decoded_credentials.split(':', 1)

        # Verificar credenciales (usar las mismas de Veripagos)
        expected_username = "Sauterdev"
        expected_password = "ec%Nb1Xaox"
        
        if username != expected_username or password != expected_password:
            return JsonResponse({'error': 'Credenciales inválidas'}, status=401)

        # Procesar datos del webhook
        data = json.loads(request.body)
        
        movement_id = data.get('movimiento_id')
        status = data.get('estado', '').lower()
        remitente = data.get('remitente', {})

        # Buscar la transacción
        try:
            payment = PaymentTransaction.objects.get(movement_id=str(movement_id))
        except PaymentTransaction.DoesNotExist:
            return JsonResponse({'error': 'Transacción no encontrada'}, status=404)

        # Actualizar estado si está completado
        if status == 'completado' and not payment.is_completed:
            payment.status = 'completed'
            payment.completed_at = timezone.now()
            payment.sender_name = remitente.get('nombre')
            payment.sender_bank = remitente.get('banco')
            payment.sender_document = remitente.get('documento')
            payment.sender_account = remitente.get('cuenta')
            payment.save()

        return JsonResponse({'message': 'Webhook procesado exitosamente'}, status=200)

    except Exception as e:
        return JsonResponse({'error': f'Error procesando webhook: {str(e)}'}, status=500)

def _calculate_expiry_date(validity_string):
    """
    Calcula la fecha de expiración basada en el string de vigencia
    Formato: "días/horas:minutos"
    """
    try:
        days_part, time_part = validity_string.split('/')
        days = int(days_part)
        
        hours_part, minutes_part = time_part.split(':')
        hours = int(hours_part)
        minutes = int(minutes_part)
        
        expiry_delta = timedelta(days=days, hours=hours, minutes=minutes)
        return timezone.now() + expiry_delta
        
    except (ValueError, AttributeError):
        # Si hay error en el formato, usar 15 minutos por defecto
        return timezone.now() + timedelta(minutes=15)
