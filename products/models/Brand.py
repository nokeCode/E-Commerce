from django.db import models
from .Category import Category

class Brand(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='image/logo/', blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.name