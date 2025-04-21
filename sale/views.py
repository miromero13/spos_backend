from rest_framework import viewsets
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import action
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Case, When, IntegerField, Value as V
from drf_spectacular.utils import extend_schema, OpenApiParameter
from datetime import datetime

from sale.models import Sale, CashRegister
from sale.serializers import SaleSerializer, SaleDetailSerializer, CashRegisterSerializer
from inventory.models import Product
from config.response import response
from user.permissions import IsAdminOrCashier, IsAdminOrCustomerOrCashier
from config.response import StandardResponseSerializerSuccess, StandardResponseSerializerError, StandardResponseSerializerSuccessList

@extend_schema(
    request=SaleSerializer,
    responses={
        201: StandardResponseSerializerSuccess,
        400: StandardResponseSerializerError,
        404: StandardResponseSerializerError
    }
)
class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrCustomerOrCashier]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='limit', description='Cantidad de resultados', required=False, type=int),
            OpenApiParameter(name='offset', description='Inicio del listado', required=False, type=int),
            OpenApiParameter(name='order', description='Campo de ordenamiento (ej: +name, -email)', required=False, type=str),
            OpenApiParameter(name='attr', description='Campo para filtrar (ej: code, paid_amount)', required=False, type=str),
            OpenApiParameter(name='value', description='Valor del campo a filtrar', required=False, type=str),
        ], 
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
            500: StandardResponseSerializerError
        }
    )
    def list(self, request):
        try:
            # Query básica para obtener todas las ventas
            queryset = Sale.objects.all()

            # Filtrado por parámetros adicionales
            attr = request.query_params.get('attr')
            value = request.query_params.get('value')

            if attr and value and hasattr(Sale, attr):
                # Filtrado usando "contains" o "starts with"
                starts_with_filter = {f"{attr}__istartswith": value}
                contains_filter = {f"{attr}__icontains": value}
                queryset = queryset.filter(Q(**contains_filter))
                
                # Ordenar por relevancia si el valor empieza con el texto
                queryset = queryset.annotate(
                    relevance=Case(
                        When(**starts_with_filter, then=V(0)),
                        default=V(1),
                        output_field=IntegerField()
                    )
                ).order_by('relevance')

            elif attr and not hasattr(Sale, attr):
                return response(
                    400,
                    f"El campo '{attr}' no es válido para filtrado"
                )

            # Ordenar resultados
            order = request.query_params.get('order')
            if order:
                try:
                    queryset = queryset.order_by(order)
                except Exception:
                    return response(
                        400,
                        f"No se pudo ordenar por '{order}'"
                    )

            # Paginación: limit y offset
            limit = request.query_params.get('limit')
            offset = request.query_params.get('offset', 0)

            if limit is not None:
                try:
                    limit = int(limit)
                    offset = int(offset)
                    queryset = queryset[offset:offset+limit]
                except ValueError:
                    return response(
                        400,
                        "Los valores de limit y offset deben ser enteros"
                    )

            # Serializar datos
            serializer = SaleSerializer(queryset, many=True)
            return response(
                200,
                "Ventas encontradas",
                data=serializer.data,
                count_data=len(queryset)
            )

        except Exception as e:
            return response(
                500,
                f"Error al obtener ventas: {str(e)}"
            )

    def retrieve(self, request, pk=None):
        try:
            sale = Sale.objects.get(pk=pk)
            serializer = SaleSerializer(sale)
            return response(200, "Venta encontrada", data=serializer.data)
        except Sale.DoesNotExist:
            return response(404, "Venta no encontrada")

def create(self, request):
        data = request.data
        cash_register_id = data.get('cash_register')
        customer_id = data.get('customer')

        try:
            # Validar caja
            cash_register = CashRegister.objects.get(id=cash_register_id)
            if cash_register_id:
                try:
                    cash_register = CashRegister.objects.get(id=cash_register_id)
                    if cash_register.closing:
                        return response(400, "La caja está cerrada.")
                except CashRegister.DoesNotExist:
                    return response(404, "Caja no encontrada.")

            with transaction.atomic():
                data['customer'] = str(customer_id)  # Asociamos el cliente con la venta
                serializer = SaleSerializer(data=data)
                if serializer.is_valid():
                    sale = serializer.save()

                    return response(201, "Venta creada correctamente", data=self.get_serializer(sale).data)

                return response(400, "Errores de validación en la venta", error=serializer.errors)

        except CashRegister.DoesNotExist:
            return response(404, "Caja no encontrada")
        except Exception as e:
            transaction.set_rollback(True)
            return response(500, f"Error al crear la venta: {str(e)}")


