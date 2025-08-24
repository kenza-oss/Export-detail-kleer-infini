"""
Services pour la gestion des OTP et l'authentification
Supporte Twilio, Vonage et mode console pour l'envoi de SMS OTP
Version sécurisée avec protection contre les attaques
"""

import random
import string
import logging
import hashlib
import hmac
import time
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from django.conf import settings
from .models import OTPCode, User
import phonenumbers

# Configuration du logger
logger = logging.getLogger(__name__)

class OTPSecurityService:
    """Service de sécurité pour les OTP"""
    
    @staticmethod
    def generate_secure_otp():
        """Génère un code OTP cryptographiquement sécurisé"""
        # Utilisation de secrets pour une meilleure sécurité
        try:
            import secrets
            return ''.join(secrets.choice(string.digits) for _ in range(6))
        except ImportError:
            # Fallback pour Python < 3.6
            return ''.join(random.SystemRandom().choice(string.digits) for _ in range(6))
    
    @staticmethod
    def hash_otp_code(code: str, salt: str = None) -> str:
        """Hache un code OTP avec un salt unique"""
        if salt is None:
            salt = str(int(time.time()))
        
        secret = str(getattr(settings, 'SECRET_KEY', 'kleerlogistics')).encode()
        message = f"{code}:{salt}".encode()
        
        # Double hachage pour plus de sécurité
        first_hash = hmac.new(secret, message, hashlib.sha256).hexdigest()
        final_hash = hmac.new(secret, first_hash.encode(), hashlib.sha256).hexdigest()
        
        return f"{final_hash}:{salt}"
    
    @staticmethod
    def verify_otp_hash(code: str, hashed_code: str) -> bool:
        """Vérifie un code OTP contre son hash"""
        try:
            stored_hash, salt = hashed_code.split(':', 1)
            computed_hash = OTPSecurityService.hash_otp_code(code, salt).split(':', 1)[0]
            return hmac.compare_digest(stored_hash, computed_hash)
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def generate_device_fingerprint(request) -> str:
        """Génère un fingerprint unique pour l'appareil"""
        if not request:
            return "unknown"
        
        # Collecte d'informations non-identifiantes
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        
        # Création d'un hash unique
        fingerprint_data = f"{user_agent}:{accept_language}:{accept_encoding}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]

