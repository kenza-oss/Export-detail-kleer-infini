"""
Services pour la gestion des paiements algériens
Support pour CIB, Eddahabia et paiement en espèces au bureau
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
                description=f"Paiement {card_type.upper()} pour {shipment.tracking_number if shipment else 'transaction générale'}",
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
                description=f"Paiement en espèces pour {shipment.tracking_number if shipment else 'transaction générale'}",
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
    def validate_card_payment(card_type, card_number=None, amount=None):
        """
        Valide un paiement par carte.
        
        Args:
            card_type: Type de carte
            card_number: Numéro de carte (optionnel pour les tests)
            amount: Montant (optionnel pour les tests)
            
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
            
            # Validation du numéro de carte (format basique) - optionnel pour les tests
            if card_number is not None:
                if not card_number or len(str(card_number)) < 13:
                    return {
                        'valid': False,
                        'error': 'Numéro de carte invalide'
                    }
            
            # Validation du montant - optionnel pour les tests
            if amount is not None:
                if amount <= 0:
                    return {
                        'valid': False,
                        'error': 'Montant invalide'
                    }
            
            # Validation des limites (à configurer selon les banques)
            if amount is not None:
                max_amount = getattr(settings, f'{card_type.upper()}_MAX_AMOUNT', 100000)
                if amount > max_amount:
                    return {
                        'valid': False,
                        'error': f'Montant supérieur à la limite autorisée ({max_amount} DA)'
                    }
            
            return {
                'valid': True,
                'card_type': card_type,
                'card_last_four': card_number[-4:] if card_number else '',
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


class ChargilyPaymentService:
    """Service pour l'intégration Chargily Pay."""
    
    @staticmethod
    def create_chargily_payment(user, amount, payment_mode, shipment=None, **kwargs):
        """
        Crée un paiement via Chargily Pay.
        
        Args:
            user: Utilisateur qui effectue le paiement
            amount: Montant du paiement
            payment_mode: Mode de paiement (edahabia, cib, baridi_mob)
            shipment: Envoi associé (optionnel)
            **kwargs: Autres paramètres
            
        Returns:
            dict: Résultat du paiement
        """
        try:
            # Validation du mode de paiement
            valid_modes = ['edahabia', 'cib', 'baridi_mob']
            if payment_mode not in valid_modes:
                raise ValueError(f"Mode de paiement invalide. Utilisez: {', '.join(valid_modes)}")
            
            # Créer la transaction
            transaction = Transaction.objects.create(
                user=user,
                shipment=shipment,
                type='payment',
                amount=amount,
                currency='DZD',
                payment_method='chargily',
                payment_gateway='chargily',
                description=f"Paiement Chargily {payment_mode} pour {shipment.tracking_number if shipment else 'transaction'}",
                status='pending',
                metadata={
                    'payment_mode': payment_mode,
                    'chargily_integration': True,
                    'back_url': kwargs.get('back_url'),
                    'webhook_url': kwargs.get('webhook_url'),
                    **kwargs
                }
            )
            
            # En production, intégrer avec l'API Chargily
            # chargily_response = ChargilyAPI.create_checkout(transaction, payment_mode)
            
            # Simulation pour les tests
            chargily_url = f"https://pay.chargily.com/checkout/{transaction.transaction_id}"
            
            logger.info(f"Paiement Chargily créé: {transaction.transaction_id}")
            
            return {
                'success': True,
                'transaction_id': transaction.transaction_id,
                'chargily_url': chargily_url,
                'payment_mode': payment_mode
            }
            
        except Exception as e:
            logger.error(f"Erreur création paiement Chargily: {str(e)}")
            raise
    
    @staticmethod
    def process_chargily_webhook(webhook_data):
        """
        Traite un webhook Chargily.
        
        Args:
            webhook_data: Données du webhook
            
        Returns:
            bool: Succès du traitement
        """
        try:
            transaction_id = webhook_data.get('order_id')
            status = webhook_data.get('status')
            amount = webhook_data.get('amount')
            
            if not all([transaction_id, status]):
                logger.error("Données webhook Chargily incomplètes")
                return False
            
            try:
                transaction = Transaction.objects.get(
                    transaction_id=transaction_id,
                    payment_method='chargily'
                )
            except Transaction.DoesNotExist:
                logger.error(f"Transaction Chargily non trouvée: {transaction_id}")
                return False
            
            # Mettre à jour le statut
            if status == 'paid':
                transaction.status = 'completed'
                transaction.completed_at = timezone.now()
                transaction.metadata.update({
                    'chargily_payment_id': webhook_data.get('id'),
                    'webhook_received_at': timezone.now().isoformat(),
                    'webhook_data': webhook_data
                })
                transaction.save()
                
                # Mettre à jour le portefeuille
                if transaction.type == 'payment':
                    wallet, created = Wallet.objects.get_or_create(user=transaction.user)
                    wallet.add_funds(amount, 'payment')
                
                logger.info(f"Webhook Chargily traité avec succès: {transaction_id}")
                return True
            
            elif status in ['failed', 'cancelled']:
                transaction.status = 'failed'
                transaction.metadata.update({
                    'chargily_payment_id': webhook_data.get('id'),
                    'webhook_received_at': timezone.now().isoformat(),
                    'failure_reason': webhook_data.get('failure_reason', 'Unknown')
                })
                transaction.save()
                
                logger.info(f"Paiement Chargily échoué: {transaction_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur traitement webhook Chargily: {str(e)}")
            return False


class CommissionService:
    """Service pour la gestion des commissions."""
    
    @staticmethod
    def calculate_commission(shipment_id, total_amount, commission_rate=25.0):
        """
        Calcule les commissions pour un envoi.
        
        Args:
            shipment_id: ID de l'envoi
            total_amount: Montant total
            commission_rate: Taux de commission (par défaut 25%)
            
        Returns:
            dict: Détails des commissions
        """
        try:
            commission_amount = (total_amount * commission_rate) / 100
            traveler_amount = total_amount - commission_amount
            
            return {
                'shipment_id': shipment_id,
                'total_amount': total_amount,
                'commission_rate': commission_rate,
                'commission_amount': commission_amount,
                'traveler_amount': traveler_amount
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul commission: {str(e)}")
            raise
    
    @staticmethod
    def apply_commission(user, shipment_id, commission_amount, traveler_amount, description=None):
        """
        Applique une commission à un envoi.
        
        Args:
            user: Utilisateur qui applique la commission
            shipment_id: ID de l'envoi
            commission_amount: Montant de la commission
            traveler_amount: Montant pour le voyageur
            description: Description de la commission
            
        Returns:
            Transaction: Transaction de commission créée
        """
        try:
            # Créer la transaction de commission
            commission_transaction = Transaction.objects.create(
                user=user,
                type='commission',
                amount=commission_amount,
                currency='DZD',
                description=description or f"Commission sur envoi {shipment_id}",
                status='completed',
                metadata={
                    'shipment_id': shipment_id,
                    'traveler_amount': traveler_amount,
                    'commission_type': 'platform_fee'
                }
            )
            
            logger.info(f"Commission appliquée: {commission_transaction.transaction_id}")
            return commission_transaction
            
        except Exception as e:
            logger.error(f"Erreur application commission: {str(e)}")
            raise


class BankTransferService:
    """Service pour la gestion des virements bancaires."""
    
    @staticmethod
    def request_bank_transfer(user, amount, bank_name, account_number, account_holder, description=None):
        """
        Demande un virement bancaire.
        
        Args:
            user: Utilisateur qui demande le virement
            amount: Montant du virement
            bank_name: Nom de la banque
            account_number: Numéro de compte
            account_holder: Nom du titulaire
            description: Description du virement
            
        Returns:
            Transaction: Transaction de virement créée
        """
        try:
            # Vérifier le solde du portefeuille
            wallet, created = Wallet.objects.get_or_create(user=user)
            if not wallet.can_withdraw(amount):
                raise ValueError("Solde insuffisant pour le virement")
            
            # Créer la transaction de virement
            transfer_transaction = Transaction.objects.create(
                user=user,
                type='withdrawal',
                amount=amount,
                currency='DZD',
                payment_method='bank_transfer',
                description=description or f"Virement vers {bank_name}",
                status='pending',
                metadata={
                    'bank_name': bank_name,
                    'account_number': account_number,
                    'account_holder': account_holder,
                    'transfer_type': 'bank_transfer',
                    'request_date': timezone.now().isoformat()
                }
            )
            
            logger.info(f"Demande de virement créée: {transfer_transaction.transaction_id}")
            return transfer_transaction
            
        except Exception as e:
            logger.error(f"Erreur demande virement: {str(e)}")
            raise
    
    @staticmethod
    def confirm_bank_transfer(transfer_id, bank_reference, confirmed_by, confirmation_date=None, notes=None):
        """
        Confirme un virement bancaire.
        
        Args:
            transfer_id: ID de la transaction de virement
            bank_reference: Référence bancaire
            confirmed_by: Utilisateur qui confirme
            confirmation_date: Date de confirmation
            notes: Notes de confirmation
            
        Returns:
            bool: Succès de la confirmation
        """
        try:
            try:
                transfer_transaction = Transaction.objects.get(
                    transaction_id=transfer_id,
                    type='withdrawal',
                    payment_method='bank_transfer',
                    status='pending'
                )
            except Transaction.DoesNotExist:
                logger.error(f"Transaction de virement non trouvée: {transfer_id}")
                return False
            
            # Confirmer le virement
            transfer_transaction.status = 'completed'
            transfer_transaction.completed_at = timezone.now()
            transfer_transaction.metadata.update({
                'bank_reference': bank_reference,
                'confirmation_date': confirmation_date or timezone.now().date().isoformat(),
                'confirmed_by': confirmed_by.id,
                'notes': notes,
                'confirmation_timestamp': timezone.now().isoformat()
            })
            transfer_transaction.save()
            
            # Déduire du portefeuille
            wallet, created = Wallet.objects.get_or_create(user=transfer_transaction.user)
            wallet.deduct_funds(transfer_transaction.amount, 'withdrawal')
            
            logger.info(f"Virement confirmé: {transfer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur confirmation virement: {str(e)}")
            return False
    
    @staticmethod
    def get_transfer_history(user, limit=50):
        """
        Récupère l'historique des virements d'un utilisateur.
        
        Args:
            user: Utilisateur
            limit: Nombre maximum de virements à récupérer
            
        Returns:
            QuerySet: Transactions de virement
        """
        try:
            return Transaction.objects.filter(
                user=user,
                type='withdrawal',
                payment_method='bank_transfer'
            ).order_by('-created_at')[:limit]
            
        except Exception as e:
            logger.error(f"Erreur historique virements: {str(e)}")
            return Transaction.objects.none()
