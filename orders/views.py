import json
from products.models import Category
import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from cart.cart import Cart
from .models import Order, OrderItem, ShippingAddress, Payment
import uuid
from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from cart.utils import get_cart_total
# Create your views here.

@login_required
def order(request):
    list_categ = Category.objects.all()
    # Render the payment page with cart totals
    cart = Cart(request)
    context = {
        'cart_items': list(cart),
        'cart_total': cart.get_total_price(),
        'list_categ': list_categ,
    }
    return render(request, 'orders/order.html', context)


@login_required
@require_POST
def create_order(request):
    """Create Order, OrderItems, ShippingAddress and Payment from posted data.

    Accepts JSON or form-encoded data. Expects:
      - payment_method ('card'|'paypal')
      - address, city, postal_code, country, phone
      - card_number (only last4 used), card_name, expiry_month, expiry_year
      - tip (optional)

    Returns JSON with success and order id.
    """
    import json

    # parse body
    data = {}
    if request.POST:
        data.update(request.POST.dict())
    if request.body:
        try:
            payload = json.loads(request.body.decode())
            if isinstance(payload, dict):
                data.update(payload)
        except Exception:
            pass

    # basic validation
    payment_method = data.get('payment_method', 'card')
    address = data.get('address')
    postal_code = data.get('postal_code') or data.get('postl-code')
    city = data.get('city')
    country = data.get('country')
    phone = data.get('phone') or data.get('delivery-phone')

    if not all([address, postal_code, city, country]):
        return JsonResponse({'success': False, 'error': 'missing_address'}, status=400)

    cart = Cart(request)
    if len(cart) == 0:
        return JsonResponse({'success': False, 'error': 'empty_cart'}, status=400)

    # create order
    order = Order.objects.create(user=request.user, total=cart.get_total_price())

    # create order items
    for item in cart:
        OrderItem.objects.create(
            order=order,
            product=item['product'],
            quantity=item['quantity'],
            price=item['price']
        )
        # update stock (simple decrement)
        try:
            p = item['product']
            if hasattr(p, 'stock'):
                p.stock = max(0, p.stock - item['quantity'])
                p.save()
        except Exception:
            pass

    # create shipping address
    ShippingAddress.objects.create(
        order=order,
        address=address,
        city=city,
        postal_code=postal_code,
        country=country
    )

    # create payment record
    tip = float(data.get('tip') or 0)
    amount = float(order.total) + tip

    payment = Payment.objects.create(
        order=order,
        method=payment_method,
        amount=amount,
    )

    # If card, capture minimal meta
    if payment_method == Payment.METHOD_CARD:
        card_number = (data.get('card_number') or '').replace(' ', '')
        if len(card_number) >= 4:
            payment.card_last4 = card_number[-4:]
            # naive card brand detection
            if card_number.startswith('4'):
                payment.card_brand = 'Visa'
            elif card_number.startswith('5'):
                payment.card_brand = 'MasterCard'
            elif card_number.startswith('3'):
                payment.card_brand = 'Amex'
            else:
                payment.card_brand = 'Card'

    # simulate transaction id and mark paid
    transaction_id = uuid.uuid4().hex
    payment.transaction_id = transaction_id
    payment.mark_paid(transaction_id=transaction_id)

    # clear cart
    cart.clear()

    return JsonResponse({'success': True, 'order_id': order.id})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/detail.html', {'order': order})


stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
@csrf_exempt
def create_checkout_session(request):
    cart = Cart(request)

    if not cart:
        return JsonResponse({"error": "Cart empty"}, status=400)

    line_items = []

    for item in cart:
        line_items.append({
            "price_data": {
                "currency": "eur",
                "product_data": {
                    "name": item["product"].name,
                },
                "unit_amount": int(item["price"] * 100),
            },
            "quantity": item["quantity"],
        })

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url=request.build_absolute_uri("/payment/success/"),
        cancel_url=request.build_absolute_uri("/cart/"),
        metadata={
            "user_id": request.user.id,
        }
    )

    return JsonResponse({"url": session.url})

@login_required
def checkout(request):
    cart = Cart(request)

    if not cart:
        return redirect("cart_detail")

    return render(request, "orders/checkout.html", {
        "cart_items": list(cart),
        "cart_total": cart.get_total_price(),
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY
    })


stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session['metadata']['order_id']

        order = Order.objects.get(id=order_id)
        payment = order.payment

        payment.mark_paid(transaction_id=session.id)
        order.status = 'C'
        order.save()

    return HttpResponse(status=200)

@csrf_exempt
def create_payment_intent(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    amount = int(get_cart_total(request) * 100)  # en centimes

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="eur",
            automatic_payment_methods={"enabled": True},
            metadata={
                "user_id": request.user.id if request.user.is_authenticated else "guest"
            }
        )
    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({
        "client_secret": intent.client_secret
    })

from decimal import Decimal

@login_required
def payment_success(request):
    cart = request.session.get('cart', {})

    if not cart:
        return redirect('cart')

    total = sum(
        Decimal(item['price']) * int(item['quantity'])
        for item in cart.values()
    )

    order = Order.objects.create(
        user=request.user,
        total=total,
        status="C"  # Completed
    )

    Payment.objects.create(
        order=order,
        method="stripe",
        amount=total,
        status="paid",
        provider="stripe"
    )

    # vider le panier
    request.session['cart'] = {}
    request.session.modified = True

    return JsonResponse({
        "success": True,
        "order_number": order.order_number,
        "amount": str(total)
    })

@login_required
@require_POST
def payment_confirm(request):
    cart = Cart(request)

    if not cart:
        return JsonResponse({"error": "Cart empty"}, status=400)

    data = json.loads(request.body)
    payment_intent_id = data.get("payment_intent")

    # Récupérer les détails du PaymentIntent depuis Stripe
    try:
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    except stripe.error.StripeError as e:
        return JsonResponse({"error": f"Stripe error: {str(e)}"}, status=400)

    # Extraire les détails de paiement
    payment_method_id = payment_intent.payment_method
    card_info = {}
    
    if payment_method_id:
        try:
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            if payment_method.card:
                card_info = {
                    'brand': payment_method.card.brand,
                    'last4': payment_method.card.last4,
                    'exp_month': payment_method.card.exp_month,
                    'exp_year': payment_method.card.exp_year,
                }
        except stripe.error.StripeError as e:
            print(f"Error retrieving payment method: {str(e)}")

    # Créer la commande
    order = Order.objects.create(
        user=request.user,
        total=cart.get_total_price(),
        status="completed"
    )

    # Créer les articles de commande
    for item in cart:
        OrderItem.objects.create(
            order=order,
            product=item['product'],
            quantity=item['quantity'],
            price=item['price']
        )

    # Créer l'adresse de livraison
    ShippingAddress.objects.create(
        order=order,
        full_name=data["full_name"],
        address=data["address"],
        city=data["city"],
        postal_code=data["postal_code"],
        country=data["country"]
    )

    # Créer le paiement avec les infos de la carte
    payment = Payment.objects.create(
        order=order,
        provider="stripe",
        method="card",
        amount=order.total,
        status="paid",
        transaction_id=payment_intent_id,
        card_brand=card_info.get('brand'),
        card_last4=card_info.get('last4'),
        card_exp_month=card_info.get('exp_month'),
        card_exp_year=card_info.get('exp_year'),
        metadata={
            'payment_intent_id': payment_intent_id,
            'payment_method_id': payment_method_id,
        }
    )

    # Vider le panier
    request.session['cart'] = {}
    request.session.modified = True

    return JsonResponse({"success": True})

@login_required
@require_POST
def payment_confirm_paypal(request):
    cart = Cart(request)

    if not cart:
        return JsonResponse({"error": "Cart empty"}, status=400)

    data = json.loads(request.body)

    order = Order.objects.create(
        user=request.user,
        total=cart.get_total_price(),
        status="C"
    )

    for item in cart:
        OrderItem.objects.create(
            order=order,
            product=item['product'],
            quantity=item['quantity'],
            price=item['price']
        )

    Payment.objects.create(
        order=order,
        provider="paypal",
        method="paypal",
        amount=order.total,
        status="paid",
        transaction_id=data["paypal_order_id"]
    )

    request.session['cart'] = {}
    request.session.modified = True

    return JsonResponse({"success": True})


def payement_paypal(request):
    # Logique de confirmation de paiement PayPal
    return JsonResponse({"success": True})