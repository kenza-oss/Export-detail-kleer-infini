"""
Views for payments app - Payment and wallet management
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
import random
import string
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Wallet, Transaction, Commission
from .serializers import (
    WalletSerializer, TransactionSerializer, CommissionSerializer,
    PaymentMethodSerializer, ChargilyPaySerializer
)
from config.swagger_examples import (
    PAYMENT_CREATE_EXAMPLE, PAYMENT_WEBHOOK_EXAMPLE, ERROR_EXAMPLES
)
from config.swagger_config import (
    payment_create_schema
)


class WalletView(APIView):
    """Vue pour la gestion du portefeuille."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer le portefeuille de l'utilisateur",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Portefeuille récupéré",
                examples={"application/json": {
                    "success": True,
                    "wallet": {
                        "id": 1,
                        "user": 1,
                        "balance": 1500.00,
                        "currency": "DZD",
                        "is_active": True,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                }}
            )
        }
    )
    def get(self, request):
        """Récupérer le portefeuille de l'utilisateur."""
        try:
            wallet = Wallet.objects.get(user=request.user)
            serializer = WalletSerializer(wallet)
            return Response({
                'success': True,
                'wallet': serializer.data
            })
        except Wallet.DoesNotExist:
            # Créer un portefeuille si il n'existe pas
            wallet = Wallet.objects.create(user=request.user)
            serializer = WalletSerializer(wallet)
            return Response({
                'success': True,
                'wallet': serializer.data
            })


class TransactionListView(APIView):
    """Vue pour la liste des transactions."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Lister les transactions de l'utilisateur",
        manual_parameters=[
            openapi.Parameter(
                'transaction_type',
                openapi.IN_QUERY,
                description="Type de transaction",
                type=openapi.TYPE_STRING,
                enum=['deposit', 'withdrawal', 'transfer', 'payment', 'refund']
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Statut de la transaction",
                type=openapi.TYPE_STRING,
                enum=['pending', 'completed', 'failed', 'cancelled']
            ),
            openapi.Parameter(
                'date_from',
                openapi.IN_QUERY,
                description="Date de début (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            ),
            openapi.Parameter(
                'date_to',
                openapi.IN_QUERY,
                description="Date de fin (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des transactions",
                examples={"application/json": {
                    "success": True,
                    "transactions": [
                        {
                            "id": 1,
                            "transaction_type": "deposit",
                            "amount": 500.00,
                            "currency": "DZD",
                            "payment_method": "card",
                            "status": "completed",
                            "reference": "DEP123456",
                            "created_at": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "count": 1
                }}
            )
        }
    )
    def get(self, request):
        """Récupérer l'historique des transactions."""
        transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
        serializer = TransactionSerializer(transactions, many=True)
        
        return Response({
            'success': True,
            'transactions': serializer.data,
            'count': transactions.count()
        })


