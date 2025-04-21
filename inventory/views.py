from rest_framework import viewsets
from django.db import transaction
from django.db.models import Q, Case, When, IntegerField, Value as V
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, OpenApiParameter

from inventory.models import Product, Category, Discount, Purchase, PurchaseDetail
from inventory.serializers import ProductSerializer, CategorySerializer, DiscountSerializer, PurchaseSerializer
from config.response import response, StandardResponseSerializerSuccessList, StandardResponseSerializerError, StandardResponseSerializerSuccess
from user.permissions import IsAdminOrCustomerOrCashier

@extend_schema(
    request=CategorySerializer,
    responses={
        201: StandardResponseSerializerSuccess,
        400: StandardResponseSerializerError,
        404: StandardResponseSerializerError
    }
)
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrCustomerOrCashier]

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = CategorySerializer(data=data)
        if serializer.is_valid():
            category = serializer.save()
            return response(201, "Categoría creada exitosamente", data=CategorySerializer(category).data)
        return response(400, "Errores de validación", error=serializer.errors)
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='limit', description='Cantidad de resultados', required=False, type=int),
            OpenApiParameter(name='offset', description='Inicio del listado', required=False, type=int),
            OpenApiParameter(name='order', description='Campo de ordenamiento (ej: +name, -email)', required=False, type=str),
            OpenApiParameter(name='attr', description='Campo para filtrar (ej: name, description)', required=False, type=str),
            OpenApiParameter(name='value', description='Valor del campo a filtrar', required=False, type=str),
        ], 
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
            500: StandardResponseSerializerError
        }
    )
    def list(self, request, limit=None, offset=0, order=None, attr=None, value=None):
        try:
            # Query básica para obtener todas las categorías
            queryset = Category.objects.all()
            
            # Filtrado por parámetros adicionales
            if attr and value and hasattr(Category, attr):
                # Filtrado usando "contains" o "starts with"
                starts_with_filter = {f"{attr}__istartswith": value}
                contains_filter = {f"{attr}__icontains": value}
                queryset = queryset.filter(Q(**contains_filter))
                
                # Ordenar por relevancia si el valor empieza con el texto
                queryset = queryset.annotate(
                    relevance=Case(
                        When(**starts_with_filter, then=V(0)),
                        default=V(1),
                        output_field=IntegerField()
                    )
                ).order_by('relevance')                
            elif attr and not hasattr(Category, attr):
                return response(
                    400,
                    f"El campo '{attr}' no es válido para filtrado"
                )   
            
            # Ordenar resultados
            order = request.query_params.get('order')
            if order:
                try:
                    queryset = queryset.order_by(order)
                except Exception:
                    return response(
                        400,
                        f"No se pudo ordenar por '{order}'"
                    )   
                
            # Paginación: limit y offset
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
                
            # Serializar datos
            serializer = CategorySerializer(queryset, many=True)
            return response(
                200,
                "Categorías encontradas",
                data=serializer.data,
                count_data=len(queryset)
            )
        except Exception as e:
            return response(
                500,
                f"Error al obtener categorías: {str(e)}"
            )
        
    def retrieve(self, request, pk=None):
        try:
            category = Category.objects.get(pk=pk)
            serializer = CategorySerializer(category)
            return response(200, "Categoría encontrada", data=serializer.data)
        except Category.DoesNotExist:
            return response(404, "Categoría no encontrada")
        
    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        if category.products.exists():
            return response(400, "La categoría no puede ser eliminada porque tiene productos asociados")
        category.delete()
        return response(200, "Categoría eliminada correctamente")

