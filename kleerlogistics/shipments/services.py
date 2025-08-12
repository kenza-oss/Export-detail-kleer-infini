"""
Services pour la gestion des OTP de livraison
Implémentation complète du système OTP de confirmation de livraison
selon le cahier des charges Kleer Logistics
"""

import random
import string
import logging
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from django.conf import settings
from .models import Shipment, DeliveryOTP
from users.services import OTPService

logger = logging.getLogger(__name__)


class DeliveryOTPService:
    """Service pour la gestion des OTP de livraison"""
    
    @staticmethod
    def generate_delivery_otp(shipment, request=None):
        """
        Génère un OTP de livraison à 6 chiffres et l'envoie au destinataire.
        
        Args:
            shipment: Instance du modèle Shipment
            request: Objet request pour la sécurité
            
        Returns:
            tuple: (success: bool, otp: str, message: str)
        """
        try:
            # Vérifier que l'envoi est en transit
            if shipment.status != 'in_transit':
                return False, None, "L'envoi doit être en transit pour générer un OTP de livraison"
            
            # Vérifier que le voyageur a pris le colis
            if not shipment.matched_trip or not shipment.matched_trip.traveler:
                return False, None, "Aucun voyageur associé à cet envoi"
            
            # Générer un OTP sécurisé à 6 chiffres
            otp_code = ''.join(random.choices(string.digits, k=6))
            
            # Créer l'enregistrement OTP de livraison
            delivery_otp = DeliveryOTP.objects.create(
                shipment=shipment,
                otp_code=otp_code,
                recipient_phone=shipment.recipient_phone,
                recipient_name=shipment.recipient_name,
                generated_by=shipment.matched_trip.traveler,
                expires_at=timezone.now() + timedelta(hours=24)  # Expire dans 24h
            )
            
            # Envoyer le SMS au destinataire
            sms_success, sms_message = DeliveryOTPService._send_delivery_otp_sms(
                shipment.recipient_phone,
                otp_code,
                shipment.recipient_name,
                shipment.tracking_number
            )
            
            if sms_success:
                # Mettre à jour le statut de l'envoi
                shipment.delivery_otp = otp_code
                shipment.save()
                
                logger.info(f"Delivery OTP generated for shipment {shipment.tracking_number}: {otp_code}")
                
                return True, otp_code, f"OTP de livraison généré et envoyé au destinataire. {sms_message}"
            else:
                # Supprimer l'OTP si l'envoi SMS a échoué
                delivery_otp.delete()
                return False, None, f"Erreur lors de l'envoi du SMS: {sms_message}"
                
        except Exception as e:
            logger.error(f"Error generating delivery OTP for shipment {shipment.tracking_number}: {str(e)}")
            return False, None, f"Erreur lors de la génération de l'OTP: {str(e)}"
    
    @staticmethod
    def verify_delivery_otp(shipment, provided_otp, verified_by_user=None, request=None):
        """
        Vérifie l'OTP de livraison fourni par le destinataire.
        
        Args:
            shipment: Instance du modèle Shipment
            provided_otp: Code OTP fourni par le destinataire
            verified_by_user: Utilisateur qui vérifie (voyageur)
            request: Objet request pour la sécurité
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Récupérer l'OTP de livraison valide
            delivery_otp = DeliveryOTP.objects.filter(
                shipment=shipment,
                otp_code=provided_otp,
                is_used=False,
                expires_at__gt=timezone.now()
            ).first()
            
            if not delivery_otp:
                # Incrémenter le compteur de tentatives échouées
                DeliveryOTPService._increment_failed_attempts(shipment.tracking_number, request)
                return False, "Code OTP invalide ou expiré"
            
            # Vérifier que le voyageur qui vérifie est bien celui associé
            if verified_by_user and shipment.matched_trip:
                if verified_by_user != shipment.matched_trip.traveler:
                    return False, "Vous n'êtes pas autorisé à vérifier cet OTP de livraison"
            
            # Marquer l'OTP comme utilisé
            delivery_otp.is_used = True
            delivery_otp.verified_at = timezone.now()
            delivery_otp.verified_by = verified_by_user
            delivery_otp.save()
            
            # Mettre à jour le statut de l'envoi
            shipment.status = 'delivered'
            shipment.delivery_date = timezone.now()
            shipment.save()
            
            # Reset des compteurs de tentatives
            DeliveryOTPService._reset_failed_attempts(shipment.tracking_number, request)
            
            logger.info(f"Delivery OTP verified for shipment {shipment.tracking_number} by {verified_by_user.username if verified_by_user else 'unknown'}")
            
            return True, "Livraison confirmée avec succès"
            
        except Exception as e:
            logger.error(f"Error verifying delivery OTP for shipment {shipment.tracking_number}: {str(e)}")
            return False, f"Erreur lors de la vérification: {str(e)}"
    
    @staticmethod
    def resend_delivery_otp(shipment, request=None):
        """
        Renvoie l'OTP de livraison au destinataire.
        
        Args:
            shipment: Instance du modèle Shipment
            request: Objet request pour la sécurité
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Vérifier la limitation de taux pour le renvoi
            cache_key = f"delivery_otp_resend_{shipment.tracking_number}"
            resend_count = cache.get(cache_key, 0)
            
            if resend_count >= 3:  # Maximum 3 renvois
                return False, "Nombre maximum de renvois atteint. Contactez le support."
            
            # Récupérer l'OTP existant non utilisé
            existing_otp = DeliveryOTP.objects.filter(
                shipment=shipment,
                is_used=False,
                expires_at__gt=timezone.now()
            ).first()
            
            if not existing_otp:
                return False, "Aucun OTP de livraison valide trouvé"
            
            # Renvoyer le SMS
            sms_success, sms_message = DeliveryOTPService._send_delivery_otp_sms(
                shipment.recipient_phone,
                existing_otp.otp_code,
                shipment.recipient_name,
                shipment.tracking_number
            )
            
            if sms_success:
                # Incrémenter le compteur de renvois
                cache.set(cache_key, resend_count + 1, 3600)  # 1 heure
                
                logger.info(f"Delivery OTP resent for shipment {shipment.tracking_number}")
                return True, f"OTP de livraison renvoyé avec succès. {sms_message}"
            else:
                return False, f"Erreur lors du renvoi: {sms_message}"
                
        except Exception as e:
            logger.error(f"Error resending delivery OTP for shipment {shipment.tracking_number}: {str(e)}")
            return False, f"Erreur lors du renvoi: {str(e)}"
    
    @staticmethod
    def _send_delivery_otp_sms(recipient_phone, otp_code, recipient_name, tracking_number):
        """
        Envoie le SMS avec l'OTP de livraison au destinataire.
        
        Args:
            recipient_phone: Numéro de téléphone du destinataire
            otp_code: Code OTP à 6 chiffres
            recipient_name: Nom du destinataire
            tracking_number: Numéro de suivi de l'envoi
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Utiliser le service SMS existant
            message_template = getattr(settings, 'DELIVERY_OTP_MESSAGE_TEMPLATE', 
                "Bonjour {name}, votre colis {tracking} arrive bientôt. Code de livraison: {otp}. "
                "Remettez ce code au livreur pour confirmer la réception. "
                "Ce code expire dans 24h. - KleerLogistics")
            
            message_body = message_template.format(
                name=recipient_name,
                tracking=tracking_number,
                otp=otp_code
            )
            
            # Envoyer via le service SMS configuré
            return OTPService.send_otp_sms(recipient_phone, otp_code)
            
        except Exception as e:
            logger.error(f"Error sending delivery OTP SMS to {recipient_phone}: {str(e)}")
            return False, f"Erreur SMS: {str(e)}"
    
    @staticmethod
    def _increment_failed_attempts(tracking_number, request=None):
        """Incrémente le compteur de tentatives échouées"""
        cache_key = f"delivery_otp_failed_{tracking_number}"
        attempts = cache.get(cache_key, 0) + 1
        cache.set(cache_key, attempts, 1800)  # 30 minutes
        
        if request:
            device_fp = getattr(request, 'device_fingerprint', 'unknown')
            device_key = f"delivery_otp_failed_device_{tracking_number}_{device_fp}"
            device_attempts = cache.get(device_key, 0) + 1
            cache.set(device_key, device_attempts, 1800)
    
    @staticmethod
    def _reset_failed_attempts(tracking_number, request=None):
        """Reset les compteurs de tentatives échouées"""
        cache_key = f"delivery_otp_failed_{tracking_number}"
        cache.delete(cache_key)
        
        if request:
            device_fp = getattr(request, 'device_fingerprint', 'unknown')
            device_key = f"delivery_otp_failed_device_{tracking_number}_{device_fp}"
            cache.delete(device_key)
    
    @staticmethod
    def cleanup_expired_otps():
        """Nettoie tous les OTP de livraison expirés"""
        try:
            expired_count = DeliveryOTP.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()[0]
            
            logger.info(f"Cleaned up {expired_count} expired delivery OTPs")
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired delivery OTPs: {str(e)}")
            return 0
    
    @staticmethod
    def get_delivery_otp_status(shipment):
        """
        Récupère le statut de l'OTP de livraison pour un envoi.
        
        Args:
            shipment: Instance du modèle Shipment
            
        Returns:
            dict: Statut de l'OTP de livraison
        """
        try:
            active_otp = DeliveryOTP.objects.filter(
                shipment=shipment,
                is_used=False,
                expires_at__gt=timezone.now()
            ).first()
            
            used_otp = DeliveryOTP.objects.filter(
                shipment=shipment,
                is_used=True
            ).first()
            
            return {
                'has_active_otp': active_otp is not None,
                'has_used_otp': used_otp is not None,
                'otp_generated_at': active_otp.created_at if active_otp else None,
                'otp_expires_at': active_otp.expires_at if active_otp else None,
                'otp_verified_at': used_otp.verified_at if used_otp else None,
                'recipient_phone': shipment.recipient_phone,
                'recipient_name': shipment.recipient_name
            }
            
        except Exception as e:
            logger.error(f"Error getting delivery OTP status for shipment {shipment.tracking_number}: {str(e)}")
            return {}


class ShipmentDeliveryService:
    """Service pour la gestion complète de la livraison"""
    
    @staticmethod
    def initiate_delivery_process(shipment, traveler_user):
        """
        Initie le processus de livraison quand le voyageur prend le colis.
        
        Args:
            shipment: Instance du modèle Shipment
            traveler_user: Utilisateur voyageur
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Vérifier que l'envoi peut être mis en transit
            if shipment.status not in ['matched', 'pending']:
                return False, "L'envoi ne peut pas être mis en transit"
            
            # Mettre à jour le statut
            shipment.status = 'in_transit'
            shipment.save()
            
            # Générer automatiquement l'OTP de livraison
            otp_success, otp_code, otp_message = DeliveryOTPService.generate_delivery_otp(shipment)
            
            if otp_success:
                logger.info(f"Delivery process initiated for shipment {shipment.tracking_number} by {traveler_user.username}")
                return True, f"Processus de livraison initié. {otp_message}"
            else:
                # Revenir au statut précédent si l'OTP n'a pas pu être généré
                shipment.status = 'matched'
                shipment.save()
                return False, f"Erreur lors de l'initiation: {otp_message}"
                
        except Exception as e:
            logger.error(f"Error initiating delivery process for shipment {shipment.tracking_number}: {str(e)}")
            return False, f"Erreur lors de l'initiation: {str(e)}"
    
    @staticmethod
    def complete_delivery(shipment, otp_code, traveler_user):
        """
        Complète la livraison avec vérification de l'OTP.
        
        Args:
            shipment: Instance du modèle Shipment
            otp_code: Code OTP fourni par le destinataire
            traveler_user: Utilisateur voyageur
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Vérifier l'OTP
            otp_success, otp_message = DeliveryOTPService.verify_delivery_otp(
                shipment, otp_code, traveler_user
            )
            
            if otp_success:
                # Libérer le paiement au voyageur
                payment_success, payment_message = ShipmentDeliveryService._release_traveler_payment(shipment)
                
                if payment_success:
                    logger.info(f"Delivery completed for shipment {shipment.tracking_number} by {traveler_user.username}")
                    return True, f"Livraison complétée avec succès. {payment_message}"
                else:
                    logger.warning(f"Delivery completed but payment release failed for shipment {shipment.tracking_number}")
                    return True, f"Livraison complétée mais erreur de paiement: {payment_message}"
            else:
                return False, otp_message
                
        except Exception as e:
            logger.error(f"Error completing delivery for shipment {shipment.tracking_number}: {str(e)}")
            return False, f"Erreur lors de la finalisation: {str(e)}"
    
    @staticmethod
    def _release_traveler_payment(shipment):
        """
        Libère le paiement au voyageur après confirmation de livraison.
        
        Args:
            shipment: Instance du modèle Shipment
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if not shipment.matched_trip or not shipment.matched_trip.traveler:
                return False, "Aucun voyageur associé"
            
            traveler = shipment.matched_trip.traveler
            
            # Calculer le montant à verser (prix - commission)
            if shipment.price:
                commission_rate = getattr(traveler, 'commission_rate', 10.00) / 100
                commission_amount = shipment.price * commission_rate
                traveler_amount = shipment.price - commission_amount
                
                # Créditer le portefeuille du voyageur
                traveler.wallet_balance += traveler_amount
                traveler.total_trips += 1
                traveler.save()
                
                logger.info(f"Payment released to traveler {traveler.username}: {traveler_amount} DA")
                return True, f"Paiement de {traveler_amount} DA libéré au voyageur"
            else:
                return False, "Aucun montant à verser"
                
        except Exception as e:
            logger.error(f"Error releasing traveler payment for shipment {shipment.tracking_number}: {str(e)}")
            return False, f"Erreur de paiement: {str(e)}"
