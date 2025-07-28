"""
Security decorators for KleerLogistics views.
"""

import functools
import logging
from django.http import HttpResponseForbidden, JsonResponse
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from config.validators import SecurityValidator, sanitize_user_input


def rate_limit(key_func=None, rate='100/h', block=True):
    """
    Rate limiting decorator for views.
    
    Args:
        key_func: Function to generate cache key (default: IP address)
        rate: Rate limit string (e.g., '100/h', '5/m')
        block: Whether to block requests or just log them
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Parse rate limit
            requests, period = _parse_rate_limit(rate)
            
            # Generate cache key
            if key_func:
                cache_key = f"rate_limit:{key_func(request)}"
            else:
                cache_key = f"rate_limit:{_get_client_ip(request)}"
            
            # Check current requests
            current_requests = cache.get(cache_key, 0)
            
            if current_requests >= requests:
                if block:
                    return HttpResponseForbidden(_('Rate limit exceeded. Please try again later.'))
                else:
                    # Log but don't block
                    logger = logging.getLogger('security')
                    logger.warning(f'Rate limit exceeded for {cache_key}')
            
            # Increment request count
            cache.set(cache_key, current_requests + 1, period)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def _parse_rate_limit(rate_string):
    """Parse rate limit string (e.g., '100/h' -> (100, 3600))."""
    requests, period = rate_string.split('/')
    requests = int(requests)
    
    if period == 's':
        period = 1
    elif period == 'm':
        period = 60
    elif period == 'h':
        period = 3600
    elif period == 'd':
        period = 86400
    else:
        period = 3600  # Default to 1 hour
    
    return requests, period


def _get_client_ip(request):
    """Get the real client IP address."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def sanitize_input(view_func):
    """Decorator to sanitize input data."""
    @functools.wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        # Sanitize GET parameters
        if request.GET:
            request.GET = _sanitize_querydict(request.GET)
        
        # Sanitize POST parameters
        if request.POST:
            request.POST = _sanitize_querydict(request.POST)
        
        # Sanitize JSON data
        if hasattr(request, 'data') and request.data:
            request.data = sanitize_user_input(request.data)
        
        return view_func(request, *args, **kwargs)
    return wrapped_view


def _sanitize_querydict(querydict):
    """Sanitize QueryDict values."""
    from django.http import QueryDict
    
    sanitized = QueryDict(mutable=True)
    
    for key, value in querydict.items():
        if isinstance(value, str):
            sanitized_value = SecurityValidator.sanitize_html(value)
            sanitized.appendlist(key, sanitized_value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    sanitized_item = SecurityValidator.sanitize_html(item)
                    sanitized.appendlist(key, sanitized_item)
                else:
                    sanitized.appendlist(key, item)
        else:
            sanitized.appendlist(key, value)
    
    return sanitized


def validate_file_upload(allowed_extensions=None, max_size_mb=10):
    """Decorator to validate file uploads."""
    if allowed_extensions is None:
        allowed_extensions = ['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx']
    
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if request.method == 'POST' and request.FILES:
                for field_name, uploaded_file in request.FILES.items():
                    # Check file size
                    if not SecurityValidator.validate_file_size(uploaded_file.size, max_size_mb):
                        return JsonResponse({
                            'error': f'File size must not exceed {max_size_mb}MB.'
                        }, status=400)
                    
                    # Check file type
                    if not SecurityValidator.validate_file_type(uploaded_file.name, allowed_extensions):
                        return JsonResponse({
                            'error': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'
                        }, status=400)
                    
                    # Sanitize filename
                    uploaded_file.name = SecurityValidator.sanitize_filename(uploaded_file.name)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def log_suspicious_activity(view_func):
    """Decorator to log suspicious activity."""
    @functools.wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        # Check for suspicious patterns
        suspicious_patterns = [
            r'\.\./',  # Path traversal
            r'<script',  # XSS attempt
            r'javascript:',  # XSS attempt
            r'data:text/html',  # XSS attempt
            r'vbscript:',  # XSS attempt
        ]
        
        request_path = request.path.lower()
        request_headers = str(request.headers).lower()
        
        for pattern in suspicious_patterns:
            if re.search(pattern, request_path, re.IGNORECASE) or \
               re.search(pattern, request_headers, re.IGNORECASE):
                # Log suspicious request
                logger = logging.getLogger('security')
                logger.warning(
                    f'Suspicious activity detected: {request.method} {request.path} '
                    f'from {_get_client_ip(request)}'
                )
                break
        
        return view_func(request, *args, **kwargs)
    return wrapped_view


def require_https(view_func):
    """Decorator to require HTTPS."""
    @functools.wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.is_secure() and not settings.DEBUG:
            return HttpResponseForbidden(_('HTTPS is required for this endpoint.'))
        return view_func(request, *args, **kwargs)
    return wrapped_view


def validate_json_schema(schema):
    """Decorator to validate JSON schema."""
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    from jsonschema import validate
                    validate(request.data, schema)
                except ImportError:
                    # jsonschema not installed, skip validation
                    pass
                except Exception as e:
                    return JsonResponse({
                        'error': f'Invalid data format: {str(e)}'
                    }, status=400)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


# Combined security decorator for API views
def secure_api_view(methods=None, rate_limit_rate='100/h', require_auth=True):
    """Combined security decorator for API views."""
    def decorator(view_func):
        # Apply multiple decorators
        if methods:
            view_func = require_http_methods(methods)(view_func)
        
        view_func = rate_limit(rate=rate_limit_rate)(view_func)
        view_func = sanitize_input(view_func)
        view_func = log_suspicious_activity(view_func)
        
        if require_auth:
            view_func = api_view(methods or ['GET', 'POST'])(view_func)
            view_func = permission_classes([IsAuthenticated])(view_func)
        
        return view_func
    return decorator


# Combined security decorator for file upload views
def secure_file_upload_view(allowed_extensions=None, max_size_mb=10, rate_limit_rate='10/h'):
    """Combined security decorator for file upload views."""
    def decorator(view_func):
        view_func = require_http_methods(['POST'])(view_func)
        view_func = rate_limit(rate=rate_limit_rate)(view_func)
        view_func = validate_file_upload(allowed_extensions, max_size_mb)(view_func)
        view_func = sanitize_input(view_func)
        view_func = log_suspicious_activity(view_func)
        view_func = api_view(['POST'])(view_func)
        view_func = permission_classes([IsAuthenticated])(view_func)
        return view_func
    return decorator


# Import required modules
import re
from django.conf import settings 