@extend_schema(
    request=CashRegisterSerializer,
    responses={
        201: StandardResponseSerializerSuccess,
        400: StandardResponseSerializerError,
        404: StandardResponseSerializerError,
        403: StandardResponseSerializerError
    }
)
class CashRegisterViewSet(viewsets.ModelViewSet):
    queryset = CashRegister.objects.all()
    serializer_class = CashRegisterSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrCashier]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='limit', description='Cantidad de resultados', required=False, type=int),
            OpenApiParameter(name='offset', description='Inicio del listado', required=False, type=int),
            OpenApiParameter(name='order', description='Campo de ordenamiento (ej: +name, -email)', required=False, type=str),
            OpenApiParameter(name='attr', description='Campo para filtrar (ej: code, paid_amount)', required=False, type=str),
            OpenApiParameter(name='value', description='Valor del campo a filtrar', required=False, type=str),
        ], 
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
            500: StandardResponseSerializerError
        }
    )
    def list(self, request):
        try:
            # Query básica para obtener todas las cajas
            queryset = CashRegister.objects.all()
            
            # Filtrado por parámetros adicionales
            attr = request.query_params.get('attr')
            value = request.query_params.get('value')
            if attr and value and hasattr(CashRegister, attr):
                # Filtrado usando "contains" y "starts with"
                starts_with_filter = {f"{attr}__istartswith": value}
                contains_filter = {f"{attr}__icontains": value}

                # Filtrar por "contains" y usar "starts_with" para orden
                queryset = queryset.filter(Q(**contains_filter))

                # Ordenar por relevancia si el valor empieza con el texto
                queryset = queryset.annotate(
                    relevance=Case(
                        When(**starts_with_filter, then=V(0)),
                        default=V(1),
                        output_field=IntegerField()
                    )
                ).order_by('relevance')                
            elif attr and not hasattr(CashRegister, attr):
                return response(
                    400,
                    f"El campo '{attr}' no es válido para filtrado"
                )   

            # Ordenar resultados
            order = request.query_params.get('order')
            if order:
                try:
                    queryset = queryset.order_by(order)
                except Exception:
                    return response(
                        400,
                        f"No se pudo ordenar por '{order}'"
                    )   
                
            # Paginación: limit y offset
            limit = request.query_params.get('limit')
            offset = request.query_params.get('offset', 0)
            
            if limit is not None:
                try:
                    limit = int(limit)
                    offset = int(offset)
                    queryset = queryset[offset:offset+limit]
                except ValueError:
                    return response(
                        400,
                        "Los valores de limit y offset deben ser enteros"
                    )
                
            # Serializar datos
            serializer = CashRegisterSerializer(queryset, many=True)
            return response(
                200,
                "Cajas encontradas",
                data=serializer.data,
                count_data=len(queryset)
            )
        except Exception as e:
            return response(
                500,
                f"Error al obtener cajas: {str(e)}"
            )
    def retrieve(self, request, pk=None):
        try:
            cash_register = CashRegister.objects.get(pk=pk)
            serializer = CashRegisterSerializer(cash_register)
            return response(200, "Caja encontrada", data=serializer.data)
        except CashRegister.DoesNotExist:
            return response(404, "Caja no encontrada")

    def create(self, request):
        data = request.data.copy()
        user = request.user

         # Verificar si ya hay una caja abierta para el usuario
        if CashRegister.objects.filter(user=user, closing=None).exists():
            return response(400, "El usuario ya tiene una caja abierta.")

        # Crear la caja
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            cash_register = serializer.save(user=user)
            return response(201, "Caja creada correctamente", data=serializer.data)
        return response(400, "Errores de validación", error=serializer.errors)
    
    @extend_schema(
        responses={
            200: StandardResponseSerializerSuccess, 
            404: StandardResponseSerializerError, 
            500: StandardResponseSerializerError
        },
    )
    @action(methods=["get"], detail=False, url_path="validate_user_cash_register", permission_classes=[IsAdminOrCashier])
    def validate_user_cash_register(self, request):
        try:
            user = request.user
            cash_register = CashRegister.objects.filter(user=user, closing=None).first()
            if cash_register:
                return response(
                    200, 
                    "El usuario tiene una caja abierta.", 
                    data={
                        "id": cash_register.id,
                        "validate": True,
                    }
                )
            else:
                return response(200, "El usuario no tiene una caja abierta.", data={"validate": False})
        except Exception as e:
            return response(500, f"Error al validar la caja del usuario: {str(e)}")

    @extend_schema(
        responses={
            200: SaleDetailSerializer, 
            404: StandardResponseSerializerError, 
            500: StandardResponseSerializerError
        },
    )
    @action(detail=False, methods=["get"], url_path="close_current_register", permission_classes=[IsAdminOrCashier])
    def close_current_register(self, request):
        try:
            user = request.user
            cash_register = CashRegister.objects.filter(user=user, closing=None).first()

            if not cash_register:
                return response(404, "No se encontró una caja abierta para este usuario.")

            if cash_register.closing:
                return response(400, "La caja ya está cerrada.")

            cash_register.close_register()
            return response(200, "Caja cerrada correctamente.")
        except Exception as e:
            return response(500, f"Error al cerrar la caja: {str(e)}")

    def update(self, request, *args, **kwargs):
        return response(403, "Actualización de cajas no permitida.")


    def destroy(self, request, pk=None):
        return response(403, "La caja no puede ser eliminada una vez creada")