class OTPService:
    """Service pour la gestion des OTP avec sécurité renforcée"""
    
    @staticmethod
    def normalize_phone_number(raw_phone_number: str) -> str:
        """Normalise un numéro en format E.164 (ex: +213XXXXXXXXX).
        Si l'analyse échoue, renvoie la valeur originale.
        """
        try:
            default_region = getattr(settings, 'PHONENUMBER_DEFAULT_REGION', 'DZ')
            parsed = phonenumbers.parse(str(raw_phone_number), default_region)
            if not phonenumbers.is_valid_number(parsed):
                return raw_phone_number
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            return raw_phone_number
    
    @staticmethod
    def get_cache_key(phone_number, action='otp'):
        """Génère une clé de cache pour l'OTP"""
        return f"otp_{action}_{phone_number}"
    
    @staticmethod
    def check_rate_limit(phone_number, request=None):
        """Vérifie la limitation de taux pour l'envoi d'OTP avec fingerprint d'appareil"""
        cache_key = OTPService.get_cache_key(phone_number, 'rate_limit')
        attempts = cache.get(cache_key, 0)
        
        logger.info(f"Rate limit check for {phone_number}: {attempts} attempts")
        
        # Vérification du fingerprint d'appareil si disponible
        if request:
            device_fp = OTPSecurityService.generate_device_fingerprint(request)
            device_key = f"otp_device_{phone_number}_{device_fp}"
            device_attempts = cache.get(device_key, 0)
            
            logger.info(f"Device attempts for {phone_number}: {device_attempts}")
            
            # Limitation plus stricte par appareil
            if device_attempts >= getattr(settings, 'OTP_MAX_DEVICE_ATTEMPTS', 2):
                logger.warning(f"Device rate limit exceeded for {phone_number}: {device_attempts} attempts")
                return False, f"Trop de tentatives depuis cet appareil. Réessayez dans {getattr(settings, 'OTP_RESEND_COOLDOWN_MINUTES', 5)} minute(s)."
        
        if attempts >= getattr(settings, 'OTP_MAX_ATTEMPTS', 3):
            logger.warning(f"Rate limit exceeded for {phone_number}: {attempts} attempts")
            return False, f"Trop de tentatives. Réessayez dans {getattr(settings, 'OTP_RESEND_COOLDOWN_MINUTES', 5)} minute(s)."
        
        return True, None
    
    @staticmethod
    def increment_rate_limit(phone_number, request=None):
        """Incrémente le compteur de tentatives avec fingerprint d'appareil"""
        cache_key = OTPService.get_cache_key(phone_number, 'rate_limit')
        attempts = cache.get(cache_key, 0) + 1
        # Le cache doit durer plus longtemps que le cooldown pour maintenir le blocage
        cache_duration = getattr(settings, 'OTP_RESEND_COOLDOWN_MINUTES', 5) * 60 * 2  # 2x le cooldown
        cache.set(cache_key, attempts, cache_duration)
        
        logger.info(f"Incremented rate limit for {phone_number}: {attempts} attempts, cache_key: {cache_key}, duration: {cache_duration}s")
        
        # Incrémenter aussi le compteur par appareil
        if request:
            device_fp = OTPSecurityService.generate_device_fingerprint(request)
            device_key = f"otp_device_{phone_number}_{device_fp}"
            device_attempts = cache.get(device_key, 0) + 1
            cache.set(device_key, device_attempts, cache_duration)
            logger.info(f"Device attempts for {phone_number}: {device_attempts}, device_key: {device_key}")

    @staticmethod
    def _check_verify_rate_limit(phone_number: str, request=None):
        key = OTPService.get_cache_key(phone_number, 'verify_attempts')
        attempts = cache.get(key, 0)
        max_attempts = getattr(settings, 'OTP_VERIFY_MAX_ATTEMPTS', getattr(settings, 'OTP_MAX_ATTEMPTS', 5))
        
        # Vérification du fingerprint d'appareil
        if request:
            device_fp = OTPSecurityService.generate_device_fingerprint(request)
            device_key = f"otp_verify_device_{phone_number}_{device_fp}"
            device_attempts = cache.get(device_key, 0)
            max_device_attempts = getattr(settings, 'OTP_VERIFY_MAX_DEVICE_ATTEMPTS', 3)
            
            if device_attempts >= max_device_attempts:
                logger.warning(f"OTP verification device rate-limited for {phone_number} from {device_fp}")
                return False
        
        if attempts >= max_attempts:
            logger.warning(f"OTP verification rate-limited for {phone_number}")
            return False
        return True

    @staticmethod
    def _increment_verify_attempts(phone_number: str, request=None):
        key = OTPService.get_cache_key(phone_number, 'verify_attempts')
        attempts = cache.get(key, 0) + 1
        cooldown_minutes = getattr(settings, 'OTP_VERIFY_COOLDOWN_MINUTES', 5)
        cache.set(key, attempts, cooldown_minutes * 60)
        
        # Incrémenter aussi le compteur par appareil
        if request:
            device_fp = OTPSecurityService.generate_device_fingerprint(request)
            device_key = f"otp_verify_device_{phone_number}_{device_fp}"
            device_attempts = cache.get(device_key, 0) + 1
            cache.set(device_key, device_attempts, cooldown_minutes * 60)

    @staticmethod
    def _reset_verify_attempts(phone_number: str, request=None):
        key = OTPService.get_cache_key(phone_number, 'rate_limit')
        cache.delete(key)
        
        # Reset des compteurs par appareil
        if request:
            device_fp = OTPSecurityService.generate_device_fingerprint(request)
            device_key = f"otp_device_{phone_number}_{device_fp}"
            cache.delete(device_key)
            
            verify_device_key = f"otp_verify_device_{phone_number}_{device_fp}"
            cache.delete(verify_device_key)
    
    @staticmethod
    def create_otp(user, phone_number, request=None):
        """Crée un nouveau code OTP pour un utilisateur avec sécurité renforcée"""
        # Normaliser le numéro
        phone_number = OTPService.normalize_phone_number(phone_number)
        
        # Vérifier la limitation de taux
        can_send, error_message = OTPService.check_rate_limit(phone_number, request)
        if not can_send:
            logger.warning(f"OTP rate limit exceeded for {phone_number}")
            return None, None, error_message
        
        # Supprimer les anciens OTP non utilisés pour ce numéro
        expired_count = OTPCode.cleanup_expired_otps()
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired OTPs for {phone_number}")
        
        # Vérifier le nombre maximum d'OTP actifs
        active_count = OTPCode.get_active_otp_count(phone_number)
        max_active_otps = getattr(settings, 'OTP_MAX_ACTIVE_PER_PHONE', 3)
        
        if active_count >= max_active_otps:
            logger.warning(f"Too many active OTPs for {phone_number}: {active_count}")
            return None, None, "Trop d'OTP actifs. Veuillez attendre l'expiration des codes précédents."
        
        # Vérifier s'il y a déjà un OTP valide récent (pour éviter le spam)
        # Seulement si on n'a pas atteint la limite de tentatives
        recent_otp = OTPCode.objects.filter(
            phone_number=phone_number,
            is_used=False,
            expires_at__gt=timezone.now(),
            created_at__gt=timezone.now() - timedelta(minutes=2)  # Augmenté à 2 minutes
        ).first()
        
        if recent_otp:
            logger.info(f"Recent OTP already exists for {phone_number}, reusing it")
            return recent_otp, None, None
        
        # Créer un nouveau OTP sécurisé
        code = OTPSecurityService.generate_secure_otp()
        expires_at = timezone.now() + timedelta(minutes=getattr(settings, 'OTP_EXPIRY_MINUTES', 10))
        
        # Si pas d'utilisateur authentifié, essayer de trouver un utilisateur par numéro de téléphone
        if not user:
            try:
                user = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                # Pour l'inscription, permettre l'envoi d'OTP sans utilisateur
                user = None
        
        # Hacher le code avant stockage
        hashed_code = OTPSecurityService.hash_otp_code(code)

        otp = OTPCode.objects.create(
            user=user,
            phone_number=phone_number,
            code=hashed_code,
            expires_at=expires_at
        )
        
        # Incrémenter le compteur de tentatives
        OTPService.increment_rate_limit(phone_number, request)
        
        # Log de sécurité
        logger.info(f"OTP created for {phone_number}, user: {user.username if user else 'anonymous'}")
        
        return otp, code, None
    
    @staticmethod
    def verify_otp(phone_number, code, user=None, request=None):
        """Vérifie un code OTP avec sécurité renforcée."""
        # Normaliser
        phone_number = OTPService.normalize_phone_number(phone_number)

        # Vérifier limitations de tentatives
        if not OTPService._check_verify_rate_limit(phone_number, request):
            logger.warning(f"OTP verification rate-limited for {phone_number}")
            return False, None

        # Récupérer le dernier OTP valide pour ce numéro
        otp = (
            OTPCode.objects.filter(
                phone_number=phone_number,
                is_used=False,
                expires_at__gt=timezone.now(),
            )
            .order_by('-created_at')
            .first()
        )

        if not otp:
            OTPService._increment_verify_attempts(phone_number, request)
            logger.warning(f"No valid OTP found for {phone_number}")
            return False, None

        # Vérifier le code avec le nouveau service de sécurité
        if OTPSecurityService.verify_otp_hash(code, otp.code):
            # Succès: marquer OTP comme utilisé
            otp.mark_as_used()

            # Choisir l'utilisateur cible pour marquer vérification
            target_user = None
            if user and getattr(user, 'is_authenticated', False):
                target_user = user
            elif otp.user:
                target_user = otp.user

            if target_user:
                target_user.phone_number = phone_number
                target_user.is_phone_verified = True
                target_user.save()
                
                # Log de succès
                logger.info(f"OTP verified successfully for {phone_number}, user: {target_user.username}")

            # Reset des compteurs
            OTPService._reset_verify_attempts(phone_number, request)
            return True, target_user

        # Mauvais code
        OTPService._increment_verify_attempts(phone_number, request)
        logger.warning(f"Invalid OTP code for {phone_number}")
        return False, None
    
    @staticmethod
    def send_otp_sms(phone_number, code):
        """
        Envoie un OTP par SMS via différents providers.
        
        Args:
            phone_number (str): Numéro de téléphone au format international (+213XXXXXXXXX)
            code (str): Code OTP à 6 chiffres
            
        Returns:
            tuple: (success: bool, message: str)
            
        Providers supportés:
            - console: Affichage en console (développement)
            - twilio: Twilio SMS API (production)
            - vonage: Vonage SMS API (production)
            
        Configuration requise dans settings.py:
            SMS_PROVIDER = 'twilio'  # ou 'vonage' ou 'console'
            
            # Pour Twilio:
            TWILIO_ACCOUNT_SID = 'your_account_sid'
            TWILIO_AUTH_TOKEN = 'your_auth_token'
            TWILIO_FROM_NUMBER = '+1234567890'
            
            # Pour Vonage:
            VONAGE_API_KEY = 'your_api_key'
            VONAGE_API_SECRET = 'your_api_secret'
            VONAGE_FROM_NUMBER = 'KleerLogistics'
        """
        sms_provider = getattr(settings, 'SMS_PROVIDER', 'console')
        
        try:
            if sms_provider == 'console':
                return OTPService._send_console_sms(phone_number, code)
            elif sms_provider == 'twilio':
                return OTPService._send_twilio_sms(phone_number, code)
            elif sms_provider == 'vonage':
                return OTPService._send_vonage_sms(phone_number, code)
            else:
                logger.warning(f"Provider SMS non reconnu: {sms_provider}, utilisation du mode console")
                return OTPService._send_console_sms(phone_number, code)
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi SMS: {str(e)}")
            return False, f"Erreur lors de l'envoi: {str(e)}"
    
    @staticmethod
    def _send_console_sms(phone_number, code):
        """Mode développement - affiche l'OTP dans la console"""
        message = f"[CONSOLE SMS] OTP envoyé au {phone_number}"
        logger.info(message)
        return True, "SMS envoyé (mode console)"
    
    @staticmethod
    def _send_twilio_sms(phone_number, code):
        """
        Envoie un SMS via Twilio
        
        Nécessite: pip install twilio
        """
        try:
            from twilio.rest import Client
            from twilio.base.exceptions import TwilioException
            
            # Configuration Twilio
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            from_number = getattr(settings, 'TWILIO_FROM_NUMBER', None)
            
            if not all([account_sid, auth_token, from_number]):
                raise ValueError("Configuration Twilio incomplète. Vérifiez TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN et TWILIO_FROM_NUMBER")
            
            # Initialiser le client Twilio
            client = Client(account_sid, auth_token)
            
            # Créer le message avec template configuré
            expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
            message_template = getattr(settings, 'OTP_MESSAGE_TEMPLATE', 
                                     "Votre code de vérification KleerLogistics: {code}. Ce code expire dans {minutes} minutes.")
            message_body = message_template.format(code=code, minutes=expiry_minutes)
            
            # Envoyer le SMS
            message = client.messages.create(
                body=message_body,
                from_=from_number,
                to=phone_number
            )
            
            logger.info(f"SMS Twilio envoyé avec succès. SID: {message.sid}")
            return True, f"SMS envoyé via Twilio (SID: {message.sid})"
            
        except ImportError:
            error_msg = "Module twilio non installé. Exécutez: pip install twilio"
            logger.error(error_msg)
            return False, error_msg
            
        except TwilioException as e:
            error_msg = f"Erreur Twilio: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Erreur inattendue Twilio: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def _send_vonage_sms(phone_number, code):
        """
        Envoie un SMS via Vonage (ex-Nexmo)
        
        Nécessite: pip install vonage
        """
        try:
            import vonage
            
            # Configuration Vonage
            api_key = getattr(settings, 'VONAGE_API_KEY', None)
            api_secret = getattr(settings, 'VONAGE_API_SECRET', None)
            from_number = getattr(settings, 'VONAGE_FROM_NUMBER', 'KleerLogistics')
            
            if not all([api_key, api_secret]):
                raise ValueError("Configuration Vonage incomplète. Vérifiez VONAGE_API_KEY et VONAGE_API_SECRET")
            
            # Initialiser le client Vonage
            client = vonage.Client(key=api_key, secret=api_secret)
            sms = vonage.Sms(client)
            
            # Créer le message avec template configuré
            expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
            message_template = getattr(settings, 'OTP_MESSAGE_TEMPLATE', 
                                     "Votre code de vérification KleerLogistics: {code}. Ce code expire dans {minutes} minutes.")
            message_body = message_template.format(code=code, minutes=expiry_minutes)
            
            # Envoyer le SMS
            response = sms.send_message({
                "from": from_number,
                "to": phone_number,
                "text": message_body,
            })
            
            if response["messages"][0]["status"] == "0":
                message_id = response["messages"][0]["message-id"]
                logger.info(f"SMS Vonage envoyé avec succès. ID: {message_id}")
                return True, f"SMS envoyé via Vonage (ID: {message_id})"
            else:
                error_msg = f"Erreur Vonage: {response['messages'][0]['error-text']}"
                logger.error(error_msg)
                return False, error_msg
                
        except ImportError:
            error_msg = "Module vonage non installé. Exécutez: pip install vonage"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Erreur inattendue Vonage: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

