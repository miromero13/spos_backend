from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Q, Case, When, IntegerField, Value as V
from django.contrib.auth import authenticate

from user.serializers import LoginSerializer
from .permissions import (
    IsAdministrator,
    IsAdminOrCustomerOrCashier
)
from .models import User
from .serializers import UserSerializer
from .utils import send_verification_email, verify_token
from config.response import response, StandardResponseSerializerSuccess, StandardResponseSerializerSuccessList, StandardResponseSerializerError

@extend_schema(
    request=LoginSerializer,
    responses={
        200: StandardResponseSerializerSuccess,
        401: StandardResponseSerializerError,
        403: StandardResponseSerializerError
        }
)
class LoginAdminView(APIView):
    def post(self, request):
        email = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=email, password=password)

        if not user:
            return response(401, "Email o contraseña incorrectos")
        if not user.is_active:
            return response(403, "Cuenta inactiva")
        if user.role not in ['administrator', 'cashier']:
            return response(403, "Rol no autorizado")        

        token = RefreshToken.for_user(user)
        return response(
            200,
            "Login exitoso",
            data={
                "access": str(token.access_token),
                "refresh": str(token),
                "user": UserSerializer(user).data
            }
        )


@extend_schema(
    request=LoginSerializer,
    responses={
        200: StandardResponseSerializerSuccess,
        401: StandardResponseSerializerError,
        403: StandardResponseSerializerError
    }
)
class LoginCustomerView(APIView):
    def post(self, request):
        email = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=email, password=password)

        if not user:
            return response(401, "Credenciales inválidas")        
        if not user.email_verified:
            return response(403, "Debes verificar tu correo")        
        if not user.is_active:
            return response(403, "Cuenta inactiva")        
        if user.role != 'customer':
            return response(403, "Solo clientes pueden iniciar sesión aquí")

        token = RefreshToken.for_user(user)
        return response(
            200,
            "Login cliente exitoso",
            data={
                "access": str(token.access_token),
                "refresh": str(token)
            }
        )


@extend_schema(
    request=UserSerializer,
    responses={
        201: StandardResponseSerializerSuccess,
        400: StandardResponseSerializerError
    }
)
class RegisterCustomerView(APIView):
    def post(self, request):
        data = request.data.copy()
        data['role'] = 'customer'
        data['is_active'] = False

        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            send_verification_email(user)
            return response(
                201,
                "Cliente registrado correctamente. Revisa tu correo para activarlo.",
                data=UserSerializer(user).data  # opcional, si quieres retornar los datos
            )

        return response(
            400,
            "Errores de validación",
            error=serializer.errors
        )

@extend_schema(
    parameters=[
        OpenApiParameter(name="token", description="Token de verificación", required=True, type=str)
    ],
    responses={
        200: StandardResponseSerializerSuccess,
        400: StandardResponseSerializerError,
        404: StandardResponseSerializerError
    }
)
class VerifyEmailView(APIView):
    def get(self, request):
        token = request.query_params.get("token")
        email = verify_token(token)

        if not email:
            return response(400, "Token inválido o expirado")        

        try:
            user = User.objects.get(email=email)
            user.email_verified = True
            user.is_active = True
            user.save()
            return response(200, "Correo verificado con éxito")        
        except User.DoesNotExist:
            return response(404, "Usuario no encontrado")        


@extend_schema(
    responses={
        200: UserSerializer,
        403: StandardResponseSerializerError
    }
)
class CheckTokenView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrCustomerOrCashier]

    def get(self, request):
        user = request.user
        if not user.is_active:
            return response(403, "Cuenta inactiva")

        return response(
            200,
            "Token válido",
            data={  
                "id": user.id,  
                "name": user.name,
                "phone": user.phone,  
                "email": user.email,  
                "role": user.role  
            }
        )
    

