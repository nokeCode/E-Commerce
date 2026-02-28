from django.db import models
from .Order import Order

class ShippingAddress(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    full_name = models.CharField(max_length=150, default='')
    phone = models.CharField(max_length=20, default='')


    def __str__(self):
        return f"Shipping for Order #{self.order.id}"