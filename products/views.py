from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from products.models import Brand, Category, Product, ProductImage

def shop(request):
    
    categories = Category.objects.all()
    images_by_category = {}

    for category in categories:
        images = ProductImage.objects.filter(product__category=category)[:4]
        images_by_category[category] = images

    return render(request, "products/shop.html", {
        'images_by_category': images_by_category,
    })
    
def show_categ(request, slug):
    list_brand = Brand.objects.all()
    list_categ = Category.objects.all()
    categori = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=categori)


    # Liste de tuples (produit, image principale ou None)
    product_with_image = []
    for prod in products:
        main_img = prod.images.filter(is_main=True).first() or prod.images.first()
        product_with_image.append((prod, main_img))

    paginator = Paginator(product_with_image, 4)
    page = request.GET.get('page', 1)# 6 produits par page
    try:
        prods = paginator.page(page)
    except:
        prods = paginator.page(1)

    return render(request, "products/show_categ.html", {
        'list_categ': list_categ,
        'list_categ_prod': categori,
        'list_brand': list_brand,
        'product_with_image': prods,
    })
    
def show_product(request, slug):
    prod  = get_object_or_404(Product, slug = slug)
    image =  prod.images.all()
    list_prod  = Product.objects.all()
    list_categ = Category.objects.all()
    # check favorite status
    is_favorite = False
    if request.user.is_authenticated:
        from .models import Favorite
        is_favorite = Favorite.objects.filter(user=request.user, product=prod).exists()

    # Soumission d'un avis
    if request.method == 'POST':
        # Importer ici pour éviter dépendances circulaires au module import time
        from reviews.models import Review

        if not request.user.is_authenticated:
            # Rediriger vers la page de connexion si l'utilisateur n'est pas connecté
            return redirect('signin')

        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()

        try:
            rating_int = int(rating)
            if rating_int < 1 or rating_int > 5:
                raise ValueError('Rating outside range')
        except Exception:
            # ignore invalid input
            return redirect('product', slug=slug)

        # Un seul avis par utilisateur et produit : update or create
        obj, created = Review.objects.update_or_create(
            user=request.user,
            product=prod,
            defaults={
                'rating': rating_int,
                'comment': comment,
            }
        )

        if created:
            from django.contrib import messages
            messages.success(request, "Merci — votre avis a été publié.")
        else:
            from django.contrib import messages
            messages.success(request, "Merci — votre avis a été mis à jour.")

        return redirect('product', slug=slug)

    reviews = prod.reviews.all().order_by('-created_at')
    return render(request, "products/single-product.html", {
        'prod' : prod,
        'list_prod' : list_prod,
        'images' : image,
        'reviews': reviews,
        'is_favorite': is_favorite,
        'list_categ': list_categ,
    })


def toggle_favorite(request, slug):
    from django.http import JsonResponse
    from .models import Favorite
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'auth_required'}, status=403)

    prod = get_object_or_404(Product, slug=slug)
    fav, created = Favorite.objects.get_or_create(user=request.user, product=prod)
    if not created:
        # already existed => remove (toggle off)
        fav.delete()
        status = 'removed'
    else:
        status = 'added'

    return JsonResponse({'status': status, 'count': prod.favorited_by.count()})
