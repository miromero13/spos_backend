# recommendations.py
from collections import defaultdict
from django.db.models import Count
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class RecommendationEngine:
    @staticmethod
    def generate_frequent_pairs():
        """Genera asociaciones basadas en productos comprados juntos"""
        from sale.models import SaleDetail
        from user.models import ProductRecommendation
        
        # Obtener todos los pares de productos en las mismas ventas
        sales_with_multiple = SaleDetail.objects.values(
            'sale'
        ).annotate(
            product_count=Count('product')
        ).filter(
            product_count__gt=1
        ).values_list('sale', flat=True)

        product_pairs = defaultdict(int)
        
        for sale_id in sales_with_multiple:
            products = SaleDetail.objects.filter(
                sale_id=sale_id
            ).values_list('product', flat=True).distinct()
            
            products = list(products)
            for i in range(len(products)):
                for j in range(i+1, len(products)):
                    pair = tuple(sorted((products[i], products[j])))
                    product_pairs[pair] += 1

        # Guardar las asociaciones
        ProductRecommendation.objects.filter(
            recommendation_type='frequently_bought'
        ).delete()

        for (prod1, prod2), frequency in product_pairs.items():
            ProductRecommendation.objects.update_or_create(
                source_product_id=prod1,
                recommended_product_id=prod2,
                defaults={
                    'score': frequency,
                    'recommendation_type': 'frequently_bought'
                }
            )
            ProductRecommendation.objects.update_or_create(
                source_product_id=prod2,
                recommended_product_id=prod1,
                defaults={
                    'score': frequency,
                    'recommendation_type': 'frequently_bought'
                }
            )

    @staticmethod
    def generate_content_based_recommendations():
        """Recomendaciones basadas en similitud de contenido"""
        from .models import Product, ProductRecommendation
        
        products = Product.objects.filter(is_active=True)
        df = pd.DataFrame(list(products.values('id', 'name', 'description', 'category__name')))
        
        # Crear características combinadas
        df['content'] = df['name'] + ' ' + df['description'] + ' ' + df['category__name']
        
        # Vectorización TF-IDF
        tfidf = TfidfVectorizer(stop_words=['spanish', 'english'])
        tfidf_matrix = tfidf.fit_transform(df['content'])
        
        # Calcular similitud coseno
        cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
        
        # Guardar recomendaciones
        ProductRecommendation.objects.filter(
            recommendation_type='category'
        ).delete()

        for idx, row in df.iterrows():
            sim_scores = list(enumerate(cosine_sim[idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            
            for i, score in sim_scores[1:6]:  # Top 5 recomendaciones
                if score > 0.2:  # Umbral mínimo de similitud
                    ProductRecommendation.objects.update_or_create(
                        source_product_id=row['id'],
                        recommended_product_id=df.iloc[i]['id'],
                        defaults={
                            'score': float(score),
                            'recommendation_type': 'category'
                        }
                    )

    @staticmethod
    def get_recommendations(product_id, limit=4):
        """Obtiene recomendaciones para un producto"""
        from .models import ProductRecommendation, Product
        
        # Primero buscar recomendaciones frecuentes
        frequent_recs = ProductRecommendation.objects.filter(
            source_product_id=product_id,
            recommendation_type='frequently_bought'
        ).order_by('-score')[:limit]
        
        # Si no hay suficientes, complementar con recomendaciones por contenido
        if frequent_recs.count() < limit:
            content_recs = ProductRecommendation.objects.filter(
                source_product_id=product_id,
                recommendation_type='category'
            ).exclude(
                recommended_product_id__in=[r.recommended_product_id for r in frequent_recs]
            ).order_by('-score')[:limit - frequent_recs.count()]
            
            recommendations = list(frequent_recs) + list(content_recs)
        else:
            recommendations = frequent_recs
        
        # Asegurar que no se recomiende el mismo producto
        recommended_products = []
        seen_ids = set()
        
        for rec in recommendations:
            if rec.recommended_product_id != product_id and rec.recommended_product_id not in seen_ids:
                try:
                    product = Product.objects.get(id=rec.recommended_product_id, is_active=True)
                    recommended_products.append(product)
                    seen_ids.add(product.id)
                    if len(recommended_products) >= limit:
                        break
                except Product.DoesNotExist:
                    continue
        
        return recommended_products