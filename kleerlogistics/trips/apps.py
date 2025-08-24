from django.apps import AppConfig


class TripsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trips'
    verbose_name = 'Gestion des Trajets'
    
    def ready(self):
        """Configuration lors du démarrage de l'app."""
        try:
            import trips.signals  # noqa
        except ImportError:
            pass
