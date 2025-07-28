"""
Django settings for KleerLogistics project.
"""

import os

# Set the Django settings module based on environment
DJANGO_SETTINGS_MODULE = os.environ.get('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Import the appropriate settings
if DJANGO_SETTINGS_MODULE == 'config.settings.development':
    from .settings.development import *
elif DJANGO_SETTINGS_MODULE == 'config.settings.production':
    from .settings.production import *
elif DJANGO_SETTINGS_MODULE == 'config.settings.testing':
    from .settings.testing import *
else:
    from .settings.development import *
