import os
from django.conf import settings
from pathlib import Path


# Configuration des uploads (décommenter la ligne appropriée selon vos besoins)
USE_MEDIA_ROOT = True  # True pour utiliser MEDIA_ROOT (recommandé), False pour STATIC_ROOT

def _get_upload_directory():
    """Retourne le répertoire d'upload configuré"""
    if USE_MEDIA_ROOT:
        return settings.MEDIA_ROOT
    else:
        return settings.STATIC_ROOT


def get_product_image_upload_path(instance, filename):
    """
    Génère le chemin d'upload dynamique pour les images de produit.
    Format: image/categorie_slug/brand_slug/filename
    Crée automatiquement les dossiers s'ils n'existent pas.
    
    Le fichier sera sauvegardé dans:
    - MEDIA_ROOT/image/{category_slug}/{brand_slug}/{filename} (recommandé)
    - STATIC_ROOT/image/{category_slug}/{brand_slug}/{filename} (alternatif)
    """
    # Récupérer la catégorie et la marque du produit
    category_slug = instance.product.category.slug if instance.product.category else 'uncategorized'
    brand_slug = instance.product.brand.slug if instance.product.brand else 'no-brand'
    
    # Construire le chemin relatif
    upload_path = f"image/{category_slug}/{brand_slug}/{filename}"
    
    # Créer les dossiers s'ils n'existent pas dans le répertoire approprié
    root_dir = _get_upload_directory()
    full_path = os.path.join(root_dir, upload_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    return upload_path


def get_profile_image_upload_path(instance, filename):
    """
    Génère le chemin d'upload dynamique pour les images de profil utilisateur.
    Format: image/profile/username/filename
    Crée automatiquement les dossiers s'ils n'existent pas.
    
    Le fichier sera sauvegardé dans:
    - MEDIA_ROOT/image/profile/{username}/{filename} (recommandé)
    - STATIC_ROOT/image/profile/{username}/{filename} (alternatif)
    """
    username = instance.user.username if hasattr(instance, 'user') else 'default'
    upload_path = f"image/profile/{username}/{filename}"
    
    # Créer les dossiers s'ils n'existent pas dans le répertoire approprié
    root_dir = _get_upload_directory()
    full_path = os.path.join(root_dir, upload_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    return upload_path


def ensure_category_image_folder(category_slug):
    """
    Crée automatiquement le dossier pour une catégorie.
    Appelé quand une nouvelle catégorie est créée au via signals.
    
    Crée: MEDIA_ROOT/image/{category_slug} ou STATIC_ROOT/image/{category_slug}
    """
    root_dir = _get_upload_directory()
    folder_path = os.path.join(root_dir, 'image', category_slug)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path
