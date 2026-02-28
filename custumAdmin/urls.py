from django.urls import path
from . import views

urlpatterns = [
    path( 'login/' , views.admin_login , name='admin_login' ),
    path('admin_logout/', views.admin_logout, name='admin_logout'),
    path('', views.admin, name='Admin'),
    #path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/<int:id>/', views.product_detail, name='product_detail'),
    path('products/<int:id>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:id>/delete/', views.product_delete, name='product_delete'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/<int:id>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:id>/', views.category_detail, name='category_detail'),
    path('categories/<int:id>/delete/', views.category_delete, name='category_delete'),
    path('api/categories/toggle-status/', views.toggle_category_status, name='toggle_category_status'),
    path('clients/', views.client_list, name='client_list'),
    path('clients/add/', views.client_add, name='client_add'),
    path('clients/<int:id>/', views.client_detail, name='client_detail'),
    path('clients/<int:id>/edit/', views.client_edit, name='client_edit'),
    path('clients/<int:id>/delete/', views.client_delete, name='client_delete'),
    path('clients/<int:client_id>/toggle-status/', views.client_toggle_status, name='client_toggle_status'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:id>/', views.order_detail, name='order_detail'),
    path('api/orders/update-status/', views.update_order_status, name='update_order_status'),
    
    path('admis/', views.admins, name='administrator'),
    path('appearance/', views.appearance, name='appearance'),
    path('settings/', views.settings, name='setting'),
    path('localisation/', views.localisation, name='localisation'),
    

]
