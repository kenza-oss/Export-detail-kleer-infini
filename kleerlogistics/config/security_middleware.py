"""
Security Middleware for KleerLogistics
Provides advanced security features including anomaly detection, IP tracking, and threat prevention.
"""

import logging
from django.http import HttpResponseForbidden, HttpResponse
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
import ipaddress
import re
from datetime import timedelta
from typing import Dict, List, Optional

logger = logging.getLogger('security')

class SecurityMiddleware:
    """
    Middleware de sécurité avancé pour KleerLogistics.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
            r'<iframe',
            r'<object',
            r'<embed',
            r'<applet',
            r'<meta[^>]*refresh',
            r'<link[^>]*javascript',
            r'<form[^>]*action[^>]*javascript',
        ]
        
        # IPs suspectes (à étendre)
        self.suspicious_ips = set()
        
        # User agents suspects
        self.suspicious_user_agents = [
            'sqlmap',
            'nikto',
            'nmap',
            'w3af',
            'burp',
            'zap',
            'acunetix',
            'nessus',
            'openvas',
            'metasploit',
            'hydra',
            'medusa',
            'john',
            'hashcat',
        ]

    def __call__(self, request):
        # Vérifications de sécurité avant traitement
        security_check = self.perform_security_checks(request)
        if security_check:
            return security_check
        
        # Traitement de la requête
        response = self.get_response(request)
        
        # Ajout des headers de sécurité
        response = self.add_security_headers(response)
        
        # Logging de sécurité
        self.log_security_event(request, response)
        
        return response

    def perform_security_checks(self, request) -> Optional[HttpResponse]:
        """Effectuer toutes les vérifications de sécurité."""
        
        # 1. Vérification de l'IP
        ip_check = self.check_ip_address(request)
        if ip_check:
            return ip_check
        
        # 2. Vérification du User Agent
        ua_check = self.check_user_agent(request)
        if ua_check:
            return ua_check
        
        # 3. Vérification des paramètres suspects
        param_check = self.check_suspicious_parameters(request)
        if param_check:
            return param_check
        
        # 4. Vérification du rate limiting
        rate_check = self.check_rate_limiting(request)
        if rate_check:
            return rate_check
        
        # 5. Vérification des tentatives de connexion échouées
        if hasattr(request, 'user') and request.user.is_authenticated:
            login_check = self.check_failed_login_attempts(request)
            if login_check:
                return login_check
        
        return None

    def check_ip_address(self, request) -> Optional[HttpResponse]:
        """Vérifier l'adresse IP pour les menaces."""
        client_ip = self.get_client_ip(request)
        
        # Vérifier si l'IP est dans la liste noire
        if client_ip in self.suspicious_ips:
            logger.warning(f"Suspicious IP detected: {client_ip}")
            return HttpResponseForbidden("Access denied")
        
        # Vérifier les IPs privées (si non autorisées)
        if not settings.DEBUG and not getattr(settings, 'TESTING', False):
            try:
                ip = ipaddress.ip_address(client_ip)
                if ip.is_private and not self.is_allowed_private_ip(client_ip):
                    logger.warning(f"Private IP access attempt: {client_ip}")
                    return HttpResponseForbidden("Access denied")
            except ValueError:
                pass
        
        return None

    def check_user_agent(self, request) -> Optional[HttpResponse]:
        """Vérifier le User Agent pour les outils d'attaque."""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        for suspicious_ua in self.suspicious_user_agents:
            if suspicious_ua in user_agent:
                logger.warning(f"Suspicious User Agent detected: {user_agent}")
                return HttpResponseForbidden("Access denied")
        
        return None

    def check_suspicious_parameters(self, request) -> Optional[HttpResponse]:
        """Vérifier les paramètres pour les injections."""
        # Vérifier les paramètres GET
        for key, value in request.GET.items():
            if self.is_suspicious_content(value):
                logger.warning(f"Suspicious GET parameter detected: {key}={value}")
                return HttpResponseForbidden("Access denied")
        
        # Vérifier les paramètres POST
        for key, value in request.POST.items():
            if self.is_suspicious_content(value):
                logger.warning(f"Suspicious POST parameter detected: {key}={value}")
                return HttpResponseForbidden("Access denied")
        
        return None

    def check_rate_limiting(self, request) -> Optional[HttpResponse]:
        """Vérifier le rate limiting."""
        client_ip = self.get_client_ip(request)
        endpoint = request.path
        
        # Clé de cache pour le rate limiting
        cache_key = f"rate_limit:{client_ip}:{endpoint}"
        
        # Récupérer le nombre de requêtes
        request_count = cache.get(cache_key, 0)
        
        # Définir les limites selon l'endpoint
        limits = {
            '/api/auth/login/': 5,  # 5 tentatives par minute
            '/api/auth/register/': 3,  # 3 inscriptions par heure
            '/api/payments/': 20,  # 20 paiements par heure
            'default': 100,  # 100 requêtes par heure par défaut
        }
        
        limit = limits.get(endpoint, limits['default'])
        
        if request_count >= limit:
            logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")
            return HttpResponseForbidden("Rate limit exceeded")
        
        # Incrémenter le compteur
        cache.set(cache_key, request_count + 1, 3600)  # 1 heure
        
        return None

    def check_failed_login_attempts(self, request) -> Optional[HttpResponse]:
        """Vérifier les tentatives de connexion échouées."""
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.is_account_locked():
                logger.warning(f"Account locked for user: {request.user.email}")
                return HttpResponseForbidden("Account temporarily locked")
        
        return None

    def add_security_headers(self, response: HttpResponse) -> HttpResponse:
        """Ajouter les headers de sécurité."""
        security_headers = getattr(settings, 'SECURITY_HEADERS', {})
        
        for header, value in security_headers.items():
            response[header] = value
        
        # Headers supplémentaires
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response

    def log_security_event(self, request, response):
        """Logger les événements de sécurité."""
        client_ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        method = request.method
        path = request.path
        status_code = response.status_code
        
        # Logger les événements suspects
        if status_code in [403, 404, 500]:
            logger.warning(
                f"Security event - IP: {client_ip}, Method: {method}, "
                f"Path: {path}, Status: {status_code}, UA: {user_agent}"
            )
        
        # Logger les tentatives d'accès aux endpoints sensibles
        sensitive_endpoints = [
            '/admin/',
            '/api/auth/',
            '/api/payments/',
            '/api/users/',
        ]
        
        if any(endpoint in path for endpoint in sensitive_endpoints):
            logger.info(
                f"Access to sensitive endpoint - IP: {client_ip}, "
                f"Method: {method}, Path: {path}, User: {getattr(request.user, 'email', 'anonymous')}"
            )

    def get_client_ip(self, request) -> str:
        """Obtenir l'adresse IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def is_allowed_private_ip(self, ip: str) -> bool:
        """Vérifier si une IP privée est autorisée."""
        allowed_private_ips = getattr(settings, 'ALLOWED_PRIVATE_IPS', [])
        return ip in allowed_private_ips

    def is_suspicious_content(self, content: str) -> bool:
        """Vérifier si le contenu est suspect."""
        if not isinstance(content, str):
            return False
        
        content_lower = content.lower()
        
        # Vérifier les patterns suspects
        for pattern in self.suspicious_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return True
        
        # Vérifier les tentatives d'injection SQL
        sql_patterns = [
            'union select',
            'drop table',
            'delete from',
            'insert into',
            'update set',
            'or 1=1',
            'or 1 = 1',
            '--',
            '/*',
            '*/',
            'xp_',
            'sp_',
        ]
        
        for pattern in sql_patterns:
            if pattern in content_lower:
                return True
        
        return False 