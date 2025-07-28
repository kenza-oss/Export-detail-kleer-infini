"""
Production settings for KleerLogistics project.
Optimized for Backend Development - DevOps configurations handled separately.
"""

from .base import *

# =============================================================================
# CORE DJANGO SETTINGS FOR BACKEND
# =============================================================================

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Backend-specific: Configure allowed hosts for your API endpoints
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# =============================================================================
# DATABASE CONFIGURATION (Backend Priority)
# =============================================================================

# PostgreSQL Database Configuration
# Note: DevOps team will handle connection pooling and optimization
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
            # Backend-specific database optimizations
            'connect_timeout': 10,
            'application_name': 'kleerlogistics_backend',
        },
        # Connection pooling handled by DevOps
        'CONN_MAX_AGE': 600,  # 10 minutes
        'CONN_HEALTH_CHECKS': True,
    }
}

# =============================================================================
# CACHE & REDIS CONFIGURATION (Backend Priority)
# =============================================================================

# Redis Configuration for Production
REDIS_URL = os.environ.get('REDIS_URL')

# Celery Configuration for Production
CELERY_BROKER_URL = f"{REDIS_URL}/0"
CELERY_RESULT_BACKEND = f"{REDIS_URL}/0"

# Cache Configuration for Production
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f"{REDIS_URL}/1",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'TIMEOUT': 300,  # 5 minutes default timeout
    },
    'session': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f"{REDIS_URL}/2",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'TIMEOUT': 3600,  # 1 hour for sessions
    },
    'api': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f"{REDIS_URL}/3",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'TIMEOUT': 600,  # 10 minutes for API responses
    }
}

# =============================================================================
# SECURITY SETTINGS (Backend Implementation)
# =============================================================================

# SSL/HTTPS Configuration
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Backend-specific security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
X_CONTENT_TYPE_OPTIONS = 'nosniff'

# =============================================================================
# CORS & API SETTINGS (Backend Priority)
# =============================================================================

# CORS Settings for Production
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = True

# Backend-specific CORS settings
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# =============================================================================
# EMAIL CONFIGURATION (Backend Implementation)
# =============================================================================

# Email Configuration for Production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# Backend-specific email settings
EMAIL_TIMEOUT = 30  # 30 seconds timeout
EMAIL_USE_LOCALTIME = True

# =============================================================================
# FILE HANDLING (Backend Implementation)
# =============================================================================

# Static files for Production
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Media files for Production (consider using cloud storage)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Backend-specific file upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# =============================================================================
# LOGGING CONFIGURATION (Backend Priority)
# =============================================================================

# Logging for Production
LOGGING['handlers']['file']['level'] = 'WARNING'
LOGGING['loggers']['kleerlogistics']['level'] = 'INFO'

# Backend-specific logging enhancements
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['file'],
    'level': 'WARNING',
    'propagate': False,
}

LOGGING['loggers']['celery'] = {
    'handlers': ['file'],
    'level': 'INFO',
    'propagate': False,
}

LOGGING['loggers']['kleerlogistics.api'] = {
    'handlers': ['file'],
    'level': 'INFO',
    'propagate': False,
}

# =============================================================================
# API & REST FRAMEWORK SETTINGS (Backend Priority)
# =============================================================================

# Production-specific REST Framework settings
REST_FRAMEWORK.update({
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'burst': '60/minute',
    },
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1', 'v2'],
    'DEFAULT_VERSION_PARAM': 'version',
})

# =============================================================================
# CELERY CONFIGURATION (Backend Priority)
# =============================================================================

# Celery Production Settings
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_TASK_IGNORE_RESULT = False
CELERY_TASK_STORE_EAGER_RESULT = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_DISABLE_RATE_LIMITS = False

# =============================================================================
# PERFORMANCE & OPTIMIZATION (Backend Priority)
# =============================================================================

# Database query optimization
DATABASES['default']['OPTIONS'].update({
    'statement_timeout': 30000,  # 30 seconds
    'idle_in_transaction_session_timeout': 60000,  # 60 seconds
})

# Session optimization
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'

# =============================================================================
# PRODUCTION FLAGS
# =============================================================================

# Production-specific settings
PRODUCTION = True

# Backend-specific environment flags
ENABLE_API_DOCUMENTATION = os.environ.get('ENABLE_API_DOCUMENTATION', 'True').lower() == 'true'
ENABLE_DEBUG_TOOLBAR = False
ENABLE_SILK_PROFILING = False

# =============================================================================
# BACKEND-SPECIFIC CONFIGURATIONS
# =============================================================================

# API Rate limiting for specific endpoints
API_RATE_LIMITS = {
    'auth': {
        'login': '5/minute',
        'register': '3/hour',
        'password_reset': '3/hour',
    },
    'shipments': {
        'create': '10/hour',
        'list': '100/hour',
        'detail': '200/hour',
    },
    'payments': {
        'create': '20/hour',
        'webhook': '100/hour',
    },
}

# Backend health check endpoints
HEALTH_CHECK_ENDPOINTS = [
    '/health/',
    '/health/db/',
    '/health/cache/',
    '/health/celery/',
]

# =============================================================================
# ENVIRONMENT-SPECIFIC OVERRIDES
# =============================================================================

# Override settings based on environment variables
if os.environ.get('ENABLE_DEBUG_MODE'):
    DEBUG = True
    LOGGING['loggers']['kleerlogistics']['level'] = 'DEBUG'

if os.environ.get('DISABLE_SSL_REDIRECT'):
    SECURE_SSL_REDIRECT = False

# =============================================================================
# BACKEND DEVELOPMENT NOTES
# =============================================================================

"""
Backend Developer Notes:
- All database migrations should be tested in staging before production
- API versioning is enabled - maintain backward compatibility
- Rate limiting is configured per endpoint - adjust as needed
- Health check endpoints are available for monitoring
- Celery tasks have time limits - optimize long-running tasks
- Cache is configured for sessions, API responses, and general use
- Logging is configured for different components - check logs regularly

DevOps Team Responsibilities:
- SSL certificate management
- Load balancer configuration
- Database connection pooling
- Redis cluster management
- Container orchestration
- Monitoring and alerting
- Backup and disaster recovery
""" 