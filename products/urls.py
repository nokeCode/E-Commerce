from django.urls import path
from HStore import settings
from . import views
from django.conf.urls.static import static


urlpatterns = [
    path('', views.shop, name='shop'),
    path('category/<str:slug>/', views.show_categ, name ='category'),
    path('product/<str:slug>/', views.show_product, name ='product'),
    path('product/<str:slug>/favorite/', views.toggle_favorite, name='product_favorite'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
