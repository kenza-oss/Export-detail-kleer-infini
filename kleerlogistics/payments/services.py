"""
Services pour la gestion des paiements algériens
Support pour CIB, Eddahabia et paiement en espèces au bureau
selon le cahier des charges Kleer Logistics
"""

import logging
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from .models import Transaction, PaymentMethod, Wallet

logger = logging.getLogger(__name__)


class AlgerianPaymentService:
    """Service pour la gestion des paiements algériens."""
    
    @staticmethod
    def create_card_payment(user, amount, card_type, shipment=None, **kwargs):
        """
        Crée un paiement par carte bancaire algérienne (CIB/Eddahabia).
        
        Args:
            user: Utilisateur qui effectue le paiement
            amount: Montant du paiement
            card_type: Type de carte ('cib' ou 'eddahabia')
            shipment: Envoi associé (optionnel)
            **kwargs: Autres paramètres (card_last_four, card_holder_name, etc.)
            
        Returns:
            Transaction: Transaction créée
        """
        try:
            # Validation du type de carte
            if card_type not in ['cib', 'eddahabia']:
                raise ValueError("Type de carte non supporté. Utilisez 'cib' ou 'eddahabia'")
            
            # Créer la transaction
            transaction = Transaction.objects.create(
                user=user,
                shipment=shipment,
                type='payment',
                amount=amount,
                currency='DZD',
                payment_method=card_type,
                payment_gateway=card_type,
                card_type=card_type,
                card_last_four=kwargs.get('card_last_four', ''),
                card_holder_name=kwargs.get('card_holder_name', ''),
                description=f"Paiement {card_type.upper()} pour {shipment.tracking_number if shipment else 'transaction'}",
                metadata={
                    'card_type': card_type,
                    'payment_processor': 'algerian_bank',
                    'is_online': True,
                    **kwargs
                }
            )
            
            logger.info(f"Transaction carte {card_type} créée: {transaction.transaction_id}")
            return transaction
            
        except Exception as e:
            logger.error(f"Erreur création paiement carte {card_type}: {str(e)}")
            raise
    
    @staticmethod
    def create_cash_payment(user, amount, shipment=None, office_location=None, **kwargs):
        """
        Crée un paiement en espèces au bureau.
        
        Args:
            user: Utilisateur qui effectue le paiement
            amount: Montant du paiement
            shipment: Envoi associé (optionnel)
            office_location: Bureau de paiement
            **kwargs: Autres paramètres
            
        Returns:
            Transaction: Transaction créée
        """
        try:
            # Créer la transaction en attente
            transaction = Transaction.objects.create(
                user=user,
                shipment=shipment,
                type='payment',
                amount=amount,
                currency='DZD',
                payment_method='cash',
                payment_gateway='manual',
                cash_payment_location=office_location or "Bureau Kleer Infini - Alger Centre",
                description=f"Paiement en espèces pour {shipment.tracking_number if shipment else 'transaction'}",
                metadata={
                    'payment_type': 'cash',
                    'office_location': office_location,
                    'is_online': False,
                    **kwargs
                }
            )
            
            logger.info(f"Transaction espèces créée: {transaction.transaction_id}")
            return transaction
            
        except Exception as e:
            logger.error(f"Erreur création paiement espèces: {str(e)}")
            raise
    
    @staticmethod
    def confirm_cash_payment(transaction_id, confirmed_by_user, payment_date=None):
        """
        Confirme un paiement en espèces.
        
        Args:
            transaction_id: ID de la transaction
            confirmed_by_user: Utilisateur qui confirme le paiement
            payment_date: Date de paiement (optionnel)
            
        Returns:
            Transaction: Transaction confirmée
        """
        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
            
            if not transaction.is_cash_payment:
                raise ValueError("Cette transaction n'est pas un paiement en espèces")
            
            if transaction.status != 'pending':
                raise ValueError("Seule une transaction en attente peut être confirmée")
            
            # Confirmer le paiement
            transaction.confirm_cash_payment(confirmed_by_user, payment_date)
            
            logger.info(f"Paiement espèces confirmé: {transaction_id}")
            return transaction
            
        except Transaction.DoesNotExist:
            raise ValueError("Transaction non trouvée")
        except Exception as e:
            logger.error(f"Erreur confirmation paiement espèces: {str(e)}")
            raise
    
    @staticmethod
    def process_card_payment(transaction_id, payment_data):
        """
        Traite un paiement par carte (simulation pour CIB/Eddahabia).
        
        Args:
            transaction_id: ID de la transaction
            payment_data: Données de paiement
            
        Returns:
            dict: Résultat du traitement
        """
        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
            
            if not transaction.is_card_payment:
                raise ValueError("Cette transaction n'est pas un paiement par carte")
            
            if transaction.status != 'pending':
                raise ValueError("Seule une transaction en attente peut être traitée")
            
            # Simuler le traitement bancaire
            # En production, intégrer avec les APIs CIB/Eddahabia
            
            # Mettre à jour les métadonnées
            transaction.metadata.update({
                'payment_processed': True,
                'processing_date': timezone.now().isoformat(),
                'bank_response': 'success',
                **payment_data
            })
            
            # Marquer comme terminé
            transaction.status = 'processing'
            transaction.save()
            
            # Simuler un délai de traitement
            # En production, attendre la réponse de la banque
            
            # Finaliser la transaction
            transaction.complete()
            
            logger.info(f"Paiement carte traité: {transaction_id}")
            return {
                'success': True,
                'transaction_id': transaction_id,
                'status': 'completed',
                'message': f"Paiement {transaction.card_type.upper()} traité avec succès"
            }
            
        except Transaction.DoesNotExist:
            raise ValueError("Transaction non trouvée")
        except Exception as e:
            logger.error(f"Erreur traitement paiement carte: {str(e)}")
            return {
                'success': False,
                'transaction_id': transaction_id,
                'error': str(e)
            }
    
    @staticmethod
    def get_available_payment_methods(amount=None):
        """
        Récupère les méthodes de paiement disponibles.
        
        Args:
            amount: Montant pour filtrer les méthodes disponibles
            
        Returns:
            list: Liste des méthodes de paiement
        """
        try:
            methods = PaymentMethod.objects.filter(is_active=True)
            
            if amount:
                methods = [m for m in methods if m.is_available_for_amount(amount)]
            
            return methods
            
        except Exception as e:
            logger.error(f"Erreur récupération méthodes de paiement: {str(e)}")
            return []
    
    @staticmethod
    def calculate_payment_fees(amount, payment_method):
        """
        Calcule les frais pour une méthode de paiement.
        
        Args:
            amount: Montant du paiement
            payment_method: Méthode de paiement
            
        Returns:
            dict: Frais calculés
        """
        try:
            method = PaymentMethod.objects.get(name=payment_method, is_active=True)
            fees = method.calculate_fees(amount)
            total_amount = amount + fees
            
            return {
                'base_amount': amount,
                'fees': fees,
                'total_amount': total_amount,
                'fee_percentage': method.processing_fee,
                'fixed_fee': method.fixed_fee
            }
            
        except PaymentMethod.DoesNotExist:
            return {
                'base_amount': amount,
                'fees': Decimal('0.00'),
                'total_amount': amount,
                'fee_percentage': Decimal('0.00'),
                'fixed_fee': Decimal('0.00')
            }
        except Exception as e:
            logger.error(f"Erreur calcul frais: {str(e)}")
            raise


