"""
Security middleware for KleerLogistics project.
"""

import re
import logging
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware pour ajouter des en-têtes de sécurité."""
    
    def process_response(self, request, response):
        """Ajouter les en-têtes de sécurité à la réponse."""
        # Headers de sécurité de base
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HSTS (HTTP Strict Transport Security)
        if getattr(settings, 'SECURE_SSL_REDIRECT', False):
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """Middleware pour la limitation de taux."""
    
    def process_request(self, request):
        """Vérifier la limitation de taux."""
        if not getattr(settings, 'RATELIMIT_ENABLE', True):
            return None
        
        # Identifier la clé de rate limiting
        client_ip = self.get_client_ip(request)
        endpoint = request.path
        
        # Créer une clé unique pour cette combinaison IP/endpoint
        rate_key = f"{settings.RATELIMIT_KEY_PREFIX}:{client_ip}:{endpoint}"
        
        # Vérifier le nombre de requêtes
        request_count = cache.get(rate_key, 0)
        
        # Limites par défaut (peuvent être configurées dans settings)
        limits = getattr(settings, 'RATELIMIT_RULES', {})
        default_limit = limits.get('api_general', '100/h')  # 100 requêtes par heure
        
        # Parser la limite (format: "nombre/période")
        limit_parts = default_limit.split('/')
        max_requests = int(limit_parts[0])
        period = limit_parts[1]
        
        # Convertir la période en secondes
        period_seconds = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }.get(period[-1], 3600)
        
        if request_count >= max_requests:
            return JsonResponse({
                'success': False,
                'error': 'Rate limit exceeded',
                'message': f'Too many requests. Limit: {max_requests} per {period}'
            }, status=429)
        
        # Incrémenter le compteur
        cache.set(rate_key, request_count + 1, period_seconds)
        
        return None
    
    def get_client_ip(self, request):
        """Obtenir l'IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class InputSanitizationMiddleware(MiddlewareMixin):
    """Middleware pour la sanitisation des entrées."""
    
    def process_request(self, request):
        """Sanitiser les données d'entrée."""
        # Liste des patterns suspects
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
            r'onclick=',
            r'<iframe',
            r'<object',
            r'<embed',
        ]
        
        # Vérifier les paramètres GET
        for key, value in request.GET.items():
            if self.contains_suspicious_content(value, suspicious_patterns):
                return JsonResponse({
                    'success': False,
                    'error': 'Suspicious input detected',
                    'message': 'Input contains potentially dangerous content'
                }, status=400)
        
        # Vérifier les paramètres POST
        if request.method == 'POST':
            for key, value in request.POST.items():
                if self.contains_suspicious_content(value, suspicious_patterns):
                    return JsonResponse({
                        'success': False,
                        'error': 'Suspicious input detected',
                        'message': 'Input contains potentially dangerous content'
                    }, status=400)
        
        return None
    
    def contains_suspicious_content(self, value, patterns):
        """Vérifier si une valeur contient du contenu suspect."""
        if not isinstance(value, str):
            return False
        
        value_lower = value.lower()
        for pattern in patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False


