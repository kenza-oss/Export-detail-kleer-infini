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
    def get(self, request):
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
            
            methods = AlgerianPaymentService.get_available_payment_methods(amount)
            serializer = PaymentMethodSerializer(methods, many=True)
            
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
                data['card_type'],
                data['card_number'],
                data['amount']
            )
            
            if not validation['valid']:
                return Response({
                    'success': False,
                    'error': validation['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer la transaction
            transaction = AlgerianPaymentService.create_card_payment(
                user=request.user,
                amount=data['amount'],
                card_type=data['card_type'],
                shipment=data.get('shipment'),
                card_last_four=validation['card_last_four'],
                card_holder_name=data.get('card_holder_name', ''),
                card_number=data['card_number']  # Ne pas stocker en production
            )
            
            # Traiter le paiement
            result = AlgerianPaymentService.process_card_payment(
                transaction.transaction_id,
                {
                    'card_number': data['card_number'],
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
