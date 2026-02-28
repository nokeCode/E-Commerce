from django.shortcuts import redirect, render
from products.models import Category, Product, Brand, ProductImage
from django.db.models import Q, Count
from datetime import timedelta
from django.utils import timezone

# Create your views here.
def index(request):
    
    list_brand = Brand.objects.all()
    categories = Category.objects.all()
    images_by_category = {}
    
    for category in categories:
        images = ProductImage.objects.filter(product__category=category)[:4]
        images_by_category[category] = images
    
    # ========== PRODUITS LES PLUS POPULAIRES ==========
    # Basé sur le nombre de commandes
    from orders.models.OrderItem import OrderItem
    popular_products = (
        Product.objects
        .annotate(order_count=Count('orderitem', distinct=True))
        .filter(order_count__gt=0)
        .order_by('-order_count')[:8]
    )
    
    # Ajouter les images principales
    for product in popular_products:
        product.main_image = product.images.filter(is_main=True).first() or product.images.first()
        # Calculer le nombre d'avis
        product.review_count = product.reviews.count()
    
    # ========== PRODUITS NOUVEAUTÉS ==========
    # Produits créés dans les 30 derniers jours
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_products = (
        Product.objects
        .filter(created_at__gte=thirty_days_ago)
        .order_by('-created_at')[:8]
    )
    
    # Ajouter les images principales
    for product in new_products:
        product.main_image = product.images.filter(is_main=True).first() or product.images.first()
        product.review_count = product.reviews.count()
        
    return render(request, "core/home.html",
                 { 'list_categ' : categories ,
                    'list_brand' : list_brand,
                    'images_by_category': images_by_category,
                    'popular_products': popular_products,
                    'new_products': new_products,
                  })


def contact(request):
    return render(request, "core/contact.html")

def header(request):
    list_categ = Category.objects.all()
    list_brand = Brand.objects.all()
    return render(request, "core/header.html", 
                  { 'list_categ' : list_categ ,
                    'list_brand' : list_brand
                   })

def search(request):
    query = request.GET.get('q', '').strip()
    list_categ = Category.objects.all()
    # Par défaut, pas de résultats si pas de requête (évite d'afficher tout)
    products = Product.objects.none()

    if query:
        products = (
            Product.objects
            .filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query)
            )
            .select_related('category')
            .prefetch_related('images', 'reviews')
            .distinct()
        )

    # Attacher l'image principale à chaque produit pour simplifier le template
    for product in products:
        product.main_image = product.images.filter(is_main=True).first() or product.images.first()

    return render(request, "core/search.html", {
        'products': products,
        'query': query,
        'list_categ': list_categ,
    })
    
    from django.shortcuts import redirect
from django.views.decorators.http import require_POST

@require_POST
def update_location(request):
    city = request.POST.get("city")
    country = request.POST.get("country")

    request.session["city"] = city
    request.session["country"] = country

    return redirect(request.META.get("HTTP_REFERER", "Home"))
    