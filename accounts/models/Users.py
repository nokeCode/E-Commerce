from django.contrib.auth.models import AbstractUser
from django.db import models

class Users(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    first_name =  models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=100,blank=True)
    phone = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=10, choices=(('M', 'Male'), ('F', 'Female'), ('O', 'Other')), blank=True)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):  
        return self.email
