from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import DeliveryAddress

class DeliveryAddressSerializer(serializers.ModelSerializer):
    """Serializador para direcciones de entrega"""
    
    name = serializers.CharField(
        max_length=100,
        help_text="Nombre descriptivo para la dirección (ej: Mi casa, Trabajo)"
    )
    address_line = serializers.CharField(
        help_text="Dirección completa (calle, número, referencias)"
    )
    city = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Ciudad"
    )
    state = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Departamento o estado"
    )
    postal_code = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text="Código postal"
    )
    latitude = serializers.DecimalField(
        max_digits=11,
        decimal_places=8,
        help_text="Latitud de la ubicación (ej: -17.38950000)"
    )
    longitude = serializers.DecimalField(
        max_digits=12,
        decimal_places=8,
        help_text="Longitud de la ubicación (ej: -66.15680000)"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Notas adicionales o referencias para el delivery"
    )

    class Meta:
        model = DeliveryAddress
        fields = ['id', 'name', 'latitude', 'longitude', 'address_line', 'city', 'state', 'postal_code', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre de la dirección es obligatorio.")
        return value

    def validate_latitude(self, value):
        if not (-90 <= float(value) <= 90):
            raise serializers.ValidationError("La latitud debe estar entre -90 y 90.")
        return value

    def validate_longitude(self, value):
        if not (-180 <= float(value) <= 180):
            raise serializers.ValidationError("La longitud debe estar entre -180 y 180.")
        return value

    def validate_address_line(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("La dirección es obligatoria.")
        return value
