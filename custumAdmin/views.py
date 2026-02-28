import os
from django.utils.text import slugify
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from django.db import models
from products.models import Brand, Category, Product, ProductImage
from accounts.models.Users import Users
from orders.models.Order import Order

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .decorators import superadmin_required


# Fonction utilitaire pour les notifications
def get_admin_notifications(request):
    """Récupère les notifications pour l'admin (stock bas, commandes en attente, etc.)"""
    notifications = []
    
    # 1. Produits en stock faible (< 10)
    low_stock_products = Product.objects.filter(stock__lt=10, stock__gt=0).count()
    if low_stock_products > 0:
        notifications.append({
            'type': 'warning',
            'icon': 'fa-exclamation-triangle',
            'message': f'⚠️ {low_stock_products} produit(s) en stock faible',
            'color': '#FF6B35'
        })
    
    # 2. Produits en rupture de stock
    out_of_stock = Product.objects.filter(stock=0).count()
    if out_of_stock > 0:
        notifications.append({
            'type': 'danger',
            'icon': 'fa-times-circle',
            'message': f'🔴 {out_of_stock} produit(s) en rupture de stock',
            'color': '#dc3545'
        })
    
    # 3. Commandes en attente (non expédiées)
    from django.utils import timezone
    pending_orders = Order.objects.filter(status__in=['pending', 'confirmed']).count()
    if pending_orders > 0:
        notifications.append({
            'type': 'info',
            'icon': 'fa-shopping-cart',
            'message': f'📦 {pending_orders} commande(s) à traiter',
            'color': '#17a2b8'
        })
    
    # 4. Commandes livrées récemment (dernières 24h) - succès
    twenty_four_hours_ago = timezone.now() - __import__('datetime').timedelta(hours=24)
    recent_deliveries = Order.objects.filter(status='delivered', updated_at__gte=twenty_four_hours_ago).count()
    if recent_deliveries > 0:
        notifications.append({
            'type': 'success',
            'icon': 'fa-check-circle',
            'message': f'✅ {recent_deliveries} commande(s) livrée(s) aujourd\'hui',
            'color': '#28a745'
        })
    
    # 5. Nouveaux utilisateurs (derniers 7 jours)
    seven_days_ago = timezone.now() - __import__('datetime').timedelta(days=7)
    new_users = Users.objects.filter(date_joined__gte=seven_days_ago).count()
    if new_users > 0:
        notifications.append({
            'type': 'primary',
            'icon': 'fa-user-plus',
            'message': f'👤 {new_users} nouvel(les) utilisateur(s) inscrit(s)',
            'color': '#A67C52'
        })
    
    return notifications


# Dashboard


def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_superuser:
                login(request, user)
                return redirect('Admin')  # Page d’accueil admin
            else:
                messages.error(request, "Vous n’avez pas les permissions pour accéder à cette page.")
        else:
            messages.error(request, "Identifiants incorrects.")

    return render(request, 'custumAdmin/signin.html')

def admin_logout(request):
    logout(request)
    messages.success(request, "deconnécté avec succes")
    return redirect('admin_login')

