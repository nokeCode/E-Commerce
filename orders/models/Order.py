from django.db import models
from accounts.models import Users
from django.contrib.auth.models import User
from products.models import Product
import uuid

class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PREPARING = 'preparing'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    
    STATUS_CHOICES = (
        (STATUS_PENDING, 'En attente'),
        (STATUS_PREPARING, 'En préparation'),
        (STATUS_SHIPPED, 'Expédiée'),
        (STATUS_DELIVERED, 'Livrée'),
        (STATUS_CANCELLED, 'Annulée'),
        (STATUS_COMPLETED, 'Complétée'),
        (STATUS_FAILED, 'Échouée'),
    )
    
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    order_number = models.CharField(max_length=20, unique=True, default='', editable=False, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} by {self.user.email}"
    
    # Logique métier pour les transitions de statut
    def get_allowed_transitions(self):
        """Retourne les statuts vers lesquels on peut transitionner"""
        transitions = {
            self.STATUS_PENDING: [self.STATUS_PREPARING, self.STATUS_CANCELLED],
            self.STATUS_PREPARING: [self.STATUS_SHIPPED, self.STATUS_PENDING],
            self.STATUS_SHIPPED: [self.STATUS_DELIVERED],
            self.STATUS_DELIVERED: [],  # Pas de transition à partir de 'delivered'
            self.STATUS_COMPLETED: [],  # Pas de transition à partir de 'completed'
            self.STATUS_CANCELLED: [],  # Pas de transition à partir de 'cancelled'
            self.STATUS_FAILED: [self.STATUS_PENDING],  # Possibilité de relancer
        }
        return transitions.get(self.status, [])
    
    def can_transition_to(self, new_status):
        """Vérifie si une transition vers new_status est permise"""
        return new_status in self.get_allowed_transitions()
    
    def transition_to(self, new_status):
        """Effectue la transition si elle est valide"""
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {self.status} to {new_status}. "
                f"Allowed transitions: {self.get_allowed_transitions()}"
            )
        self.status = new_status
        self.save()
        return True