class AuthService:
    """Service pour l'authentification"""
    
    @staticmethod
    def create_user_with_profile(user_data):
        """Créer un utilisateur avec son profil."""
        from django.db import transaction
        
        with transaction.atomic():
            # Créer l'utilisateur
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                phone_number=user_data.get('phone_number'),
                role=user_data.get('role', 'sender')
            )
            
            # Le profil sera créé automatiquement par le signal
            # Pas besoin de le créer manuellement
            
            return user
    
    @staticmethod
    def authenticate_user(credentials, request=None):
        """Authentifie un utilisateur avec email/téléphone et mot de passe"""
        from django.contrib.auth import authenticate
        
        username = credentials.get('username')  # email ou téléphone
        password = credentials.get('password')
        
        if not username or not password:
            return None, "Identifiants manquants"
        
        # Si request est fourni, l'utiliser pour l'authentification (nécessaire pour Django Axes)
        if request:
            user = authenticate(request, username=username, password=password)
        else:
            user = authenticate(username=username, password=password)
        
        if user is None:
            return None, "Identifiants invalides"
        
        if not user.is_active:
            return None, "Compte désactivé"
        
        return user, None
    
    @staticmethod
    def update_user_role(user, new_role):
        """Met à jour le rôle d'un utilisateur"""
        if new_role not in dict(User.ROLE_CHOICES):
            return False, "Rôle invalide"
        
        user.role = new_role
        user.save()
        return True, "Rôle mis à jour avec succès"
    
    @staticmethod
    def get_user_permissions(user):
        """Récupère les permissions d'un utilisateur"""
        return {
            'is_admin': user.is_admin,
            'is_sender': user.is_sender,
            'is_traveler': user.is_traveler,
            'can_access_admin_panel': user.can_access_admin_panel(),
            'is_phone_verified': user.is_phone_verified,
            'is_document_verified': user.is_document_verified,
            'role': user.role,
            'permissions': list(user.get_all_permissions())
        } 