@extend_schema(
    request=DiscountSerializer,
    responses={
        201: StandardResponseSerializerSuccess,
        400: StandardResponseSerializerError,
        404: StandardResponseSerializerError
    }
)
class DiscountViewSet(viewsets.ModelViewSet):
    queryset = Discount.objects.all()
    serializer_class = DiscountSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrCustomerOrCashier]

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = DiscountSerializer(data=data)
        if serializer.is_valid():
            discount = serializer.save()
            return response(201, "Descuento creado exitosamente", data=DiscountSerializer(discount).data)
        return response(400, "Errores de validación", error=serializer.errors)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='limit', description='Cantidad de resultados', required=False, type=int),
            OpenApiParameter(name='offset', description='Inicio del listado', required=False, type=int),
            OpenApiParameter(name='order', description='Campo de ordenamiento (ej: +name, -email)', required=False, type=str),
            OpenApiParameter(name='attr', description='Campo para filtrar (ej: name, description)', required=False, type=str),
            OpenApiParameter(name='value', description='Valor del campo a filtrar', required=False, type=str),
        ], 
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
            500: StandardResponseSerializerError
        }
    )
    def list(self, request, limit=None, offset=0, order=None, attr=None, value=None):
        try:
            # Query básica para obtener todas las descuentos
            queryset = Discount.objects.all()
            
            # Filtrado por parámetros adicionales
            if attr and value and hasattr(Discount, attr):
                # Filtrado usando "contains" o "starts with"
                starts_with_filter = {f"{attr}__istartswith": value}
                contains_filter = {f"{attr}__icontains": value}
                queryset = queryset.filter(Q(**contains_filter))
                
                # Ordenar por relevancia si el valor empieza con el texto
                queryset = queryset.annotate(
                    relevance=Case(
                        When(**starts_with_filter, then=V(0)),
                        default=V(1),
                        output_field=IntegerField()
                    )
                ).order_by('relevance')                
            elif attr and not hasattr(Discount, attr):
                return response(
                    400,
                    f"El campo '{attr}' no es válido para filtrado"
                )   
            
            # Ordenar resultados
            order = request.query_params.get('order')
            if order:
                try:
                    queryset = queryset.order_by(order)
                except Exception:
                    return response(
                        400,
                        f"No se pudo ordenar por '{order}'"
                    )   
                
            # Paginación: limit y offset
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
                
            # Serializar datos
            serializer = DiscountSerializer(queryset, many=True)
            return response(
                200,
                "Descuentos encontrados",
                data=serializer.data,
                count_data=len(queryset)
            )
        except Exception as e:
            return response(
                500,
                f"Error al obtener descuentos: {str(e)}"
            )
        
    def retrieve(self, request, pk=None):
        try:
            discount = Discount.objects.get(pk=pk)
            serializer = DiscountSerializer(discount)
            return response(200, "Descuento encontrado", data=serializer.data)
        except Discount.DoesNotExist:
            return response(404, "Descuento no encontrado")
        
    def destroy(self, request, *args, **kwargs):
        discount = self.get_object()
        if discount.products.exists():
            return response(400, "El descuento no puede ser eliminado porque tiene productos asociados")
        discount.delete()
        return response(200, "Descuento eliminado correctamente")

@extend_schema(
    request=ProductSerializer,
    responses={
        201: StandardResponseSerializerSuccess,
        400: StandardResponseSerializerError,
        404: StandardResponseSerializerError
    }
)
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrCustomerOrCashier]

    def create(self, request, *args, **kwargs):
        data = request.data
        print("data", data)
        serializer = ProductSerializer(data=data)
        if serializer.is_valid():
            product = serializer.save()
            return response(201, "Producto creado exitosamente", data=ProductSerializer(product).data)
        return response(400, "Errores de validación", error=serializer.errors)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ProductSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return response(200, "Producto actualizado", data=serializer.data)
        return response(400, "Errores de validación", error=serializer.errors)
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='limit', description='Cantidad de resultados', required=False, type=int),
            OpenApiParameter(name='offset', description='Inicio del listado', required=False, type=int),
            OpenApiParameter(name='order', description='Campo de ordenamiento (ej: +name, -email)', required=False, type=str),
            OpenApiParameter(name='attr', description='Campo para filtrar (ej: name, description)', required=False, type=str),
            OpenApiParameter(name='value', description='Valor del campo a filtrar', required=False, type=str),
        ], 
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
            500: StandardResponseSerializerError
        }
    )
    def list(self, request, limit=None, offset=0, order=None, attr=None, value=None):
        try:
            # Query básica para obtener todas las descuentos
            queryset = Product.objects.all()
            
            # Filtrado por parámetros adicionales
            if attr and value and hasattr(Product, attr):
                # Filtrado usando "contains" o "starts with"
                starts_with_filter = {f"{attr}__istartswith": value}
                contains_filter = {f"{attr}__icontains": value}
                queryset = queryset.filter(Q(**contains_filter))
                
                # Ordenar por relevancia si el valor empieza con el texto
                queryset = queryset.annotate(
                    relevance=Case(
                        When(**starts_with_filter, then=V(0)),
                        default=V(1),
                        output_field=IntegerField()
                    )
                ).order_by('relevance')                
            elif attr and not hasattr(Product, attr):
                return response(
                    400,
                    f"El campo '{attr}' no es válido para filtrado"
                )   
            
            # Ordenar resultados
            order = request.query_params.get('order')
            if order:
                try:                    
                    queryset = queryset.order_by(order)
                except Exception:
                    return response(
                        400,
                        f"No se pudo ordenar por '{order}'"
                    )   
                
            # Paginación: limit y offset
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
                
            # Serializar datos
            serializer = ProductSerializer(queryset, many=True)
            return response(
                200,
                "Productos encontrados",
                data=serializer.data,
                count_data=len(queryset)
            )
        except Exception as e:
            return response(
                500,
                f"Error al obtener productos: {str(e)}"
            )
        
    def retrieve(self, request, pk=None):
        try:
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product)
            return response(200, "Producto encontrado", data=serializer.data)
        except Product.DoesNotExist:
            return response(404, "Producto no encontrado")
        
    def destroy(self, request, *args, **kwargs):
        product = self.get_object()
        if product.stock > 0:
            return response(400, "El producto no puede ser eliminado porque tiene stock")
        product.delete()
        return response(200, "Producto eliminado correctamente")

