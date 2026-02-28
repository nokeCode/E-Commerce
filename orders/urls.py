from django.urls import path
from . import views 
urlpatterns = [
    path('orders/', views.order, name="order"),
    path('checkout/', views.checkout, name='checkout'),
    #path('orders/create/', views.create_order, name='order_create'),
    #path('orders/<int:order_id>/', views.order_detail, name="order_detail"),  
    #path('orders/create-stripe-session/<int:order_id>/', views.create_stripe_session, name='create_stripe_session'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path("create-payment-intent/", views.create_payment_intent, name="create_payment_intent"),
    path("payment-success/", views.payment_success, name="payment_success"),
    path("payment/confirm/", views.payment_confirm, name="payment_confirm"),
    path("payement_paypal/", views.payement_paypal, name="payment_confirm_paypal"),
]