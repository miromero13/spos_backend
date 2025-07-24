from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid

class PaymentTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('expired', 'Expirado'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('qr', 'QR Veripagos'),
        ('card', 'Tarjeta'),
        ('cash', 'Efectivo'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    movement_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Datos específicos de Veripagos QR
    qr_code = models.TextField(null=True, blank=True)  # QR en base64
    qr_validity = models.CharField(max_length=20, default="1/00:00")
    extra_data = models.JSONField(default=dict, blank=True)
    
    # Información del remitente (cuando se complete el pago)
    sender_name = models.CharField(max_length=200, null=True, blank=True)
    sender_bank = models.CharField(max_length=100, null=True, blank=True)
    sender_document = models.CharField(max_length=50, null=True, blank=True)
    sender_account = models.CharField(max_length=50, null=True, blank=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payment_transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.id} - {self.user.username} - {self.amount} Bs - {self.status}"

    @property
    def is_completed(self):
        return self.status == 'completed'

    @property
    def is_pending(self):
        return self.status == 'pending'

    @property
    def formatted_qr_code(self):
        """Retorna el QR formateado para mostrar en frontend"""
        if self.qr_code:
            return f"data:image/png;base64,{self.qr_code}"
        return None
