from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory
from inventory.models import Product
from user.serializers import UserSerializer
from delivery.serializers import DeliveryAddressSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(read_only=True)
    product_description = serializers.CharField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_description',
            'quantity', 'unit_price', 'total_price'
        ]

    def validate_product(self, value):
        if not value.is_active:
            raise serializers.ValidationError("El producto no está disponible.")
        return value

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0.")
        return value


class OrderCreateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        help_text="Lista de items del pedido con product_id, quantity y price"
    )

    class Meta:
        model = Order
        fields = [
            'payment_method', 'payment_status', 'total_amount',
            'delivery_notes', 'items'
        ]

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("El pedido debe tener al menos un item.")
        
        for item in value:
            if 'product_id' not in item:
                raise serializers.ValidationError("Cada item debe tener un product_id.")
            if 'quantity' not in item:
                raise serializers.ValidationError("Cada item debe tener una quantity.")
            if 'price' not in item:
                raise serializers.ValidationError("Cada item debe tener un price.")
        
        return value

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        
        # Crear el pedido
        order = Order.objects.create(
            user=user,
            **validated_data
        )
        
        # Obtener la dirección de entrega del usuario
        if hasattr(user, 'delivery_address'):
            order.delivery_address = user.delivery_address
        
        # Crear los items del pedido
        total_subtotal = 0
        for item_data in items_data:
            try:
                product = Product.objects.get(id=item_data['product_id'])
                
                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item_data['quantity'],
                    unit_price=item_data['price']
                )
                
                total_subtotal += order_item.total_price
                
            except Product.DoesNotExist:
                # Si un producto no existe, eliminar el pedido y lanzar error
                order.delete()
                raise serializers.ValidationError(f"Producto con ID {item_data['product_id']} no encontrado.")
        
        # Actualizar subtotal del pedido
        order.subtotal = total_subtotal
        # Por ahora no calculamos impuestos ni costo de delivery
        order.tax_amount = 0
        order.delivery_fee = 0
        # Verificar que el total coincida
        calculated_total = order.subtotal + order.tax_amount + order.delivery_fee
        if abs(float(order.total_amount) - float(calculated_total)) > 0.01:
            order.delete()
            raise serializers.ValidationError("El total del pedido no coincide con los items.")
        
        order.save()
        
        # Crear historial de estado
        OrderStatusHistory.objects.create(
            order=order,
            new_status=order.status,
            notes="Pedido creado"
        )
        
        return order


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    delivery_address = DeliveryAddressSerializer(read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    
    # Campos con labels amigables
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'status_display',
            'payment_method', 'payment_method_display',
            'payment_status', 'payment_status_display',
            'subtotal', 'tax_amount', 'delivery_fee', 'total_amount',
            'delivery_notes', 'estimated_delivery_time', 'actual_delivery_time',
            'created_at', 'updated_at', 'user', 'delivery_address',
            'items', 'total_items'
        ]


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by = UserSerializer(read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = [
            'id', 'previous_status', 'new_status', 'notes',
            'changed_by', 'created_at'
        ]
