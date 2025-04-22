from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from sale.models import Sale, SaleDetail, CashRegister
from user.models import User
from user.serializers import UserSerializer
from inventory.models import Product
from inventory.serializers import ProductSerializer



class SaleDetailSerializer(serializers.ModelSerializer):
    # Usamos PrimaryKeyRelatedField para que solo se pase el ID del producto
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    
    # Usamos el ProductSerializer para mostrar el producto como objeto en la representación (read)
    product_detail = ProductSerializer(source='product', read_only=True)

    
    class Meta:
        model = SaleDetail
        fields = '__all__'
        read_only_fields = ['discount', 'subtotal', 'sale']
        extra_kwargs = {
            'sale': {'required': False},
        }

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor que cero.")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor que cero.")
        return value   


class SaleSerializer(serializers.ModelSerializer):
    details = SaleDetailSerializer(many=True)

    class Meta:
        model = Sale
        fields = '__all__'
        read_only_fields = ['code', 'paid_amount']
        extra_kwargs = {
            'cash_register': {'required': False, 'allow_null': True}
        }

    def validate_paid_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("El monto pagado no puede ser negativo.")
        return value

    def validate_nit(self, value):
        if len(value) > 50:
            raise serializers.ValidationError("El NIT no puede exceder los 50 caracteres.")
        return value

    def generate_code(self):
        last_sale = Sale.objects.order_by('-created_at').first()
        if last_sale and last_sale.code.isdigit():
            next_number = int(last_sale.code) + 1
        else:
            next_number = 1
        return str(next_number).zfill(10)

    def create(self, validated_data):
        details_data = validated_data.pop('details', [])
        cash_register = validated_data['cash_register']

        if not details_data:
            raise serializers.ValidationError("Debe incluir al menos un detalle de venta.")

        with transaction.atomic():
            total_sale_amount = Decimal(0)
            validated_data['code'] = self.generate_code()
            sale = Sale.objects.create(**validated_data)

            for detail in details_data:
                product = detail['product']
                quantity = detail['quantity']
                price = detail['price']

                if product.stock < quantity:
                    raise serializers.ValidationError(f"Stock insuficiente para el producto: {product.name}")

                discount = Decimal(0)
                if product.discount and product.discount.is_active:
                    discount = product.discount.percentage

                subtotal = (price - (price * discount / 100)) * quantity

                SaleDetail.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    price=price,
                    discount=discount,
                    subtotal=subtotal
                )

                product.stock -= quantity
                product.save()
                total_sale_amount += subtotal

            sale.paid_amount = total_sale_amount
            sale.save()

            cash_register.sales_total += total_sale_amount
            cash_register.total += total_sale_amount
            cash_register.save()

            return sale


class CashRegisterSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = CashRegister
        fields = '__all__'
        read_only_fields = ['id', 'opening', 'closing', 'sales_total', 'purchases_total', 'total', 'user']
    
    def create(self, validated_data):
        # Automatically set opening time to now and set totals to 0
        validated_data['opening'] = timezone.now()
        validated_data['closing'] = None  # Set to None initially
        validated_data['sales_total'] = 0
        validated_data['purchases_total'] = 0
        validated_data['total'] = 0
        
        # Create the CashRegister object
        cash_register = super().create(validated_data)
        return cash_register
    
    def update(self, instance, validated_data):
        # Prevent editing the closing once it's set
        if instance.closing:
            raise serializers.ValidationError("Cannot update a closed cash register.")

        # Update the fields with the provided data
        return super().update(instance, validated_data)

    def validate_initial_balance(self, value):
        if value < 0:
            raise serializers.ValidationError("El saldo inicial no puede ser negativo.")
        return value

    def validate_sales_total(self, value):
        if value < 0:
            raise serializers.ValidationError("El total de ventas no puede ser negativo.")
        return value

    def validate_purchases_total(self, value):
        if value < 0:
            raise serializers.ValidationError("El total de compras no puede ser negativo.")
        return value

    def validate_total(self, value):
        if value < 0:
            raise serializers.ValidationError("El total no puede ser negativo.")
        return value