@superadmin_required
def admin(request):
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Sum, Count, Avg, Q
    from decimal import Decimal
    
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # ========== DONNÉES POUR LES KPI ==========
    # Ventes du jour
    daily_orders = Order.objects.filter(created_at__date=today)
    daily_sales = daily_orders.aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    # Ventes du mois
    monthly_orders = Order.objects.filter(created_at__date__gte=month_start)
    monthly_sales = monthly_orders.aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    # Nombre de commandes
    daily_orders_count = daily_orders.count()
    monthly_orders_count = monthly_orders.count()
    
    # Nouveaux clients ce mois
    new_customers_month = Users.objects.filter(date_joined__date__gte=month_start).count()
    
    # Produits vendus aujourd'hui
    from orders.models.OrderItem import OrderItem
    products_sold = OrderItem.objects.filter(
        order__created_at__date=today
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    # Panier moyen
    avg_cart = daily_orders.filter(total__gt=0).aggregate(avg=Avg('total'))['avg'] or Decimal('0')
    
    # Taux de conversion (estimé: commandes/visiteurs)
    conversion_rate = Decimal('2.4')  # À remplacer par logique réelle si vous avez les visiteurs
    
    # Valeur vie client
    customer_ltv = Decimal('187')  # À calculer selon votre logique
    
    # ========== DONNÉES POUR LES GRAPHIQUES ==========
    # Derniers 30 jours de ventes
    days_data = []
    sales_data_current = []
    for i in range(30, 0, -1):
        date = today - timedelta(days=i)
        day_orders = Order.objects.filter(created_at__date=date)
        day_sales = day_orders.aggregate(total=Sum('total'))['total'] or Decimal('0')
        days_data.append(str(date.day))
        sales_data_current.append(float(day_sales))
    
    # Statuts des commandes
    pending_count = Order.objects.filter(status=Order.STATUS_PENDING).count()
    preparing_count = Order.objects.filter(status=Order.STATUS_PREPARING).count()
    shipped_count = Order.objects.filter(status=Order.STATUS_SHIPPED).count()
    delivered_count = Order.objects.filter(status=Order.STATUS_DELIVERED).count()
    cancelled_count = Order.objects.filter(status=Order.STATUS_CANCELLED).count()
    
    total_orders_count = pending_count + preparing_count + shipped_count + delivered_count + cancelled_count
    
    # Calculer les pourcentages
    if total_orders_count > 0:
        pending_pct = round((pending_count / total_orders_count) * 100, 1)
        preparing_pct = round((preparing_count / total_orders_count) * 100, 1)
        shipped_pct = round((shipped_count / total_orders_count) * 100, 1)
        delivered_pct = round((delivered_count / total_orders_count) * 100, 1)
        cancelled_pct = round((cancelled_count / total_orders_count) * 100, 1)
    else:
        pending_pct = preparing_pct = shipped_pct = delivered_pct = cancelled_pct = 0
    
    orders_by_status = {
        'pending': pending_count,
        'preparing': preparing_count,
        'shipped': shipped_count,
        'delivered': delivered_count,
        'cancelled': cancelled_count,
        'pending_pct': pending_pct,
        'preparing_pct': preparing_pct,
        'shipped_pct': shipped_pct,
        'delivered_pct': delivered_pct,
        'cancelled_pct': cancelled_pct,
    }
    
    # Top 5 produits
    top_products = OrderItem.objects.values('product__name', 'product__id').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(models.F('quantity') * models.F('price'), output_field=models.DecimalField())
    ).order_by('-total_revenue')[:5]
    
    # Enrichir avec le prix unitaire et les images
    top_products_list = []
    for idx, item in enumerate(top_products, 1):
        try:
            product = Product.objects.get(id=item['product__id'])
            main_image = product.images.filter(is_main=True).first() or product.images.first()
            image_url = main_image.image.url if main_image and hasattr(main_image, 'image') else 'https://via.placeholder.com/40x40'
            
            top_products_list.append({
                'rank': idx,
                'name': item['product__name'],
                'quantity': item['total_quantity'],
                'revenue': float(item['total_revenue']),
                'stock': product.stock,
                'image_url': image_url,
            })
        except Product.DoesNotExist:
            pass
    
    # Stock critique (moins de 10 unités)
    critical_stock = Product.objects.filter(stock__lt=10).order_by('stock')[:5]
    critical_stock_list = []
    for product in critical_stock:
        main_image = product.images.filter(is_main=True).first() or product.images.first()
        image_url = main_image.image.url if main_image and hasattr(main_image, 'image') else 'https://via.placeholder.com/40x40'
        critical_stock_list.append({
            'name': product.name,
            'stock': product.stock,
            'image_url': image_url,
        })
    
    # Heures d'achat (12 intervalles horaires)
    hours_data = [0] * 12
    all_orders = Order.objects.filter(created_at__date__gte=today - timedelta(days=7))
    for order in all_orders:
        hour = order.created_at.hour
        interval = hour // 2  # 0-2, 2-4, etc.
        if interval < 12:
            hours_data[interval] += 1
    
    # Dernières commandes
    recent_orders = Order.objects.all().order_by('-created_at')[:4]
    recent_orders_list = []
    for order in recent_orders:
        recent_orders_list.append({
            'id': order.id,
            'number': order.order_number[:8] if order.order_number else f'#{order.id}',
            'user_name': order.user.username if hasattr(order.user, 'username') else order.user.email,
            'total': float(order.total),
            'status': order.get_status_display() if hasattr(order, 'get_status_display') else order.status,
            'status_key': order.status,
            'created_at': order.created_at,
        })
    
    context = {
        'today': today,
        # KPIs
        'daily_sales': float(daily_sales),
        'monthly_sales': float(monthly_sales),
        'daily_orders': daily_orders_count,
        'monthly_orders': monthly_orders_count,
        'new_customers_month': new_customers_month,
        'products_sold': products_sold,
        'avg_cart': float(avg_cart),
        'conversion_rate': float(conversion_rate),
        'customer_ltv': float(customer_ltv),
        # Graphiques
        'days': days_data,
        'sales_data_current': sales_data_current,
        'orders_by_status': orders_by_status,
        'top_products': top_products_list,
        'critical_stock': critical_stock_list,
        'hours_data': hours_data,
        'recent_orders': recent_orders_list,
        # Notifications
        'notifications': get_admin_notifications(request),
    }
    
    return render(request, "custumAdmin/dashboard_new.html", context)


# Products
@superadmin_required
def product_list(request):
    from django.core.paginator import Paginator

    qs = Product.objects.all().order_by('-created_at')

    # search
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(name__icontains=q)  # simple search on name

    # filter by category
    cat = request.GET.get('category')
    if cat:
        qs = qs.filter(category__id=cat)

    # filter by vendor/brand
    vendor = request.GET.get('vendor')
    if vendor:
        qs = qs.filter(brand__id=vendor)

    # counts for top filters (best-effort)
    all_count = Product.objects.count()
    published_count = Product.objects.filter(stock__gt=0).count()
    drafts_count = Product.objects.filter(stock__lte=0).count()
    on_discount_count = Product.objects.filter(price__lt=0).count()  # placeholder

    # pagination
    per_page = 10
    page = request.GET.get('page', 1)
    paginator = Paginator(qs, per_page)
    try:
        page_obj = paginator.get_page(page)
    except Exception:
        page_obj = paginator.get_page(1)

    categories = Category.objects.all()
    brands = Brand.objects.all()

    # Attach a `main_image_url` attribute to each product for template convenience
    for prod in page_obj.object_list:
        try:
            main_img = prod.images.filter(is_main=True).first() or prod.images.first()
            prod.main_image_url = main_img.image.url if main_img and getattr(main_img, 'image', None) else ''
        except Exception:
            prod.main_image_url = ''

    return render(request, "custumAdmin/list/products_list.html", {
        "products": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "q": q,
        "categories": categories,
        "brands": brands,
        "all_count": all_count,
        "published_count": published_count,
        "drafts_count": drafts_count,
        "on_discount_count": on_discount_count,
    })

