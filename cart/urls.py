from django.urls import path
from . import views

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('add-ajax/', views.cart_add_ajax, name='cart_add_ajax'),
    path('update-ajax/', views.cart_update_ajax, name='cart_update_ajax'),
]
