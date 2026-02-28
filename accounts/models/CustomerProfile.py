from django.db import models
from .Users import Users
from django.contrib.auth.models import User
from products.utils import get_profile_image_upload_path

class CustomerProfile(models.Model):
    user = models.OneToOneField(Users, on_delete=models.CASCADE)
    address = models.TextField(blank=True)
    photo = models.ImageField(upload_to=get_profile_image_upload_path, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    is_vip = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile of {self.user.email}"