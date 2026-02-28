"""
URL configuration for HStore project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import allauth  # type: ignore
urlpatterns = [
    path('', include('core.urls')),
    path('shop/', include('products.urls')),
    path('dj-admin/', admin.site.urls),
    path('admin/', include('custumAdmin.urls')),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('accounts.urls')),
    path('cart/', include('cart.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('orders/', include('orders.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Inclure les URL d'allauth uniquement si le package est installé
try:
    import allauth  # type: ignore
    urlpatterns += [
        path('accounts/', include('allauth.urls')),
    ]
except Exception:
    # allauth n'est pas installé dans cet environnement (tests/dev minimal)
    pass



