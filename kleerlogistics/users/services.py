"""
Services pour la gestion des OTP et l'authentification
Supporte Twilio, Vonage et mode console pour l'envoi de SMS OTP
"""

import random
import string
import logging
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from django.conf import settings
from .models import OTPCode, User
import hashlib
import hmac
import phonenumbers

# Configuration du logger
logger = logging.getLogger(__name__)

class OTPService:
    """Service pour la gestion des OTP"""
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
    def generate_otp():
        """Génère un code OTP à 6 chiffres"""
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    def get_cache_key(phone_number, action='otp'):
        """Génère une clé de cache pour l'OTP"""
        return f"otp_{action}_{phone_number}"
    
    @staticmethod
    def check_rate_limit(phone_number):
        """Vérifie la limitation de taux pour l'envoi d'OTP"""
        cache_key = OTPService.get_cache_key(phone_number, 'rate_limit')
        attempts = cache.get(cache_key, 0)
        
        if attempts >= getattr(settings, 'OTP_MAX_ATTEMPTS', 3):
            return False, f"Trop de tentatives. Réessayez dans {getattr(settings, 'OTP_RESEND_COOLDOWN_MINUTES', 1)} minute(s)."
        
        return True, None
    
    @staticmethod
    def increment_rate_limit(phone_number):
        """Incrémente le compteur de tentatives"""
        cache_key = OTPService.get_cache_key(phone_number, 'rate_limit')
        attempts = cache.get(cache_key, 0) + 1
        cache.set(cache_key, attempts, getattr(settings, 'OTP_RESEND_COOLDOWN_MINUTES', 1) * 60)

    @staticmethod
    def _check_verify_rate_limit(phone_number: str):
        key = OTPService.get_cache_key(phone_number, 'verify_attempts')
        attempts = cache.get(key, 0)
        max_attempts = getattr(settings, 'OTP_VERIFY_MAX_ATTEMPTS', getattr(settings, 'OTP_MAX_ATTEMPTS', 5))
        if attempts >= max_attempts:
            return False
        return True

    @staticmethod
    def _increment_verify_attempts(phone_number: str):
        key = OTPService.get_cache_key(phone_number, 'verify_attempts')
        attempts = cache.get(key, 0) + 1
        cooldown_minutes = getattr(settings, 'OTP_VERIFY_COOLDOWN_MINUTES', 5)
        cache.set(key, attempts, cooldown_minutes * 60)

    @staticmethod
    def _reset_verify_attempts(phone_number: str):
        key = OTPService.get_cache_key(phone_number, 'verify_attempts')
        cache.delete(key)
    
    @staticmethod
    def create_otp(user, phone_number):
        """Crée un nouveau code OTP pour un utilisateur"""
        # Normaliser le numéro
        phone_number = OTPService.normalize_phone_number(phone_number)
        # Vérifier la limitation de taux
        can_send, error_message = OTPService.check_rate_limit(phone_number)
        if not can_send:
            return None, None, error_message
        
        # Supprimer les anciens OTP non utilisés pour ce numéro
        OTPCode.objects.filter(
            phone_number=phone_number,
            is_used=False,
            expires_at__lt=timezone.now()
        ).delete()
        
        # Vérifier s'il y a déjà un OTP valide récent (pour éviter le spam)
        recent_otp = OTPCode.objects.filter(
            phone_number=phone_number,
            is_used=False,
            expires_at__gt=timezone.now(),
            created_at__gt=timezone.now() - timedelta(minutes=1)
        ).first()
        
        if recent_otp:
            # Ne renvoyer aucun code en clair si un OTP récent existe déjà
            return recent_otp, None, None
        
        # Créer un nouveau OTP
        code = OTPService.generate_otp()
        expires_at = timezone.now() + timedelta(minutes=getattr(settings, 'OTP_EXPIRY_MINUTES', 10))
        
        # Si pas d'utilisateur authentifié, essayer de trouver un utilisateur par numéro de téléphone
        if not user:
            try:
                user = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                # Pour l'inscription, permettre l'envoi d'OTP sans utilisateur
                user = None
        
        # Hacher le code avant stockage
        secret = str(getattr(settings, 'SECRET_KEY', 'kleerlogistics')).encode()
        hashed_code = hmac.new(secret, code.encode(), hashlib.sha256).hexdigest()

        otp = OTPCode.objects.create(
            user=user,
            phone_number=phone_number,
            code=hashed_code,
            expires_at=expires_at
        )
        
        # Incrémenter le compteur de tentatives
        OTPService.increment_rate_limit(phone_number)
        
        return otp, code, None
    
    @staticmethod
    def verify_otp(phone_number, code, user=None):
        """Vérifie un code OTP (code en clair fourni par l'utilisateur)."""
        # Normaliser
        phone_number = OTPService.normalize_phone_number(phone_number)

        # Vérifier limitations de tentatives
        if not OTPService._check_verify_rate_limit(phone_number):
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
            OTPService._increment_verify_attempts(phone_number)
            return False, None

        # Hacher le code fourni et comparer
        secret = str(getattr(settings, 'SECRET_KEY', 'kleerlogistics')).encode()
        hashed_input = hmac.new(secret, str(code).encode(), hashlib.sha256).hexdigest()

        if hmac.compare_digest(hashed_input, otp.code):
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

            # Reset des compteurs
            cache.delete(OTPService.get_cache_key(phone_number, 'rate_limit'))
            OTPService._reset_verify_attempts(phone_number)
            return True, target_user

        # Mauvais code
        OTPService._increment_verify_attempts(phone_number)
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