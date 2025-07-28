"""
Configuration de sécurité pour JWT et OTP
"""

import os
from datetime import timedelta

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-jwt-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_LIFETIME = timedelta(minutes=60)
JWT_REFRESH_TOKEN_LIFETIME = timedelta(days=7)
JWT_ROTATE_REFRESH_TOKENS = True
JWT_BLACKLIST_AFTER_ROTATION = True

# OTP Configuration
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
OTP_MAX_ATTEMPTS = 3
OTP_RESEND_COOLDOWN_MINUTES = 1

# SMS Configuration (pour production)
SMS_PROVIDER = os.environ.get('SMS_PROVIDER', 'console')  # console, twilio, vonage
SMS_API_KEY = os.environ.get('SMS_API_KEY', '')
SMS_API_SECRET = os.environ.get('SMS_API_SECRET', '')
SMS_FROM_NUMBER = os.environ.get('SMS_FROM_NUMBER', '')

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Password Validation
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGITS = True
PASSWORD_REQUIRE_SPECIAL_CHARS = True

# Rate Limiting
RATE_LIMIT_LOGIN_ATTEMPTS = 5
RATE_LIMIT_LOGIN_WINDOW = 300  # 5 minutes
RATE_LIMIT_OTP_ATTEMPTS = 3
RATE_LIMIT_OTP_WINDOW = 600  # 10 minutes

# Session Configuration
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600  # 1 hour

# CSRF Configuration
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'users.backends.PhoneNumberBackend',
]

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Login URLs
LOGIN_URL = '/api/auth/login/'
LOGIN_REDIRECT_URL = '/api/auth/profile/'
LOGOUT_REDIRECT_URL = '/api/auth/login/' 