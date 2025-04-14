from rest_framework.permissions import BasePermission

class IsAdministrator(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'administrator'

class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'customer'

class IsCashier(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'cashier'

class IsAdminOrCashier(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['administrator', 'cashier']

class IsAdminOrCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['administrator', 'customer']

class IsAdminOrCustomerOrCashier(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['administrator', 'customer', 'cashier']