"""
Views for shipments app - Package shipping management with JSON responses
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.apps import apps
import uuid
import random
import string
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from .models import Shipment, ShipmentTracking, Package, ShipmentDocument, ShipmentRating
from matching.models import Match
from users.permissions import IsAdminUser
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

logger = logging.getLogger(__name__)


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
            
            # Récupérer les vrais matches depuis la base de données
            matches = []
            
            if shipment.status == 'pending':
                # Récupérer les matches en attente
                pending_matches = Match.objects.filter(
                    shipment=shipment,
                    status='pending'
                ).select_related('trip', 'trip__traveler').order_by('-compatibility_score')
                
                for match in pending_matches:
                    matches.append({
                        'id': match.id,
                        'traveler': {
                            'id': match.trip.traveler.id,
                            'name': f"{match.trip.traveler.first_name} {match.trip.traveler.last_name}",
                            'rating': getattr(match.trip.traveler, 'rating', 0),
                            'total_trips': apps.get_model('trips', 'Trip').objects.filter(traveler=match.trip.traveler, status='completed').count()
                        },
                        'trip': {
                            'id': match.trip.id,
                            'origin': match.trip.origin_city,
                            'destination': match.trip.destination_city,
                            'departure_date': match.trip.departure_date.strftime('%Y-%m-%d'),
                            'available_capacity': match.trip.remaining_weight
                        },
                        'compatibility_score': float(match.compatibility_score),
                        'estimated_cost': float(match.proposed_price),
                        'estimated_delivery': match.trip.arrival_date.strftime('%Y-%m-%d'),
                        'status': 'available',
                        'expires_at': match.expires_at.isoformat() if match.expires_at else None
                    })
                    
            elif shipment.status == 'matched' and shipment.matched_trip:
                # Récupérer le match accepté
                accepted_match = Match.objects.filter(
                    shipment=shipment,
                    trip=shipment.matched_trip,
                    status='accepted'
                ).select_related('trip', 'trip__traveler').first()
                
                if accepted_match:
                    matches.append({
                        'id': accepted_match.id,
                        'traveler': {
                            'id': accepted_match.trip.traveler.id,
                            'name': f"{accepted_match.trip.traveler.first_name} {accepted_match.trip.traveler.last_name}",
                            'rating': getattr(accepted_match.trip.traveler, 'rating', 0),
                            'total_trips': apps.get_model('trips', 'Trip').objects.filter(traveler=accepted_match.trip.traveler, status='completed').count()
                        },
                        'trip': {
                            'id': accepted_match.trip.id,
                            'origin': accepted_match.trip.origin_city,
                            'destination': accepted_match.trip.destination_city,
                            'departure_date': accepted_match.trip.departure_date.strftime('%Y-%m-%d'),
                            'available_capacity': accepted_match.trip.remaining_weight
                        },
                        'compatibility_score': float(accepted_match.compatibility_score),
                        'estimated_cost': float(accepted_match.proposed_price),
                        'estimated_delivery': accepted_match.trip.arrival_date.strftime('%Y-%m-%d'),
                        'status': 'accepted',
                        'accepted_at': accepted_match.responded_at.isoformat() if accepted_match.responded_at else None
                    })
                    
            elif shipment.status == 'in_transit' and shipment.matched_trip:
                # Récupérer le match actif pendant le transport
                active_match = Match.objects.filter(
                    shipment=shipment,
                    trip=shipment.matched_trip,
                    status='accepted'
                ).select_related('trip', 'trip__traveler').first()
                
                if active_match:
                    matches.append({
                        'id': active_match.id,
                        'traveler': {
                            'id': active_match.trip.traveler.id,
                            'name': f"{active_match.trip.traveler.first_name} {active_match.trip.traveler.last_name}",
                            'rating': getattr(active_match.trip.traveler, 'rating', 0),
                            'total_trips': apps.get_model('trips', 'Trip').objects.filter(traveler=active_match.trip.traveler, status='completed').count()
                        },
                        'trip': {
                            'id': active_match.trip.id,
                            'origin': active_match.trip.origin_city,
                            'destination': active_match.trip.destination_city,
                            'departure_date': active_match.trip.departure_date.strftime('%Y-%m-%d'),
                            'available_capacity': active_match.trip.remaining_weight
                        },
                        'compatibility_score': float(active_match.compatibility_score),
                        'estimated_cost': float(active_match.proposed_price),
                        'estimated_delivery': active_match.trip.arrival_date.strftime('%Y-%m-%d'),
                        'status': 'active',
                        'accepted_at': active_match.responded_at.isoformat() if active_match.responded_at else None
                    })
            
            return Response({
                'success': True,
                'matches': matches,
                'count': len(matches),
                'shipment_status': shipment.status
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
            
            # Vérifier que le shipment est en attente
            if shipment.status != 'pending':
                return Response({
                    'success': False,
                    'message': f'Impossible d\'accepter un match pour un envoi avec le statut: {shipment.status}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer le match depuis la base de données
            try:
                match = Match.objects.get(
                    id=match_id,
                    shipment=shipment,
                    status='pending'
                )
            except Match.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Match non trouvé ou déjà traité'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Vérifier que le match peut être accepté
            if not match.can_be_accepted:
                return Response({
                    'success': False,
                    'message': 'Ce match ne peut pas être accepté'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Accepter le match en utilisant la méthode du modèle
            try:
                match.accept()
                
                # Récupérer les informations mises à jour
                shipment.refresh_from_db()
                
                return Response({
                    'success': True,
                    'message': 'Match accepté avec succès',
                    'shipment_status': shipment.status,
                    'match_details': {
                        'match_id': match.id,
                        'accepted_at': match.responded_at.isoformat() if match.responded_at else None,
                        'traveler': {
                            'id': match.trip.traveler.id,
                            'name': f"{match.trip.traveler.first_name} {match.trip.traveler.last_name}",
                            'rating': getattr(match.trip.traveler, 'rating', 0)
                        },
                        'trip': {
                            'id': match.trip.id,
                            'origin': match.trip.origin_city,
                            'destination': match.trip.destination_city,
                            'departure_date': match.trip.departure_date.strftime('%Y-%m-%d'),
                            'arrival_date': match.trip.arrival_date.strftime('%Y-%m-%d')
                        },
                        'compatibility_score': float(match.compatibility_score),
                        'proposed_price': float(match.proposed_price)
                    }
                })
                
            except ValueError as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
                
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
    
    @swagger_auto_schema(
        operation_description="Génère un OTP de livraison et l'envoie au destinataire",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={},
            required=[]
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="OTP de livraison généré avec succès",
                examples={"application/json": {
                    "success": True,
                    "message": "OTP de livraison généré et envoyé au destinataire",
                    "otp_info": {
                        "recipient_name": "Ahmed Benali",
                        "recipient_phone": "+213XXXXXXXXX",
                        "expires_at": "2024-01-15T14:30:00Z",
                        "time_remaining_minutes": 1440
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur lors de la génération",
                examples={"application/json": {
                    "success": False,
                    "message": "L'envoi doit être en transit pour générer un OTP de livraison"
                }}
            )
        }
    )
    def post(self, request, tracking_number):
        """Génère un OTP de livraison et l'envoie au destinataire."""
        try:
            # Récupérer l'envoi
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            
            # Vérifier que l'utilisateur est le voyageur associé
            if shipment.matched_trip and shipment.matched_trip.traveler != request.user:
                return Response({
                    'success': False,
                    'message': 'Vous n\'êtes pas autorisé à générer l\'OTP pour cet envoi'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Générer l'OTP de livraison
            from .services import DeliveryOTPService
            success, otp_code, message = DeliveryOTPService.generate_delivery_otp(shipment, request)
            
            if success:
                # Récupérer les informations de l'OTP
                otp_status = DeliveryOTPService.get_delivery_otp_status(shipment)
                
                return Response({
                    'success': True,
                    'message': message,
                    'otp_info': {
                        'recipient_name': otp_status.get('recipient_name'),
                        'recipient_phone': otp_status.get('recipient_phone'),
                        'expires_at': otp_status.get('otp_expires_at'),
                        'time_remaining_minutes': otp_status.get('time_remaining_minutes', 0)
                    }
                })
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error generating delivery OTP: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la génération de l\'OTP'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyDeliveryOTPView(APIView):
    """Vue pour vérifier l'OTP de livraison fourni par le destinataire."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Vérifie l'OTP de livraison et confirme la livraison",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'otp': openapi.Schema(type=openapi.TYPE_STRING, description="Code OTP à 6 chiffres fourni par le destinataire")
            },
            required=['otp']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Livraison confirmée avec succès",
                examples={"application/json": {
                    "success": True,
                    "message": "Livraison confirmée avec succès. Paiement de 3000 DA libéré au voyageur",
                    "delivery_info": {
                        "delivery_date": "2024-01-15T14:30:00Z",
                        "recipient_name": "Ahmed Benali",
                        "payment_released": True,
                        "amount_released": 3000.00
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="OTP invalide ou erreur",
                examples={"application/json": {
                    "success": False,
                    "message": "Code OTP invalide ou expiré"
                }}
            )
        }
    )
    def post(self, request, tracking_number):
        """Vérifie l'OTP de livraison et confirme la livraison."""
        try:
            # Récupérer l'envoi
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            
            # Vérifier que l'utilisateur est le voyageur associé
            if shipment.matched_trip and shipment.matched_trip.traveler != request.user:
                return Response({
                    'success': False,
                    'message': 'Vous n\'êtes pas autorisé à vérifier l\'OTP pour cet envoi'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Récupérer le code OTP
            otp_code = request.data.get('otp')
            if not otp_code:
                return Response({
                    'success': False,
                    'message': 'Code OTP requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier l'OTP et compléter la livraison
            from .services import ShipmentDeliveryService
            success, message = ShipmentDeliveryService.complete_delivery(
                shipment, otp_code, request.user
            )
            
            if success:
                # Récupérer les informations de livraison
                delivery_info = {
                    'delivery_date': shipment.delivery_date,
                    'recipient_name': shipment.recipient_name,
                    'payment_released': True,
                    'amount_released': shipment.price if shipment.price else 0
                }
                
                return Response({
                    'success': True,
                    'message': message,
                    'delivery_info': delivery_info
                })
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error verifying delivery OTP: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la vérification de l\'OTP'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResendDeliveryOTPView(APIView):
    """Vue pour renvoyer l'OTP de livraison au destinataire."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Renvoie l'OTP de livraison au destinataire",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={},
            required=[]
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="OTP renvoyé avec succès",
                examples={"application/json": {
                    "success": True,
                    "message": "OTP de livraison renvoyé avec succès"
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur lors du renvoi",
                examples={"application/json": {
                    "success": False,
                    "message": "Aucun OTP de livraison valide trouvé"
                }}
            )
        }
    )
    def post(self, request, tracking_number):
        """Renvoie l'OTP de livraison au destinataire."""
        try:
            # Récupérer l'envoi
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            
            # Vérifier que l'utilisateur est le voyageur associé
            if shipment.matched_trip and shipment.matched_trip.traveler != request.user:
                return Response({
                    'success': False,
                    'message': 'Vous n\'êtes pas autorisé à renvoyer l\'OTP pour cet envoi'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Renvoyer l'OTP
            from .services import DeliveryOTPService
            success, message = DeliveryOTPService.resend_delivery_otp(shipment, request)
            
            return Response({
                'success': success,
                'message': message
            }, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)
                
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error resending delivery OTP: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors du renvoi de l\'OTP'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeliveryOTPStatusView(APIView):
    """Vue pour récupérer le statut de l'OTP de livraison."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupère le statut de l'OTP de livraison",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Statut de l'OTP de livraison",
                examples={"application/json": {
                    "success": True,
                    "otp_status": {
                        "has_active_otp": True,
                        "has_used_otp": False,
                        "otp_generated_at": "2024-01-15T10:30:00Z",
                        "otp_expires_at": "2024-01-16T10:30:00Z",
                        "time_remaining_minutes": 1200,
                        "recipient_name": "Ahmed Benali",
                        "recipient_phone": "+213XXXXXXXXX"
                    }
                }}
            )
        }
    )
    def get(self, request, tracking_number):
        """Récupère le statut de l'OTP de livraison."""
        try:
            # Récupérer l'envoi
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            
            # Récupérer le statut de l'OTP
            from .services import DeliveryOTPService
            otp_status = DeliveryOTPService.get_delivery_otp_status(shipment)
            
            return Response({
                'success': True,
                'otp_status': otp_status
            })
                
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting delivery OTP status: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la récupération du statut'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InitiateDeliveryProcessView(APIView):
    """Vue pour initier le processus de livraison quand le voyageur prend le colis."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Initie le processus de livraison et génère automatiquement l'OTP",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={},
            required=[]
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Processus de livraison initié",
                examples={"application/json": {
                    "success": True,
                    "message": "Processus de livraison initié. OTP de livraison généré et envoyé au destinataire."
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur lors de l'initiation",
                examples={"application/json": {
                    "success": False,
                    "message": "L'envoi ne peut pas être mis en transit"
                }}
            )
        }
    )
    def post(self, request, tracking_number):
        """Initie le processus de livraison."""
        try:
            # Récupérer l'envoi
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            
            # Vérifier que l'utilisateur est le voyageur associé
            if shipment.matched_trip and shipment.matched_trip.traveler != request.user:
                return Response({
                    'success': False,
                    'message': 'Vous n\'êtes pas autorisé à initier la livraison pour cet envoi'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Initier le processus de livraison
            from .services import ShipmentDeliveryService
            success, message = ShipmentDeliveryService.initiate_delivery_process(shipment, request.user)
            
            return Response({
                'success': success,
                'message': message
            }, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)
                
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error initiating delivery process: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de l\'initiation du processus'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConfirmDeliveryView(APIView):
    """Vue pour confirmer la livraison avec des notes et signature."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Confirme la livraison avec des notes et signature du destinataire",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'delivery_notes': openapi.Schema(type=openapi.TYPE_STRING, description="Notes sur la livraison"),
                'recipient_signature': openapi.Schema(type=openapi.TYPE_STRING, description="Signature du destinataire")
            },
            required=['delivery_notes', 'recipient_signature']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Livraison confirmée avec succès",
                examples={"application/json": {
                    "success": True,
                    "message": "Livraison confirmée avec succès",
                    "delivery_confirmation": {
                        "delivery_date": "2024-01-15T14:30:00Z",
                        "recipient_name": "Ahmed Benali",
                        "delivery_notes": "Livré en bon état",
                        "recipient_signature": "Ahmed Benali",
                        "payment_released": True,
                        "amount_released": 3000.00
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur lors de la confirmation",
                examples={"application/json": {
                    "success": False,
                    "message": "L'envoi doit être en transit pour confirmer la livraison"
                }}
            )
        }
    )
    def post(self, request, tracking_number):
        """Confirme la livraison avec des notes et signature."""
        try:
            # Récupérer l'envoi
            shipment = Shipment.objects.get(
                tracking_number=tracking_number,
                sender=request.user
            )
            
            # Vérifier que l'utilisateur est le voyageur associé
            if shipment.matched_trip and shipment.matched_trip.traveler != request.user:
                return Response({
                    'success': False,
                    'message': 'Vous n\'êtes pas autorisé à confirmer la livraison pour cet envoi'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Vérifier que l'envoi est en transit
            if shipment.status != 'in_transit':
                return Response({
                    'success': False,
                    'message': 'L\'envoi doit être en transit pour confirmer la livraison'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer les données de confirmation
            delivery_notes = request.data.get('delivery_notes')
            recipient_signature = request.data.get('recipient_signature')
            
            if not delivery_notes or not recipient_signature:
                return Response({
                    'success': False,
                    'message': 'Notes de livraison et signature du destinataire sont requises'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Confirmer la livraison
            from .services import ShipmentDeliveryService
            success, message = ShipmentDeliveryService.confirm_delivery(
                shipment, delivery_notes, recipient_signature, request.user
            )
            
            if success:
                # Récupérer les informations de confirmation
                delivery_confirmation = {
                    'delivery_date': shipment.delivery_date,
                    'recipient_name': shipment.recipient_name,
                    'delivery_notes': delivery_notes,
                    'recipient_signature': recipient_signature,
                    'payment_released': True,
                    'amount_released': shipment.price if shipment.price else 0
                }
                
                return Response({
                    'success': True,
                    'message': message,
                    'delivery_confirmation': delivery_confirmation
                })
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error confirming delivery: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la confirmation de la livraison'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Views pour l'administration
class AdminShipmentListView(APIView):
    """Vue admin pour la liste de tous les envois."""
    
    permission_classes = [IsAdminUser]
    
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
    
    permission_classes = [IsAdminUser]
    
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
            
            # Gérer les fichiers multipart/form-data
            data = request.data.copy()
            
            # Si c'est un fichier multipart, traiter correctement
            if request.content_type and 'multipart/form-data' in request.content_type:
                # Les données sont déjà dans request.data
                pass
            else:
                # Pour les requêtes JSON, vérifier si un fichier est fourni
                if 'file' not in request.FILES:
                    return Response({
                        'success': False,
                        'message': 'Un fichier est requis pour l\'upload'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = ShipmentDocumentCreateSerializer(data=data, files=request.FILES)
            if serializer.is_valid():
                document = serializer.save(shipment=shipment)
                
                # Mettre à jour les métadonnées du fichier
                if document.file:
                    document.file_size = document.file.size
                    document.mime_type = document.file.content_type
                    document.save()
                
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
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de l\'upload du document'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    
    permission_classes = [IsAdminUser]
    
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
    
    permission_classes = [IsAdminUser]
    
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
    
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Liste de toutes les évaluations."""
        ratings = ShipmentRating.objects.all().select_related('shipment', 'rater')
        serializer = ShipmentRatingSerializer(ratings, many=True)
        
        return Response({
            'success': True,
            'ratings': serializer.data,
            'count': ratings.count()
        })
