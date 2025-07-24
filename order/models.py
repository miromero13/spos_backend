from django.db import models
from django.db import transaction
from user.models import User
from inventory.models import Product
from delivery.models import DeliveryAddress

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmado'),
        ('preparing', 'Preparando'),
        ('ready', 'Listo'),
        ('delivering', 'En camino'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    ]
    
    PAYMENT_METHODS = [
        ('qr', 'Código QR'),
        ('card', 'Tarjeta de Crédito/Débito'),
        ('cash', 'Efectivo'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('refunded', 'Reembolsado'),
    ]

    # Información básica del pedido
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Información de pago
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='qr')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Montos
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Información de entrega
    delivery_address = models.ForeignKey(
        DeliveryAddress, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='orders'
    )
    delivery_notes = models.TextField(blank=True, null=True)
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    actual_delivery_time = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            from datetime import datetime
            # Generar número de pedido único: ORD-YYYYMMDD-XXXX
            today = datetime.now().strftime('%Y%m%d')
            unique_id = str(uuid.uuid4())[:4].upper()
            self.order_number = f'ORD-{today}-{unique_id}'
        
        # Verificar si el estado cambió a 'delivered'
        is_new = self.pk is None
        old_status = None
        if not is_new:
            old_instance = Order.objects.get(pk=self.pk)
            old_status = old_instance.status
        
        super().save(*args, **kwargs)
        
        # Si el estado cambió a 'delivered', crear una venta
        if not is_new and old_status != 'delivered' and self.status == 'delivered':
            self._create_sale_from_order()

    def _create_sale_from_order(self):
        """Convierte esta orden en una venta cuando se marca como entregada"""
        from sale.models import Sale, SaleDetail
        import uuid
        from datetime import datetime
        
        with transaction.atomic():
            # Generar código único para la venta
            today = datetime.now().strftime('%Y%m%d')
            unique_id = str(uuid.uuid4())[:4].upper()
            sale_code = f'SALE-{today}-{unique_id}'
            
            # Crear la venta
            sale = Sale.objects.create(
                code=sale_code,
                paid_amount=self.total_amount,
                nit=self.user.ci,  # Usar CI del usuario como NIT
                customer=self.user,
                # cash_register se puede asignar más tarde si es necesario
            )
            
            # Crear los detalles de venta basados en los items de la orden
            for order_item in self.items.all():
                SaleDetail.objects.create(
                    product=order_item.product,
                    sale=sale,
                    quantity=order_item.quantity,
                    price=order_item.unit_price,
                    discount=0,  # Por defecto sin descuento
                    subtotal=order_item.total_price
                )
            
            return sale

    def __str__(self):
        return f"Pedido {self.order_number} - {self.user.name}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Snapshot de la información del producto al momento del pedido
    product_name = models.CharField(max_length=200)
    product_description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'order_items'
        unique_together = ['order', 'product']

    def save(self, *args, **kwargs):
        # Calcular precio total automáticamente
        self.total_price = self.unit_price * self.quantity
        
        # Guardar snapshot del producto
        if self.product:
            self.product_name = self.product.name
            self.product_description = self.product.description
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} - {self.order.order_number}"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=20, blank=True, null=True)
    new_status = models.CharField(max_length=20)
    notes = models.TextField(blank=True, null=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_status_history'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order.order_number}: {self.previous_status} → {self.new_status}"
