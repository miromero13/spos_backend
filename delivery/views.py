from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiExample
from user.permissions import IsAdminOrCustomerOrCashier
from config.response import response
from .models import DeliveryAddress
from .serializers import DeliveryAddressSerializer

@extend_schema(tags=['Dirección de Entrega'])
class DeliveryAddressViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrCustomerOrCashier]

    def get_user_address(self):
        """Obtener la dirección del usuario actual"""
        try:
            return DeliveryAddress.objects.get(user=self.request.user)
        except DeliveryAddress.DoesNotExist:
            return None

    @extend_schema(
        summary="Obtener dirección de entrega",
        description="Obtiene la dirección de entrega del usuario actual",
        responses={
            200: DeliveryAddressSerializer,
            404: {"description": "No hay dirección configurada"}
        }
    )
    def retrieve(self, request, pk=None):
        """Obtener la dirección del usuario (pk no se usa, siempre devuelve la dirección del usuario actual)"""
        try:
            address = self.get_user_address()
            if not address:
                return response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="No tienes una dirección de entrega configurada",
                    error="No address found"
                )
            
            serializer = DeliveryAddressSerializer(address)
            return response(
                status_code=status.HTTP_200_OK,
                message="Dirección obtenida exitosamente",
                data=serializer.data
            )
        except Exception as e:
            return response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Error al obtener dirección: {str(e)}",
                error=str(e)
            )

    @extend_schema(
        summary="Crear o actualizar dirección de entrega",
        description="Crea una nueva dirección de entrega o actualiza la existente",
        request=DeliveryAddressSerializer,
        responses={
            200: DeliveryAddressSerializer,
            201: DeliveryAddressSerializer,
            400: {"description": "Datos inválidos"}
        },
        examples=[
            OpenApiExample(
                "Ejemplo de dirección",
                value={
                    "name": "Mi casa",
                    "address_line": "Av. Heroínas 123",
                    "city": "Cochabamba",
                    "state": "Cochabamba",
                    "postal_code": "0000",
                    "latitude": "-17.3895",
                    "longitude": "-66.1568",
                    "notes": "Casa de color azul"
                }
            )
        ]
    )
    def create(self, request):
        """Crear o actualizar la dirección del usuario"""
        try:
            existing_address = self.get_user_address()
            
            if existing_address:
                # Si ya existe, actualizarla
                serializer = DeliveryAddressSerializer(existing_address, data=request.data, partial=False)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                
                return response(
                    status_code=status.HTTP_200_OK,
                    message="Dirección actualizada exitosamente",
                    data=serializer.data
                )
            else:
                # Si no existe, crearla
                serializer = DeliveryAddressSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save(user=request.user)
                
                return response(
                    status_code=status.HTTP_201_CREATED,
                    message="Dirección creada exitosamente",
                    data=serializer.data
                )
        except Exception as e:
            return response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"Error al guardar dirección: {str(e)}",
                error=str(e)
            )

    @extend_schema(
        summary="Actualizar dirección de entrega",
        description="Actualiza la dirección de entrega existente",
        request=DeliveryAddressSerializer,
        responses={
            200: DeliveryAddressSerializer,
            404: {"description": "No hay dirección configurada"},
            400: {"description": "Datos inválidos"}
        }
    )
    def update(self, request, pk=None):
        """Actualizar la dirección del usuario"""
        try:
            address = self.get_user_address()
            if not address:
                return response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="No tienes una dirección de entrega configurada",
                    error="No address found"
                )
            
            serializer = DeliveryAddressSerializer(address, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return response(
                status_code=status.HTTP_200_OK,
                message="Dirección actualizada exitosamente",
                data=serializer.data
            )
        except Exception as e:
            return response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"Error al actualizar dirección: {str(e)}",
                error=str(e)
            )

    @extend_schema(
        summary="Eliminar dirección de entrega",
        description="Elimina la dirección de entrega del usuario",
        responses={
            200: {"description": "Dirección eliminada exitosamente"},
            404: {"description": "No hay dirección configurada"}
        }
    )
    def destroy(self, request, pk=None):
        """Eliminar la dirección del usuario"""
        try:
            address = self.get_user_address()
            if not address:
                return response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="No tienes una dirección de entrega configurada",
                    error="No address found"
                )
            
            address.delete()
            
            return response(
                status_code=status.HTTP_200_OK,
                message="Dirección eliminada exitosamente"
            )
        except Exception as e:
            return response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"Error al eliminar dirección: {str(e)}",
                error=str(e)
            )
