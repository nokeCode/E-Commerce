from django.db import models
from .Product import Product
from products.utils import get_product_image_upload_path

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=get_product_image_upload_path)
    is_main = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.product.name}"
    
    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"