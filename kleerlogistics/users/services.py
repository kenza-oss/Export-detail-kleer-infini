"""
Services pour la gestion des OTP et l'authentification
"""

import random
import string
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from django.conf import settings
from .models import OTPCode, User

class OTPService:
    """Service pour la gestion des OTP"""
    
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
    def create_otp(user, phone_number):
        """Crée un nouveau code OTP pour un utilisateur"""
        # Vérifier la limitation de taux
        can_send, error_message = OTPService.check_rate_limit(phone_number)
        if not can_send:
            return None, error_message
        
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
            return recent_otp, None
        
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
        
        otp = OTPCode.objects.create(
            user=user,
            phone_number=phone_number,
            code=code,
            expires_at=expires_at
        )
        
        # Incrémenter le compteur de tentatives
        OTPService.increment_rate_limit(phone_number)
        
        return otp, None
    
    @staticmethod
    def verify_otp(phone_number, code):
        """Vérifie un code OTP"""
        try:
            otp = OTPCode.objects.get(
                phone_number=phone_number,
                code=code,
                is_used=False,
                expires_at__gt=timezone.now()
            )
            
            # Marquer comme utilisé
            otp.mark_as_used()
            
            # Marquer le téléphone comme vérifié si un utilisateur existe
            user = otp.user
            if user:
                user.phone_number = phone_number
                user.is_phone_verified = True
                user.save()
            
            # Réinitialiser la limitation de taux
            cache_key = OTPService.get_cache_key(phone_number, 'rate_limit')
            cache.delete(cache_key)
            
            return True, user
        except OTPCode.DoesNotExist:
            return False, None
    
    @staticmethod
    def send_otp_sms(phone_number, code):
        """
        Envoie un OTP par SMS.
        En production, intégrer avec un service SMS comme Twilio, Vonage, etc.
        """
        sms_provider = getattr(settings, 'SMS_PROVIDER', 'console')
        
        if sms_provider == 'console':
            # Mode développement - afficher dans la console
            print(f"[SMS] OTP {code} envoyé au {phone_number}")
            return True
        elif sms_provider == 'twilio':
            # TODO: Implémenter l'intégration Twilio
            return OTPService._send_twilio_sms(phone_number, code)
        elif sms_provider == 'vonage':
            # TODO: Implémenter l'intégration Vonage
            return OTPService._send_vonage_sms(phone_number, code)
        else:
            print(f"[SMS] OTP {code} envoyé au {phone_number} (provider: {sms_provider})")
            return True
    
    @staticmethod
    def _send_twilio_sms(phone_number, code):
        """Envoie un SMS via Twilio"""
        # TODO: Implémenter l'intégration Twilio
        print(f"[Twilio] OTP {code} envoyé au {phone_number}")
        return True
    
    @staticmethod
    def _send_vonage_sms(phone_number, code):
        """Envoie un SMS via Vonage"""
        # TODO: Implémenter l'intégration Vonage
        print(f"[Vonage] OTP {code} envoyé au {phone_number}")
        return True

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