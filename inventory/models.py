from django.db import models
from config.models import BaseModel

class Category(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Discount(BaseModel):
    name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    expiration_date = models.DateField()

    def __str__(self):
        return f"{self.name} - {self.percentage}%"

class Product(BaseModel):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    stock_minimum = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    photo_url = models.TextField(blank=True)    

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    discount = models.OneToOneField(Discount, on_delete=models.SET_NULL, null=True, blank=True, related_name='product')

    def __str__(self):
        return self.name

class Purchase(BaseModel):
    reason = models.TextField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    code = models.CharField(max_length=20, unique=True)

    # user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases', role='administrator')
    def __str__(self):
        return f"Purchase {self.code}"

class PurchaseDetail(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='purchase_details')
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='details')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"