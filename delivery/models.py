from django.db import models
from user.models import User

class DeliveryAddress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='delivery_address')
    name = models.CharField(max_length=100, default="Mi dirección")
    address_line = models.TextField(default="Dirección no especificada")
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    latitude = models.DecimalField(max_digits=11, decimal_places=8)  # -90.12345678 a 90.12345678
    longitude = models.DecimalField(max_digits=12, decimal_places=8)  # -180.12345678 a 180.12345678
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'delivery_addresses'

    def __str__(self):
        return f"{self.name} - {self.user.name}"
