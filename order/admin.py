from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price', 'product_name', 'product_description')

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'status', 'payment_method', 
        'payment_status', 'total_amount', 'created_at'
    ]
    list_filter = [
        'status', 'payment_method', 'payment_status', 
        'created_at', 'updated_at'
    ]
    search_fields = [
        'order_number', 'user__name', 'user__email'
    ]
    readonly_fields = [
        'order_number', 'created_at', 'updated_at', 'total_items'
    ]
    fieldsets = (
        ('Información del Pedido', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Información de Pago', {
            'fields': ('payment_method', 'payment_status')
        }),
        ('Montos', {
            'fields': ('subtotal', 'tax_amount', 'delivery_fee', 'total_amount')
        }),
        ('Entrega', {
            'fields': ('delivery_address', 'delivery_notes', 'estimated_delivery_time', 'actual_delivery_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': ('total_items',),
            'classes': ('collapse',)
        })
    )
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'delivery_address'
        ).prefetch_related('items', 'status_history')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'order', 'product_name', 'quantity', 'unit_price', 'total_price'
    ]
    list_filter = ['order__status', 'order__created_at']
    search_fields = [
        'order__order_number', 'product__name', 'product_name'
    ]
    readonly_fields = ['total_price', 'product_name', 'product_description']

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'order', 'previous_status', 'new_status', 'changed_by', 'created_at'
    ]
    list_filter = ['new_status', 'previous_status', 'created_at']
    search_fields = ['order__order_number', 'notes']
    readonly_fields = ['created_at']
