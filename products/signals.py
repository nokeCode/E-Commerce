from django.db.models.signals import post_save
from django.dispatch import receiver
from products.models import Category
from products.utils import ensure_category_image_folder


@receiver(post_save, sender=Category)
def create_category_image_folder(sender, instance, created, **kwargs):
    """
    Signal pour créer automatiquement le dossier image d'une catégorie
    quand celle-ci est créée.
    """
    if created:
        ensure_category_image_folder(instance.slug)