class DepositView(APIView):
    """Vue pour déposer de l'argent."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Effectuer un dépôt",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                'payment_method': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['card', 'bank_transfer', 'chargily']
                )
            },
            required=['amount']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Dépôt effectué",
                examples={"application/json": {
                    "success": True,
                    "message": "Dépôt effectué avec succès",
                    "transaction": {
                        "id": 1,
                        "transaction_type": "deposit",
                        "amount": 500.00,
                        "currency": "DZD",
                        "payment_method": "card",
                        "status": "completed",
                        "reference": "DEP123456"
                    },
                    "new_balance": 2000.00
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "message": "Montant invalide"
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Portefeuille non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Portefeuille non trouvé"
                }}
            )
        }
    )
    def post(self, request):
        """Effectuer un dépôt."""
        amount = request.data.get('amount')
        payment_method = request.data.get('payment_method', 'card')
        
        if not amount or amount <= 0:
            return Response({
                'success': False,
                'message': 'Montant invalide'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                wallet = Wallet.objects.get(user=request.user)
                
                # Créer la transaction
                transaction_obj = Transaction.objects.create(
                    user=request.user,
                    transaction_type='deposit',
                    amount=amount,
                    payment_method=payment_method,
                    status='completed',
                    reference=f"DEP{random.randint(100000, 999999)}"
                )
                
                # Mettre à jour le solde
                wallet.balance += amount
                wallet.save()
                
                return Response({
                    'success': True,
                    'message': 'Dépôt effectué avec succès',
                    'transaction': TransactionSerializer(transaction_obj).data,
                    'new_balance': wallet.balance
                })
        except Wallet.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Portefeuille non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class WithdrawView(APIView):
    """Vue pour retirer de l'argent."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Effectuer un retrait."""
        amount = request.data.get('amount')
        bank_account = request.data.get('bank_account')
        
        if not amount or amount <= 0:
            return Response({
                'success': False,
                'message': 'Montant invalide'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not bank_account:
            return Response({
                'success': False,
                'message': 'Compte bancaire requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                wallet = Wallet.objects.get(user=request.user)
                
                if wallet.balance < amount:
                    return Response({
                        'success': False,
                        'message': 'Solde insuffisant'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Créer la transaction
                transaction_obj = Transaction.objects.create(
                    user=request.user,
                    transaction_type='withdrawal',
                    amount=amount,
                    payment_method='bank_transfer',
                    status='pending',
                    reference=f"WTH{random.randint(100000, 999999)}",
                    notes=f"Retrait vers {bank_account}"
                )
                
                # Mettre à jour le solde
                wallet.balance -= amount
                wallet.save()
                
                return Response({
                    'success': True,
                    'message': 'Demande de retrait soumise',
                    'transaction': TransactionSerializer(transaction_obj).data,
                    'new_balance': wallet.balance
                })
        except Wallet.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Portefeuille non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class TransferView(APIView):
    """Vue pour transférer de l'argent."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Effectuer un transfert."""
        amount = request.data.get('amount')
        recipient_email = request.data.get('recipient_email')
        message = request.data.get('message', '')
        
        if not amount or amount <= 0:
            return Response({
                'success': False,
                'message': 'Montant invalide'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not recipient_email:
            return Response({
                'success': False,
                'message': 'Email du destinataire requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from users.models import User
            recipient = User.objects.get(email=recipient_email)
            
            if recipient == request.user:
                return Response({
                    'success': False,
                    'message': 'Impossible de transférer vers votre propre compte'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                sender_wallet = Wallet.objects.get(user=request.user)
                recipient_wallet, created = Wallet.objects.get_or_create(user=recipient)
                
                if sender_wallet.balance < amount:
                    return Response({
                        'success': False,
                        'message': 'Solde insuffisant'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Créer les transactions
                sender_transaction = Transaction.objects.create(
                    user=request.user,
                    transaction_type='transfer_out',
                    amount=amount,
                    payment_method='wallet_transfer',
                    status='completed',
                    reference=f"TFO{random.randint(100000, 999999)}",
                    notes=f"Transfert vers {recipient_email}: {message}"
                )
                
                recipient_transaction = Transaction.objects.create(
                    user=recipient,
                    transaction_type='transfer_in',
                    amount=amount,
                    payment_method='wallet_transfer',
                    status='completed',
                    reference=f"TFI{random.randint(100000, 999999)}",
                    notes=f"Transfert de {request.user.email}: {message}"
                )
                
                # Mettre à jour les soldes
                sender_wallet.balance -= amount
                sender_wallet.save()
                
                recipient_wallet.balance += amount
                recipient_wallet.save()
                
                return Response({
                    'success': True,
                    'message': 'Transfert effectué avec succès',
                    'transaction': TransactionSerializer(sender_transaction).data,
                    'new_balance': sender_wallet.balance
                })
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Destinataire non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Wallet.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Portefeuille non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class ChargilyPayView(APIView):
    """Vue pour l'intégration Chargily Pay."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Créer un paiement Chargily."""
        amount = request.data.get('amount')
        payment_method = request.data.get('payment_method', 'edahabia')  # edahabia, cib, baridi
        
        if not amount or amount <= 0:
            return Response({
                'success': False,
                'message': 'Montant invalide'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # En production, intégrer avec l'API Chargily
        # Pour la démonstration, on simule
        
        payment_data = {
            'id': f"CHG{random.randint(100000, 999999)}",
            'amount': amount,
            'currency': 'DZD',
            'payment_method': payment_method,
            'status': 'pending',
            'checkout_url': f"https://epay.chargily.com/pay/{random.randint(100000, 999999)}",
            'expires_at': timezone.now() + timezone.timedelta(hours=24)
        }
        
        return Response({
            'success': True,
            'message': 'Paiement Chargily créé',
            'payment': payment_data
        })


class ChargilyPayCallbackView(APIView):
    """Vue pour les callbacks Chargily Pay."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Traiter le callback de Chargily."""
        # En production, vérifier la signature et traiter le paiement
        payment_id = request.data.get('id')
        status = request.data.get('status')
        
        if status == 'paid':
            # Traiter le paiement réussi
            return Response({
                'success': True,
                'message': 'Paiement traité avec succès'
            })
        else:
            return Response({
                'success': False,
                'message': 'Paiement échoué'
            }, status=status.HTTP_400_BAD_REQUEST)


class ProcessShipmentPaymentView(APIView):
    """Vue pour traiter le paiement d'un envoi."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, shipment_id):
        """Traiter le paiement d'un envoi."""
        payment_method = request.data.get('payment_method', 'wallet')
        
        try:
            from shipments.models import Shipment
            shipment = Shipment.objects.get(id=shipment_id, user=request.user)
            
            if payment_method == 'wallet':
                return self.process_wallet_payment(request, shipment)
            elif payment_method in ['edahabia', 'cib', 'baridi']:
                return self.process_chargily_payment(request, shipment)
            else:
                return Response({
                    'success': False,
                    'message': 'Méthode de paiement non supportée'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def process_wallet_payment(self, request, shipment):
        """Traiter le paiement par portefeuille."""
        try:
            wallet = Wallet.objects.get(user=request.user)
            
            if wallet.balance < shipment.shipping_cost:
                return Response({
                    'success': False,
                    'message': 'Solde insuffisant'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # Créer la transaction
                transaction_obj = Transaction.objects.create(
                    user=request.user,
                    transaction_type='shipment_payment',
                    amount=shipment.shipping_cost,
                    payment_method='wallet',
                    status='completed',
                    reference=f"SPM{random.randint(100000, 999999)}",
                    notes=f"Paiement envoi {shipment.tracking_number}"
                )
                
                # Mettre à jour le solde
                wallet.balance -= shipment.shipping_cost
                wallet.save()
                
                # Mettre à jour l'envoi
                shipment.payment_status = 'paid'
                shipment.payment_method = 'wallet'
                shipment.payment_date = timezone.now()
                shipment.save()
                
                return Response({
                    'success': True,
                    'message': 'Paiement traité avec succès',
                    'transaction': TransactionSerializer(transaction_obj).data,
                    'new_balance': wallet.balance
                })
        except Wallet.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Portefeuille non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def process_chargily_payment(self, request, shipment):
        """Traiter le paiement Chargily."""
        payment_method = request.data.get('payment_method')
        
        # Simuler la création d'un paiement Chargily
        payment_data = {
            'id': f"CHG{random.randint(100000, 999999)}",
            'amount': shipment.shipping_cost,
            'currency': 'DZD',
            'payment_method': payment_method,
            'status': 'pending',
            'checkout_url': f"https://epay.chargily.com/pay/{random.randint(100000, 999999)}",
            'expires_at': timezone.now() + timezone.timedelta(hours=24)
        }
        
        return Response({
            'success': True,
            'message': 'Paiement Chargily créé',
            'payment': payment_data
        })


class CommissionListView(APIView):
    """Vue pour la liste des commissions."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupérer les commissions de l'utilisateur."""
        commissions = Commission.objects.filter(user=request.user).order_by('-created_at')
        serializer = CommissionSerializer(commissions, many=True)
        
        return Response({
            'success': True,
            'commissions': serializer.data,
            'count': commissions.count()
        })


class RefundView(APIView):
    """Vue pour les remboursements."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, transaction_id):
        """Demander un remboursement."""
        reason = request.data.get('reason', '')
        
        try:
            transaction_obj = Transaction.objects.get(
                id=transaction_id,
                user=request.user,
                status='completed'
            )
            
            # Créer le remboursement
            refund_transaction = Transaction.objects.create(
                user=request.user,
                transaction_type='refund',
                amount=transaction_obj.amount,
                payment_method=transaction_obj.payment_method,
                status='pending',
                reference=f"REF{random.randint(100000, 999999)}",
                notes=f"Remboursement de {transaction_obj.reference}: {reason}"
            )
            
            return Response({
                'success': True,
                'message': 'Demande de remboursement soumise',
                'refund': TransactionSerializer(refund_transaction).data
            })
        except Transaction.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Transaction non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)


class PaymentAnalyticsView(APIView):
    """Vue pour les analytics de paiement."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupérer les statistiques de paiement."""
        user_transactions = Transaction.objects.filter(user=request.user)
        
        analytics = {
            'total_transactions': user_transactions.count(),
            'total_deposits': user_transactions.filter(transaction_type='deposit').count(),
            'total_withdrawals': user_transactions.filter(transaction_type='withdrawal').count(),
            'total_transfers': user_transactions.filter(transaction_type__in=['transfer_in', 'transfer_out']).count(),
            'total_spent': sum(t.amount for t in user_transactions.filter(transaction_type='shipment_payment')),
            'total_earned': sum(t.amount for t in user_transactions.filter(transaction_type='commission')),
            'current_balance': Wallet.objects.get(user=request.user).balance
        }
        
        return Response({
            'success': True,
            'analytics': analytics
        })


# Views pour l'administration
class AdminTransactionListView(APIView):
    """Vue admin pour la liste de toutes les transactions."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Liste de toutes les transactions."""
        transactions = Transaction.objects.all().select_related('user')
        serializer = TransactionSerializer(transactions, many=True)
        
        return Response({
            'success': True,
            'transactions': serializer.data,
            'count': transactions.count()
        })


class AdminWalletListView(APIView):
    """Vue admin pour la liste de tous les portefeuilles."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Liste de tous les portefeuilles."""
        wallets = Wallet.objects.all().select_related('user')
        serializer = WalletSerializer(wallets, many=True)
        
        return Response({
            'success': True,
            'wallets': serializer.data,
            'count': wallets.count()
        })
