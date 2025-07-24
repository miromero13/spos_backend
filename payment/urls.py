from django.urls import path
from . import views

urlpatterns = [
    path('generate-qr/', views.generate_qr_payment, name='generate_qr_payment'),
    path('verify-status/', views.verify_payment_status, name='verify_payment_status'),
    path('transactions/', views.get_payment_transactions, name='get_payment_transactions'),
    path('webhook/', views.veripagos_webhook, name='veripagos_webhook'),
]
