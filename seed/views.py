from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from decimal import Decimal
from datetime import date, timedelta
import random
import pandas as pd

from user.models import User
from inventory.models import Category, Product, Discount
from config.response import response

class SeedView(APIView):
    
    def create_products_dataset(self):
        """Crear dataset de 300 productos con pandas y URLs de imágenes reales"""
        
        # Definir productos por categoría con URLs de imágenes reales
        products_data = {
            'Smartphones': [
                # iPhones
                {'name': 'iPhone 15 Pro Max', 'purchase_price': 7500, 'sale_price': 8900, 'stock': 15, 'description': 'iPhone 15 Pro Max con chip A17 Pro y titanio', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-pro-max-naturaltitanium-pdp-image-position-1a_AV1?wid=750&hei=750'},
                {'name': 'iPhone 15 Pro', 'purchase_price': 6500, 'sale_price': 7800, 'stock': 20, 'description': 'iPhone 15 Pro con chip A17 Pro', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-pro-naturaltitanium-pdp-image-position-1a_AV1?wid=750&hei=750'},
                {'name': 'iPhone 15', 'purchase_price': 5200, 'sale_price': 6200, 'stock': 25, 'description': 'iPhone 15 con chip A16 Bionic', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-pink-pdp-image-position-1a_AV1?wid=750&hei=750'},
                {'name': 'iPhone 14', 'purchase_price': 4800, 'sale_price': 5800, 'stock': 30, 'description': 'iPhone 14 con cámara dual avanzada', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-14-blue-pdp-image-position-1a_AV1?wid=750&hei=750'},
                {'name': 'iPhone 13', 'purchase_price': 3800, 'sale_price': 4600, 'stock': 35, 'description': 'iPhone 13 con chip A15 Bionic', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-13-pink-pdp-image-position-1a_AV1?wid=750&hei=750'},
                
                # Samsung Galaxy
                {'name': 'Samsung Galaxy S24 Ultra', 'purchase_price': 7200, 'sale_price': 8500, 'stock': 12, 'description': 'Galaxy S24 Ultra con S Pen y IA', 'photo_url': 'https://images.samsung.com/is/image/samsung/p6pim/pe/2401/gallery/pe-galaxy-s24-ultra-s928-sm-s928bztqpeo-thumb-539573459'},
                {'name': 'Samsung Galaxy S24', 'purchase_price': 5800, 'sale_price': 6900, 'stock': 18, 'description': 'Galaxy S24 con inteligencia artificial', 'photo_url': 'https://images.samsung.com/is/image/samsung/p6pim/pe/2401/gallery/pe-galaxy-s24-s921-sm-s921bzvcpeo-thumb-539572949'},
                {'name': 'Samsung Galaxy S23', 'purchase_price': 4800, 'sale_price': 5700, 'stock': 22, 'description': 'Galaxy S23 con cámara profesional', 'photo_url': 'https://images.samsung.com/is/image/samsung/p6pim/pe/galaxy-s23/gallery/pe-galaxy-s23-s911-sm-s911bzgcpeo-thumb-534850774'},
                {'name': 'Samsung Galaxy A54', 'purchase_price': 2800, 'sale_price': 3400, 'stock': 40, 'description': 'Galaxy A54 con cámara triple', 'photo_url': 'https://images.samsung.com/is/image/samsung/p6pim/pe/galaxy-a54-5g/gallery/pe-galaxy-a54-5g-a546-sm-a546elvlpeo-thumb-537122530'},
                {'name': 'Samsung Galaxy A34', 'purchase_price': 2200, 'sale_price': 2700, 'stock': 45, 'description': 'Galaxy A34 económico y funcional', 'photo_url': 'https://images.samsung.com/is/image/samsung/p6pim/pe/galaxy-a34-5g/gallery/pe-galaxy-a34-5g-a346-sm-a346mlvbpeo-thumb-537122408'},
                
                # Xiaomi
                {'name': 'Xiaomi 14 Ultra', 'purchase_price': 6200, 'sale_price': 7300, 'stock': 10, 'description': 'Xiaomi 14 Ultra con Leica', 'photo_url': 'https://i01.appmifile.com/v1/MI_18455B3E4DA706226CF7535A58E875F0267/pms_1710316855.91532602.png'},
                {'name': 'Xiaomi Redmi Note 13 Pro', 'purchase_price': 2400, 'sale_price': 2900, 'stock': 35, 'description': 'Redmi Note 13 Pro con cámara de 200MP', 'photo_url': 'https://i01.appmifile.com/v1/MI_18455B3E4DA706226CF7535A58E875F0267/pms_1697602351.49997890.png'},
                {'name': 'Xiaomi Redmi Note 13', 'purchase_price': 1800, 'sale_price': 2200, 'stock': 50, 'description': 'Redmi Note 13 relación precio-calidad', 'photo_url': 'https://i01.appmifile.com/v1/MI_18455B3E4DA706226CF7535A58E875F0267/pms_1697602351.49997891.png'},
                {'name': 'Xiaomi POCO X5 Pro', 'purchase_price': 2600, 'sale_price': 3100, 'stock': 28, 'description': 'POCO X5 Pro gaming phone', 'photo_url': 'https://i01.appmifile.com/v1/MI_18455B3E4DA706226CF7535A58E875F0267/pms_1676879725.74745464.png'},
                
                # Otros
                {'name': 'Google Pixel 8 Pro', 'purchase_price': 5800, 'sale_price': 6800, 'stock': 15, 'description': 'Pixel 8 Pro con IA de Google', 'photo_url': 'https://lh3.googleusercontent.com/9KPPjhS29wy1XaPIAHPGBZeOyv6Xq5aN7vVjD9kQHjD9gB2QN_jZlOWUEjm8zD4'},
                {'name': 'OnePlus 11', 'purchase_price': 4200, 'sale_price': 5000, 'stock': 20, 'description': 'OnePlus 11 con carga rápida', 'photo_url': 'https://oasis.opstatics.com/content/dam/oasis/page/2023/global/product/11/pc/green.png'},
                {'name': 'Huawei P60 Pro', 'purchase_price': 4800, 'sale_price': 5600, 'stock': 18, 'description': 'Huawei P60 Pro con cámara Leica', 'photo_url': 'https://consumer.huawei.com/content/dam/huawei-cbg-site/common/mkt/pdp/phones/p60-pro/img/pc/huawei-p60-pro-black.png'}
            ],
            
            'Laptops': [
                # MacBooks
                {'name': 'MacBook Pro 16" M3 Max', 'purchase_price': 18500, 'sale_price': 21500, 'stock': 5, 'description': 'MacBook Pro 16" con chip M3 Max', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mbp16-spacegray-select-202310?wid=750&hei=750'},
                {'name': 'MacBook Pro 14" M3 Pro', 'purchase_price': 14500, 'sale_price': 16800, 'stock': 8, 'description': 'MacBook Pro 14" con chip M3 Pro', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mbp14-spacegray-select-202310?wid=750&hei=750'},
                {'name': 'MacBook Air 15" M3', 'purchase_price': 10500, 'sale_price': 12200, 'stock': 12, 'description': 'MacBook Air 15" con chip M3', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mba15-midnight-select-202306?wid=750&hei=750'},
                {'name': 'MacBook Air 13" M3', 'purchase_price': 8500, 'sale_price': 9800, 'stock': 15, 'description': 'MacBook Air 13" con chip M3', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mba13-midnight-select-202402?wid=750&hei=750'},
                
                # Dell
                {'name': 'Dell XPS 17', 'purchase_price': 12000, 'sale_price': 14200, 'stock': 6, 'description': 'Dell XPS 17 4K OLED', 'photo_url': 'https://i.dell.com/is/image/DellContent/content/dam/ss2/product-images/dell-client-products/notebooks/xps-notebooks/xps-17-9730/media-gallery/silver/notebook-xps-17-9730-nt-silver-gallery-4.psd'},
                {'name': 'Dell XPS 15', 'purchase_price': 9500, 'sale_price': 11200, 'stock': 10, 'description': 'Dell XPS 15 premium', 'photo_url': 'https://i.dell.com/is/image/DellContent/content/dam/ss2/product-images/dell-client-products/notebooks/xps-notebooks/xps-15-9530/media-gallery/silver/notebook-xps-15-9530-nt-silver-gallery-4.psd'},
                {'name': 'Dell XPS 13', 'purchase_price': 7200, 'sale_price': 8500, 'stock': 12, 'description': 'Dell XPS 13 ultraportátil', 'photo_url': 'https://i.dell.com/is/image/DellContent/content/dam/ss2/product-images/dell-client-products/notebooks/xps-notebooks/xps-13-9315/media-gallery/silver/notebook-xps-13-9315-nt-silver-gallery-4.psd'},
                {'name': 'Dell Inspiron 15 3000', 'purchase_price': 3200, 'sale_price': 3900, 'stock': 25, 'description': 'Dell Inspiron 15 económica', 'photo_url': 'https://i.dell.com/is/image/DellContent/content/dam/ss2/product-images/dell-client-products/notebooks/inspiron-notebooks/inspiron-15-3520/media-gallery/silver/notebook-inspiron-15-3520-nt-silver-gallery-4.psd'},
                
                # Lenovo
                {'name': 'Lenovo ThinkPad X1 Carbon', 'purchase_price': 11500, 'sale_price': 13200, 'stock': 8, 'description': 'ThinkPad X1 Carbon empresarial', 'photo_url': 'https://p1-ofp.static.pub/fes/cms/2023/08/14/n7c8rbyf2n8pzsai2bwuu93l3c7tkx832016.png'},
                {'name': 'Lenovo ThinkPad T14', 'purchase_price': 7800, 'sale_price': 9200, 'stock': 12, 'description': 'ThinkPad T14 profesional', 'photo_url': 'https://p1-ofp.static.pub/fes/cms/2023/05/24/vu1wqkpqeudqnwb7a6zb0zl9f7o2pe339469.png'},
                {'name': 'Lenovo IdeaPad Gaming 3', 'purchase_price': 4800, 'sale_price': 5600, 'stock': 15, 'description': 'IdeaPad Gaming 3 para juegos', 'photo_url': 'https://p1-ofp.static.pub/fes/cms/2023/04/13/lhmzugkcbvjr1v3i2hvmjg1n8dqaav639008.png'},
                
                # HP
                {'name': 'HP Spectre x360 16', 'purchase_price': 9800, 'sale_price': 11500, 'stock': 7, 'description': 'HP Spectre x360 16 convertible', 'photo_url': 'https://ssl-product-images.www8-hp.com/digmedialib/prodimg/lowres/c08186267.png'},
                {'name': 'HP EliteBook 840 G10', 'purchase_price': 8500, 'sale_price': 9900, 'stock': 10, 'description': 'HP EliteBook 840 empresarial', 'photo_url': 'https://ssl-product-images.www8-hp.com/digmedialib/prodimg/lowres/c08186334.png'},
                {'name': 'HP Pavilion 15', 'purchase_price': 3800, 'sale_price': 4500, 'stock': 20, 'description': 'HP Pavilion 15 uso general', 'photo_url': 'https://ssl-product-images.www8-hp.com/digmedialib/prodimg/lowres/c08186342.png'},
                
                # ASUS
                {'name': 'ASUS ROG Zephyrus G16', 'purchase_price': 15500, 'sale_price': 18200, 'stock': 5, 'description': 'ASUS ROG Zephyrus G16 gaming', 'photo_url': 'https://dlcdnwebimgs.asus.com/gain/0c67c84c-d191-48a7-b7a2-c1bb39c1e6b7/'},
                {'name': 'ASUS ZenBook 14', 'purchase_price': 6200, 'sale_price': 7300, 'stock': 15, 'description': 'ASUS ZenBook 14 ultrabook', 'photo_url': 'https://dlcdnwebimgs.asus.com/gain/0c67c84c-d191-48a7-b7a2-c1bb39c1e6b8/'},
                {'name': 'ASUS VivoBook 15', 'purchase_price': 3500, 'sale_price': 4200, 'stock': 25, 'description': 'ASUS VivoBook 15 económica', 'photo_url': 'https://dlcdnwebimgs.asus.com/gain/0c67c84c-d191-48a7-b7a2-c1bb39c1e6b9/'},
                
                # MSI
                {'name': 'MSI Creator Z17', 'purchase_price': 14200, 'sale_price': 16500, 'stock': 4, 'description': 'MSI Creator Z17 para creadores', 'photo_url': 'https://asset.msi.com/resize/image/global/product/product_1642741799b3a00a7c2e7bda6da7cce62a29d63eb1.png62405b38c58fe0f07fcef2367d8a9ba1/1024.png'},
                {'name': 'MSI Katana 15', 'purchase_price': 5800, 'sale_price': 6800, 'stock': 12, 'description': 'MSI Katana 15 gaming', 'photo_url': 'https://asset.msi.com/resize/image/global/product/product_1642741800b3a00a7c2e7bda6da7cce62a29d63eb2.png62405b38c58fe0f07fcef2367d8a9ba2/1024.png'}
            ],
            
            'Tablets': [
                # iPads
                {'name': 'iPad Pro 12.9" M4', 'purchase_price': 8500, 'sale_price': 9800, 'stock': 8, 'description': 'iPad Pro 12.9" con chip M4', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-pro-13-select-wifi-spacegray-202405?wid=750&hei=750'},
                {'name': 'iPad Pro 11" M4', 'purchase_price': 6500, 'sale_price': 7600, 'stock': 12, 'description': 'iPad Pro 11" con chip M4', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-pro-11-select-wifi-spacegray-202405?wid=750&hei=750'},
                {'name': 'iPad Air 11" M2', 'purchase_price': 4800, 'sale_price': 5600, 'stock': 15, 'description': 'iPad Air 11" con chip M2', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-air-11-select-wifi-purple-202405?wid=750&hei=750'},
                {'name': 'iPad Air 13" M2', 'purchase_price': 5200, 'sale_price': 6100, 'stock': 12, 'description': 'iPad Air 13" con chip M2', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-air-13-select-wifi-purple-202405?wid=750&hei=750'},
                {'name': 'iPad 10.9"', 'purchase_price': 3200, 'sale_price': 3800, 'stock': 20, 'description': 'iPad 10.9" básico', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-10th-gen-select-wifi-blue-202212?wid=750&hei=750'},
                {'name': 'iPad mini 6', 'purchase_price': 3800, 'sale_price': 4500, 'stock': 18, 'description': 'iPad mini 6 portátil', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-mini-select-wifi-purple-202109?wid=750&hei=750'},
                
                # Samsung Tablets
                {'name': 'Samsung Galaxy Tab S9 Ultra', 'purchase_price': 7800, 'sale_price': 9100, 'stock': 6, 'description': 'Galaxy Tab S9 Ultra con S Pen', 'photo_url': 'https://images.samsung.com/is/image/samsung/p6pim/pe/galaxy-tab-s9-ultra/gallery/pe-galaxy-tab-s9-ultra-x910-sm-x910nzaepeo-thumb-537657946'},
                {'name': 'Samsung Galaxy Tab S9', 'purchase_price': 4800, 'sale_price': 5600, 'stock': 12, 'description': 'Galaxy Tab S9 premium', 'photo_url': 'https://images.samsung.com/is/image/samsung/p6pim/pe/galaxy-tab-s9/gallery/pe-galaxy-tab-s9-x710-sm-x710nzaepeo-thumb-537657823'},
                {'name': 'Samsung Galaxy Tab A8', 'purchase_price': 1800, 'sale_price': 2200, 'stock': 25, 'description': 'Galaxy Tab A8 económica', 'photo_url': 'https://images.samsung.com/is/image/samsung/p6pim/pe/galaxy-tab-a8/gallery/pe-galaxy-tab-a8-x205-sm-x205nzaapeo-thumb-537122223'},
                
                # Huawei Tablets
                {'name': 'Huawei MatePad Pro 12.6"', 'purchase_price': 4200, 'sale_price': 4900, 'stock': 10, 'description': 'MatePad Pro con M-Pencil', 'photo_url': 'https://consumer.huawei.com/content/dam/huawei-cbg-site/common/mkt/pdp/tablets/matepad-pro-12-6-2021/img/pc/huawei-matepad-pro-12-6-grey.png'},
                {'name': 'Huawei MatePad 11"', 'purchase_price': 2800, 'sale_price': 3300, 'stock': 15, 'description': 'MatePad 11" premium', 'photo_url': 'https://consumer.huawei.com/content/dam/huawei-cbg-site/common/mkt/pdp/tablets/matepad-11-2023/img/pc/huawei-matepad-11-space-grey.png'},
                
                # Lenovo Tablets
                {'name': 'Lenovo Tab P12 Pro', 'purchase_price': 3800, 'sale_price': 4500, 'stock': 8, 'description': 'Tab P12 Pro OLED', 'photo_url': 'https://p1-ofp.static.pub/fes/cms/2023/08/14/n7c8rbyf2n8pzsai2bwuu93l3c7tkx832023.png'},
                {'name': 'Lenovo Tab M10 Plus', 'purchase_price': 1200, 'sale_price': 1500, 'stock': 30, 'description': 'Tab M10 Plus básica', 'photo_url': 'https://p1-ofp.static.pub/fes/cms/2023/08/14/n7c8rbyf2n8pzsai2bwuu93l3c7tkx832024.png'}
            ],
            
            'Audio': [
                # Auriculares Premium
                {'name': 'Sony WH-1000XM5', 'purchase_price': 2200, 'sale_price': 2800, 'stock': 25, 'description': 'Auriculares con cancelación de ruido líder', 'photo_url': 'https://sony.scene7.com/is/image/sonyglobalsolutions/wh-1000xm5_Primary_image?$categorypdpnav$&fmt=png-alpha'},
                {'name': 'Bose QuietComfort Ultra', 'purchase_price': 2800, 'sale_price': 3400, 'stock': 20, 'description': 'Bose QC Ultra premium', 'photo_url': 'https://assets.bose.com/content/dam/cloudassets/Bose_DAM/Web/consumer_electronics/global/products/headphones/qc_ultra_headphones/product_silo_images/QC_Ultra_Headphones_Black_EC_Hero_1920x1080.png'},
                {'name': 'AirPods Pro 2', 'purchase_price': 1800, 'sale_price': 2200, 'stock': 35, 'description': 'AirPods Pro 2da generación', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/MQD83?wid=750&hei=750'},
                {'name': 'AirPods Max', 'purchase_price': 3800, 'sale_price': 4500, 'stock': 12, 'description': 'AirPods Max over-ear', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/airpods-max-select-spacegray-202011?wid=750&hei=750'},
                {'name': 'Sennheiser HD 660S', 'purchase_price': 3200, 'sale_price': 3800, 'stock': 8, 'description': 'Sennheiser HD 660S audiófilo', 'photo_url': 'https://en-us.sennheiser.com/img/3838/HD_660_S_01_sq_sennheiser.png'},
                
                # Parlantes Bluetooth
                {'name': 'JBL Flip 6', 'purchase_price': 680, 'sale_price': 850, 'stock': 40, 'description': 'JBL Flip 6 resistente al agua', 'photo_url': 'https://ca.jbl.com/dw/image/v2/BFND_PRD/on/demandware.static/-/Sites-masterCatalog_Harman/default/dw497b5b9b/pdp/JBL_FLIP6_HERO_BLACK_0072_x1-1605x1605px.png'},
                {'name': 'JBL Charge 5', 'purchase_price': 1200, 'sale_price': 1500, 'stock': 30, 'description': 'JBL Charge 5 powerbank', 'photo_url': 'https://ca.jbl.com/dw/image/v2/BFND_PRD/on/demandware.static/-/Sites-masterCatalog_Harman/default/dw87d1e91e/pdp/JBL_CHARGE5_HERO_BLACK_0072_x1-1605x1605px.png'},
                {'name': 'Bose SoundLink Revolve+', 'purchase_price': 1800, 'sale_price': 2200, 'stock': 18, 'description': 'Bose SoundLink Revolve+ 360°', 'photo_url': 'https://assets.bose.com/content/dam/cloudassets/Bose_DAM/Web/consumer_electronics/global/products/speakers/soundlink_revolve_plus_ii/product_silo_images/SoundLink_Revolve_Plus_II_Black_Hero.png'},
                {'name': 'Sony SRS-XB43', 'purchase_price': 1400, 'sale_price': 1750, 'stock': 22, 'description': 'Sony SRS-XB43 Extra Bass', 'photo_url': 'https://sony.scene7.com/is/image/sonyglobalsolutions/srs-xb43_Primary_image?$categorypdpnav$&fmt=png-alpha'},
                
                # Gaming Audio
                {'name': 'SteelSeries Arctis Pro', 'purchase_price': 1800, 'sale_price': 2200, 'stock': 15, 'description': 'SteelSeries Arctis Pro gaming', 'photo_url': 'https://media.steelseriescdn.com/thumbs/catalog/items/61486/bb895fb8c1bd44b399e4eca6f05d4c7d.png.500x400_q100_crop-fit_optimize.png'},
                {'name': 'Razer BlackShark V2 Pro', 'purchase_price': 1200, 'sale_price': 1500, 'stock': 20, 'description': 'Razer BlackShark V2 Pro wireless', 'photo_url': 'https://assets2.razerzone.com/images/pnx.assets/618c0b65424070a1957c0cea74f7fa7e/razer-blackshark-v2-pro-2023-category-hero-mobile.jpg'}
            ],
            
            'Gaming': [
                # Consolas
                {'name': 'PlayStation 5', 'purchase_price': 3800, 'sale_price': 4500, 'stock': 8, 'description': 'PlayStation 5 nueva generación', 'photo_url': 'https://gmedia.playstation.com/is/image/SIEPDC/ps5-product-thumbnail-01-en-14sep21?$facebook$'},
                {'name': 'PlayStation 5 Digital', 'purchase_price': 3200, 'sale_price': 3800, 'stock': 10, 'description': 'PlayStation 5 Digital Edition', 'photo_url': 'https://gmedia.playstation.com/is/image/SIEPDC/ps5-digital-product-thumbnail-01-en-14sep21?$facebook$'},
                {'name': 'Xbox Series X', 'purchase_price': 3600, 'sale_price': 4200, 'stock': 12, 'description': 'Xbox Series X más potente', 'photo_url': 'https://assets.xboxservices.com/assets/fb/d2/fbd2cb56-5c25-414d-9f46-e6a164cdf5e4.png'},
                {'name': 'Xbox Series S', 'purchase_price': 2200, 'sale_price': 2700, 'stock': 18, 'description': 'Xbox Series S compacta', 'photo_url': 'https://assets.xboxservices.com/assets/5c/73/5c73bf42-fea1-478b-b35d-5c3b4b1c7c9d.png'},
                {'name': 'Nintendo Switch OLED', 'purchase_price': 2800, 'sale_price': 3400, 'stock': 15, 'description': 'Nintendo Switch OLED portátil', 'photo_url': 'https://assets.nintendo.com/image/upload/c_fill,w_1200/q_auto:best/f_auto/dpr_2.0/ncom/software/switch/70010000000964/3fb832b770b348c93aa376f3789f8b3a0eaf3b90c6a5d19a6159e8c7bf8b8a27'},
                {'name': 'Nintendo Switch Lite', 'purchase_price': 1800, 'sale_price': 2200, 'stock': 25, 'description': 'Nintendo Switch Lite económica', 'photo_url': 'https://assets.nintendo.com/image/upload/c_fill,w_1200/q_auto:best/f_auto/dpr_2.0/ncom/en_US/switch/site-design-update/hardware/switch-lite/nintendo-switch-lite-coral-front-1200x675.jpg'},
                
                # Mandos y Accesorios Gaming
                {'name': 'DualSense Controller PS5', 'purchase_price': 520, 'sale_price': 680, 'stock': 30, 'description': 'Control DualSense PS5', 'photo_url': 'https://gmedia.playstation.com/is/image/SIEPDC/dualsense-wireless-controller-thumbnail-01-en-15dec20?$facebook$'},
                {'name': 'Xbox Wireless Controller', 'purchase_price': 450, 'sale_price': 580, 'stock': 35, 'description': 'Control Xbox inalámbrico', 'photo_url': 'https://assets.xboxservices.com/assets/86/3b/863b1c85-5b3e-423b-9d4e-5c4a3b4c1c2d.png'},
                {'name': 'Pro Controller Nintendo', 'purchase_price': 480, 'sale_price': 620, 'stock': 25, 'description': 'Pro Controller Switch', 'photo_url': 'https://assets.nintendo.com/image/upload/c_fill,w_1200/q_auto:best/f_auto/dpr_2.0/ncom/en_US/switch/accessories/pro-controller/nintendo-switch-pro-controller-image.jpg'}
            ],
            
            'Smart Home': [
                {'name': 'Amazon Echo Dot 5ta Gen', 'purchase_price': 380, 'sale_price': 480, 'stock': 50, 'description': 'Echo Dot con Alexa', 'photo_url': 'https://m.media-amazon.com/images/I/714Rq4k05UL._AC_SL1000_.jpg'},
                {'name': 'Google Nest Hub 2da Gen', 'purchase_price': 850, 'sale_price': 1050, 'stock': 25, 'description': 'Google Nest Hub con pantalla', 'photo_url': 'https://lh3.googleusercontent.com/ZPPcVx_5vLRtYyqOBc6BqCGx0oFr6tkD4HQq6U-Xq_7e4jC7v-Hq7B6kOJm_QiPvVQw'},
                {'name': 'Ring Video Doorbell 4', 'purchase_price': 1200, 'sale_price': 1500, 'stock': 20, 'description': 'Ring Video Doorbell HD', 'photo_url': 'https://ring.com/content/dam/pdp/device-hero-images/doorbell-4/doorbell-4-satin-nickel-front-facing.png'},
                {'name': 'Philips Hue Starter Kit', 'purchase_price': 1800, 'sale_price': 2200, 'stock': 15, 'description': 'Philips Hue luces inteligentes', 'photo_url': 'https://www.philips-hue.com/content/dam/hue/en/products/smart-lighting/white-and-color-ambiance/starter-kits/e27-3-pack-bridge/packaging/hue-wca-starter-kit-e27-3-pack-bridge-packaging.png'}
            ],
            
            'Accesorios': [
                # Cables y Cargadores
                {'name': 'Cable USB-C a USB-C 2m', 'purchase_price': 120, 'sale_price': 180, 'stock': 100, 'description': 'Cable USB-C 2 metros', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/MQKJ3?wid=750&hei=750'},
                {'name': 'Cable Lightning a USB-C', 'purchase_price': 150, 'sale_price': 220, 'stock': 80, 'description': 'Cable Lightning a USB-C Apple', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/MQGJ3?wid=750&hei=750'},
                {'name': 'Cargador MagSafe Wireless', 'purchase_price': 280, 'sale_price': 380, 'stock': 60, 'description': 'Cargador MagSafe inalámbrico', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/MHXH3?wid=750&hei=750'},
                {'name': 'Power Bank Anker 20000mAh', 'purchase_price': 420, 'sale_price': 580, 'stock': 45, 'description': 'Power Bank Anker 20000mAh', 'photo_url': 'https://d2eebagvwr542c.cloudfront.net/catalog/product/cache/d17513e3b63736bb5d8dffa85c33092e/a/1/a1287h11-1.jpg'},
                
                # Periféricos PC
                {'name': 'Logitech MX Master 3S', 'purchase_price': 650, 'sale_price': 820, 'stock': 35, 'description': 'Mouse Logitech MX Master 3S', 'photo_url': 'https://resource.logitechg.com/w_386,ar_1.0,c_limit,f_auto,q_auto,dpr_2.0/d_transparent.gif/content/dam/logitech/en/products/mice/mx-master-3s/gallery/mx-master-3s-mouse-top-view-graphite.png'},
                {'name': 'Apple Magic Keyboard', 'purchase_price': 850, 'sale_price': 1050, 'stock': 25, 'description': 'Apple Magic Keyboard', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/MK2A3?wid=750&hei=750'},
                {'name': 'Keychron K2 Mechanical', 'purchase_price': 950, 'sale_price': 1200, 'stock': 20, 'description': 'Teclado mecánico Keychron K2', 'photo_url': 'https://cdn.shopify.com/s/files/1/0059/0630/1017/products/Keychron-K2-wireless-mechanical-keyboard-for-Mac-Windows-iOS-Gateron-blue-switch-white-backlight-aluminum-frame_1800x1800.jpg'},
                
                # Monitores
                {'name': 'Samsung Odyssey G7 27"', 'purchase_price': 2800, 'sale_price': 3400, 'stock': 12, 'description': 'Monitor Samsung Odyssey G7 27" 240Hz', 'photo_url': 'https://images.samsung.com/is/image/samsung/p6pim/pe/lc27g75tqslxpe/gallery/pe-odyssey-g7-lc27g75tqslxpe-290355216'},
                {'name': 'LG UltraWide 34"', 'purchase_price': 3200, 'sale_price': 3800, 'stock': 8, 'description': 'Monitor LG UltraWide 34" 4K', 'photo_url': 'https://gscs.lge.com/content/dam/lge/global/monitors/ultrawide/34wk95u-w/gallery/34WK95U-W_Gallery_06.jpg'},
                {'name': 'Dell UltraSharp 27" 4K', 'purchase_price': 2200, 'sale_price': 2700, 'stock': 15, 'description': 'Monitor Dell UltraSharp 27" 4K', 'photo_url': 'https://i.dell.com/is/image/DellContent/content/dam/ss2/product-images/dell-display-and-accessories/monitors/ultrasharp-monitors/u2723qe/media-gallery/monitor-u2723qe-gallery-1.psd'},
                
                # Almacenamiento
                {'name': 'Samsung SSD T7 1TB', 'purchase_price': 850, 'sale_price': 1100, 'stock': 30, 'description': 'SSD externo Samsung T7 1TB', 'photo_url': 'https://images.samsung.com/is/image/samsung/p6pim/pe/mu-pc1t0t-ww/gallery/pe-portable-ssd-t7-mu-pc1t0t-ww-531731637'},
                {'name': 'SanDisk Extreme Pro 2TB', 'purchase_price': 1200, 'sale_price': 1500, 'stock': 20, 'description': 'SSD SanDisk Extreme Pro 2TB', 'photo_url': 'https://documents.westerndigital.com/content/dam/doc/product-overview/en-us/sandisk-extreme-pro-portable-ssd-v2-product-overview.png'},
                
                # Smartwatches
                {'name': 'Apple Watch Series 9 45mm', 'purchase_price': 3200, 'sale_price': 3800, 'stock': 18, 'description': 'Apple Watch Series 9 45mm', 'photo_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/watch-s9-45-alum-pink-nc-9_VW_PF+watch-face-9-45-alum-pink-nc-9_VW_PF?wid=750&hei=750'},
                {'name': 'Samsung Galaxy Watch 6', 'purchase_price': 2200, 'sale_price': 2700, 'stock': 22, 'description': 'Samsung Galaxy Watch 6', 'photo_url': 'https://images.samsung.com/is/image/samsung/p6pim/pe/galaxy-watch6/gallery/pe-galaxy-watch6-r930-sm-r930nzsapeo-thumb-537654776'},
                {'name': 'Garmin Venu 3', 'purchase_price': 2800, 'sale_price': 3400, 'stock': 15, 'description': 'Garmin Venu 3 deportivo', 'photo_url': 'https://static.garmin.com/en/products/010-02784-11/g/rf-lg.jpg'}
            ]
        }
        
        # Crear DataFrame con pandas
        all_products = []
        for category, products in products_data.items():
            for product in products:
                product['category'] = category
                all_products.append(product)
        
        # Generar productos adicionales para llegar a 300
        while len(all_products) < 300:
            for category, products in products_data.items():
                if len(all_products) >= 300:
                    break
                # Crear variaciones de productos existentes
                base_product = random.choice(products)
                variation = base_product.copy()
                
                # Crear variaciones realistas
                colors = ['Negro', 'Blanco', 'Azul', 'Rojo', 'Verde', 'Gris', 'Rosa', 'Dorado', 'Plata']
                storage_options = ['64GB', '128GB', '256GB', '512GB', '1TB', '2TB']
                
                if 'iPhone' in variation['name'] or 'Samsung' in variation['name']:
                    color = random.choice(colors)
                    storage = random.choice(storage_options[:4])  # Tamaños más comunes para móviles
                    variation['name'] = f"{variation['name']} {storage} {color}"
                    variation['purchase_price'] = int(variation['purchase_price'] * random.uniform(0.9, 1.1))
                    variation['sale_price'] = int(variation['sale_price'] * random.uniform(0.9, 1.1))
                elif 'MacBook' in variation['name'] or 'Laptop' in variation['name']:
                    storage = random.choice(storage_options[2:])  # Tamaños más grandes para laptops
                    ram = random.choice(['8GB', '16GB', '32GB'])
                    variation['name'] = f"{variation['name']} {storage} {ram}"
                    variation['purchase_price'] = int(variation['purchase_price'] * random.uniform(0.95, 1.15))
                    variation['sale_price'] = int(variation['sale_price'] * random.uniform(0.95, 1.15))
                else:
                    color = random.choice(colors)
                    variation['name'] = f"{variation['name']} {color}"
                    variation['purchase_price'] = int(variation['purchase_price'] * random.uniform(0.92, 1.08))
                    variation['sale_price'] = int(variation['sale_price'] * random.uniform(0.92, 1.08))
                
                variation['stock'] = random.randint(5, 50)
                all_products.append(variation)
        
        return pd.DataFrame(all_products[:300])  # Limitar a exactamente 300 productos

    def get(self, request):
        created_items = []
        
        # Crear usuarios administradores y cajeros
        admin_emails = ['admin@mail.com']
        cashier_emails = ['cashier@mail.com']
        
        for email in admin_emails:
            if not User.objects.filter(email=email).exists():
                try:
                    admin_user = User.objects.create_superuser(
                        ci='0000001',
                        email=email,
                        name='Admin Inicial',
                        phone='11111111',
                        password='admin123',
                        role='administrator'
                    )
                    admin_user.email_verified = True
                    admin_user.save()
                    created_items.append('Usuario administrador')
                except Exception as e:
                    print(f"Error creando admin: {e}")
                    continue

        for email in cashier_emails:
            if not User.objects.filter(email=email).exists():
                try:
                    cashier_user = User.objects.create_superuser(
                        ci='0000002',
                        email=email,
                        name='Cajero Inicial',
                        phone='22222222',
                        password='cashier123',
                        role='cashier'
                    )
                    cashier_user.email_verified = True
                    cashier_user.save()
                    created_items.append('Usuario cajero')
                except Exception as e:
                    print(f"Error creando cajero: {e}")
                    continue

        # Crear clientes
        customers_data = [
            {'ci': '1234567', 'email': 'juan@mail.com', 'name': 'Juan Pérez', 'phone': '70123456'},
            {'ci': '2345678', 'email': 'maria@mail.com', 'name': 'María García', 'phone': '71234567'},
            {'ci': '3456789', 'email': 'carlos@mail.com', 'name': 'Carlos López', 'phone': '72345678'},
            {'ci': '4567890', 'email': 'ana@mail.com', 'name': 'Ana Rodríguez', 'phone': '73456789'},
            {'ci': '5678901', 'email': 'luis@mail.com', 'name': 'Luis Martínez', 'phone': '74567890'},
        ]

        customer_count = 0
        for customer_data in customers_data:
            if not User.objects.filter(email=customer_data['email']).exists():
                try:
                    user = User.objects.create_user(
                        ci=customer_data['ci'],
                        email=customer_data['email'],
                        name=customer_data['name'],
                        phone=customer_data['phone'],
                        password='customer123',
                        role='customer'
                    )
                    user.email_verified = True
                    user.is_active = True
                    user.save()
                    customer_count += 1
                except Exception as e:
                    print(f"Error creando cliente {customer_data['email']}: {e}")
                    continue
        
        if customer_count > 0:
            created_items.append(f'{customer_count} clientes')

        # Crear categorías
        categories_data = [
            {'name': 'Smartphones', 'description': 'Teléfonos inteligentes de última generación'},
            {'name': 'Laptops', 'description': 'Computadoras portátiles para trabajo y gaming'},
            {'name': 'Tablets', 'description': 'Tabletas para entretenimiento y productividad'},
            {'name': 'Accesorios', 'description': 'Cables, cargadores y otros accesorios'},
            {'name': 'Audio', 'description': 'Auriculares, parlantes y equipos de audio'},
            {'name': 'Gaming', 'description': 'Consolas y accesorios para videojuegos'},
            {'name': 'Smart Home', 'description': 'Dispositivos inteligentes para el hogar'},
        ]

        categories = {}
        category_count = 0
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            categories[cat_data['name']] = category
            if created:
                category_count += 1
        
        if category_count > 0:
            created_items.append(f'{category_count} categorías')

        # Crear descuentos
        discounts_data = [
            {'name': 'Descuento Black Friday', 'percentage': Decimal('15.00'), 'expiration_date': date.today() + timedelta(days=30)},
            {'name': 'Descuento Estudiantes', 'percentage': Decimal('10.00'), 'expiration_date': date.today() + timedelta(days=90)},
            {'name': 'Descuento Fin de Temporada', 'percentage': Decimal('20.00'), 'expiration_date': date.today() + timedelta(days=15)},
            {'name': 'Descuento Premium', 'percentage': Decimal('25.00'), 'expiration_date': date.today() + timedelta(days=60)},
            {'name': 'Descuento VIP', 'percentage': Decimal('30.00'), 'expiration_date': date.today() + timedelta(days=45)},
        ]

        available_discounts = []
        discount_count = 0
        for disc_data in discounts_data:
            discount, created = Discount.objects.get_or_create(
                name=disc_data['name'],
                defaults=disc_data
            )
            available_discounts.append(discount)
            if created:
                discount_count += 1
        
        if discount_count > 0:
            created_items.append(f'{discount_count} descuentos')

        # Usar pandas para crear 300 productos con URLs reales
        try:
            products_df = self.create_products_dataset()
            product_count = 0
            discount_index = 0
            
            for _, row in products_df.iterrows():
                if not Product.objects.filter(name=row['name']).exists():
                    try:
                        category_name = row['category']
                        if category_name in categories:
                            product_data = {
                                'name': row['name'],
                                'description': row['description'],
                                'category': categories[category_name],
                                'purchase_price': Decimal(str(row['purchase_price'])),
                                'sale_price': Decimal(str(row['sale_price'])),
                                'stock': row['stock'],
                                'stock_minimum': max(5, row['stock'] // 4),
                                'photo_url': row.get('photo_url', ''),
                            }
                            
                            # Asignar descuento único solo a algunos productos especiales
                            if discount_index < len(available_discounts):
                                discount = available_discounts[discount_index]
                                if not Product.objects.filter(discount=discount).exists():
                                    product_data['discount'] = discount
                                    discount_index += 1
                            
                            Product.objects.create(**product_data)
                            product_count += 1
                            
                    except Exception as e:
                        print(f"Error creando producto {row.get('name', 'unknown')}: {e}")
                        continue
            
            if product_count > 0:
                created_items.append(f'{product_count} productos con imágenes')
                
        except Exception as e:
            print(f"Error procesando productos con pandas: {e}")
            created_items.append("Error procesando productos")

        # Preparar mensaje de respuesta
        if created_items:
            message = f"✅ Seeders ejecutados exitosamente. Se crearon: {', '.join(created_items)}."
        else:
            message = "ℹ️ No se crearon nuevos elementos. La base de datos ya contiene los datos iniciales."

        return response(200, message)
