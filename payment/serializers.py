from rest_framework import serializers
from .models import PaymentTransaction

class PaymentTransactionSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()  # Convertir UUID a string
    user = serializers.SerializerMethodField()  # Convertir UUID del user a string
    formatted_qr_code = serializers.ReadOnlyField()
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    def get_id(self, obj):
        return str(obj.id)
    
    def get_user(self, obj):
        return str(obj.user.id)
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'user', 'user_email', 'movement_id', 'amount', 
            'payment_method', 'status', 'qr_code', 'formatted_qr_code',
            'qr_validity', 'extra_data', 'sender_name', 'sender_bank',
            'sender_document', 'sender_account', 'created_at', 
            'updated_at', 'expires_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'movement_id', 'qr_code', 'formatted_qr_code',
            'sender_name', 'sender_bank', 'sender_document', 
            'sender_account', 'created_at', 'updated_at', 
            'completed_at'
        ]

class GenerateQRSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    extra_data = serializers.JSONField(required=False, default=dict)
    validity = serializers.CharField(max_length=20, default="1/00:00")
    detail = serializers.CharField(max_length=200, required=False)

class VerifyPaymentSerializer(serializers.Serializer):
    payment_id = serializers.CharField()

class PaymentStatusSerializer(serializers.Serializer):
    movement_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    detail = serializers.CharField()
    status = serializers.CharField()
    sender_name = serializers.CharField()
    sender_bank = serializers.CharField()
    sender_document = serializers.CharField()
    sender_account = serializers.CharField()