class OTPMaintenanceService:
    """Service de maintenance pour les OTP"""
    
    @staticmethod
    def cleanup_expired_otps():
        """Nettoie tous les OTP expirés"""
        try:
            expired_count = OTPCode.cleanup_expired_otps()
            logger.info(f"Cleaned up {expired_count} expired OTPs")
            return expired_count
        except Exception as e:
            logger.error(f"Error cleaning up expired OTPs: {str(e)}")
            return 0
    
    @staticmethod
    def cleanup_rate_limit_cache():
        """Nettoie le cache des limitations de taux expirées"""
        try:
            # Cette méthode sera appelée par une tâche Celery périodique
            # Pour l'instant, on utilise le cache Django qui se nettoie automatiquement
            logger.info("Rate limit cache cleanup completed")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up rate limit cache: {str(e)}")
            return False
    
    @staticmethod
    def get_otp_statistics():
        """Retourne des statistiques sur les OTP"""
        try:
            total_otps = OTPCode.objects.count()
            active_otps = OTPCode.objects.filter(
                is_used=False,
                expires_at__gt=timezone.now()
            ).count()
            expired_otps = OTPCode.objects.filter(
                expires_at__lt=timezone.now()
            ).count()
            
            return {
                'total_otps': total_otps,
                'active_otps': active_otps,
                'expired_otps': expired_otps,
                'cleanup_needed': expired_otps > 0
            }
        except Exception as e:
            logger.error(f"Error getting OTP statistics: {str(e)}")
            return {}
    
    @staticmethod
    def monitor_suspicious_activity():
        """Surveille les activités suspectes liées aux OTP"""
        try:
            # Vérifier les numéros avec trop de tentatives
            suspicious_phones = []
            
            # Cette logique peut être étendue selon les besoins
            # Par exemple, détecter les tentatives de brute force
            
            if suspicious_phones:
                logger.warning(f"Suspicious OTP activity detected: {suspicious_phones}")
            
            return suspicious_phones
        except Exception as e:
            logger.error(f"Error monitoring suspicious activity: {str(e)}")
            return []


