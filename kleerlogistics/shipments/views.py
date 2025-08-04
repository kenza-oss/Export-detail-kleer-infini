"""
Views for shipments app - Package shipping management with JSON responses
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
import uuid
import random
import string
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Shipment, ShipmentTracking, Package, ShipmentDocument, ShipmentRating
from .serializers import (
    ShipmentSerializer, ShipmentCreateSerializer, ShipmentDetailSerializer,
    ShipmentTrackingSerializer, ShipmentStatusSerializer, PackageSerializer,
    PackageCreateSerializer, ShipmentDocumentSerializer, ShipmentDocumentCreateSerializer,
    ShipmentRatingSerializer, ShipmentRatingCreateSerializer, ShipmentWithDetailsSerializer
)
from config.swagger_examples import (
    SHIPMENT_CREATE_EXAMPLE, SHIPMENT_LIST_EXAMPLE, SHIPMENT_UPDATE_EXAMPLE,
    ERROR_EXAMPLES
)
from config.swagger_config import (
    shipment_create_schema, shipment_list_schema
)


class ShipmentListView(APIView):
    """Vue pour la liste des envois."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Lister les envois de l'utilisateur",
        manual_parameters=[
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Statut de l'envoi",
                type=openapi.TYPE_STRING,
                enum=['pending', 'in_transit', 'delivered', 'cancelled']
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
                description="Liste des envois",
                examples={"application/json": {
                    "success": True,
                    "shipments": [
                        {
                            "id": 1,
                            "tracking_number": "KL123456789",
                            "origin": "Alger",
                            "destination": "Oran",
                            "weight": 2.5,
                            "status": "pending",
                            "shipping_cost": 1500.00,
                            "created_at": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "count": 1
                }}
            )
        }
    )
    def get(self, request):
        """Liste des envois de l'utilisateur connecté."""
        shipments = Shipment.objects.filter(sender=request.user).order_by('-created_at')
        serializer = ShipmentSerializer(shipments, many=True)
        
        return Response({
            'success': True,
            'shipments': serializer.data,
            'count': shipments.count()
        })


class ShipmentCreateView(APIView):
    """Vue pour la création d'envois."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Créer un nouvel envoi",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'origin': openapi.Schema(type=openapi.TYPE_STRING),
                'destination': openapi.Schema(type=openapi.TYPE_STRING),
                'weight': openapi.Schema(type=openapi.TYPE_NUMBER),
                'description': openapi.Schema(type=openapi.TYPE_STRING),
                'shipping_cost': openapi.Schema(type=openapi.TYPE_NUMBER),
                'package_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['document', 'package', 'fragile', 'express']
                ),
                'insurance': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'urgent': openapi.Schema(type=openapi.TYPE_BOOLEAN)
            },
            required=['origin', 'destination', 'weight']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Envoi créé",
                examples={"application/json": {
                    "success": True,
                    "message": "Envoi créé avec succès",
                    "shipment": {
                        "tracking_number": "KL123456789",
                        "status": "pending",
                        "id": 1
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "errors": {
                        "origin": ["Ce champ est requis."],
                        "weight": ["Ce champ doit être un nombre positif."]
                    }
                }}
            )
        }
    )
    def post(self, request):
        """Créer un nouvel envoi."""
        serializer = ShipmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                # Générer un numéro de suivi unique
                tracking_number = self.generate_tracking_number()
                
                shipment = serializer.save(
                    sender=request.user,
                    tracking_number=tracking_number,
                    status='pending'
                )
                
                # Créer un événement de suivi initial
                ShipmentTracking.objects.create(
                    shipment=shipment,
                    status='created',
                    description='Envoi créé',
                    location='Origine'
                )
            
            return Response({
                'success': True,
                'message': 'Envoi créé avec succès',
                'shipment': {
                    'tracking_number': shipment.tracking_number,
                    'status': shipment.status,
                    'id': shipment.id
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def generate_tracking_number(self):
        """Générer un numéro de suivi unique."""
        while True:
            # Format: KL + 9 chiffres
            number = ''.join(random.choices(string.digits, k=9))
            tracking_number = f"KL{number}"
            
            if not Shipment.objects.filter(tracking_number=tracking_number).exists():
                return tracking_number


class ShipmentDetailView(APIView):
    """Vue pour les détails d'un envoi."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer les détails d'un envoi",
        manual_parameters=[
            openapi.Parameter(
                'tracking_number',
                openapi.IN_PATH,
                description="Numéro de suivi de l'envoi",
                type=openapi.TYPE_STRING
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Détails de l'envoi",
                examples={"application/json": {
                    "success": True,
                    "shipment": {
                        "id": 1,
                        "tracking_number": "KL123456789",
                        "origin": "Alger",
                        "destination": "Oran",
                        "weight": 2.5,
                        "description": "Documents importants",
                        "status": "pending",
                        "shipping_cost": 1500.00,
                        "package_type": "document",
                        "insurance": True,
                        "urgent": False,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Envoi non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Envoi non trouvé"
                }}
            )
        }
    )
    def get(self, request, tracking_number):
        """Récupérer les détails d'un envoi."""
        try:
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            serializer = ShipmentDetailSerializer(shipment)
            
            return Response({
                'success': True,
                'shipment': serializer.data
            })
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, tracking_number):
        """Mettre à jour un envoi."""
        try:
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            serializer = ShipmentCreateSerializer(shipment, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Envoi mis à jour avec succès',
                    'shipment': serializer.data
                })
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, tracking_number):
        """Supprimer un envoi."""
        try:
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user,
                status='pending'  # Seulement les envois en attente peuvent être supprimés
            )
            shipment.delete()
            
            return Response({
                'success': True,
                'message': 'Envoi supprimé avec succès'
            }, status=status.HTTP_204_NO_CONTENT)
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé ou ne peut pas être supprimé'
            }, status=status.HTTP_404_NOT_FOUND)


class ShipmentStatusView(APIView):
    """Vue pour la gestion du statut des envois."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, tracking_number):
        """Récupérer le statut d'un envoi."""
        try:
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            serializer = ShipmentStatusSerializer(shipment)
            
            return Response({
                'success': True,
                'status': serializer.data
            })
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class ShipmentTrackingView(APIView):
    """Vue pour le suivi des envois."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, tracking_number):
        """Récupérer l'historique de suivi d'un envoi."""
        try:
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            tracking_events = ShipmentTracking.objects.filter(shipment=shipment).order_by('-timestamp')
            serializer = ShipmentTrackingSerializer(tracking_events, many=True)
            
            return Response({
                'success': True,
                'tracking_events': serializer.data,
                'current_status': shipment.status
            })
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class AddTrackingEventView(APIView):
    """Vue pour ajouter un événement de suivi."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, tracking_number):
        """Ajouter un événement de suivi."""
        try:
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            
            serializer = ShipmentTrackingSerializer(data=request.data)
            if serializer.is_valid():
                tracking_event = serializer.save(shipment=shipment)
                
                # Mettre à jour le statut de l'envoi si nécessaire
                if tracking_event.event_type in ['picked_up', 'in_transit', 'delivered']:
                    status_mapping = {
                        'picked_up': 'in_transit',
                        'in_transit': 'in_transit',
                        'delivered': 'delivered'
                    }
                    shipment.status = status_mapping.get(tracking_event.event_type, shipment.status)
                    shipment.save()
                
                return Response({
                    'success': True,
                    'message': 'Événement de suivi ajouté',
                    'tracking_event': serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class ShipmentMatchesView(APIView):
    """Vue pour les matches d'un envoi."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, tracking_number):
        """Récupérer les matches pour un envoi."""
        try:
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            
            # Simuler des matches (en production, utiliser l'algorithme de matching)
            matches = []
            if shipment.status == 'pending':
                # Créer des matches fictifs pour la démonstration
                matches = [
                    {
                        'id': 1,
                        'traveler': {
                            'id': 2,
                            'name': 'Ahmed Benali',
                            'rating': 4.8,
                            'total_trips': 15
                        },
                        'trip': {
                            'id': 1,
                            'origin': shipment.origin,
                            'destination': shipment.destination,
                            'departure_date': '2024-02-15',
                            'available_capacity': 5.0
                        },
                        'compatibility_score': 0.95,
                        'estimated_cost': 150.00,
                        'estimated_delivery': '2024-02-20'
                    }
                ]
            
            return Response({
                'success': True,
                'matches': matches,
                'count': len(matches)
            })
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class AcceptMatchView(APIView):
    """Vue pour accepter un match."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, tracking_number, match_id):
        """Accepter un match pour un envoi."""
        try:
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            
            # En production, vérifier que le match existe et est valide
            # Pour la démonstration, on simule l'acceptation
            
            shipment.status = 'matched'
            shipment.save()
            
            return Response({
                'success': True,
                'message': 'Match accepté avec succès',
                'shipment_status': shipment.status
            })
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class ShipmentPaymentView(APIView):
    """Vue pour la gestion des paiements d'envoi."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, tracking_number):
        """Récupérer les informations de paiement d'un envoi."""
        try:
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            
            return Response({
                'success': True,
                'payment_info': {
                    'shipment_id': shipment.id,
                    'tracking_number': shipment.tracking_number,
                    'amount': shipment.shipping_cost,
                    'currency': 'EUR',
                    'status': shipment.payment_status,
                    'payment_method': shipment.payment_method
                }
            })
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class ProcessPaymentView(APIView):
    """Vue pour traiter le paiement d'un envoi."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, tracking_number):
        """Traiter le paiement d'un envoi."""
        try:
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            
            payment_method = request.data.get('payment_method', 'card')
            
            # Simuler le traitement du paiement
            shipment.payment_status = 'paid'
            shipment.is_paid = True
            shipment.payment_method = payment_method
            shipment.payment_date = timezone.now()
            shipment.save()
            
            return Response({
                'success': True,
                'message': 'Paiement traité avec succès',
                'payment_status': shipment.payment_status,
                'transaction_id': f"TXN{random.randint(100000, 999999)}"
            })
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class GenerateDeliveryOTPView(APIView):
    """Vue pour générer un OTP de livraison."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, tracking_number):
        """Générer un OTP pour la livraison."""
        try:
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            
            # Générer un OTP à 6 chiffres
            otp = ''.join(random.choices(string.digits, k=6))
            shipment.delivery_otp = otp
            shipment.save()
            
            return Response({
                'success': True,
                'message': 'OTP de livraison généré',
                'otp': otp  # En production, envoyer par SMS
            })
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class VerifyDeliveryOTPView(APIView):
    """Vue pour vérifier l'OTP de livraison."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, tracking_number):
        """Vérifier l'OTP de livraison."""
        try:
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            
            provided_otp = request.data.get('otp')
            
            if shipment.delivery_otp == provided_otp:
                return Response({
                    'success': True,
                    'message': 'OTP vérifié avec succès'
                })
            else:
                return Response({
                    'success': False,
                    'message': 'OTP incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class ConfirmDeliveryView(APIView):
    """Vue pour confirmer la livraison."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, tracking_number):
        """Confirmer la livraison d'un envoi."""
        try:
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            
            shipment.status = 'delivered'
            shipment.delivery_date = timezone.now()
            shipment.save()
            
            # Ajouter un événement de suivi
            ShipmentTracking.objects.create(
                shipment=shipment,
                event_type='delivered',
                description='Livraison confirmée',
                location=shipment.destination
            )
            
            return Response({
                'success': True,
                'message': 'Livraison confirmée avec succès',
                'delivery_date': shipment.delivery_date
            })
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


# Views pour l'administration
class AdminShipmentListView(APIView):
    """Vue admin pour la liste de tous les envois."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Liste de tous les envois."""
        shipments = Shipment.objects.all().select_related('sender')
        serializer = ShipmentSerializer(shipments, many=True)
        
        return Response({
            'success': True,
            'shipments': serializer.data,
            'count': shipments.count()
        })


class AdminShipmentDetailView(APIView):
    """Vue admin pour les détails d'un envoi."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request, tracking_number):
        """Détails d'un envoi spécifique."""
        try:
            shipment = Shipment.objects.get(tracking_number=tracking_number)
            serializer = ShipmentDetailSerializer(shipment)
            return Response({
                'success': True,
                'shipment': serializer.data
            })
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


# Nouvelles vues pour Package
class PackageDetailView(APIView):
    """Vue pour les détails d'un colis."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, shipment_id):
        """Récupérer les détails d'un colis."""
        try:
            shipment = Shipment.objects.get(
                id=shipment_id,
                sender=request.user
            )
            package = Package.objects.get(shipment=shipment)
            serializer = PackageSerializer(package)
            
            return Response({
                'success': True,
                'package': serializer.data
            })
        except (Shipment.DoesNotExist, Package.DoesNotExist):
            return Response({
                'success': False,
                'message': 'Colis non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request, shipment_id):
        """Créer les détails d'un colis."""
        try:
            shipment = Shipment.objects.get(
                id=shipment_id,
                sender=request.user
            )
            
            # Vérifier si les détails existent déjà
            if Package.objects.filter(shipment=shipment).exists():
                return Response({
                    'success': False,
                    'message': 'Les détails du colis existent déjà'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = PackageCreateSerializer(data=request.data)
            if serializer.is_valid():
                package = serializer.save(shipment=shipment)
                response_serializer = PackageSerializer(package)
                
                return Response({
                    'success': True,
                    'message': 'Détails du colis créés avec succès',
                    'package': response_serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, shipment_id):
        """Mettre à jour les détails d'un colis."""
        try:
            shipment = Shipment.objects.get(
                id=shipment_id,
                sender=request.user
            )
            package = Package.objects.get(shipment=shipment)
            
            serializer = PackageCreateSerializer(package, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                response_serializer = PackageSerializer(package)
                
                return Response({
                    'success': True,
                    'message': 'Détails du colis mis à jour avec succès',
                    'package': response_serializer.data
                })
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except (Shipment.DoesNotExist, Package.DoesNotExist):
            return Response({
                'success': False,
                'message': 'Colis non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


# Nouvelles vues pour ShipmentDocument
class ShipmentDocumentListView(APIView):
    """Vue pour la liste des documents d'un envoi."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, shipment_id):
        """Récupérer la liste des documents d'un envoi."""
        try:
            shipment = Shipment.objects.get(
                id=shipment_id,
                sender=request.user
            )
            documents = ShipmentDocument.objects.filter(shipment=shipment)
            serializer = ShipmentDocumentSerializer(documents, many=True)
            
            return Response({
                'success': True,
                'documents': serializer.data,
                'count': documents.count()
            })
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request, shipment_id):
        """Ajouter un document à un envoi."""
        try:
            shipment = Shipment.objects.get(
                id=shipment_id,
                sender=request.user
            )
            
            serializer = ShipmentDocumentCreateSerializer(data=request.data)
            if serializer.is_valid():
                document = serializer.save(shipment=shipment)
                response_serializer = ShipmentDocumentSerializer(document)
                
                return Response({
                    'success': True,
                    'message': 'Document ajouté avec succès',
                    'document': response_serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class ShipmentDocumentDetailView(APIView):
    """Vue pour les détails d'un document d'envoi."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, shipment_id, document_id):
        """Récupérer les détails d'un document."""
        try:
            shipment = Shipment.objects.get(
                id=shipment_id,
                sender=request.user
            )
            document = ShipmentDocument.objects.get(
                id=document_id,
                shipment=shipment
            )
            serializer = ShipmentDocumentSerializer(document)
            
            return Response({
                'success': True,
                'document': serializer.data
            })
        except (Shipment.DoesNotExist, ShipmentDocument.DoesNotExist):
            return Response({
                'success': False,
                'message': 'Document non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, shipment_id, document_id):
        """Supprimer un document."""
        try:
            shipment = Shipment.objects.get(
                id=shipment_id,
                sender=request.user
            )
            document = ShipmentDocument.objects.get(
                id=document_id,
                shipment=shipment
            )
            document.delete()
            
            return Response({
                'success': True,
                'message': 'Document supprimé avec succès'
            }, status=status.HTTP_204_NO_CONTENT)
        except (Shipment.DoesNotExist, ShipmentDocument.DoesNotExist):
            return Response({
                'success': False,
                'message': 'Document non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


# Nouvelles vues pour ShipmentRating
class ShipmentRatingView(APIView):
    """Vue pour les évaluations d'envois."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, shipment_id):
        """Récupérer l'évaluation d'un envoi."""
        try:
            shipment = Shipment.objects.get(
                id=shipment_id,
                sender=request.user
            )
            
            # Vérifier si l'envoi est livré
            if shipment.status != 'delivered':
                return Response({
                    'success': False,
                    'message': 'Seuls les envois livrés peuvent être évalués'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                rating = ShipmentRating.objects.get(shipment=shipment)
                serializer = ShipmentRatingSerializer(rating)
                
                return Response({
                    'success': True,
                    'rating': serializer.data
                })
            except ShipmentRating.DoesNotExist:
                return Response({
                    'success': True,
                    'rating': None,
                    'message': 'Aucune évaluation trouvée'
                })
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request, shipment_id):
        """Créer une évaluation pour un envoi."""
        try:
            shipment = Shipment.objects.get(
                id=shipment_id,
                sender=request.user
            )
            
            # Vérifier si l'envoi est livré
            if shipment.status != 'delivered':
                return Response({
                    'success': False,
                    'message': 'Seuls les envois livrés peuvent être évalués'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier si l'utilisateur a déjà évalué cet envoi
            if ShipmentRating.objects.filter(shipment=shipment, rater=request.user).exists():
                return Response({
                    'success': False,
                    'message': 'Vous avez déjà évalué cet envoi'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = ShipmentRatingCreateSerializer(
                data=request.data,
                context={'request': request, 'shipment_id': shipment_id}
            )
            if serializer.is_valid():
                rating = serializer.save(shipment=shipment, rater=request.user)
                response_serializer = ShipmentRatingSerializer(rating)
                
                return Response({
                    'success': True,
                    'message': 'Évaluation créée avec succès',
                    'rating': response_serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class ShipmentWithAllDetailsView(APIView):
    """Vue pour récupérer un envoi avec tous ses détails."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, shipment_id):
        """Récupérer un envoi avec tous ses détails."""
        try:
            shipment = Shipment.objects.get(
                id=shipment_id,
                sender=request.user
            )
            serializer = ShipmentWithDetailsSerializer(shipment)
            
            return Response({
                'success': True,
                'shipment': serializer.data
            })
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


# Vues d'administration pour les nouveaux modèles
class AdminPackageListView(APIView):
    """Vue admin pour la liste de tous les colis."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Liste de tous les colis."""
        packages = Package.objects.all().select_related('shipment')
        serializer = PackageSerializer(packages, many=True)
        
        return Response({
            'success': True,
            'packages': serializer.data,
            'count': packages.count()
        })


class AdminDocumentListView(APIView):
    """Vue admin pour la liste de tous les documents."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Liste de tous les documents."""
        documents = ShipmentDocument.objects.all().select_related('shipment')
        serializer = ShipmentDocumentSerializer(documents, many=True)
        
        return Response({
            'success': True,
            'documents': serializer.data,
            'count': documents.count()
        })


class AdminRatingListView(APIView):
    """Vue admin pour la liste de toutes les évaluations."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Liste de toutes les évaluations."""
        ratings = ShipmentRating.objects.all().select_related('shipment', 'rater')
        serializer = ShipmentRatingSerializer(ratings, many=True)
        
        return Response({
            'success': True,
            'ratings': serializer.data,
            'count': ratings.count()
        })
