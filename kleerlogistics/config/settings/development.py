"""
Development settings for KleerLogistics project.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# PostgreSQL Database Configuration for Development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'kleerlogistics'),
        'USER': os.environ.get('DB_USER', 'romualdo'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'supersecure'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
            'application_name': 'kleerlogistics_dev',
        },
        # Development-specific settings
        'CONN_MAX_AGE': 60,  # 1 minute for development
        'CONN_HEALTH_CHECKS': True,
    }
}

# Redis Configuration for Development
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')

# Celery Configuration for Development
CELERY_BROKER_URL = f"{REDIS_URL}/0"
CELERY_RESULT_BACKEND = f"{REDIS_URL}/0"

# Cache Configuration for Development - Use Redis for consistency with production
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f"{REDIS_URL}/1",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'TIMEOUT': 300,  # 5 minutes
    },
    'session': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f"{REDIS_URL}/2",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'TIMEOUT': 3600,  # 1 hour
    }
}

# Fallback to local memory cache if Redis is not available
try:
    import redis
    redis.Redis.from_url(REDIS_URL).ping()
except:
    print("⚠️  Redis not available. Using local memory cache.")
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }

# Email Configuration for Development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Debug Toolbar (temporarily disabled to avoid namespace issues)
# if DEBUG:
#     INSTALLED_APPS += ['debug_toolbar']
#     MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
#     INTERNAL_IPS = ['127.0.0.1']

# CORS Settings for Development
CORS_ALLOW_ALL_ORIGINS = True

# Logging for Development
LOGGING['loggers']['kleerlogistics']['level'] = 'DEBUG'

# Add database logging for development
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': False,
}

# Static files serving in development
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Media files serving in development
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Development-specific settings
DEVELOPMENT = True 