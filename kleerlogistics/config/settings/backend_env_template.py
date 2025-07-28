# =============================================================================
# KLEERLOGISTICS - TEMPLATE CONFIGURATION ENVIRONNEMENT
# =============================================================================
# Copiez ce fichier vers .env et modifiez les valeurs selon votre environnement

# =============================================================================
# BASE CONFIGURATION
# =============================================================================
DEBUG=True
SECRET_KEY=django-insecure-^f14iq795^q7^_1b$q0f%xvo3ky)@i4)5j4!pyk$&bf8e9!w1q
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# =============================================================================
# BASE DE DONNÉES POSTGRESQL
# =============================================================================
DB_NAME=kleerlogistics
DB_USER=romualdo
DB_PASSWORD=supersecure
DB_HOST=localhost
DB_PORT=5432

# =============================================================================
# REDIS & CELERY
# =============================================================================
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# =============================================================================
# PAYMENT GATEWAY (CHARGILY)
# =============================================================================
CHARGILY_API_KEY=your-chargily-api-key
CHARGILY_SECRET_KEY=your-chargily-secret-key
CHARGILY_WEBHOOK_SECRET=your-chargily-webhook-secret

# =============================================================================
# SECURITY & RATE LIMITING
# =============================================================================
AXES_FAILURE_LIMIT=5
AXES_COOLOFF_TIME=1
RATELIMIT_ENABLE=True

# =============================================================================
# FILE UPLOAD
# =============================================================================
FILE_UPLOAD_MAX_MEMORY_SIZE=10485760
DATA_UPLOAD_MAX_MEMORY_SIZE=10485760

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================
LANGUAGE_CODE=fr-fr
TIME_ZONE=Africa/Algiers

# =============================================================================
# CORS SETTINGS
# =============================================================================
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000

# =============================================================================
# LOGGING
# =============================================================================
LOG_LEVEL=INFO
LOG_FILE=logs/kleerlogistics.log

# =============================================================================
# DEVELOPMENT SPECIFIC
# =============================================================================
DEVELOPMENT=True 