from django.urls import path
from . import views
    
urlpatterns = [
    path('', views.index, name="Home"),
    path('contact/', views.contact, name="Contact"),
    path('header/', views.header, name="header"),
    path('search/', views.search, name="search"),
    path("update-location/", views.update_location, name="update_location"),
]
