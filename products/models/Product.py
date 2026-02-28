from django.db import models
from .Category import Category
from .Brand import Brand
from accounts.models import Users
from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def get_average_rating(self):
        """Calcule la note moyenne basée sur les avis associés."""
        reviews = self.reviews.all()
        if reviews.count() == 0:
            return 0
        total_rating = sum(review.rating for review in reviews)
        return round(total_rating / reviews.count(), 1)
    
    def get_reviews_count(self):
        """Retourne le nombre d'avis pour ce produit."""
        return self.reviews.count()
    
    
class Favorite(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.email} favourite {self.product.name}"


        