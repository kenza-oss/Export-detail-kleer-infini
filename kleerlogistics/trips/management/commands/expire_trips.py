"""
Commande Django pour expirer automatiquement les trajets en retard
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from trips.signals import expire_expired_trips, cleanup_old_trips


class Command(BaseCommand):
    """Commande pour expirer les trajets en retard."""
    
    help = 'Expire automatiquement les trajets en retard et nettoie les anciens trajets'
    
    def add_arguments(self, parser):
        """Ajouter des arguments à la commande."""
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Nettoyer également les anciens trajets (plus de 6 mois)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simuler l\'exécution sans effectuer de modifications'
        )
    
    def handle(self, *args, **options):
        """Exécuter la commande."""
        self.stdout.write(
            self.style.SUCCESS('🚀 Début de l\'expiration automatique des trajets...')
        )
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('⚠️  Mode simulation activé - Aucune modification ne sera effectuée')
            )
        
        try:
            with transaction.atomic():
                # Expirer les trajets en retard
                if not options['dry_run']:
                    expire_expired_trips()
                
                # Nettoyer les anciens trajets si demandé
                if options['cleanup']:
                    if not options['dry_run']:
                        cleanup_old_trips()
                    else:
                        self.stdout.write(
                            self.style.WARNING('🧹 Nettoyage des anciens trajets simulé')
                        )
                
                self.stdout.write(
                    self.style.SUCCESS('✅ Expiration automatique terminée avec succès')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de l\'expiration: {e}')
            )
            raise