class SQLInjectionProtectionMiddleware(MiddlewareMixin):
    """Middleware pour la protection contre les injections SQL."""
    
    def process_request(self, request):
        """Détecter les tentatives d'injection SQL."""
        sql_patterns = [
            r'(\b(union|select|insert|update|delete|drop|create|alter)\b)',
            r'(\b(or|and)\b\s+\d+\s*=\s*\d+)',
            r'(\b(union|select)\b.*\bfrom\b)',
            r'(\b(union|select)\b.*\bwhere\b)',
            r'(\b(union|select)\b.*\border\b\s+by)',
            r'(\b(union|select)\b.*\bgroup\b\s+by)',
            r'(\b(union|select)\b.*\bhaving\b)',
            r'(\b(union|select)\b.*\blimit\b)',
            r'(\b(union|select)\b.*\boffset\b)',
            r'(\b(union|select)\b.*\btop\b)',
            r'(\b(union|select)\b.*\bdistinct\b)',
            r'(\b(union|select)\b.*\bcount\b)',
            r'(\b(union|select)\b.*\bsum\b)',
            r'(\b(union|select)\b.*\bavg\b)',
            r'(\b(union|select)\b.*\bmax\b)',
            r'(\b(union|select)\b.*\bmin\b)',
            r'(\b(union|select)\b.*\bcase\b)',
            r'(\b(union|select)\b.*\bwhen\b)',
            r'(\b(union|select)\b.*\bthen\b)',
            r'(\b(union|select)\b.*\belse\b)',
            r'(\b(union|select)\b.*\bend\b)',
            r'(\b(union|select)\b.*\bas\b)',
            r'(\b(union|select)\b.*\bin\b)',
            r'(\b(union|select)\b.*\bbetween\b)',
            r'(\b(union|select)\b.*\blike\b)',
            r'(\b(union|select)\b.*\bis\b\s+null)',
            r'(\b(union|select)\b.*\bis\b\s+not\s+null)',
            r'(\b(union|select)\b.*\bexists\b)',
            r'(\b(union|select)\b.*\bnot\b\s+exists)',
            r'(\b(union|select)\b.*\bin\b\s*\()',
            r'(\b(union|select)\b.*\bnot\b\s+in\b\s*\()',
            r'(\b(union|select)\b.*\bany\b)',
            r'(\b(union|select)\b.*\ball\b)',
            r'(\b(union|select)\b.*\bsome\b)',
            r'(\b(union|select)\b.*\bwith\b)',
            r'(\b(union|select)\b.*\bcte\b)',
            r'(\b(union|select)\b.*\brecursive\b)',
            r'(\b(union|select)\b.*\bwindow\b)',
            r'(\b(union|select)\b.*\bover\b)',
            r'(\b(union|select)\b.*\bpartition\b\s+by)',
            r'(\b(union|select)\b.*\border\b\s+by)',
            r'(\b(union|select)\b.*\brows\b)',
            r'(\b(union|select)\b.*\brange\b)',
            r'(\b(union|select)\b.*\bpreceding\b)',
            r'(\b(union|select)\b.*\bfollowing\b)',
            r'(\b(union|select)\b.*\bunbounded\b)',
            r'(\b(union|select)\b.*\bcurrent\b\s+row)',
            r'(\b(union|select)\b.*\brow\b\s+number)',
            r'(\b(union|select)\b.*\brank\b)',
            r'(\b(union|select)\b.*\bdense_rank\b)',
            r'(\b(union|select)\b.*\bntile\b)',
            r'(\b(union|select)\b.*\blead\b)',
            r'(\b(union|select)\b.*\blag\b)',
            r'(\b(union|select)\b.*\bfirst_value\b)',
            r'(\b(union|select)\b.*\blast_value\b)',
            r'(\b(union|select)\b.*\bnth_value\b)',
            r'(\b(union|select)\b.*\bpercent_rank\b)',
            r'(\b(union|select)\b.*\bcume_dist\b)',
            r'(\b(union|select)\b.*\bpercentile_cont\b)',
            r'(\b(union|select)\b.*\bpercentile_disc\b)',
            r'(\b(union|select)\b.*\bmedian\b)',
            r'(\b(union|select)\b.*\bstddev\b)',
            r'(\b(union|select)\b.*\bvariance\b)',
            r'(\b(union|select)\b.*\bcorr\b)',
            r'(\b(union|select)\b.*\bcovar_pop\b)',
            r'(\b(union|select)\b.*\bcovar_samp\b)',
            r'(\b(union|select)\b.*\bregr_slope\b)',
            r'(\b(union|select)\b.*\bregr_intercept\b)',
            r'(\b(union|select)\b.*\bregr_count\b)',
            r'(\b(union|select)\b.*\bregr_r2\b)',
            r'(\b(union|select)\b.*\bregr_avgx\b)',
            r'(\b(union|select)\b.*\bregr_avgy\b)',
            r'(\b(union|select)\b.*\bregr_sxx\b)',
            r'(\b(union|select)\b.*\bregr_syy\b)',
            r'(\b(union|select)\b.*\bregr_sxy\b)',
            r'(\b(union|select)\b.*\bregr_slope\b)',
            r'(\b(union|select)\b.*\bregr_intercept\b)',
            r'(\b(union|select)\b.*\bregr_count\b)',
            r'(\b(union|select)\b.*\bregr_r2\b)',
            r'(\b(union|select)\b.*\bregr_avgx\b)',
            r'(\b(union|select)\b.*\bregr_avgy\b)',
            r'(\b(union|select)\b.*\bregr_sxx\b)',
            r'(\b(union|select)\b.*\bregr_syy\b)',
            r'(\b(union|select)\b.*\bregr_sxy\b)',
        ]
        
        # Vérifier tous les paramètres
        all_params = {}
        all_params.update(request.GET)
        all_params.update(request.POST)
        
        for key, value in all_params.items():
            if isinstance(value, str) and self.detect_sql_injection(value, sql_patterns):
                logger.warning(f"Potential SQL injection detected from IP: {self.get_client_ip(request)}")
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid input detected',
                    'message': 'Request contains invalid characters'
                }, status=400)
        
        return None
    
    def detect_sql_injection(self, value, patterns):
        """Détecter les tentatives d'injection SQL."""
        value_lower = value.lower()
        for pattern in patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False
    
    def get_client_ip(self, request):
        """Obtenir l'IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class FileUploadSecurityMiddleware(MiddlewareMixin):
    """Middleware pour la sécurité des uploads de fichiers."""
    
    def process_request(self, request):
        """Vérifier la sécurité des fichiers uploadés."""
        if request.method == 'POST' and request.FILES:
            for uploaded_file in request.FILES.values():
                if not self.is_file_safe(uploaded_file):
                    return JsonResponse({
                        'success': False,
                        'error': 'Unsafe file type',
                        'message': 'File type not allowed'
                    }, status=400)
        
        return None
    
    def is_file_safe(self, uploaded_file):
        """Vérifier si un fichier est sûr."""
        # Types de fichiers autorisés
        allowed_types = [
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/webp',
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain',
        ]
        
        # Vérifier le type MIME
        if uploaded_file.content_type not in allowed_types:
            return False
        
        # Vérifier la taille (max 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            return False
        
        # Vérifier l'extension
        safe_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt']
        file_name = uploaded_file.name.lower()
        if not any(file_name.endswith(ext) for ext in safe_extensions):
            return False
        
        return True


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware pour le logging des requêtes."""
    
    def process_request(self, request):
        """Logger les informations de la requête."""
        logger.info(f"Request: {request.method} {request.path} from {self.get_client_ip(request)}")
        return None
    
    def process_response(self, request, response):
        """Logger les informations de la réponse."""
        logger.info(f"Response: {response.status_code} for {request.method} {request.path}")
        return response
    
    def get_client_ip(self, request):
        """Obtenir l'IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip 