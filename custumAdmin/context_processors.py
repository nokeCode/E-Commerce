from django.utils import timezone
import datetime
from products.models import Product
from orders.models.Order import Order
from accounts.models import Users


def admin_notifications(request):
    """
    Context processor pour ajouter les notifications admin à tous les templates.
    """
    # Vérifier que c'est un admin
    if not request.user.is_authenticated or not request.user.is_superuser:
        return {'admin_notifications': [], 'notification_count': 0}
    
    notifications = []
    
    # 1. Produits en stock faible (< 10)
    low_stock_products = Product.objects.filter(stock__lt=10, stock__gt=0).count()
    if low_stock_products > 0:
        notifications.append({
            'type': 'warning',
            'icon': 'fa-exclamation-triangle',
            'message': f'⚠️ {low_stock_products} produit(s) en stock faible',
            'color': '#FF6B35'
        })
    
    # 2. Produits en rupture de stock
    out_of_stock = Product.objects.filter(stock=0).count()
    if out_of_stock > 0:
        notifications.append({
            'type': 'danger',
            'icon': 'fa-times-circle',
            'message': f'🔴 {out_of_stock} produit(s) en rupture de stock',
            'color': '#dc3545'
        })
    
    # 3. Commandes en attente (non expédiées)
    pending_orders = Order.objects.filter(status__in=['pending', 'confirmed']).count()
    if pending_orders > 0:
        notifications.append({
            'type': 'info',
            'icon': 'fa-shopping-cart',
            'message': f'📦 {pending_orders} commande(s) à traiter',
            'color': '#17a2b8'
        })
    
    # 4. Commandes livrées récemment (dernières 24h) - succès
    twenty_four_hours_ago = timezone.now() - datetime.timedelta(hours=24)
    recent_deliveries = Order.objects.filter(status='delivered', updated_at__gte=twenty_four_hours_ago).count()
    if recent_deliveries > 0:
        notifications.append({
            'type': 'success',
            'icon': 'fa-check-circle',
            'message': f'✅ {recent_deliveries} commande(s) livrée(s) aujourd\'hui',
            'color': '#28a745'
        })
    
    # 5. Nouveaux utilisateurs (derniers 7 jours)
    seven_days_ago = timezone.now() - datetime.timedelta(days=7)
    new_users = Users.objects.filter(date_joined__gte=seven_days_ago).count()
    if new_users > 0:
        notifications.append({
            'type': 'primary',
            'icon': 'fa-user-plus',
            'message': f'👤 {new_users} nouvel(les) utilisateur(s) inscrit(s)',
            'color': '#A67C52'
        })
    
    return {
        'admin_notifications': notifications,
        'notification_count': len(notifications)
    }
