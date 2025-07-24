from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from config.response import response
from .models import Order, OrderStatusHistory
from .serializers import OrderSerializer, OrderCreateSerializer, OrderStatusHistorySerializer

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    def get_queryset(self):
        # Los administradores pueden ver todos los pedidos
        # Los usuarios normales solo pueden ver sus propios pedidos
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Order.objects.all().prefetch_related(
                'items__product', 'delivery_address', 'status_history'
            ).select_related('user')
        else:
            return Order.objects.filter(user=self.request.user).prefetch_related(
                'items__product', 'delivery_address', 'status_history'
            )

    @extend_schema(
        summary="Listar pedidos del usuario",
        description="Obtiene todos los pedidos realizados por el usuario autenticado",
        responses={
            200: OrderSerializer(many=True),
        }
    )
    def list(self, request):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return response(
                status_code=200,
                message="Pedidos obtenidos exitosamente",
                data=serializer.data
            )
        except Exception as e:
            return response(
                status_code=500,
                message=f"Error al obtener pedidos: {str(e)}"
            )

    @extend_schema(
        summary="Crear nuevo pedido",
        description="Crea un nuevo pedido con los items especificados",
        request=OrderCreateSerializer,
        responses={
            201: OrderSerializer,
            400: "Error de validación",
        },
        examples=[
            OpenApiExample(
                "Ejemplo de pedido",
                value={
                    "payment_method": "qr",
                    "payment_status": "completed",
                    "total_amount": 45.50,
                    "delivery_notes": "Tocar el timbre dos veces",
                    "items": [
                        {
                            "product_id": "12345",
                            "quantity": 2,
                            "price": 15.00
                        },
                        {
                            "product_id": "67890",
                            "quantity": 1,
                            "price": 15.50
                        }
                    ]
                }
            )
        ]
    )
    def create(self, request):
        try:
            serializer = self.get_serializer(data=request.data, context={'request': request})
            
            if serializer.is_valid():
                order = serializer.save()
                response_serializer = OrderSerializer(order)
                return response(
                    status_code=201,
                    message="Pedido creado exitosamente",
                    data=response_serializer.data
                )
            else:
                return response(
                    status_code=400,
                    message="Error al crear pedido",
                    error=serializer.errors
                )
                
        except Exception as e:
            return response(
                status_code=500,
                message=f"Error al crear pedido: {str(e)}"
            )

    @extend_schema(
        summary="Obtener detalles de un pedido",
        description="Obtiene los detalles completos de un pedido específico",
        responses={
            200: OrderSerializer,
            404: "Pedido no encontrado",
        }
    )
    def retrieve(self, request, pk=None):
        try:
            order = self.get_object()
            serializer = self.get_serializer(order)
            return response(
                status_code=200,
                message="Pedido obtenido exitosamente",
                data=serializer.data
            )
        except Order.DoesNotExist:
            return response(
                status_code=404,
                message="Pedido no encontrado"
            )
        except Exception as e:
            return response(
                status_code=500,
                message=f"Error al obtener pedido: {str(e)}"
            )

    @extend_schema(
        summary="Actualizar estado del pedido",
        description="Actualiza el estado de un pedido. Si se marca como 'delivered', se crea automáticamente una venta.",
        request={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "confirmed", "preparing", "ready", "delivering", "delivered", "cancelled"]
                },
                "notes": {
                    "type": "string",
                    "description": "Notas opcionales sobre el cambio de estado"
                }
            },
            "required": ["status"]
        },
        responses={
            200: OrderSerializer,
            400: "Estado inválido",
            404: "Pedido no encontrado",
        }
    )
    def partial_update(self, request, pk=None):
        try:
            order = self.get_object()
            old_status = order.status
            
            if 'status' in request.data:
                new_status = request.data['status']
                notes = request.data.get('notes', f"Estado actualizado desde la app web")
                
                # Actualizar el estado
                order.status = new_status
                order.save()  # Esto disparará la creación de venta si el estado es 'delivered'
                
                # Crear historial de cambio de estado
                OrderStatusHistory.objects.create(
                    order=order,
                    previous_status=old_status,
                    new_status=new_status,
                    notes=notes,
                    changed_by=request.user
                )
                
                message = "Estado del pedido actualizado exitosamente"
                if old_status != 'delivered' and new_status == 'delivered':
                    message += ". Se ha creado automáticamente una venta correspondiente."
            
            serializer = self.get_serializer(order)
            return response(
                status_code=200,
                message=message,
                data=serializer.data
            )
            
        except Order.DoesNotExist:
            return response(
                status_code=404,
                message="Pedido no encontrado"
            )
        except Exception as e:
            return response(
                status_code=500,
                message=f"Error al actualizar pedido: {str(e)}"
            )

    @extend_schema(
        summary="Historial de estados del pedido",
        description="Obtiene el historial completo de cambios de estado de un pedido",
        responses={
            200: OrderStatusHistorySerializer(many=True),
            404: "Pedido no encontrado",
        }
    )
    @action(detail=True, methods=['get'])
    def status_history(self, request, pk=None):
        try:
            order = self.get_object()
            history = order.status_history.all()
            serializer = OrderStatusHistorySerializer(history, many=True)
            return response(
                status_code=200,
                message="Historial obtenido exitosamente",
                data=serializer.data
            )
        except Order.DoesNotExist:
            return response(
                status_code=404,
                message="Pedido no encontrado"
            )
        except Exception as e:
            return response(
                status_code=500,
                message=f"Error al obtener historial: {str(e)}"
            )