class PaymentValidationService:
    """Service pour la validation des paiements."""
    
    @staticmethod
    def validate_card_payment(card_type, card_number, amount):
        """
        Valide un paiement par carte.
        
        Args:
            card_type: Type de carte
            card_number: Numéro de carte
            amount: Montant
            
        Returns:
            dict: Résultat de la validation
        """
        try:
            # Validation du type de carte
            if card_type not in ['cib', 'eddahabia']:
                return {
                    'valid': False,
                    'error': 'Type de carte non supporté'
                }
            
            # Validation du numéro de carte (format basique)
            if not card_number or len(card_number) < 13:
                return {
                    'valid': False,
                    'error': 'Numéro de carte invalide'
                }
            
            # Validation du montant
            if amount <= 0:
                return {
                    'valid': False,
                    'error': 'Montant invalide'
                }
            
            # Validation des limites (à configurer selon les banques)
            max_amount = getattr(settings, f'{card_type.upper()}_MAX_AMOUNT', 100000)
            if amount > max_amount:
                return {
                    'valid': False,
                    'error': f'Montant supérieur à la limite autorisée ({max_amount} DA)'
                }
            
            return {
                'valid': True,
                'card_type': card_type,
                'card_last_four': card_number[-4:],
                'amount': amount
            }
            
        except Exception as e:
            logger.error(f"Erreur validation carte: {str(e)}")
            return {
                'valid': False,
                'error': 'Erreur de validation'
            }
    
    @staticmethod
    def validate_cash_payment(amount, office_location):
        """
        Valide un paiement en espèces.
        
        Args:
            amount: Montant
            office_location: Bureau de paiement
            
        Returns:
            dict: Résultat de la validation
        """
        try:
            # Validation du montant
            if amount <= 0:
                return {
                    'valid': False,
                    'error': 'Montant invalide'
                }
            
            # Validation des limites espèces
            max_cash_amount = getattr(settings, 'CASH_MAX_AMOUNT', 50000)
            if amount > max_cash_amount:
                return {
                    'valid': False,
                    'error': f'Montant supérieur à la limite espèces ({max_cash_amount} DA)'
                }
            
            # Validation du bureau
            if not office_location:
                return {
                    'valid': False,
                    'error': 'Bureau de paiement requis'
                }
            
            return {
                'valid': True,
                'amount': amount,
                'office_location': office_location
            }
            
        except Exception as e:
            logger.error(f"Erreur validation espèces: {str(e)}")
            return {
                'valid': False,
                'error': 'Erreur de validation'
            }


