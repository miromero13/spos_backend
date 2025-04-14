from rest_framework import serializers
from datetime import date
from inventory.models import Category, Discount, Product, Purchase, PurchaseDetail


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        return value


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = '__all__'

    def validate_percentage(self, value):
        if value <= 0 or value > 100:
            raise serializers.ValidationError("El porcentaje debe estar entre 0 y 100.")
        return value

    def validate_expiration_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("La fecha de expiración no puede estar en el pasado.")
        return value


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre del producto no puede estar vacío.")
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("El stock no puede ser negativo.")
        return value

    def validate_stock_minimum(self, value):
        if value < 0:
            raise serializers.ValidationError("El stock mínimo no puede ser negativo.")
        return value

    def validate(self, data):
        if data.get('stock_minimum') > data.get('stock'):
            raise serializers.ValidationError("El stock mínimo no puede ser mayor al stock actual.")
        if data.get('purchase_price') > data.get('sale_price'):
            raise serializers.ValidationError("El precio de compra no puede ser mayor al precio de venta.")
        return data


class PurchaseDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseDetail
        fields = '__all__'
        # extra

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor que cero.")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor que cero.")
        return value

    def validate(self, data):
        expected_subtotal = data.get('quantity') * data.get('price')
        if data.get('subtotal') != expected_subtotal:
            raise serializers.ValidationError("El subtotal debe ser igual a cantidad por precio.")
        return data


class PurchaseSerializer(serializers.ModelSerializer):
    details = PurchaseDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Purchase
        fields = '__all__'

    def validate_total_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto total debe ser mayor que cero.")
        return value

    def validate_reason(self, value):
        if not value.strip():
            raise serializers.ValidationError("El motivo no puede estar vacío.")
        return value
