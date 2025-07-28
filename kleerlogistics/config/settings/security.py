"""
Security settings for KleerLogistics.
This file contains security configurations that can be imported by different environment settings.
"""

import os
from datetime import timedelta

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# CSRF Settings
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Session Security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600  # 1 hour

# Password Security
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# Additional Security Headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # Set to True in production

# File Upload Security
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_SCRIPT_SRC = ("'self'",)
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https:", "data:")
CSP_CONNECT_SRC = ("'self'",)
CSP_MEDIA_SRC = ("'self'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_FRAME_SRC = ("'none'",)
CSP_WORKER_SRC = ("'self'",)
CSP_MANIFEST_SRC = ("'self'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_UPGRADE_INSECURE_REQUESTS = True

# Django Axes Configuration (Brute Force Protection)
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5  # Number of failed attempts before lockout
AXES_LOCK_OUT_AT_FAILURE = True
AXES_COOLOFF_TIME = 1  # Hours
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True
AXES_LOCK_OUT_BY_USER_OR_IP = False
AXES_LOCK_OUT_BY_IP_AND_USERNAME = True
AXES_USE_USER_AGENT = True
AXES_VERBOSE = True
AXES_LOCKOUT_TEMPLATE = 'axes/lockout.html'
AXES_LOCKOUT_URL = '/locked-out/'
AXES_RESET_ON_SUCCESS = True

# Rate Limiting Configuration
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_KEY_PREFIX = 'rl'

# Rate Limiting Rules (requests per time period)
RATELIMIT_RULES = {
    'api_auth': '5/m',  # 5 requests per minute for auth endpoints
    'api_general': '100/h',  # 100 requests per hour for general API
    'api_upload': '10/h',  # 10 uploads per hour
    'api_payment': '20/h',  # 20 payment requests per hour
    'admin_login': '3/m',  # 3 admin login attempts per minute
    'user_registration': '3/h',  # 3 registrations per hour per IP
    'password_reset': '3/h',  # 3 password reset requests per hour
}

# JWT Security Settings
JWT_SECURITY_SETTINGS = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'TOKEN_USER_CLASS': 'users.User',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# CORS Security Settings
CORS_SECURITY_SETTINGS = {
    'CORS_ALLOWED_ORIGINS': [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    'CORS_ALLOWED_ORIGIN_REGEXES': [
        r"^https://\w+\.kleerinfini\.com$",
        r"^https://kleerinfini\.com$",
    ],
    'CORS_ALLOW_CREDENTIALS': True,
    'CORS_ALLOW_METHODS': [
        'DELETE',
        'GET',
        'OPTIONS',
        'PATCH',
        'POST',
        'PUT',
    ],
    'CORS_ALLOW_HEADERS': [
        'accept',
        'accept-encoding',
        'authorization',
        'content-type',
        'dnt',
        'origin',
        'user-agent',
        'x-csrftoken',
        'x-requested-with',
    ],
    'CORS_EXPOSE_HEADERS': [
        'content-type',
        'content-disposition',
    ],
    'CORS_PREFLIGHT_MAX_AGE': 86400,  # 24 hours
}

# Security Logging Configuration
SECURITY_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'logs/security.log',
            'formatter': 'security',
        },
        'security_console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'security',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['security_file', 'security_console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'axes': {
            'handlers': ['security_file', 'security_console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Security Headers
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
}

# File Upload Security
FILE_UPLOAD_SECURITY = {
    'ALLOWED_EXTENSIONS': ['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx'],
    'MAX_SIZE_MB': 10,
    'SCAN_VIRUS': False,  # Set to True if virus scanning is available
    'VALIDATE_CONTENT_TYPE': True,
    'SANITIZE_FILENAMES': True,
}

# API Security
API_SECURITY = {
    'REQUIRE_HTTPS': True,
    'RATE_LIMIT_ENABLED': True,
    'INPUT_SANITIZATION': True,
    'SQL_INJECTION_PROTECTION': True,
    'XSS_PROTECTION': True,
    'CSRF_PROTECTION': True,
}

# Database Security
DATABASE_SECURITY = {
    'CONNECTION_MAX_AGE': 600,  # 10 minutes
    'OPTIONS': {
        'sslmode': 'require',  # Require SSL for database connections
    },
}

# Cache Security
CACHE_SECURITY = {
    'ENCRYPTION': False,  # Set to True if cache encryption is needed
    'COMPRESSION': True,
    'VALIDATION': True,
}

# Email Security
EMAIL_SECURITY = {
    'USE_TLS': True,
    'USE_SSL': False,
    'REQUIRE_TLS': True,
    'VERIFY_SSL': True,
}

# Payment Security
PAYMENT_SECURITY = {
    'REQUIRE_HTTPS': True,
    'VALIDATE_AMOUNT': True,
    'MAX_AMOUNT': 1000000,  # 1 million DZD
    'CURRENCY_VALIDATION': True,
    'ALLOWED_CURRENCIES': ['DZD', 'EUR', 'USD'],
}

# User Data Security
USER_DATA_SECURITY = {
    'PASSWORD_MIN_LENGTH': 8,
    'PASSWORD_REQUIRE_UPPERCASE': True,
    'PASSWORD_REQUIRE_LOWERCASE': True,
    'PASSWORD_REQUIRE_DIGITS': True,
    'PASSWORD_REQUIRE_SPECIAL': True,
    'USERNAME_MIN_LENGTH': 3,
    'USERNAME_MAX_LENGTH': 30,
    'EMAIL_VERIFICATION_REQUIRED': True,
    'PHONE_VERIFICATION_REQUIRED': True,
}

# Shipment Security
SHIPMENT_SECURITY = {
    'MAX_WEIGHT_KG': 50,
    'MAX_DIMENSION_CM': 200,
    'PROHIBITED_ITEMS': [
        'weapon', 'drug', 'explosive', 'flammable', 'toxic', 'radioactive',
        'weapon', 'arme', 'drogue', 'explosif', 'inflammable', 'toxique'
    ],
    'CONTENT_VALIDATION': True,
    'SIZE_VALIDATION': True,
    'WEIGHT_VALIDATION': True,
} 