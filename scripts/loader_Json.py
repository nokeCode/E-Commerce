#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import json
from django.core.management.base import BaseCommand
from django.core.files import File


def main():
    """Run administrative tasks."""
    sys.path.append(os.path.dirname(os.path.dirname(__file__))) 
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HStore.settings')
    import django
    django.setup()
    try:
        from accounts.models import Users, CustomerProfile
        from cart.models import Cart, CartItem
        from orders.models import  Order, OrderItem, payement, ShippingAddress
        from products.models import  Brand, Category, Product, ProductImage
        from reviews.models import  Review
        from faker import Faker
        from django.core.files.uploadedfile import SimpleUploadedFile
        import random
        from django.utils.text import slugify
        
        fake = Faker()
        
        
        def create_users(max = 10):
            for _ in range(max):
                Users.objects.create(username = fake.unique.user_name(),
                                     first_name = fake.first_name(), 
                                     last_name = fake.last_name(), 
                                     email = fake.email(), 
                                     phone = fake.phone_number(), 
                                     gender = random.choice(['M', 'F', 'O']), 
                                     birth_date = fake.date_of_birth()
                                     )
                
        '''def create_custumer(max = 5):
            #u = list(Users.objects.all())
            u = list(Users.objects.exclude(customerprofile__isnull=False))

            for _ in range(max):
                CustomerProfile.objects.create(user = user, 
                                     address = fake.address() , 
                                     city = fake.city(), 
                                     postal_code = fake.postalcode(), 
                                     country = fake.country()
                                     )'''
        def create_custumer(max=5):
            u = list(Users.objects.exclude(customerprofile__isnull=False))  # Users sans profil
            for user in u[:max]:  # on prend jusqu'à max users sans profil
                CustomerProfile.objects.create(
                user=user,
                address=fake.address(),
                city=fake.city(),
                postal_code=fake.postcode(),
                country=fake.country()
                )
                             
                                     
        def load_categories():
            with open('categories.json', 'r', encoding='utf-8') as f:
                for cat in json.load(f):
                    Category.objects.get_or_create(
                        slug=cat['slug'],
                        defaults={
                            'name': cat['name'],
                            'icone': cat.get('icone', ''),
                            'description': cat.get('description', '')
                        }
                    )
                    print(f"Categorie ajoutée : {cat['name']}")
            print("Catégories chargées !")
       

        def load_brands():
            with open('Brand.json', 'r', encoding='utf-8') as file:
                brands = json.load(file)

            for brand_data in brands:
                try:
                    # Récupérer la liste de catégories (clé peut être "category" ou "categories")
                    categories = brand_data.get("categories") 

                    # Normaliser en liste
                    if isinstance(categories, str):
                        categories = [categories]

                    if not categories:
                        print(f"⚠️ Pas de catégorie pour la marque {brand_data['name']}")
                        continue

                    # Créer la marque pour chaque catégorie
                    for cat_name in categories:
                        try:
                            category = Category.objects.get(name=cat_name)
                            Brand.objects.get_or_create(
                                name=brand_data['name'],
                                category=category,
                                defaults={'logo': brand_data.get('logo', '')}
                            )
                            print(f"✅ Marque ajoutée : {brand_data['name']} (catégorie {cat_name})")
                        except Category.DoesNotExist:
                            print(f"❌ ERREUR: Catégorie '{cat_name}' introuvable pour la marque {brand_data['name']}")

                except Exception as e:
                    print(f"❌ ERREUR sur {brand_data.get('name', 'Inconnu')}: {str(e)}")

            print("Chargement de marques terminé !")
                             
                
      
                
        def create_product():
            with open('product.json', encoding='utf-8') as file:
                data = json.load(file)
                nbr_err = 0
            for item in data:
                try:
                    try:
                        category = Category.objects.get(name=item['category'])
                    except Category.DoesNotExist:
                        nbr_err+=1
                        print(f" {nbr_err} ⚠️ Catégorie non trouvée pour le produit : {item['name']}")
                        continue

                    # Crée ou récupère la marque
                    brand, _ = Brand.objects.get_or_create(name=item['brand'], category=category)

                    # Crée le produit
                    Product.objects.get_or_create(
                        name=item['name'],
                        slug=item['slug'],
                        defaults={
                            'description': item['description'],
                            'price': item['price'],
                            'stock': item['stock'],
                            'category': category,
                            'brand': brand
                        }
                    )
                    print(f"✅ Produit ajouté : {item['name']}")
                except Category.DoesNotExist:
                    print(f"❌ Erreur : catégorie avec slug '{item['category_slug']}' introuvable.")
                except Exception as e:
                    print(f"❌ Erreur avec le produit '{item['name']}': {e}")
            
        def create_P_Image(max = 4):
            with open('product_image.json', encoding='utf-8') as file:
                datas = json.load(file)
            for data in datas :
                try :
                    try :
                        product = Product.objects.get(name=data['product']) 
                    except Product.DoesNotExist:
                        print(f"  ⚠️ Catégorie non trouvée pour le produit : {data['name']}")
                        continue
                    ProductImage.objects.create(
                            product=product,
                            image=data['image'],
                            is_main=data['is_main']
                        )
                except Exception as e:
                    print(f"❌ Erreur avec l image '{data['name']}': {e}")
                    
                
                                
            
        def create_review(max = 1):
            users = list(Users.objects.all())
            products = list(Product.objects.all())
            for _ in range(max):
                Review.objects.create(
                                     user = random.choice(users), 
                                     product = random.choice(products), 
                                     rating=random.randint(1, 5),  
                                     comment=fake.sentence()
                                     
                                     )
        #create_users(20)        
        #create_custumer(10)        
        load_categories()     
        load_brands()        
        #create_product()        
        #create_P_Image()   
        #create_review(5)
        print(" Données générées avec succès.")    
    except Exception as err:
       print("Loading error", err)

if __name__ == '__main__':
    main()
