from django.db import models
from .Users import Users
from django.contrib.auth.models import User

class UserSession(models.Model):
    """
    NOUVEAU MODÈLE - Gestion des sessions actives pour la sécurité
    Permet de voir tous les appareils connectés
    """
    DEVICE_TYPES = [
        ('desktop', 'Ordinateur'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablette'),
    ]
    
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, blank=True, null=True)
    browser = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type} - {self.browser}"
    
    def get_device_icon(self):
        """Retourne l'icône FontAwesome appropriée"""
        icons = {
            'desktop': 'fa-desktop',
            'mobile': 'fa-mobile-alt',
            'tablet': 'fa-tablet-alt',
        }
        return icons.get(self.device_type, 'fa-laptop')
    
    class Meta:
        verbose_name = "Session utilisateur"
        verbose_name_plural = "Sessions utilisateurs"
        ordering = ['-last_activity']
