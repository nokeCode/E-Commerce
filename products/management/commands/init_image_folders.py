from django.core.management.base import BaseCommand
from products.models import Category
from products.utils import ensure_category_image_folder


class Command(BaseCommand):
    help = 'Initialise tous les dossiers d\'images pour les catégories existantes'

    def handle(self, *args, **options):
        categories = Category.objects.all()
        
        if not categories.exists():
            self.stdout.write(self.style.WARNING('⚠️  Aucune catégorie trouvée'))
            return
        
        created_count = 0
        
        for category in categories:
            try:
                ensure_category_image_folder(category.slug)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Dossier créé pour: {category.name} ({category.slug})')
                )
                created_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Erreur pour {category.name}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✨ {created_count} dossier(s) initialisé(s) avec succès!')
        )
