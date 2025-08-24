"""
App configuration for verification app - Document verification and validation
"""

from django.apps import AppConfig


class VerificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'verification'
    verbose_name = 'Vérification de Documents'
    
    def ready(self):
        """Configuration à l'initialisation de l'application."""
        try:
            import kleerlogistics.verification.signals
        except ImportError:
            pass