class OTPAuditService:
    """Service d'audit pour les OTP"""
    
    @staticmethod
    def log_otp_creation(phone_number, user, request, success, error_message=None):
        """Enregistre la création d'un OTP pour l'audit"""
        try:
            device_fp = OTPSecurityService.generate_device_fingerprint(request) if request else "unknown"
            ip_address = request.META.get('REMOTE_ADDR', 'unknown') if request else "unknown"
            
            audit_data = {
                'timestamp': timezone.now().isoformat(),
                'action': 'otp_creation',
                'phone_number': phone_number,
                'user_id': user.id if user else None,
                'username': user.username if user else 'anonymous',
                'device_fingerprint': device_fp,
                'ip_address': ip_address,
                'success': success,
                'error_message': error_message
            }
            
            logger.info(f"OTP Audit - Creation: {audit_data}")
            
            # Ici on pourrait aussi sauvegarder dans une base de données d'audit
            # ou envoyer à un service de monitoring externe
            
        except Exception as e:
            logger.error(f"Error logging OTP creation: {str(e)}")
    
    @staticmethod
    def log_otp_verification(phone_number, user, request, success, error_message=None):
        """Enregistre la vérification d'un OTP pour l'audit"""
        try:
            device_fp = OTPSecurityService.generate_device_fingerprint(request) if request else "unknown"
            ip_address = request.META.get('REMOTE_ADDR', 'unknown') if request else "unknown"
            
            audit_data = {
                'timestamp': timezone.now().isoformat(),
                'action': 'otp_verification',
                'phone_number': phone_number,
                'user_id': user.id if user else None,
                'username': user.username if user else 'anonymous',
                'device_fingerprint': device_fp,
                'ip_address': ip_address,
                'success': success,
                'error_message': error_message
            }
            
            logger.info(f"OTP Audit - Verification: {audit_data}")
            
        except Exception as e:
            logger.error(f"Error logging OTP verification: {str(e)}") 