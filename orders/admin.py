from django.contrib import admin
from .models import Order, OrderItem, ShippingAddress, Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'method', 'amount', 'status', 'transaction_id', 'paid_at')
    list_filter = ('method', 'status', 'created_at')
    search_fields = ('transaction_id', 'order__id')

# Register other models if not already registered
try:
    admin.site.register(Order)
except Exception:
    pass

try:
    admin.site.register(OrderItem)
except Exception:
    pass

try:
    admin.site.register(ShippingAddress)
except Exception:
    pass
