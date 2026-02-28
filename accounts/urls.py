from django.urls import path
from HStore import settings
from . import views
from django.conf.urls.static import static


urlpatterns = [
    path('', views.account, name='account'),
    path('account/', views.account, name='account_profile'),  # (facultatif)
    path('account/update/', views.update_profile, name='update_profile'),
    path('account/orders/', views.account_orders, name='account_orders'),
    path('account/addresses/', views.account_addresses, name='account_addresses'),
    path('account/security/', views.account_security, name='account_security'),
    path('account/security/kill/', views.account_security_kick, name='account_security_kick'),
    path('account/payments/', views.account_payments, name='account_payments'),
    path('account/notifications/', views.account_notifications, name='account_notifications'),
    path('account/notifications/action/', views.account_notifications_action, name='account_notifications_action'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.logout_view, name='logout'),
    path('verify_2fa/', views.verify_2fa, name='verify_2fa'),
    path('2fa/resend/', views.resend_2fa, name='resend_2fa'),
    path('2fa/status/', views.twofa_status, name='twofa_status'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset-complete/', views.password_reset_complete, name='password_reset_complete'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