@superadmin_required
def product_add(request):
    categories = Category.objects.all()
    brands = Brand.objects.all()

    if request.method == 'POST':
        try:

            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            price = request.POST.get('price', '0')
            stock = request.POST.get('stock', '0')
            category_id = request.POST.get('category')
            brand_id = request.POST.get('brand')

            if not name or not description or not category_id:
                return render(request, "custumAdmin/add/product_add.html", {
                    "categories": categories,
                    "brands": brands,
                    "error": "Name, description and category are required."
                })

            # Generate slug from name (ensure uniqueness)
            slug = slugify(name)
            counter = 1
            original_slug = slug
            while Product.objects.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1

            # Create product
            product = Product(
                name=name,
                slug=slug,
                description=description,
                price=float(price or 0),
                stock=int(stock or 0),
                category_id=category_id,
                brand_id=brand_id if brand_id else None,
            )
            product.save()

            # Save images from file input into MEDIA_ROOT/image/<category_slug>/<brand_slug>/
            from django.core.files.storage import default_storage
            from django.conf import settings

            files = request.FILES.getlist('images')
            try:
                cat = Category.objects.get(id=category_id)
                cat_slug = slugify(cat.name)
            except Exception:
                cat_slug = 'uncategorized'

            if brand_id:
                try:
                    br = Brand.objects.get(id=brand_id)
                    brand_slug = slugify(br.name)
                except Exception:
                    brand_slug = 'generic'
            else:
                brand_slug = 'generic'

            for idx, file in enumerate(files):
                is_main = (idx == 0)
                filename = file.name
                rel_dir = os.path.join('image', cat_slug, brand_slug)
                rel_path = os.path.join(rel_dir, filename)

                # Ensure directory exists in MEDIA_ROOT
                full_dir = os.path.join(settings.MEDIA_ROOT, rel_dir)
                os.makedirs(full_dir, exist_ok=True)

                # Save file to storage (MEDIA_ROOT)
                saved_path = default_storage.save(rel_path, file)

                # Create ProductImage record pointing to saved path
                img = ProductImage(product=product, is_main=is_main)
                img.image.name = saved_path
                img.save()

            from django.contrib import messages
            messages.success(request, f"Product '{name}' created successfully!")
            return redirect(reverse('product_list'))

        except Exception as e:
            return render(request, "custumAdmin/add/product_add.html", {
                "categories": categories,
                "brands": brands,
                "error": f"Error creating product: {e}"
            })

    return render(request, "custumAdmin/add/product_add.html", {"categories": categories, "brands": brands})

@superadmin_required
def product_detail(request, id):
    import json
    from django.utils import timezone
    from datetime import timedelta
    from orders.models import OrderItem

    product = get_object_or_404(Product, id=id)
    images = product.productimage_set.all() if hasattr(product, 'productimage_set') else product.images.all()

    # reviews and counts
    reviews = product.reviews.all()
    reviews_count = reviews.count()

    # total sales for this product (sum of quantities)
    total_sales = OrderItem.objects.filter(product=product).aggregate(models.Sum('quantity'))['quantity__sum'] or 0

    # prepare last 7 days labels and values (number of items sold each day)
    today = timezone.now().date()
    labels = []
    values = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime('%b %d'))
        day_start = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time()))
        day_end = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.max.time()))
        qty = OrderItem.objects.filter(product=product, order__created_at__range=(day_start, day_end)).aggregate(models.Sum('quantity'))['quantity__sum'] or 0
        values.append(qty)

    context = {
        "product": product,
        "images": images,
        "reviews": reviews,
        "reviews_count": reviews_count,
        "total_sales": total_sales,
        "last7days_labels": json.dumps(labels),
        "last7days_values": json.dumps(values),
    }
    return render(request, "custumAdmin/detail/product_detail.html", context)