@extend_schema(
    responses={
        200: UserSerializer,        
        400: StandardResponseSerializerError,
        404: StandardResponseSerializerError,
        500: StandardResponseSerializerError
    }
)
class UserViewSet(viewsets.ModelViewSet):    
    serializer_class = UserSerializer   
    authentication_classes = [JWTAuthentication] 
    permission_classes = [IsAdministrator]

    def create(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return response(
                201,
                "Usuario creado correctamente",
                data=UserSerializer(user).data
            )
        return response(
            400,
            "Errores de validación",
            error=serializer.errors
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(name='limit', description='Cantidad de resultados', required=False, type=int),
            OpenApiParameter(name='offset', description='Inicio del listado', required=False, type=int),
            OpenApiParameter(name='order', description='Campo de ordenamiento (ej: +name, -email)', required=False, type=str),
            OpenApiParameter(name='attr', description='Campo para filtrar (ej: name, role)', required=False, type=str),
            OpenApiParameter(name='value', description='Valor del campo a filtrar', required=False, type=str),
        ], 
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
            500: StandardResponseSerializerError
        }
    )
    def list(self, request):
        try:
            queryset = User.objects.filter(is_active=True, role__in=['administrator', 'cashier'])

            attr = request.query_params.get('attr')
            value = request.query_params.get('value')
            if attr and value and hasattr(User, attr):
                starts_with_filter = {f"{attr}__istartswith": value}
                contains_filter = {f"{attr}__icontains": value}
                queryset = queryset.filter(Q(**contains_filter))                
                queryset = queryset.annotate(
                    relevance=Case(
                        When(**starts_with_filter, then=V(0)),
                        default=V(1),
                        output_field=IntegerField()
                    )
                ).order_by('relevance')                
            elif attr and not hasattr(User, attr):
                return response(
                    400,
                    f"El campo '{attr}' no es válido para filtrado"
                )
            order = request.query_params.get('order')
            if order:
                try:
                    queryset = queryset.order_by(order)
                except Exception:
                    return response(
                        400,
                        f"No se pudo ordenar por '{order}'"
                    )

            limit = request.query_params.get('limit')
            offset = request.query_params.get('offset', 0)

            if limit is not None:
                try:
                    limit = int(limit)
                    offset = int(offset)
                    queryset = queryset[offset:offset+limit]
                except ValueError:
                    return response(
                        400,
                        "Los valores de limit y offset deben ser enteros"
                    )

            serializer = UserSerializer(queryset, many=True)
            return response(
                200,
                "Usuarios encontrados",
                data=serializer.data,
                count_data=len(queryset)
            )

        except Exception as e:
            return response(
                500,
                f"Error al obtener usuarios: {str(e)}"
            )

    def retrieve(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk, is_active=True).first()
            if not user:
                return response(404, "Usuario no encontrado")
            return response(
                200,
                "Usuario encontrado",
                data=UserSerializer(user).data
            )
        except User.DoesNotExist:
            return response(404, "Usuario no encontrado")

    def update(self, request, pk=None, partial=False):
        try:
            user = User.objects.get(pk=pk, is_active=True)
        except User.DoesNotExist:
            return response(404, "Usuario no encontrado")

        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return response(200, "Usuario actualizado", data=serializer.data)
        return response(400, "Errores de validación", error=serializer.errors)

    def destroy(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk, is_active=True).first()
            if not user:
                return response(404, "Usuario no encontrado")
            user.is_active = False
            user.save()
            return response(200, "Usuario eliminado correctamente")
        except User.DoesNotExist:
            return response(404, "Usuario no encontrado")
        
@extend_schema(
    responses={
        200: StandardResponseSerializerSuccess,
        400: StandardResponseSerializerError,
        404: StandardResponseSerializerError,
        500: StandardResponseSerializerError
    }
)
class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrCustomerOrCashier]

    def get_queryset(self):
        return User.objects.filter(is_active=True, role='customer')

    def create(self, request):
        data = request.data.copy()
        data['role'] = 'customer'
        data['is_active'] = False

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            send_verification_email(user)
            return response(
                201,
                "Cliente creado correctamente. Se envió un correo de verificación.",
                data=UserSerializer(user).data
            )
        return response(400, "Errores de validación", error=serializer.errors)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='limit', description='Cantidad de resultados', required=False, type=int),
            OpenApiParameter(name='offset', description='Inicio del listado', required=False, type=int),
            OpenApiParameter(name='order', description='Campo de ordenamiento (ej: +name, -email)', required=False, type=str),
            OpenApiParameter(name='attr', description='Campo para filtrar (ej: name, email)', required=False, type=str),
            OpenApiParameter(name='value', description='Valor del campo a filtrar', required=False, type=str),
        ],
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
            500: StandardResponseSerializerError
        }
    )
    def list(self, request):
        try:
            queryset = self.get_queryset()

            attr = request.query_params.get('attr')
            value = request.query_params.get('value')
            if attr and value and hasattr(User, attr):
                starts_with_filter = {f"{attr}__istartswith": value}
                contains_filter = {f"{attr}__icontains": value}
                queryset = queryset.filter(Q(**contains_filter))                
                queryset = queryset.annotate(
                    relevance=Case(
                        When(**starts_with_filter, then=V(0)),
                        default=V(1),
                        output_field=IntegerField()
                    )
                ).order_by('relevance')
            elif attr and not hasattr(User, attr):
                return response(400, f"El campo '{attr}' no es válido para filtrado")

            order = request.query_params.get('order')
            if order:
                try:
                    queryset = queryset.order_by(order)
                except:
                    return response(400, f"No se pudo ordenar por '{order}'")

            limit = request.query_params.get('limit')
            offset = request.query_params.get('offset', 0)
            if limit is not None:
                try:
                    limit = int(limit)
                    offset = int(offset)
                    queryset = queryset[offset:offset+limit]
                except ValueError:
                    return response(400, "Los valores de limit y offset deben ser enteros")

            serializer = self.get_serializer(queryset, many=True)
            return response(200, "Clientes encontrados", data=serializer.data, count_data=len(queryset))

        except Exception as e:
            return response(500, f"Error al obtener clientes: {str(e)}")

    def retrieve(self, request, pk=None):
        try:
            cliente = self.get_queryset().filter(pk=pk).first()
            if not cliente:
                return response(404, "Cliente no encontrado")
            return response(200, "Cliente encontrado", data=self.get_serializer(cliente).data)
        except Exception:
            return response(500, "Error al obtener cliente")

    def update(self, request, pk=None, partial=False):
        try:
            cliente = self.get_queryset().filter(pk=pk).first()
            if not cliente:
                return response(404, "Cliente no encontrado")

            serializer = self.get_serializer(cliente, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response(200, "Cliente actualizado", data=serializer.data)
            return response(400, "Errores de validación", error=serializer.errors)
        except Exception:
            return response(500, "Error al actualizar cliente")

    def destroy(self, request, pk=None):
        try:
            cliente = self.get_queryset().filter(pk=pk).first()
            if not cliente:
                return response(404, "Cliente no encontrado")

            cliente.is_active = False
            cliente.save()
            return response(200, "Cliente deshabilitado correctamente")
        except Exception:
            return response(500, "Error al deshabilitar cliente")