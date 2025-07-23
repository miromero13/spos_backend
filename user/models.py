from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from config.models import BaseModel
from django.db import models
from inventory.models import Product

class UserManager(BaseUserManager):
    def create_user(self, ci, email, name, phone, role, password=None):
        if not email:
            raise ValueError("El usuario debe tener un email electrónico")
        user = self.model(
            ci=ci,
            email=self.normalize_email(email),
            name=name,
            phone=phone,
            role=role,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, ci, email, name, phone, role='administrator', password=None):
        user = self.create_user(ci, email, name, phone, role, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    ROLES = (
        ('administrator', 'Administrador'),
        ('customer', 'Cliente'),
        ('cashier', 'Cajero'),
    )

    ci = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['ci', 'name', 'phone', 'role']

    objects = UserManager()

    def __str__(self):
        return f"{self.name} ({self.role})"

# models.py
class ProductRecommendation(models.Model):
    source_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='recommendations_as_source'
    )
    recommended_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='recommendations_as_target'
    )
    score = models.FloatField(default=0.0)
    recommendation_type = models.CharField(
        max_length=50,
        choices=[
            ('frequently_bought', 'Frecuentemente comprados juntos'),
            ('category', 'Misma categoría'),
            ('complementary', 'Complementario')
        ]
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('source_product', 'recommended_product')
        indexes = [
            models.Index(fields=['source_product', 'score']),
            models.Index(fields=['recommended_product', 'score'])
        ]