@superadmin_required
def product_edit(request, id):
    product = get_object_or_404(Product, id=id)
    categories = Category.objects.all()
    brands = Brand.objects.all()

    if request.method == 'POST':
        # update basic fields
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', '0')
        stock = request.POST.get('stock', '0')
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand')

        # validate required fields
        if not name or not description or not category_id:
            images = product.productimage_set.all() if hasattr(product, 'productimage_set') else product.images.all()
            return render(request, "custumAdmin/edit/product_edit.html", {
                "product": product,
                "categories": categories,
                "brands": brands,
                "images": images,
                "error": "Name, description and category are required."
            })

        # assign updated values
        product.name = name
        # keep slug unchanged unless you want to regenerate
        product.description = description
        product.price = float(price or 0)
        product.stock = int(stock or 0)
        product.category_id = category_id
        product.brand_id = brand_id if brand_id else None
        product.save()

        # handle deleted images
        delete_ids = request.POST.getlist('delete_images')
        if delete_ids:
            from django.conf import settings
            for img_id in delete_ids:
                try:
                    img = ProductImage.objects.get(id=img_id, product=product)
                    # delete file from storage
                    if img.image and hasattr(img.image, 'path'):
                        try:
                            os.remove(img.image.path)
                        except Exception:
                            pass
                    img.delete()
                except ProductImage.DoesNotExist:
                    pass

        # after deletion make sure there's a main image
        if not product.images.filter(is_main=True).exists():
            first = product.images.first()
            if first:
                first.is_main = True
                first.save()

        # handle new uploaded images
        from django.core.files.storage import default_storage
        from django.conf import settings

        files = request.FILES.getlist('images')
        try:
            cat = Category.objects.get(id=category_id)
            cat_slug = slugify(cat.name)
        except Exception:
            cat_slug = 'uncategorized'

        if brand_id:
            try:
                br = Brand.objects.get(id=brand_id)
                brand_slug = slugify(br.name)
            except Exception:
                brand_slug = 'generic'
        else:
            brand_slug = 'generic'

        for idx, file in enumerate(files):
            # if no existing images remain, first new one becomes main
            is_main = False
            if not product.images.exists():
                is_main = True
            filename = file.name
            rel_dir = os.path.join('image', cat_slug, brand_slug)
            rel_path = os.path.join(rel_dir, filename)

            full_dir = os.path.join(settings.MEDIA_ROOT, rel_dir)
            os.makedirs(full_dir, exist_ok=True)
            saved_path = default_storage.save(rel_path, file)

            img = ProductImage(product=product, is_main=is_main)
            img.image.name = saved_path
            img.save()

        from django.contrib import messages
        messages.success(request, f"Product '{product.name}' updated successfully!")
        return redirect(reverse('product_list'))

    images = product.productimage_set.all() if hasattr(product, 'productimage_set') else product.images.all()
    return render(request, "custumAdmin/edit/product_edit.html", {"product": product, "categories": categories, "brands": brands, "images": images})

@superadmin_required
def product_delete(request, id):
    product = get_object_or_404(Product, id=id)
    # Require POST for deletion (prevent accidental GET deletes)
    if request.method == 'POST':
        product.delete()
        return redirect(reverse('product_list'))
    # If not POST, redirect back
    return redirect(request.META.get('HTTP_REFERER', reverse('product_list')))


# Categories
@superadmin_required
def category_list(request):
    from django.core.paginator import Paginator
    
    # Base queryset
    qs = Category.objects.all().order_by('-created_at')
    
    # Recherche
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            models.Q(name__icontains=q) | 
            models.Q(description__icontains=q)
        )
    
    # Filtrer par statut
    status = request.GET.get('status')
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)
    
    # Comptage
    total_count = Category.objects.count()
    active_count = Category.objects.filter(is_active=True).count()
    inactive_count = Category.objects.filter(is_active=False).count()
    
    # Pagination
    per_page = 20
    page = request.GET.get('page', 1)
    paginator = Paginator(qs, per_page)
    try:
        page_obj = paginator.get_page(page)
    except Exception:
        page_obj = paginator.get_page(1)
    
    return render(request, "custumAdmin/list/category_list.html", {
        "page_obj": page_obj,
        "categories": page_obj.object_list,
        "total_count": total_count,
        "active_count": active_count,
        "inactive_count": inactive_count,
        "q": q,
        "status": status,
    })

