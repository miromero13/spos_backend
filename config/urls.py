"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from user.views import UserViewSet, LoginAdminView, LoginCustomerView, RegisterCustomerView, VerifyEmailView, CheckTokenView, CustomerViewSet
from sale.views import SaleViewSet, CashRegisterViewSet
from inventory.views import CategoryViewSet, DiscountViewSet, ProductViewSet, PurchaseViewSet, RecommendationAdminView
from rest_framework.routers import DefaultRouter
from seed.views import SeedView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='User')
router.register(r'customers', CustomerViewSet, basename='Customer')
router.register(r'sales', SaleViewSet, basename='Sale')
router.register(r'cash_registers', CashRegisterViewSet, basename='CashRegister')
router.register(r'categories', CategoryViewSet, basename='Category')
router.register(r'discounts', DiscountViewSet, basename='Discount')
router.register(r'products', ProductViewSet, basename='Product')
router.register(r'purchases', PurchaseViewSet, basename='Purchase')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'), 
    path('api/auth/login-admin/', LoginAdminView.as_view(), name='login_admin'),
    path('api/auth/login-customer/', LoginCustomerView.as_view(), name='login_customer'),
    path('api/auth/register-customer/', RegisterCustomerView.as_view(), name='register_customer'),
    path('api/auth/verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('api/auth/check-token/', CheckTokenView.as_view(), name='check_token'),           
    path('api/', include(router.urls)),    
    path('api/seed/', SeedView.as_view(), name='seed'),
    path('products/<str:pk>/recommendations/', ProductViewSet.as_view({'get': 'recommendations'})),
    path('api/admin/generate_recommendations/', RecommendationAdminView.as_view(), name='generate_recommendations'),

]
