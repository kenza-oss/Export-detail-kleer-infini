"""
Vues pour la gestion des paiements algériens
Support pour CIB, Eddahabia et paiement en espèces au bureau
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.utils import timezone
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from .models import Transaction, PaymentMethod, Wallet
from .serializers import (
    TransactionSerializer, PaymentMethodSerializer,
    CardPaymentSerializer, CashPaymentSerializer,
    PaymentValidationSerializer, PaymentConfirmationSerializer
)
from .services import (
    AlgerianPaymentService, PaymentValidationService, PaymentReportingService
)
from .permissions import IsOwnerOrAdmin
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


class PaymentMethodsView(APIView):
    """Vue pour récupérer les méthodes de paiement disponibles."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupère les méthodes de paiement disponibles",
        manual_parameters=[
            openapi.Parameter(
                'amount',
                openapi.IN_QUERY,
                description="Montant pour filtrer les méthodes disponibles",
                type=openapi.TYPE_NUMBER,
                required=False
            )
        ],
        responses={
            status.HTTP_200_OK: PaymentMethodSerializer(many=True),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "error": "Montant invalide"
                }}
            )
        }
    )
    def get(self, request, method_name=None):
        """Récupère les méthodes de paiement disponibles."""
        try:
            amount = request.query_params.get('amount')
            if amount:
                try:
                    amount = float(amount)
                except ValueError:
                    return Response({
                        'error': 'Montant invalide'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Si une méthode spécifique est demandée
            if method_name:
                try:
                    method = PaymentMethod.objects.get(
                        method_type=method_name,
                        is_active=True
                    )
                    serializer = PaymentMethodSerializer(method, context={'amount': amount})
                    return Response({
                        'success': True,
                        'payment_method': serializer.data
                    })
                except PaymentMethod.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': f'Méthode de paiement "{method_name}" non trouvée'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # Sinon, récupérer toutes les méthodes
            methods = AlgerianPaymentService.get_available_payment_methods(amount)
            serializer = PaymentMethodSerializer(methods, many=True, context={'amount': amount})
            
            return Response({
                'success': True,
                'payment_methods': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erreur récupération méthodes de paiement: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la récupération des méthodes de paiement'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CardPaymentView(APIView):
    """Vue pour les paiements par carte bancaire algérienne (CIB/Eddahabia)."""
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Effectue un paiement par carte bancaire algérienne",
        request_body=CardPaymentSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Paiement créé avec succès",
                examples={"application/json": {
                    "success": True,
                    "transaction": {
                        "transaction_id": "TXN123456789ABC",
                        "amount": 5000.00,
                        "payment_method": "cib",
                        "status": "pending"
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "error": "Type de carte non supporté"
                }}
            )
        }
    )
    def post(self, request):
        """Effectue un paiement par carte bancaire."""
        try:
            serializer = CardPaymentSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            
            # Validation du paiement
            validation = PaymentValidationService.validate_card_payment(
                card_type=data['card_type'],
                card_number=data.get('card_number'),
                amount=data['amount']
            )
            
            if not validation['valid']:
                return Response({
                    'success': False,
                    'error': validation['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer l'envoi si shipment_id est fourni
            shipment = None
            if data.get('shipment_id'):
                try:
                    from shipments.models import Shipment
                    shipment = Shipment.objects.get(id=data['shipment_id'])
                except Shipment.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'Envoi non trouvé'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # Créer la transaction
            transaction = AlgerianPaymentService.create_card_payment(
                user=request.user,
                amount=data['amount'],
                card_type=data['card_type'],
                shipment=shipment,
                card_last_four=validation.get('card_last_four', ''),
                card_holder_name=data.get('card_holder_name', ''),
                card_number=data.get('card_number', '')  # Ne pas stocker en production
            )
            
            # Traiter le paiement
            result = AlgerianPaymentService.process_card_payment(
                transaction.transaction_id,
                {
                    'card_number': data.get('card_number', ''),
                    'card_holder_name': data.get('card_holder_name', ''),
                    'cvv': data.get('cvv', ''),
                    'expiry_month': data.get('expiry_month', ''),
                    'expiry_year': data.get('expiry_year', '')
                }
            )
            
            if result['success']:
                transaction.refresh_from_db()
                transaction_serializer = TransactionSerializer(transaction)
                
                return Response({
                    'success': True,
                    'message': result['message'],
                    'transaction': transaction_serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Erreur paiement carte: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors du traitement du paiement'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CashPaymentView(APIView):
    """Vue pour les paiements en espèces au bureau."""
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Crée un paiement en espèces au bureau",
        request_body=CashPaymentSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Paiement en espèces créé",
                examples={"application/json": {
                    "success": True,
                    "transaction": {
                        "transaction_id": "TXN123456789ABC",
                        "amount": 5000.00,
                        "payment_method": "cash",
                        "status": "pending",
                        "cash_payment_location": "Bureau Kleer Infini - Alger Centre"
                    }
                }}
            )
        }
    )
    def post(self, request):
        """Crée un paiement en espèces."""
        try:
            serializer = CashPaymentSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            
            # Validation du paiement
            validation = PaymentValidationService.validate_cash_payment(
                data['amount'],
                data.get('office_location', 'Bureau Kleer Infini - Alger Centre')
            )
            
            if not validation['valid']:
                return Response({
                    'success': False,
                    'error': validation['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer la transaction
            transaction = AlgerianPaymentService.create_cash_payment(
                user=request.user,
                amount=data['amount'],
                shipment=data.get('shipment'),
                office_location=data.get('office_location', 'Bureau Kleer Infini - Alger Centre')
            )
            
            transaction_serializer = TransactionSerializer(transaction)
            
            return Response({
                'success': True,
                'message': 'Paiement en espèces créé. Rendez-vous au bureau pour effectuer le paiement.',
                'transaction': transaction_serializer.data,
                'instructions': {
                    'office_location': transaction.cash_payment_location,
                    'reference': transaction.transaction_id,
                    'amount': transaction.amount,
                    'status': 'En attente de paiement au bureau'
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur création paiement espèces: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la création du paiement en espèces'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CashPaymentConfirmationView(APIView):
    """Vue pour confirmer un paiement en espèces (admin/bureau)."""
    
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Confirme un paiement en espèces",
        request_body=PaymentConfirmationSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Paiement confirmé",
                examples={"application/json": {
                    "success": True,
                    "message": "Paiement en espèces confirmé avec succès"
                }}
            )
        }
    )
    def post(self, request, transaction_id):
        """Confirme un paiement en espèces."""
        try:
            serializer = PaymentConfirmationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            
            # Confirmer le paiement
            transaction = AlgerianPaymentService.confirm_cash_payment(
                transaction_id=transaction_id,
                confirmed_by_user=request.user,
                payment_date=data.get('payment_date')
            )
            
            transaction_serializer = TransactionSerializer(transaction)
            
            return Response({
                'success': True,
                'message': 'Paiement en espèces confirmé avec succès',
                'transaction': transaction_serializer.data
            })
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur confirmation paiement espèces: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la confirmation du paiement'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentFeesView(APIView):
    """Vue pour calculer les frais de paiement."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Calcule les frais pour une méthode de paiement",
        manual_parameters=[
            openapi.Parameter(
                'amount',
                openapi.IN_QUERY,
                description="Montant du paiement",
                type=openapi.TYPE_NUMBER,
                required=True
            ),
            openapi.Parameter(
                'payment_method',
                openapi.IN_QUERY,
                description="Méthode de paiement",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Frais calculés",
                examples={"application/json": {
                    "success": True,
                    "fees": {
                        "base_amount": 5000.00,
                        "fees": 50.00,
                        "total_amount": 5050.00,
                        "fee_percentage": 1.00,
                        "fixed_fee": 0.00
                    }
                }}
            )
        }
    )
    def get(self, request):
        """Calcule les frais de paiement."""
        try:
            amount = request.query_params.get('amount')
            payment_method = request.query_params.get('payment_method')
            
            if not amount or not payment_method:
                return Response({
                    'success': False,
                    'error': 'Montant et méthode de paiement requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                amount = float(amount)
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Montant invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            fees = AlgerianPaymentService.calculate_payment_fees(amount, payment_method)
            
            return Response({
                'success': True,
                'fees': fees
            })
            
        except Exception as e:
            logger.error(f"Erreur calcul frais: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors du calcul des frais'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentStatisticsView(APIView):
    """Vue pour les statistiques de paiement (admin)."""
    
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    @swagger_auto_schema(
        operation_description="Récupère les statistiques de paiement",
        manual_parameters=[
            openapi.Parameter(
                'start_date',
                openapi.IN_QUERY,
                description="Date de début (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'end_date',
                openapi.IN_QUERY,
                description="Date de fin (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Statistiques de paiement",
                examples={"application/json": {
                    "success": True,
                    "statistics": {
                        "total_transactions": 150,
                        "total_amount": 750000.00,
                        "algerian_cards": {
                            "cib": 45,
                            "eddahabia": 30
                        },
                        "cash_payments": 25
                    }
                }}
            )
        }
    )
    def get(self, request):
        """Récupère les statistiques de paiement."""
        try:
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            # Convertir les dates si fournies
            if start_date:
                try:
                    start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
                except ValueError:
                    return Response({
                        'success': False,
                        'error': 'Format de date de début invalide (YYYY-MM-DD)'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            if end_date:
                try:
                    end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
                except ValueError:
                    return Response({
                        'success': False,
                        'error': 'Format de date de fin invalide (YYYY-MM-DD)'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            statistics = PaymentReportingService.get_payment_statistics(start_date, end_date)
            
            return Response({
                'success': True,
                'statistics': statistics
            })
            
        except Exception as e:
            logger.error(f"Erreur statistiques paiement: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la récupération des statistiques'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransactionDetailView(APIView):
    """Vue pour les détails d'une transaction."""
    
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    @swagger_auto_schema(
        operation_description="Récupère les détails d'une transaction",
        responses={
            status.HTTP_200_OK: TransactionSerializer,
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Transaction non trouvée",
                examples={"application/json": {
                    "success": False,
                    "error": "Transaction non trouvée"
                }}
            )
        }
    )
    def get(self, request, transaction_id):
        """Récupère les détails d'une transaction."""
        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
            
            # Vérifier les permissions
            if not request.user.is_staff and transaction.user != request.user:
                return Response({
                    'success': False,
                    'error': 'Accès non autorisé'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = TransactionSerializer(transaction)
            
            return Response({
                'success': True,
                'transaction': serializer.data
            })
            
        except Transaction.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Transaction non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur récupération transaction: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la récupération de la transaction'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletView(APIView):
    """Vue pour la gestion des portefeuilles virtuels."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Obtenir le portefeuille de l'utilisateur",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Portefeuille récupéré avec succès",
                examples={"application/json": {
                    "success": True,
                    "wallet": {
                        "balance": 5000.00,
                        "pending_balance": 1000.00,
                        "available_balance": 4000.00,
                        "total_earned": 15000.00,
                        "total_spent": 10000.00
                    }
                }}
            )
        }
    )
    def get(self, request):
        """Obtenir le portefeuille de l'utilisateur."""
        try:
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            
            return Response({
                'success': True,
                'wallet': {
                    'balance': float(wallet.balance),
                    'pending_balance': float(wallet.pending_balance),
                    'available_balance': float(wallet.available_balance),
                    'total_earned': float(wallet.total_earned),
                    'total_spent': float(wallet.total_spent),
                    'created_at': wallet.created_at,
                    'updated_at': wallet.updated_at
                }
            })
        except Exception as e:
            logger.error(f"Erreur récupération portefeuille: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la récupération du portefeuille'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletBalanceView(APIView):
    """Vue pour obtenir le solde du portefeuille."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtenir le solde du portefeuille."""
        try:
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            
            return Response({
                'success': True,
                'balance': {
                    'available': float(wallet.available_balance),
                    'pending': float(wallet.pending_balance),
                    'total': float(wallet.balance)
                }
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Erreur lors de la récupération du solde'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletTransactionsView(APIView):
    """Vue pour l'historique des transactions du portefeuille."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtenir l'historique des transactions."""
        try:
            transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
            
            # Filtres
            transaction_type = request.query_params.get('type')
            status_filter = request.query_params.get('status')
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            if transaction_type:
                transactions = transactions.filter(type=transaction_type)
            if status_filter:
                transactions = transactions.filter(status=status_filter)
            if date_from:
                transactions = transactions.filter(created_at__gte=date_from)
            if date_to:
                transactions = transactions.filter(created_at__lte=date_to)
            
            serializer = TransactionSerializer(transactions, many=True)
            
            return Response({
                'success': True,
                'transactions': serializer.data,
                'count': transactions.count()
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Erreur lors de la récupération des transactions'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletDepositView(APIView):
    """Vue pour effectuer un dépôt sur le portefeuille."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Effectuer un dépôt."""
        try:
            amount = request.data.get('amount')
            payment_method = request.data.get('payment_method', 'chargily')
            description = request.data.get('description', 'Dépôt sur portefeuille')
            
            if not amount or float(amount) <= 0:
                return Response({
                    'success': False,
                    'error': 'Montant invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Convertir en Decimal pour éviter les problèmes de type
            from decimal import Decimal
            amount = Decimal(str(amount))
            
            # Créer la transaction de dépôt
            transaction = Transaction.objects.create(
                user=request.user,
                type='deposit',
                amount=amount,
                currency='DZD',
                payment_method=payment_method,
                description=description,
                status='pending'
            )
            
            return Response({
                'success': True,
                'transaction_id': transaction.transaction_id,
                'message': 'Dépôt initié avec succès'
            })
        except Exception as e:
            logger.error(f"Erreur lors du dépôt: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors du dépôt'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletWithdrawView(APIView):
    """Vue pour effectuer un retrait du portefeuille."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Effectuer un retrait."""
        try:
            amount = request.data.get('amount')
            withdrawal_method = request.data.get('withdrawal_method', 'bank_transfer')
            bank_account = request.data.get('bank_account')
            description = request.data.get('description', 'Retrait du portefeuille')
            
            if not amount or amount <= 0:
                return Response({
                    'success': False,
                    'error': 'Montant invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            
            if not wallet.can_withdraw(amount):
                return Response({
                    'success': False,
                    'error': 'Solde insuffisant'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer la transaction de retrait
            transaction = Transaction.objects.create(
                user=request.user,
                type='withdrawal',
                amount=amount,
                currency='DZD',
                payment_method=withdrawal_method,
                description=description,
                status='pending',
                metadata={'bank_account': bank_account}
            )
            
            return Response({
                'success': True,
                'transaction_id': transaction.transaction_id,
                'message': 'Retrait initié avec succès'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Erreur lors du retrait'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletTransferView(APIView):
    """Vue pour effectuer un transfert entre portefeuilles."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Effectuer un transfert."""
        try:
            recipient_id = request.data.get('recipient_id')
            amount = request.data.get('amount')
            description = request.data.get('description', 'Transfert entre portefeuilles')
            
            if not all([recipient_id, amount]) or amount <= 0:
                return Response({
                    'success': False,
                    'error': 'Paramètres invalides'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                recipient = get_user_model().objects.get(id=recipient_id)
            except get_user_model().DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Destinataire non trouvé'
                }, status=status.HTTP_404_NOT_FOUND)
            
            sender_wallet, created = Wallet.objects.get_or_create(user=request.user)
            recipient_wallet, created = Wallet.objects.get_or_create(user=recipient)
            
            if not sender_wallet.can_withdraw(amount):
                return Response({
                    'success': False,
                    'error': 'Solde insuffisant'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # Créer la transaction de transfert sortant
                transfer_out = Transaction.objects.create(
                    user=request.user,
                    type='transfer',
                    amount=amount,
                    currency='DZD',
                    description=f"Transfert vers {recipient.username}",
                    status='completed'
                )
                
                # Créer la transaction de transfert entrant
                transfer_in = Transaction.objects.create(
                    user=recipient,
                    type='transfer',
                    amount=amount,
                    currency='DZD',
                    description=f"Transfert reçu de {request.user.username}",
                    status='completed',
                    related_transaction=transfer_out
                )
                
                # Mettre à jour les portefeuilles
                sender_wallet.deduct_funds(amount, 'transfer')
                recipient_wallet.add_funds(amount, 'transfer')
                
                transfer_out.related_transaction = transfer_in
                transfer_out.save()
            
            return Response({
                'success': True,
                'transfer_id': transfer_out.transaction_id,
                'message': 'Transfert effectué avec succès'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Erreur lors du transfert'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChargilyPaymentView(APIView):
    """Vue pour les paiements via Chargily Pay."""
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def post(self, request):
        """Crée un paiement via Chargily Pay."""
        try:
            amount = request.data.get('amount')
            payment_mode = request.data.get('payment_mode')
            shipment_id = request.data.get('shipment_id')
            description = request.data.get('description', 'Paiement via Chargily')
            back_url = request.data.get('back_url')
            webhook_url = request.data.get('webhook_url')
            
            if not all([amount, payment_mode, shipment_id]):
                return Response({
                    'success': False,
                    'error': 'Paramètres manquants'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validation du mode de paiement
            valid_modes = ['edahabia', 'cib', 'baridi_mob']
            if payment_mode not in valid_modes:
                return Response({
                    'success': False,
                    'error': f'Mode de paiement invalide. Utilisez: {", ".join(valid_modes)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer la transaction
            transaction = Transaction.objects.create(
                user=request.user,
                type='payment',
                amount=amount,
                currency='DZD',
                payment_method='chargily',
                payment_gateway='chargily',
                description=description,
                status='pending',
                metadata={
                    'payment_mode': payment_mode,
                    'back_url': back_url,
                    'webhook_url': webhook_url,
                    'chargily_integration': True
                }
            )
            
            # Simuler l'URL Chargily (en production, intégrer avec l'API Chargily)
            chargily_url = f"https://pay.chargily.com/checkout/{transaction.transaction_id}"
            
            return Response({
                'success': True,
                'transaction_id': transaction.transaction_id,
                'chargily_url': chargily_url,
                'message': 'Paiement Chargily initié'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur création paiement Chargily: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la création du paiement Chargily'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChargilyPaymentStatusView(APIView):
    """Vue pour vérifier le statut d'un paiement Chargily."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, transaction_id):
        """Vérifie le statut d'un paiement Chargily."""
        try:
            transaction = Transaction.objects.get(
                transaction_id=transaction_id,
                user=request.user,
                payment_method='chargily'
            )
            
            return Response({
                'success': True,
                'status': transaction.status,
                'transaction_id': transaction.transaction_id,
                'amount': transaction.amount
            })
            
        except Transaction.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Transaction non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur vérification statut Chargily: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la vérification du statut'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChargilyWebhookView(APIView):
    """Vue pour recevoir les webhooks Chargily."""
    
    permission_classes = []  # Pas d'authentification pour les webhooks
    
    def post(self, request):
        """Traite les webhooks Chargily."""
        try:
            webhook_data = request.data
            transaction_id = webhook_data.get('order_id')
            status = webhook_data.get('status')
            amount = webhook_data.get('amount')
            
            if not all([transaction_id, status]):
                return Response({
                    'error': 'Données webhook incomplètes'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                transaction = Transaction.objects.get(transaction_id=transaction_id)
            except Transaction.DoesNotExist:
                return Response({
                    'error': 'Transaction non trouvée'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Mettre à jour le statut de la transaction
            if status == 'paid':
                transaction.status = 'completed'
                transaction.completed_at = timezone.now()
                transaction.metadata.update({
                    'chargily_payment_id': webhook_data.get('id'),
                    'webhook_received_at': timezone.now().isoformat()
                })
                transaction.save()
                
                # Mettre à jour le portefeuille si nécessaire
                if transaction.type == 'payment':
                    wallet, created = Wallet.objects.get_or_create(user=transaction.user)
                    wallet.add_funds(amount, 'payment')
            
            logger.info(f"Webhook Chargily traité: {transaction_id} - {status}")
            
            return Response({'success': True})
            
        except Exception as e:
            logger.error(f"Erreur traitement webhook Chargily: {str(e)}")
            return Response({
                'error': 'Erreur lors du traitement du webhook'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommissionView(APIView):
    """Vue pour la gestion des commissions."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupère les détails des commissions."""
        try:
            # En production, récupérer depuis la configuration
            commission_data = {
                'commission_rate': 25.0,  # 25%
                'min_commission': 500.00,
                'max_commission': 5000.00,
                'description': 'Commission standard Kleer Logistics'
            }
            
            return Response({
                'success': True,
                **commission_data
            })
            
        except Exception as e:
            logger.error(f"Erreur récupération commissions: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la récupération des commissions'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommissionCalculateView(APIView):
    """Vue pour calculer les commissions."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Calcule les commissions pour un envoi."""
        try:
            shipment_id = request.data.get('shipment_id')
            total_amount = request.data.get('total_amount')
            commission_rate = request.data.get('commission_rate', 25.0)
            
            if not all([shipment_id, total_amount]):
                return Response({
                    'success': False,
                    'error': 'Paramètres manquants'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            commission_amount = (total_amount * commission_rate) / 100
            traveler_amount = total_amount - commission_amount
            
            return Response({
                'success': True,
                'shipment_id': shipment_id,
                'total_amount': total_amount,
                'commission_rate': commission_rate,
                'commission_amount': commission_amount,
                'traveler_amount': traveler_amount
            })
            
        except Exception as e:
            logger.error(f"Erreur calcul commissions: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors du calcul des commissions'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommissionApplyView(APIView):
    """Vue pour appliquer les commissions."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Applique les commissions à un envoi."""
        try:
            shipment_id = request.data.get('shipment_id')
            commission_amount = request.data.get('commission_amount')
            traveler_amount = request.data.get('traveler_amount')
            description = request.data.get('description', 'Commission standard')
            
            if not all([shipment_id, commission_amount, traveler_amount]):
                return Response({
                    'success': False,
                    'error': 'Paramètres manquants'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer la transaction de commission
            commission_transaction = Transaction.objects.create(
                user=request.user,
                type='commission',
                amount=commission_amount,
                currency='DZD',
                description=description,
                status='completed',
                metadata={'shipment_id': shipment_id, 'traveler_amount': traveler_amount}
            )
            
            return Response({
                'success': True,
                'commission_transaction_id': commission_transaction.transaction_id,
                'message': 'Commission appliquée avec succès'
            })
            
        except Exception as e:
            logger.error(f"Erreur application commission: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de l\'application de la commission'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BankTransferRequestView(APIView):
    """Vue pour demander un virement bancaire."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Demande un virement bancaire."""
        try:
            amount = request.data.get('amount')
            bank_name = request.data.get('bank_name')
            account_number = request.data.get('account_number')
            account_holder = request.data.get('account_holder')
            description = request.data.get('description', 'Virement bancaire')
            
            if not all([amount, bank_name, account_number, account_holder]):
                return Response({
                    'success': False,
                    'error': 'Paramètres manquants'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier le solde du portefeuille
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            if not wallet.can_withdraw(amount):
                return Response({
                    'success': False,
                    'error': 'Solde insuffisant'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer la transaction de virement
            transfer_transaction = Transaction.objects.create(
                user=request.user,
                type='withdrawal',
                amount=amount,
                currency='DZD',
                payment_method='bank_transfer',
                description=description,
                status='pending',
                metadata={
                    'bank_name': bank_name,
                    'account_number': account_number,
                    'account_holder': account_holder,
                    'transfer_type': 'bank_transfer'
                }
            )
            
            return Response({
                'success': True,
                'transfer_id': transfer_transaction.transaction_id,
                'message': 'Demande de virement initiée'
            })
            
        except Exception as e:
            logger.error(f"Erreur demande virement: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la demande de virement'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BankTransferConfirmView(APIView):
    """Vue pour confirmer un virement (Admin)."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Confirme un virement bancaire."""
        try:
            transfer_id = request.data.get('transfer_id')
            bank_reference = request.data.get('bank_reference')
            confirmation_date = request.data.get('confirmation_date')
            notes = request.data.get('notes', 'Virement confirmé')
            
            if not all([transfer_id, bank_reference]):
                return Response({
                    'success': False,
                    'error': 'Paramètres manquants'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                transfer_transaction = Transaction.objects.get(
                    transaction_id=transfer_id,
                    type='withdrawal',
                    payment_method='bank_transfer'
                )
            except Transaction.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Transaction de virement non trouvée'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Confirmer le virement
            transfer_transaction.status = 'completed'
            transfer_transaction.completed_at = timezone.now()
            transfer_transaction.metadata.update({
                'bank_reference': bank_reference,
                'confirmation_date': confirmation_date,
                'confirmed_by': request.user.id,
                'notes': notes
            })
            transfer_transaction.save()
            
            # Déduire du portefeuille
            wallet, created = Wallet.objects.get_or_create(user=transfer_transaction.user)
            wallet.deduct_funds(transfer_transaction.amount, 'withdrawal')
            
            return Response({
                'success': True,
                'message': 'Virement confirmé avec succès'
            })
            
        except Exception as e:
            logger.error(f"Erreur confirmation virement: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la confirmation du virement'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BankTransferHistoryView(APIView):
    """Vue pour l'historique des virements."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupère l'historique des virements."""
        try:
            transfers = Transaction.objects.filter(
                user=request.user,
                type='withdrawal',
                payment_method='bank_transfer'
            ).order_by('-created_at')
            
            serializer = TransactionSerializer(transfers, many=True)
            
            return Response({
                'success': True,
                'transfers': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erreur historique virements: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la récupération de l\'historique'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CashPaymentOfficesView(APIView):
    """Vue pour la liste des bureaux de paiement."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupère la liste des bureaux de paiement."""
        try:
            offices = [
                {
                    'id': 1,
                    'name': 'Bureau Kleer Infini - Alger Centre',
                    'address': '123 Rue Didouche Mourad, Alger',
                    'phone': '+213 21 123 456',
                    'hours': 'Lun-Ven: 9h-17h, Sam: 9h-12h',
                    'coordinates': {'lat': 36.7538, 'lng': 3.0588}
                },
                {
                    'id': 2,
                    'name': 'Bureau Kleer Infini - Oran',
                    'address': '456 Boulevard de l\'ALN, Oran',
                    'phone': '+213 41 789 012',
                    'hours': 'Lun-Ven: 8h-16h, Sam: 8h-11h',
                    'coordinates': {'lat': 35.6971, 'lng': -0.6337}
                },
                {
                    'id': 3,
                    'name': 'Bureau Kleer Infini - Constantine',
                    'address': '789 Rue Larbi Ben M\'Hidi, Constantine',
                    'phone': '+213 31 345 678',
                    'hours': 'Lun-Ven: 9h-17h, Sam: 9h-12h',
                    'coordinates': {'lat': 36.3650, 'lng': 6.6147}
                }
            ]
            
            return Response({
                'success': True,
                'offices': offices
            })
            
        except Exception as e:
            logger.error(f"Erreur récupération bureaux: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la récupération des bureaux'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransactionListView(APIView):
    """Vue pour lister les transactions de l'utilisateur."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupère toutes les transactions de l'utilisateur."""
        try:
            transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
            
            # Filtres optionnels
            transaction_type = request.query_params.get('type')
            status = request.query_params.get('status')
            payment_method = request.query_params.get('payment_method')
            
            if transaction_type:
                transactions = transactions.filter(type=transaction_type)
            if status:
                transactions = transactions.filter(status=status)
            if payment_method:
                transactions = transactions.filter(payment_method=payment_method)
            
            serializer = TransactionSerializer(transactions, many=True)
            
            return Response({
                'success': True,
                'transactions': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erreur récupération transactions: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la récupération des transactions'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransactionCancelView(APIView):
    """Vue pour annuler une transaction."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, transaction_id):
        """Annule une transaction."""
        try:
            try:
                transaction = Transaction.objects.get(
                    transaction_id=transaction_id,
                    user=request.user
                )
            except Transaction.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Transaction non trouvée'
                }, status=status.HTTP_404_NOT_FOUND)
            
            reason = request.data.get('reason', '')
            description = request.data.get('description', '')
            
            transaction.cancel()
            transaction.metadata.update({
                'cancellation_reason': reason,
                'cancellation_description': description,
                'cancelled_by': request.user.id,
                'cancelled_at': timezone.now().isoformat()
            })
            transaction.save()
            
            return Response({
                'success': True,
                'message': 'Transaction annulée avec succès'
            })
            
        except Exception as e:
            logger.error(f"Erreur annulation transaction: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de l\'annulation de la transaction'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransactionRefundView(APIView):
    """Vue pour demander un remboursement."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, transaction_id):
        """Demande un remboursement."""
        try:
            try:
                transaction = Transaction.objects.get(
                    transaction_id=transaction_id,
                    user=request.user
                )
            except Transaction.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Transaction non trouvée'
                }, status=status.HTTP_404_NOT_FOUND)
            
            amount = request.data.get('amount')
            reason = request.data.get('reason', '')
            description = request.data.get('description', '')
            
            if not amount:
                return Response({
                    'success': False,
                    'error': 'Montant de remboursement requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            refund_transaction = transaction.refund(amount)
            refund_transaction.metadata.update({
                'refund_reason': reason,
                'refund_description': description,
                'refunded_by': request.user.id,
                'refunded_at': timezone.now().isoformat()
            })
            refund_transaction.save()
            
            return Response({
                'success': True,
                'refund_transaction_id': refund_transaction.transaction_id,
                'message': 'Remboursement initié avec succès'
            })
            
        except Exception as e:
            logger.error(f"Erreur remboursement: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors du remboursement'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeesCalculateView(APIView):
    """Vue pour calculer les frais pour un envoi."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Calcule les frais pour un envoi."""
        try:
            shipment_id = request.data.get('shipment_id')
            weight = request.data.get('weight', 0)
            distance = request.data.get('distance', 0)
            urgency = request.data.get('urgency', 'normal')
            insurance = request.data.get('insurance', False)
            
            if not shipment_id:
                return Response({
                    'success': False,
                    'error': 'ID de l\'envoi requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calcul des frais (logique simplifiée)
            base_fee = 1000.00  # Frais de base
            weight_fee = weight * 200.00  # 200 DA par kg
            distance_fee = distance * 5.00  # 5 DA par km
            urgency_fee = 500.00 if urgency == 'urgent' else 0.00
            insurance_fee = 300.00 if insurance else 0.00
            
            total_fees = base_fee + weight_fee + distance_fee + urgency_fee + insurance_fee
            
            return Response({
                'success': True,
                'fees_breakdown': {
                    'base_fee': base_fee,
                    'weight_fee': weight_fee,
                    'distance_fee': distance_fee,
                    'urgency_fee': urgency_fee,
                    'insurance_fee': insurance_fee
                },
                'total_fees': total_fees,
                'shipment_id': shipment_id
            })
            
        except Exception as e:
            logger.error(f"Erreur calcul frais: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors du calcul des frais'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