@superadmin_required
def category_add(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            is_active = request.POST.get('is_active') == 'on'
            icone = request.POST.get('icone')
            
            if not name or not description:
                return render(request, "custumAdmin/add/category_add.html", 
                            {"error": "Le nom et la description sont requis."})
            
            slug = slugify(name)
            counter = 1
            original_slug = slug
            while Category.objects.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
                
            category = Category(
                name=name,
                slug=slug,
                icone=icone,
                description=description,
                is_active=is_active,
            )
            category.save()
            
            return redirect(reverse('category_list'))
            
        except Exception as e:
            return render(request, "custumAdmin/add/category_add.html",
                        {"error": f"Erreur de création : {e}"})
            
    return render(request, "custumAdmin/add/category_add.html")

@superadmin_required
def category_edit(request, id):
    category = get_object_or_404(Category, id=id)
    
    if request.method == 'POST':
        try:
            category.name = request.POST.get('name', '').strip()
            category.description = request.POST.get('description', '').strip()
            category.is_active = request.POST.get('is_active') == 'on'
            category.icone = request.POST.get('icone')
            
            if not category.name or not category.description:
                return render(request, "custumAdmin/edit/category_edit.html", {
                    "category": category,
                    "error": "Le nom et la description sont requis."
                })
            
            # Générer un nouveau slug si le nom a changé
            new_slug = slugify(category.name)
            if new_slug != category.slug:
                counter = 1
                original_slug = new_slug
                while Category.objects.exclude(id=id).filter(slug=new_slug).exists():
                    new_slug = f"{original_slug}-{counter}"
                    counter += 1
                category.slug = new_slug
            
            category.save()
            return redirect(reverse('category_list'))
            
        except Exception as e:
            return render(request, "custumAdmin/edit/category_edit.html", {
                "category": category,
                "error": f"Erreur de modification : {e}"
            })
    
    return render(request, "custumAdmin/edit/category_edit.html", {"category": category})

@superadmin_required
def category_detail(request, id):
    category = get_object_or_404(Category, id=id)
    return render(request, "custumAdmin/detail/category_detail.html", {"category": category})

@superadmin_required
def category_delete(request, id):
    cat = get_object_or_404(Category, id=id)
    if request.method == 'POST':
        cat.delete()
        return redirect(reverse('category_list'))
    return redirect(request.META.get('HTTP_REFERER', reverse('category_list')))

@superadmin_required
def toggle_category_status(request):
    """API pour basculer le statut actif/inactif d'une catégorie"""
    from django.http import JsonResponse
    import json
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        category_id = data.get('category_id')
        
        if not category_id:
            return JsonResponse({'error': 'Missing category_id'}, status=400)
        
        category = Category.objects.get(id=category_id)
        category.is_active = not category.is_active
        category.save()
        
        return JsonResponse({
            'success': True,
            'is_active': category.is_active,
            'message': f'Catégorie {("activée" if category.is_active else "désactivée")}'
        })
    
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Clients (Users)
@superadmin_required
def client_list(request):
    from django.core.paginator import Paginator
    from accounts.models.CustomerProfile import CustomerProfile
    from django.utils import timezone
    from datetime import timedelta

    # Consider a "client" as a user who has a CustomerProfile OR at least one Order
    profile_users = CustomerProfile.objects.values_list('user_id', flat=True)
    order_user_ids = Order.objects.values_list('user_id', flat=True).distinct()

    client_ids = set(list(profile_users) + list(order_user_ids))
    
    # Get all clients (active AND inactive)
    qs = Users.objects.filter(id__in=client_ids).order_by('-date_joined')

    # search
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(models.Q(username__icontains=q) | models.Q(email__icontains=q) | models.Q(first_name__icontains=q) | models.Q(last_name__icontains=q))

    # Filter by status (active/inactive)
    filter_status = request.GET.get('filter', '').strip()
    if filter_status == 'active':
        qs = qs.filter(is_active=True)
    elif filter_status == 'inactive':
        qs = qs.filter(is_active=False)
    elif filter_status == 'new':
        # Nouveaux clients (moins de 7 jours)
        one_week_ago = timezone.now() - timedelta(days=7)
        qs = qs.filter(date_joined__gte=one_week_ago)
    elif filter_status == 'vip':
        # VIP clients - check if they have is_vip in CustomerProfile or high order count
        from django.db.models import Count
        qs = qs.annotate(
            order_count=Count('order', distinct=True)
        ).filter(models.Q(customerprofile__is_vip=True) | models.Q(order_count__gte=5))
    elif filter_status == 'abandoned':
        # Clients with items in cart
        qs = qs.filter(cart__items__isnull=False).distinct()

    # counts for top filters
    all_clients = Users.objects.filter(id__in=client_ids)
    total_clients = all_clients.count()
    active_count = all_clients.filter(is_active=True).count()
    inactive_count = all_clients.filter(is_active=False).count()
    
    one_week_ago = timezone.now() - timedelta(days=7)
    new_clients_count = all_clients.filter(date_joined__gte=one_week_ago).count()
    
    from django.db.models import Count
    vip_count = all_clients.filter(
        models.Q(customerprofile__is_vip=True) |
        models.Q(order__isnull=False)
    ).annotate(
        order_count=Count('order', distinct=True)
    ).filter(order_count__gte=5).distinct().count()
    
    abandoned_count = all_clients.filter(cart__items__isnull=False).distinct().count()

    # optional: list of countries for filter
    countries = CustomerProfile.objects.filter(user_id__in=client_ids).values_list('country', flat=True).distinct()

    # pagination
    per_page = 10
    page = request.GET.get('page', 1)
    paginator = Paginator(qs, per_page)
    try:
        page_obj = paginator.get_page(page)
    except Exception:
        page_obj = paginator.get_page(1)

    clients = []
    for u in page_obj.object_list:
        orders_qs = Order.objects.filter(user=u)
        orders_count = orders_qs.count()
        total_spent = orders_qs.aggregate(total=models.Sum('total'))['total'] or 0
        last_order = orders_qs.order_by('-created_at').first()
        # try to get profile
        try:
            profile = u.customerprofile
            photo_url = profile.photo.url if profile.photo else ''
            city = profile.city
            is_vip = getattr(profile, 'is_vip', False)
        except Exception:
            photo_url = ''
            city = ''
            is_vip = False

        clients.append({
            'id': u.id,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'name': f"{u.first_name or u.username} {u.last_name or ''}".strip(),
            'email': u.email,
            'photo': photo_url,
            'image': photo_url,
            'orders_count': orders_count,
            'total_spent': total_spent,
            'city': city,
            'last_seen_display': u.last_login.strftime('%b %d, %H:%M') if u.last_login else '-',
            'last_order': last_order.created_at if last_order else None,
            'last_login': u.last_login,
            'is_active': u.is_active,
            'is_vip': is_vip,
        })

    return render(request, "custumAdmin/list/client_list.html", {
        'Clients': clients,
        'page_obj': page_obj,
        'paginator': paginator,
        'q': q,
        'total_clients': total_clients,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'new_clients_count': new_clients_count,
        'vip_count': vip_count,
        'abandoned_count': abandoned_count,
        'locals_count': all_clients.filter(customerprofile__country__isnull=False).exclude(customerprofile__country="").count(),
        'countries': [c for c in countries if c],
    })

@superadmin_required
def client_toggle_status(request, client_id):
    """Toggle the is_active status of a client"""
    import json
    from django.http import JsonResponse
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
    
    try:
        user = get_object_or_404(Users, id=client_id)
        
        # Parse JSON body
        try:
            data = json.loads(request.body)
            is_active = data.get('active', not user.is_active)
        except json.JSONDecodeError:
            is_active = not user.is_active
        
        # Update the status
        user.is_active = is_active
        user.save()
        
        return JsonResponse({
            'success': True,
            'is_active': user.is_active,
            'message': 'Client ' + ('activé' if is_active else 'désactivé')
        })
    
    except Users.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Client not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@superadmin_required
def client_add(request):
    from accounts.models.CustomerProfile import CustomerProfile
    from django.contrib import messages

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', '').strip()
        birth_date = request.POST.get('birth_date', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        country = request.POST.get('country', '').strip()

        # validation
        if not username:
            return render(request, "custumAdmin/add/client_add.html", {"error": "Username is required.",
                           "username": username, "email": email})

        if Users.objects.filter(username=username).exists():
            return render(request, "custumAdmin/add/client_add.html", {"error": "Username already taken.",
                           "username": username, "email": email})

        if email and Users.objects.filter(email=email).exists():
            return render(request, "custumAdmin/add/client_add.html", {"error": "Email already in use.",
                           "username": username, "email": email})

        try:
            user = Users(username=username, email=email, first_name=first_name, last_name=last_name, phone=phone, gender=gender)
            if birth_date:
                try:
                    # store raw; Django will attempt to coerce on save if valid format
                    user.birth_date = birth_date
                except Exception:
                    pass

            # set unusable password by default
            user.set_unusable_password()
            user.save()

            # create customer profile
            photo = request.FILES.get('photo')
            profile = CustomerProfile.objects.create(
                user=user,
                address=address,
                city=city,
                postal_code=postal_code,
                country=country,
            )
            if photo:
                profile.photo = photo
                profile.save()

            messages.success(request, f"Client {username} créé avec succès.")
            return redirect(reverse('client_list'))

        except Exception as e:
            return render(request, "custumAdmin/add/client_add.html", {"error": f"Erreur: {e}",
                           "username": username, "email": email})

    return render(request, "custumAdmin/add/client_add.html")

@superadmin_required
def client_detail(request, id):
    from accounts.models.CustomerProfile import CustomerProfile
    from reviews.models.Review import Review
    from django.db.models import Count, Avg
    
    user = get_object_or_404(Users, id=id)
    try:
        profile = user.customerprofile
    except Exception:
        profile = None

    # Get orders for this user
    orders = Order.objects.filter(user=user).order_by('-created_at')
    
    # Get reviews from this user
    reviews = Review.objects.filter(user=user).order_by('-created_at')
    
    # Compute some stats
    total_orders = orders.count()
    total_spent = orders.aggregate(total=models.Sum('total'))['total'] or 0
    
    # For wishlist: we don't have a wishlist model, so we return empty for now
    # If you want to add wishlist later, create a Wishlist model
    wishlist = []
    
    # For notes: if you want to add notes functionality, create a Note model
    notes = []

    return render(request, "custumAdmin/detail/client_detail.html", {
        "client": user,
        "profile": profile,
        "orders": orders,
        "reviews": reviews,
        "total_orders": total_orders,
        "total_spent": total_spent,
        "wishlist": wishlist,
        "notes": notes,
    })

@superadmin_required
def client_edit(request, id):
    from accounts.models.CustomerProfile import CustomerProfile
    from django.contrib import messages
    
    user = get_object_or_404(Users, id=id)
    try:
        profile = user.customerprofile
    except Exception:
        profile = None
    
    countries = sorted(list(set([
        'Afghanistan', 'Afrique du Sud', 'Albanie', 'Algérie', 'Allemagne', 'Andorre',
        'Angola', 'Anguilla', 'Antarctique', 'Antigua-et-Barbuda', 'Arabie Saoudite',
        'Argentine', 'Arménie', 'Aruba', 'Australie', 'Autriche', 'Azerbaïdjan',
        'Bahamas', 'Bahreïn', 'Bangladesh', 'Barbade', 'Belgique', 'Belize',
        'Bénin', 'Bermudes', 'Bhoutan', 'Biélorussie', 'Birmanie', 'Birmanie (Myanmar)',
        'Bolivie', 'Bosnie-Herzégovine', 'Botswana', 'Brésil', 'Brunei', 'Bulgarie',
        'Burkina Faso', 'Burundi', 'Cambodge', 'Cameroun', 'Canada', 'Cap-Vert',
        'Chili', 'Chine', 'Chypre', 'Colombie', 'Comores', 'Corée du Nord',
        'Corée du Sud', 'Costa Rica', 'Côte d\'Ivoire', 'Croatie', 'Cuba', 'Danemark',
        'Djibouti', 'Dominique', 'Égypte', 'Émirats Arabes Unis', 'Équateur',
        'Érythrée', 'Espagne', 'Estonie', 'États-Unis', 'Éthiopie', 'Fidji',
        'Finlande', 'France', 'Gabon', 'Gambie', 'Géorgie', 'Ghana',
        'Gibraltar', 'Grèce', 'Grenade', 'Groenland', 'Guadeloupe', 'Guam',
        'Guatemala', 'Guernesey', 'Guinée', 'Guinée équatoriale', 'Guinée-Bissau',
        'Guyana', 'Guyane française', 'Haïti', 'Honduras', 'Hong Kong', 'Hongrie',
        'Île Bouvet', 'Île Christmas', 'Île Norfolk', 'Îles Åland', 'Îles Caïmans',
        'Îles Cocos', 'Îles Féroé', 'Îles Heard et MacDonald', 'Îles Malouines',
        'Îles Mariannes du Nord', 'Îles Marshall', 'Îles Pitcairn', 'Îles Salomon',
        'Îles Turques et Caïques', 'Îles Vierges britanniques',
        'Îles Vierges des États-Unis', 'Inde', 'Indonésie', 'Irak', 'Iran',
        'Irlande', 'Islande', 'Israël', 'Italie', 'Jamaïque', 'Japon',
        'Jersey', 'Jordanie', 'Kazakhstan', 'Kenya', 'Kirghizistan', 'Kiribati',
        'Koweït', 'Laos', 'Lesotho', 'Lettonie', 'Liban', 'Liberia',
        'Libye', 'Liechtenstein', 'Lituanie', 'Luxembourg', 'Macao', 'Macédoine',
        'Madagascar', 'Madère', 'Malaisie', 'Malawi', 'Maldives', 'Mali',
        'Malte', 'Maroc', 'Martinique', 'Mauritanie', 'Maurice', 'Mayotte',
        'Mexique', 'Micronésie', 'Moldavie', 'Monaco', 'Mongolie', 'Monténégro',
        'Montserrat', 'Mozambique', 'Namibie', 'Nauru', 'Népal', 'Nicaragua',
        'Niger', 'Nigeria', 'Niue', 'Norvège', 'Nouvelle-Calédonie',
        'Nouvelle-Zélande', 'Oman', 'Ouganda', 'Ouzbékistan', 'Pakistan', 'Palaos',
        'Palestine', 'Panama', 'Papouasie-Nouvelle-Guinée', 'Pâques', 'Paraguay',
        'Pays-Bas', 'Pérou', 'Philippines', 'Pologne', 'Polynésie française',
        'Porto Rico', 'Portugal', 'Qatar', 'La Réunion', 'Roumanie', 'Royaume-Uni',
        'Russie', 'Rwanda', 'Sahara occidental', 'Saint-Barthélemy', 'Saint-Marin',
        'Saint-Martin', 'Saint-Pierre-et-Miquelon', 'Sainte-Hélène', 'Sainte-Lucie',
        'Samoa', 'Samoa américaines', 'San Marin', 'Sao Tomé-et-Principe',
        'Sénégal', 'Serbie', 'Seychelles', 'Sierra Leone', 'Singapour',
        'Sint Maarten', 'Slovaquie', 'Slovénie', 'Somalie', 'Soudan',
        'Soudan du Sud', 'Swaziland', 'Suède', 'Suisse', 'Suriname', 'Svalbard',
        'Syrie', 'Tadjikistan', 'Taïwan', 'Tanzanie', 'Tchad', 'Terres australes',
        'Thaïlande', 'Timor oriental', 'Togo', 'Tokelau', 'Tonga',
        'Trinité-et-Tobago', 'Tunisie', 'Turkménistan', 'Turquie', 'Tuvalu',
        'Ukraine', 'Uruguay', 'Vanuatu', 'Vatican', 'Venezuela', 'Viêt Nam',
        'Wallis et Futuna', 'Yémen', 'Zambie', 'Zimbabwe'
    ])))
    
    if request.method == 'POST':
        try:
            # Update Users fields
            user.first_name = request.POST.get('first_name', user.first_name).strip()
            user.last_name = request.POST.get('last_name', user.last_name).strip()
            user.email = request.POST.get('email', user.email).strip()
            user.phone = request.POST.get('phone', user.phone).strip()
            user.gender = request.POST.get('gender', user.gender).strip()
            user.save()
            
            # Update or create CustomerProfile
            if not profile:
                profile = CustomerProfile(user=user)
            
            profile.address = request.POST.get('address', '').strip()
            profile.city = request.POST.get('city', '').strip()
            profile.postal_code = request.POST.get('postal_code', '').strip()
            profile.country = request.POST.get('country', '').strip()
            
            # Handle photo upload
            if 'photo' in request.FILES:
                profile.photo = request.FILES['photo']
            
            profile.save()
            
            messages.success(request, f"Client {user.get_full_name or user.username} modifié avec succès.")
            return redirect(reverse('client_detail', args=[user.id]))
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification : {e}")
            return render(request, "custumAdmin/edit/client_edit.html", {
                "client": user,
                "profile": profile,
                "countries": countries,
            })
    
    return render(request, "custumAdmin/edit/client_edit.html", {
        "client": user,
        "profile": profile,
        "countries": countries,
    })

@superadmin_required
def client_delete(request, id):
    user = get_object_or_404(Users, id=id)
    if request.method == 'POST':
        user.delete()
        return redirect(reverse('client_list'))
    return redirect(request.META.get('HTTP_REFERER', reverse('client_list')))


# Orders
@superadmin_required
def order_list(request):
    # Base queryset
    qs = Order.objects.select_related('user').order_by('-created_at')

    # simple search by order number, customer email, or customer name
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(models.Q(order_number__icontains=q) | 
                       models.Q(user__email__icontains=q) |
                       models.Q(user__username__icontains=q) |
                       models.Q(user__first_name__icontains=q) |
                       models.Q(user__last_name__icontains=q))

    # filter by status if provided
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)

    # counts for tabs/filters
    total_count = Order.objects.count()
    pending_count = Order.objects.filter(status=Order.STATUS_PENDING).count()
    preparing_count = Order.objects.filter(status=Order.STATUS_PREPARING).count()
    shipped_count = Order.objects.filter(status=Order.STATUS_SHIPPED).count()
    delivered_count = Order.objects.filter(status=Order.STATUS_DELIVERED).count()
    completed_count = Order.objects.filter(status=Order.STATUS_COMPLETED).count()
    cancelled_count = Order.objects.filter(status=Order.STATUS_CANCELLED).count()

    # Pagination
    from django.core.paginator import Paginator
    per_page = 20
    page = request.GET.get('page', 1)
    paginator = Paginator(qs, per_page)
    try:
        page_obj = paginator.get_page(page)
    except Exception:
        page_obj = paginator.get_page(1)

    return render(request, "custumAdmin/list/order_list.html", {
        "orders": page_obj.object_list,
        "page_obj": page_obj,
        "total_count": total_count,
        "pending_count": pending_count,
        "preparing_count": preparing_count,
        "shipped_count": shipped_count,
        "delivered_count": delivered_count,
        "completed_count": completed_count,
        "cancelled_count": cancelled_count,
        "q": q,
        "status": status,
    })

@superadmin_required
def order_detail(request, id):
    from django.http import JsonResponse
    import json
    
    # admin view of order
    order = get_object_or_404(Order, id=id)
    
    # Handle POST requests for status updates or cancellation
    if request.method == 'POST':
        action = request.POST.get('action', 'update_status')
        
        if action == 'update_status':
            new_status = request.POST.get('status', order.status)
            if new_status in [choice[0] for choice in Order.STATUS_CHOICES]:
                order.status = new_status
                order.save()
                # Redirect to same page to show updated status
                return redirect(reverse('order_detail', args=[id]))
        
        elif action == 'cancel':
            if order.status not in [Order.STATUS_CANCELLED, Order.STATUS_DELIVERED]:
                order.status = Order.STATUS_CANCELLED
                order.save()
                return redirect(reverse('order_detail', args=[id]))
    
    # Récupérer les articles, l'adresse de livraison et le paiement
    from orders.models import OrderItem, ShippingAddress, Payment
    items = OrderItem.objects.filter(order=order)
    shipping = ShippingAddress.objects.filter(order=order).first()
    payment = Payment.objects.filter(order=order).first()
    
    # compute totals
    items_subtotal = sum(item.price * item.quantity for item in items)
    discount = getattr(order, 'discount', 0)
    tax = getattr(order, 'tax', 0)
    shipping_cost = getattr(order, 'shipping_cost', 0)
    context = {
        'order': order,
        'items': items,
        'shipping': shipping,
        'payment': payment,
        'items_subtotal': items_subtotal,
        'discount': discount,
        'tax': tax,
        'shipping_cost': shipping_cost,
    }
    return render(request, "custumAdmin/detail/order_detail.html", context)

@superadmin_required
def update_order_status(request):
    """API endpoint pour mettre à jour le statut d'une commande"""
    from django.http import JsonResponse
    import json
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        new_status = data.get('status')
        
        if not order_id or not new_status:
            return JsonResponse({'error': 'Missing order_id or status'}, status=400)
        
        order = Order.objects.get(id=order_id)
        
        # Valider la transition
        if not order.can_transition_to(new_status):
            allowed = order.get_allowed_transitions()
            return JsonResponse({
                'error': f'Cannot transition from {order.status} to {new_status}',
                'allowed_transitions': allowed,
                'current_status': order.status
            }, status=400)
        
        # Effectuer la transition
        order.transition_to(new_status)
        
        return JsonResponse({
            'success': True,
            'message': f'Order status updated to {new_status}',
            'status': order.status,
            'allowed_transitions': order.get_allowed_transitions()
        })
    
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@superadmin_required    
def admins(request):
    return render(request, 'custumAdmin/admins.html')

@superadmin_required
def appearance(request):
    return render(request, 'custumAdmin/appearance.html')

@superadmin_required
def settings(request):
    return render(request, 'custumAdmin/settings.html')

@superadmin_required
def localisation(request):
    return render(request, 'custumAdmin/localisation.html')