class PaymentReportingService:
    """Service pour les rapports de paiement."""
    
    @staticmethod
    def get_payment_statistics(start_date=None, end_date=None):
        """
        Récupère les statistiques de paiement.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            dict: Statistiques de paiement
        """
        try:
            transactions = Transaction.objects.filter(type='payment')
            
            if start_date:
                transactions = transactions.filter(created_at__gte=start_date)
            if end_date:
                transactions = transactions.filter(created_at__lte=end_date)
            
            # Statistiques par méthode de paiement
            stats = {
                'total_transactions': transactions.count(),
                'total_amount': sum(t.amount for t in transactions),
                'by_method': {},
                'by_status': {},
                'algerian_cards': {
                    'cib': transactions.filter(payment_method='cib').count(),
                    'eddahabia': transactions.filter(payment_method='eddahabia').count(),
                },
                'cash_payments': transactions.filter(payment_method='cash').count(),
            }
            
            # Détail par méthode
            for method in ['cib', 'eddahabia', 'cash', 'card', 'wallet']:
                method_transactions = transactions.filter(payment_method=method)
                stats['by_method'][method] = {
                    'count': method_transactions.count(),
                    'amount': sum(t.amount for t in method_transactions),
                    'success_rate': method_transactions.filter(status='completed').count() / max(method_transactions.count(), 1) * 100
                }
            
            # Détail par statut
            for status in ['pending', 'completed', 'failed', 'cancelled']:
                status_transactions = transactions.filter(status=status)
                stats['by_status'][status] = {
                    'count': status_transactions.count(),
                    'amount': sum(t.amount for t in status_transactions)
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur statistiques paiement: {str(e)}")
            return {}
