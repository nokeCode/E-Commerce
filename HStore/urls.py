
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import allauth  # type: ignore
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
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

urlpatterns += staticfiles_urlpatterns()