class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrCustomerOrCashier]

    # No permitir la edición ni la eliminación de compras
    def update(self, request, *args, **kwargs):
        return response(405, "Las compras no se pueden editar")

    def destroy(self, request, *args, **kwargs):
        return response(405, "Las compras no se pueden eliminar")

    def create(self, request, *args, **kwargs):
        # Iniciar una transacción
        with transaction.atomic():
            try:
                data = request.data
                reason = data.get('reason')
                code = data.get('code')
                details = data.get('details')

                if not details:
                    return response(400, "Detalles de la compra son requeridos")

                # Crear la compra
                purchase = Purchase.objects.create(
                    reason=reason,
                    code=code,
                    total_amount=0  # Este campo se actualizará después
                )

                total_amount = 0
                for detail in details:
                    product_id = detail.get('product')
                    quantity = detail.get('quantity')
                    price = detail.get('price')

                    if not product_id or not quantity or not price:
                        return response(400, "Todos los campos de detalle son requeridos")

                    # Obtener el producto y verificar el stock
                    product = Product.objects.get(id=product_id)

                    # Validación de stock
                    if product.stock < quantity:
                        return response(400, f"Stock insuficiente para el producto {product.name}")

                    # Crear detalle de la compra
                    subtotal = quantity * price
                    PurchaseDetail.objects.create(
                        product=product,
                        purchase=purchase,
                        quantity=quantity,
                        price=price,
                        subtotal=subtotal
                    )

                    # Actualizar el stock del producto
                    product.stock += quantity  # Aumentamos el stock con la cantidad comprada
                    product.save()

                    total_amount += subtotal

                # Actualizar el monto total de la compra
                purchase.total_amount = total_amount
                purchase.save()

                return response(201, "Compra creada exitosamente", data=PurchaseSerializer(purchase).data)

            except Exception as e:
                # Si algo sale mal, revertir la transacción
                transaction.rollback()
                return response(500, f"Error al procesar la compra: {str(e)}")

    @extend_schema(
        parameters=[
            OpenApiParameter(name='limit', description='Cantidad de resultados', required=False, type=int),
            OpenApiParameter(name='offset', description='Inicio del listado', required=False, type=int),
            OpenApiParameter(name='order', description='Campo de ordenamiento (ej: +name, -email)', required=False, type=str),
            OpenApiParameter(name='attr', description='Campo para filtrar (ej: code, paid_amount)', required=False, type=str),
            OpenApiParameter(name='value', description='Valor del campo a filtrar', required=False, type=str),
        ], 
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
            500: StandardResponseSerializerError
        }
    )
    def list(self, request, limit=None, offset=0, order=None, attr=None, value=None):
        try:
            # Query básica para obtener todas las compras
            queryset = Purchase.objects.all()
            
            # Filtrado por parámetros adicionales
            if attr and value and hasattr(Purchase, attr):
                # Filtrado usando "contains" o "starts with"
                starts_with_filter = {f"{attr}__istartswith": value}
                contains_filter = {f"{attr}__icontains": value}
                queryset = queryset.filter(Q(**contains_filter))
                
                # Ordenar por relevancia si el valor empieza con el texto
                queryset = queryset.annotate(
                    relevance=Case(
                        When(**starts_with_filter, then=V(0)),
                        default=V(1),
                        output_field=IntegerField()
                    )
                ).order_by('relevance')                
            elif attr and not hasattr(Purchase, attr):
                return response(
                    400,
                    f"El campo '{attr}' no es válido para filtrado"
                )   
            
            # Ordenar resultados
            order = request.query_params.get('order')
            if order:
                try:
                    queryset = queryset.order_by(order)
                except Exception:
                    return response(
                        400,
                        f"No se pudo ordenar por '{order}'"
                    )   
                
            # Paginación: limit y offset
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
                
            # Serializar datos
            serializer = PurchaseSerializer(queryset, many=True)
            return response(
                200,
                "Compras encontradas",
                data=serializer.data,
                count_data=len(queryset)
            )
        except Exception as e:
            return response(
                500,
                f"Error al obtener compras: {str(e)}"
            )
        
    def retrieve(self, request, pk=None):
        try:
            purchase = Purchase.objects.get(pk=pk)
            serializer = PurchaseSerializer(purchase)
            return response(200, "Compra encontrada", data=serializer.data)
        except Purchase.DoesNotExist:
            return response(404, "Compra no encontrada")