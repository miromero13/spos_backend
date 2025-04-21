from django.db import models
from django.utils import timezone
from config.models import BaseModel
from user.models import User
from inventory.models import Product

class CashRegister(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cash_registers')
    opening = models.DateTimeField()
    closing = models.DateTimeField(null=True, blank=True)
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sales_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    purchases_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observations = models.TextField(null=True, blank=True)

    def close_register(self):
        self.closing = timezone.now()
        self.save()

    def __str__(self):
        return f"Cash Register #{self.id}"


class Sale(BaseModel):
    code = models.CharField(max_length=20, unique=True)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    nit = models.CharField(max_length=50)

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales', limit_choices_to={'role': 'customer'})
    cash_register = models.ForeignKey(CashRegister, on_delete=models.CASCADE, related_name='sales', null=True, blank=True)

    def __str__(self):
        return f"Sale {self.code}"


class SaleDetail(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sale_details')
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='details')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
