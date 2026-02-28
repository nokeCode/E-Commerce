from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect, render
from products.models import Category, Product
from .cart import Cart
from django.http import JsonResponse

# Create your views here.


def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    cart.add(product=product)
    
    return redirect('cart_detail')

from django.views.decorators.http import require_POST


@require_POST
def cart_add_ajax(request):
    """AJAX endpoint to add a product to the session-based cart and return JSON."""
    product_id = request.POST.get('product_id')
    qty = int(request.POST.get('quantity', 1) or 1)

    # validate product id
    try:
        product = get_object_or_404(Product, id=int(product_id))
    except Exception:
        return JsonResponse({'success': False, 'error': 'invalid_product'}, status=400)

    # use session-based Cart helper
    cart = Cart(request)
    cart.add(product=product, quantity=qty)

    # build cart summary
    total_items = len(cart)
    total_price = cart.get_total_price()

    from django.conf import settings
    import os

    image = product.images.filter(is_main=True).first() or product.images.first()
    image_url = ''

    if image:
        # Try the storage-provided URL first
        try:
            image_url = image.image.url or ''
        except Exception:
            image_url = ''

        # If URL is relative (starts with /), make it absolute for the client
        if image_url and not image_url.startswith('http'):
            try:
                image_url = request.build_absolute_uri(image_url)
            except Exception:
                pass

        # If image still not resolvable, try static fallback (some setups store files under static)
        if not image_url:
            static_candidate = settings.STATIC_URL.rstrip('/') + '/' + image.image.name
            static_fullpath = os.path.join(settings.BASE_DIR, 'static', image.image.name)
            if os.path.exists(static_fullpath):
                try:
                    image_url = request.build_absolute_uri(static_candidate)
                except Exception:
                    image_url = static_candidate

    # final fallback to placeholder static image
    if not image_url:
        placeholder = settings.STATIC_URL + 'image/logo/placehoder.png'
        try:
            image_url = request.build_absolute_uri(placeholder)
        except Exception:
            image_url = placeholder

    return JsonResponse({
        'success': True,
        'product': {
            'name': product.name,
            'price': str(product.price),
            'image': image_url,
            'quantity': cart.cart.get(str(product.id), {}).get('quantity', 0)
        },
        'cart': {
            'total_items': total_items,
            'total_price': str(total_price)
        }
    })

def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    cart.remove(product)
    return redirect('cart_detail')


@require_POST
def cart_update_ajax(request):
    """AJAX endpoint to update quantity for a given product in the session cart.

    Accepts form-encoded or JSON bodies. Expects: product_id, quantity (int).
    If quantity <= 0 the item is removed. Returns JSON with updated cart totals and product info.
    """
    import json

    # Accept both form-encoded and JSON payloads
    product_id = request.POST.get('product_id')
    qty_raw = request.POST.get('quantity', None)

    if not product_id and request.body:
        # try JSON body
        try:
            payload = json.loads(request.body.decode())
            product_id = payload.get('product_id')
            if 'quantity' in payload:
                qty_raw = payload.get('quantity')
        except Exception:
            pass

    if not product_id:
        return JsonResponse({'success': False, 'error': 'missing_product_id'}, status=400)

    try:
        qty = int(qty_raw or 0)
    except Exception:
        return JsonResponse({'success': False, 'error': 'invalid_quantity'}, status=400)

    try:
        product = get_object_or_404(Product, id=int(product_id))
    except Exception:
        return JsonResponse({'success': False, 'error': 'invalid_product'}, status=400)

    cart = Cart(request)

    removed = False
    if qty <= 0:
        cart.remove(product)
        removed = True
    else:
        cart.add(product=product, quantity=qty, override_quantity=True)

    # build cart summary
    total_items = len(cart)
    total_price = cart.get_total_price()

    # resolve image similar to add_ajax
    from django.conf import settings
    import os

    image = product.images.filter(is_main=True).first() or product.images.first()
    image_url = ''

    if image:
        try:
            image_url = image.image.url or ''
        except Exception:
            image_url = ''

        if image_url and not image_url.startswith('http'):
            try:
                image_url = request.build_absolute_uri(image_url)
            except Exception:
                pass

        if not image_url:
            static_candidate = settings.STATIC_URL.rstrip('/') + '/' + image.image.name
            static_fullpath = os.path.join(settings.BASE_DIR, 'static', image.image.name)
            if os.path.exists(static_fullpath):
                try:
                    image_url = request.build_absolute_uri(static_candidate)
                except Exception:
                    image_url = static_candidate

    if not image_url:
        placeholder = settings.STATIC_URL + 'image/logo/placehoder.png'
        try:
            image_url = request.build_absolute_uri(placeholder)
        except Exception:
            image_url = placeholder

    quantity_in_cart = cart.cart.get(str(product.id), {}).get('quantity', 0)

    resp = {
        'success': True,
        'product': {
            'name': product.name,
            'price': str(product.price),
            'image': image_url,
            'quantity': quantity_in_cart
        },
        'cart': {
            'total_items': total_items,
            'total_price': str(total_price)
        },
        'removed': removed
    }

    return JsonResponse(resp)


def cart_detail(request):
    cart = Cart(request)
    list_categ = Category.objects.all()
    # build list of items from session cart (Cart is iterable)
    items = list(cart)
    # mark favorites for products when user is authenticated so templates can read .is_favorite
    if request.user.is_authenticated and items:
        try:
            from products.models import Favorite
            product_ids = [item['product'].id for item in items]
            fav_ids = set(Favorite.objects.filter(user=request.user, product_id__in=product_ids).values_list('product_id', flat=True))
            for item in items:
                item['product'].is_favorite = (item['product'].id in fav_ids)
        except Exception:
            # be conservative and continue without favorite info if anything fails
            for item in items:
                item['product'].is_favorite = False
    else:
        for item in items:
            item['product'].is_favorite = False
    # lightweight wrapper to provide a .count property used by template
    class CartItems(list):
        @property
        def count(self):
            return len(self)

    cart_items = CartItems(items)

    # Compute totals expected by template
    cart_subtotal = cart.get_total_price()
    cart_discount = 0  # future: apply coupons/discount logic
    cart_total = cart_subtotal - cart_discount

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'cart_subtotal': cart_subtotal,
        'cart_discount': cart_discount,
        'cart_total': cart_total,
        'list_categ': list_categ,
    }

    return render(request, 'cart/cart.html', context)
