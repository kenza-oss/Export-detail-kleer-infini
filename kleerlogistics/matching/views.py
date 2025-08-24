"""
Views for matching app - Intelligent matching algorithm
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
import math
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Match, MatchingPreferences, MatchingRule
from .serializers import (
    MatchSerializer, MatchingPreferencesSerializer,
    MatchResultSerializer, MatchingAlgorithmSerializer
)
from .services import (
    AutomaticMatchingService, 
    MatchingNotificationService, 
    OTPDeliveryService
)
from shipments.models import Shipment
from trips.models import Trip
from users.models import User
from config.swagger_config import (
    matching_accept_schema, matching_reject_schema
)
from config.swagger_examples import (
    MATCHING_CREATE_EXAMPLE, MATCHING_ACCEPT_EXAMPLE, 
    MATCHING_REJECT_EXAMPLE, MATCHING_LIST_EXAMPLE
)


class MatchingEngineView(APIView):
    """Vue pour l'algorithme de matching intelligent."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Trouver les meilleurs matches pour un envoi ou trajet",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['shipment', 'trip'],
                    description="Type de matching"
                ),
                'item_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID de l'envoi ou du trajet"
                )
            },
            required=['type', 'item_id']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Matches trouvés",
                examples={"application/json": {
                    "success": True,
                    "matches": [
                        {
                            "id": 1,
                            "shipment": {
                                "id": 1,
                                "title": "Livraison de documents urgents",
                                "origin": "Paris",
                                "destination": "Lyon",
                                "weight": 2.5
                            },
                            "trip": {
                                "id": 2,
                                "title": "Voyage Paris-Lyon",
                                "departure_date": "2024-01-25T08:00:00Z",
                                "available_space": 100
                            },
                            "compatibility_score": 85.5,
                            "estimated_cost": 150.00,
                            "status": "pending"
                        }
                    ],
                    "count": 1,
                    "shipment_id": 1
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "message": "Type et ID requis"
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Envoi/Trajet non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Envoi non trouvé"
                }}
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
                description="Erreur serveur",
                examples={"application/json": {
                    "success": False,
                    "message": "Erreur lors du matching"
                }}
            )
        }
    )
    def post(self, request):
        """Trouver les meilleurs matches pour un envoi ou trajet."""
        match_type = request.data.get('type')  # 'shipment' ou 'trip'
        item_id = request.data.get('item_id')
        
        if not match_type or not item_id:
            return Response({
                'success': False,
                'message': 'Type et ID requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if match_type == 'shipment':
                return self.find_shipment_matches(request, item_id)
            elif match_type == 'trip':
                return self.find_trip_matches(request, item_id)
            else:
                return Response({
                    'success': False,
                    'message': 'Type invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur lors du matching: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def find_shipment_matches(self, request, shipment_id):
        """Trouver des trajets pour un envoi."""
        try:
            # Vérifier que l'envoi existe
            shipment = Shipment.objects.get(id=shipment_id)
            
            # Vérifier que l'utilisateur est le propriétaire de l'envoi
            if shipment.sender != request.user:
                return Response({
                    'success': False,
                    'message': 'Vous n\'êtes pas autorisé à accéder à cet envoi'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Vérifier que l'envoi peut être matché
            if shipment.status == 'matched':
                return Response({
                    'success': False,
                    'message': 'Cet envoi a déjà été associé à un trajet',
                    'shipment_status': shipment.status,
                    'matched_trip_id': getattr(shipment.matched_trip, 'id', None) if hasattr(shipment, 'matched_trip') else None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if shipment.status not in ['pending', 'active']:
                return Response({
                    'success': False,
                    'message': f'Cet envoi ne peut pas être matché (statut: {shipment.status})',
                    'shipment_status': shipment.status
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Algorithme de matching
            matching_result = self.calculate_shipment_matches(shipment)
            matches = matching_result['matches']
            search_info = matching_result['search_info']
            
            return Response({
                'success': True,
                'matches': matches,
                'count': len(matches),
                'shipment_id': shipment_id,
                'shipment_info': {
                    'tracking_number': shipment.tracking_number,
                    'origin_city': shipment.origin_city,
                    'destination_city': shipment.destination_city,
                    'weight': float(shipment.weight),
                    'package_type': shipment.package_type,
                    'status': shipment.status,
                    'preferred_pickup_date': shipment.preferred_pickup_date,
                    'max_delivery_date': shipment.max_delivery_date
                },
                'search_info': search_info
            })
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': f'Envoi avec l\'ID {shipment_id} non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def find_trip_matches(self, request, trip_id):
        """Trouver des envois pour un trajet."""
        try:
            # Vérifier que le trajet existe
            trip = Trip.objects.get(id=trip_id)
            
            # Vérifier que l'utilisateur est le propriétaire du trajet
            if trip.traveler != request.user:
                return Response({
                    'success': False,
                    'message': 'Vous n\'êtes pas autorisé à accéder à ce trajet'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Vérifier que le trajet peut accepter des envois
            if trip.status not in ['active', 'draft']:
                return Response({
                    'success': False,
                    'message': f'Ce trajet ne peut pas accepter d\'envois (statut: {trip.status})',
                    'trip_status': trip.status
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if trip.remaining_weight <= 0 or trip.remaining_packages <= 0:
                return Response({
                    'success': False,
                    'message': 'Ce trajet n\'a plus de capacité disponible',
                    'remaining_weight': float(trip.remaining_weight),
                    'remaining_packages': trip.remaining_packages
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Algorithme de matching
            matching_result = self.calculate_trip_matches(trip)
            matches = matching_result['matches']
            search_info = matching_result['search_info']
            
            return Response({
                'success': True,
                'matches': matches,
                'count': len(matches),
                'trip_id': trip_id,
                'trip_info': {
                    'origin_city': trip.origin_city,
                    'destination_city': trip.destination_city,
                    'remaining_weight': float(trip.remaining_weight),
                    'remaining_packages': trip.remaining_packages,
                    'status': trip.status
                },
                'search_info': search_info
            })
        except Trip.DoesNotExist:
            return Response({
                'success': False,
                'message': f'Trajet avec l\'ID {trip_id} non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def calculate_shipment_matches(self, shipment):
        """Calculer les matches pour un envoi."""
        # Critères de matching de base
        compatible_trips = Trip.objects.filter(
            status='active',
            remaining_weight__gte=shipment.weight,
            remaining_packages__gt=0,
            departure_date__gte=timezone.now().date()
        ).exclude(traveler=shipment.sender)
        
        # Filtres géographiques plus flexibles
        origin_matches = Q(origin_city__icontains=shipment.origin_city)
        destination_matches = Q(destination_city__icontains=shipment.destination_city)
        
        # Ajouter des correspondances partielles pour plus de flexibilité
        if len(shipment.origin_city) > 3:
            origin_matches |= Q(origin_city__icontains=shipment.origin_city[:3])
        if len(shipment.destination_city) > 3:
            destination_matches |= Q(destination_city__icontains=shipment.destination_city[:3])
        
        compatible_trips = compatible_trips.filter(origin_matches & destination_matches)
        
        # Vérifier la compatibilité des types de colis
        if hasattr(shipment, 'package_type') and shipment.package_type:
            compatible_trips = compatible_trips.filter(
                accepted_package_types__contains=[shipment.package_type]
            )
        
        # Vérifier la fragilité
        if hasattr(shipment, 'is_fragile') and shipment.is_fragile:
            compatible_trips = compatible_trips.filter(accepts_fragile=True)
        
        matches = []
        for trip in compatible_trips[:15]:  # Augmenter à 15 résultats
            score = self.calculate_compatibility_score(shipment, trip)
            
            if score > 0.3:  # Réduire le seuil minimum pour plus de résultats
                # Calculer le coût estimé
                price_per_kg = getattr(trip, 'min_price_per_kg', 0)
                estimated_cost = float(shipment.weight * price_per_kg) if price_per_kg else 0
                
                matches.append({
                    'id': len(matches) + 1,
                    'trip': {
                        'id': trip.id,
                        'traveler': {
                            'id': trip.traveler.id,
                            'name': f"{trip.traveler.first_name} {trip.traveler.last_name}",
                            'rating': getattr(trip.traveler, 'rating', 0),
                            'total_trips': getattr(trip.traveler, 'total_trips', 0)
                        },
                        'origin_city': trip.origin_city,
                        'destination_city': trip.destination_city,
                        'departure_date': trip.departure_date,
                        'arrival_date': trip.arrival_date,
                        'remaining_weight': float(trip.remaining_weight),
                        'remaining_packages': trip.remaining_packages,
                        'min_price_per_kg': float(price_per_kg) if price_per_kg else 0,
                        'accepts_fragile': getattr(trip, 'accepts_fragile', False),
                        'accepted_package_types': getattr(trip, 'accepted_package_types', [])
                    },
                    'compatibility_score': round(score * 100, 1),  # Convertir en pourcentage
                    'estimated_cost': round(estimated_cost, 2),
                    'estimated_delivery': trip.arrival_date,
                    'pickup_deadline': shipment.preferred_pickup_date,
                    'delivery_deadline': shipment.max_delivery_date
                })
        
        # Trier par score de compatibilité
        matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        # Ajouter des informations sur la recherche
        search_info = {
            'total_trips_found': compatible_trips.count(),
            'trips_meeting_criteria': len(matches),
            'search_criteria': {
                'origin_city': shipment.origin_city,
                'destination_city': shipment.destination_city,
                'min_weight': float(shipment.weight),
                'package_type': getattr(shipment, 'package_type', 'N/A'),
                'is_fragile': getattr(shipment, 'is_fragile', False)
            }
        }
        
        return {
            'matches': matches,
            'search_info': search_info
        }
    
    def calculate_trip_matches(self, trip):
        """Calculer les matches pour un trajet."""
        # Critères de matching de base
        compatible_shipments = Shipment.objects.filter(
            status='pending',
            weight__lte=trip.remaining_weight
        ).exclude(sender=trip.traveler)
        
        # Filtres géographiques plus flexibles
        origin_matches = Q(origin_city__icontains=trip.origin_city)
        destination_matches = Q(destination_city__icontains=trip.destination_city)
        
        # Ajouter des correspondances partielles pour plus de flexibilité
        if len(trip.origin_city) > 3:
            origin_matches |= Q(origin_city__icontains=trip.origin_city[:3])
        if len(trip.destination_city) > 3:
            destination_matches |= Q(destination_city__icontains=trip.destination_city[:3])
        
        compatible_shipments = compatible_shipments.filter(origin_matches & destination_matches)
        
        # Vérifier la compatibilité des types de colis
        if hasattr(trip, 'accepted_package_types') and trip.accepted_package_types:
            compatible_shipments = compatible_shipments.filter(
                package_type__in=trip.accepted_package_types
            )
        
        # Vérifier la fragilité
        if hasattr(trip, 'accepts_fragile') and not trip.accepts_fragile:
            compatible_shipments = compatible_shipments.filter(is_fragile=False)
        
        matches = []
        for shipment in compatible_shipments[:15]:  # Augmenter à 15 résultats
            score = self.calculate_compatibility_score(shipment, trip)
            
            if score > 0.3:  # Réduire le seuil minimum pour plus de résultats
                # Calculer les gains estimés
                min_price_per_kg = getattr(trip, 'min_price_per_kg', 0)
                estimated_earnings = float(shipment.weight) * float(min_price_per_kg) if min_price_per_kg else 0
                
                matches.append({
                    'id': len(matches) + 1,
                    'shipment': {
                        'id': shipment.id,
                        'tracking_number': shipment.tracking_number,
                        'sender': {
                            'id': shipment.sender.id,
                            'name': f"{shipment.sender.first_name} {shipment.sender.last_name}",
                            'rating': getattr(shipment.sender, 'rating', 0),
                            'email': shipment.sender.email
                        },
                        'origin_city': shipment.origin_city,
                        'destination_city': shipment.destination_city,
                        'weight': float(shipment.weight),
                        'package_type': shipment.package_type,
                        'description': shipment.description,
                        'is_fragile': getattr(shipment, 'is_fragile', False),
                        'urgency': getattr(shipment, 'urgency', 'normal'),
                        'preferred_pickup_date': shipment.preferred_pickup_date,
                        'max_delivery_date': shipment.max_delivery_date
                    },
                    'compatibility_score': round(score * 100, 1),  # Convertir en pourcentage
                    'estimated_earnings': round(estimated_earnings, 2),
                    'pickup_date': trip.departure_date,
                    'delivery_date': trip.arrival_date,
                    'weight_ratio': round(float(shipment.weight) / float(trip.remaining_weight), 2)
                })
        
        # Trier par score de compatibilité
        matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        # Ajouter des informations sur la recherche
        search_info = {
            'total_shipments_found': compatible_shipments.count(),
            'shipments_meeting_criteria': len(matches),
            'search_criteria': {
                'origin_city': trip.origin_city,
                'destination_city': trip.destination_city,
                'max_weight': float(trip.remaining_weight),
                'accepted_package_types': getattr(trip, 'accepted_package_types', []),
                'accepts_fragile': getattr(trip, 'accepts_fragile', False)
            }
        }
        
        return {
            'matches': matches,
            'search_info': search_info
        }
    
    def calculate_compatibility_score(self, shipment, trip):
        """Calculer le score de compatibilité entre un envoi et un trajet."""
        score = 0.0
        
        # 1. Compatibilité géographique (40%)
        if shipment.origin_city.lower() in trip.origin_city.lower() or trip.origin_city.lower() in shipment.origin_city.lower():
            score += 0.4
        elif shipment.origin_city.lower()[:3] == trip.origin_city.lower()[:3]:
            score += 0.3
        
        if shipment.destination_city.lower() in trip.destination_city.lower() or trip.destination_city.lower() in shipment.destination_city.lower():
            score += 0.4
        elif shipment.destination_city.lower()[:3] == trip.destination_city.lower()[:3]:
            score += 0.3
        
        # 2. Compatibilité de capacité (30%)
        capacity_ratio = float(shipment.weight / trip.remaining_weight)
        if capacity_ratio <= 1.0:
            score += 0.3 * (1 - capacity_ratio)
        
        # 3. Compatibilité temporelle (20%)
        if trip.departure_date >= timezone.now():
            days_diff = (trip.departure_date.date() - timezone.now().date()).days
            if days_diff <= 7:
                score += 0.2
            elif days_diff <= 14:
                score += 0.1
        
        # 4. Historique utilisateur (10%)
        user_rating = getattr(trip.traveler, 'rating', 0)
        score += (float(user_rating) / 5.0) * 0.1
        
        return min(score, 1.0)  # Normaliser entre 0 et 1


class MatchListView(APIView):
    """Vue pour la liste des matches."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Lister les matches de l'utilisateur",
        manual_parameters=[
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Statut du match",
                type=openapi.TYPE_STRING,
                enum=['pending', 'accepted', 'rejected']
            ),
            openapi.Parameter(
                'match_type',
                openapi.IN_QUERY,
                description="Type de match",
                type=openapi.TYPE_STRING,
                enum=['shipment', 'trip']
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des matches",
                examples={"application/json": MATCHING_LIST_EXAMPLE}
            )
        }
    )
    def get(self, request):
        """Récupérer les matches de l'utilisateur."""
        user_matches = Match.objects.filter(
            Q(shipment__sender=request.user) | Q(trip__traveler=request.user)
        ).order_by('-created_at')
        
        serializer = MatchSerializer(user_matches, many=True)
        
        return Response({
            'success': True,
            'matches': serializer.data,
            'count': user_matches.count()
        })


class AcceptMatchView(APIView):
    """Vue pour accepter un match."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Accepter un match",
        manual_parameters=[
            openapi.Parameter(
                'match_id',
                openapi.IN_PATH,
                description="ID du match",
                type=openapi.TYPE_INTEGER
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'accepted_price': openapi.Schema(type=openapi.TYPE_NUMBER),
                'message': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Match accepté",
                examples={"application/json": MATCHING_ACCEPT_EXAMPLE}
            ),
            status.HTTP_403_FORBIDDEN: openapi.Response(
                description="Non autorisé",
                examples={"application/json": {
                    "success": False,
                    "message": "Non autorisé"
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Match non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Match non trouvé"
                }}
            )
        }
    )
    def post(self, request, match_id):
        """Accepter un match."""
        try:
            match = Match.objects.get(id=match_id)
            
            # Vérifier que l'utilisateur peut accepter ce match
            # L'utilisateur doit être soit l'expéditeur soit le voyageur
            is_authorized = False
            if match.shipment and match.shipment.sender == request.user:
                is_authorized = True
            if match.trip and match.trip.traveler == request.user:
                is_authorized = True
                
            if not is_authorized:
                return Response({
                    'success': False,
                    'message': 'Non autorisé'
                }, status=status.HTTP_403_FORBIDDEN)
            
            with transaction.atomic():
                # Use the model's accept method which handles all the logic including chat activation
                match.accept()
                
                # Mettre à jour les statuts
                if match.shipment:
                    match.shipment.status = 'matched'
                    match.shipment.save()
                
                if match.trip:
                    # Réduire la capacité disponible
                    if match.shipment:
                        match.trip.remaining_weight -= match.shipment.weight
                        match.trip.remaining_packages -= 1
                        match.trip.save()
            
            return Response({
                'success': True,
                'message': 'Match accepté avec succès',
                'match_id': match.id
            })
        except Match.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Match non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class RejectMatchView(APIView):
    """Vue pour rejeter un match."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Rejeter un match",
        manual_parameters=[
            openapi.Parameter(
                'match_id',
                openapi.IN_PATH,
                description="ID du match",
                type=openapi.TYPE_INTEGER
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'reason': openapi.Schema(type=openapi.TYPE_STRING),
                'message': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Match rejeté",
                examples={"application/json": MATCHING_REJECT_EXAMPLE}
            ),
            status.HTTP_403_FORBIDDEN: openapi.Response(
                description="Non autorisé",
                examples={"application/json": {
                    "success": False,
                    "message": "Non autorisé"
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Match non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Match non trouvé"
                }}
            )
        }
    )
    def post(self, request, match_id):
        """Rejeter un match."""
        try:
            match = Match.objects.get(id=match_id)
            
            # Vérifier les permissions
            # L'utilisateur doit être soit l'expéditeur soit le voyageur
            is_authorized = False
            if match.shipment and match.shipment.sender == request.user:
                is_authorized = True
            if match.trip and match.trip.traveler == request.user:
                is_authorized = True
                
            if not is_authorized:
                return Response({
                    'success': False,
                    'message': 'Non autorisé'
                }, status=status.HTTP_403_FORBIDDEN)
            
            match.status = 'rejected'
            match.rejected_at = timezone.now()
            match.rejected_by = request.user
            match.save()
            
            return Response({
                'success': True,
                'message': 'Match rejeté',
                'match_id': match.id
            })
        except Match.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Match non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class MatchDetailView(APIView):
    """Vue pour récupérer les détails d'un match."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, match_id):
        """Récupérer les détails d'un match."""
        try:
            match = Match.objects.get(id=match_id)
            
            # Vérifier que l'utilisateur a accès à ce match
            if (request.user != match.shipment.sender and 
                request.user != match.trip.traveler and 
                not request.user.is_staff):
                return Response({
                    'success': False,
                    'message': 'Accès non autorisé'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = MatchSerializer(match)
            return Response({
                'success': True,
                'match': serializer.data
            })
            
        except Match.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Match non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class OTPDeliveryView(APIView):
    """Vue pour la gestion des OTP de livraison."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, match_id):
        """Générer un OTP de livraison."""
        try:
            match = Match.objects.get(id=match_id)
            
            # Vérifier que l'utilisateur est le voyageur
            if request.user != match.trip.traveler:
                return Response({
                    'success': False,
                    'message': 'Seul le voyageur peut générer l\'OTP'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Vérifier que le match est accepté
            if match.status != 'accepted':
                return Response({
                    'success': False,
                    'message': 'Le match doit être accepté pour générer l\'OTP'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Générer l'OTP
            otp_code = OTPDeliveryService.generate_and_send_otp(match)
            
            return Response({
                'success': True,
                'otp_code': otp_code,
                'expires_at': match.otp_expires_at.isoformat() if match.otp_expires_at else None,
                'message': 'OTP généré et envoyé'
            })
            
        except Match.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Match non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, match_id):
        """Vérifier un OTP de livraison."""
        try:
            match = Match.objects.get(id=match_id)
            otp_code = request.data.get('otp_code')
            
            if not otp_code:
                return Response({
                    'success': False,
                    'message': 'Code OTP requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier l'OTP
            if OTPDeliveryService.verify_delivery_otp(match, otp_code):
                return Response({
                    'success': True,
                    'payment_released': True,
                    'message': 'Livraison confirmée et paiement libéré'
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Code OTP invalide ou expiré'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Match.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Match non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class ChatIntegrationView(APIView):
    """Vue pour l'intégration du chat."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, match_id):
        """Activer le chat pour un match."""
        try:
            match = Match.objects.get(id=match_id)
            
            # Vérifier que l'utilisateur a accès à ce match
            if (request.user != match.shipment.sender and 
                request.user != match.trip.traveler):
                return Response({
                    'success': False,
                    'message': 'Accès non autorisé'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Vérifier que le match est accepté
            if match.status != 'accepted':
                return Response({
                    'success': False,
                    'message': 'Le match doit être accepté pour activer le chat'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Activer le chat
            if match.activate_chat():
                return Response({
                    'success': True,
                    'chat_room_id': str(match.chat_room_id),
                    'message': 'Chat activé avec succès'
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Le chat est déjà activé'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Match.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Match non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class AutomaticMatchingView(APIView):
    """Vue pour le matching automatique."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Effectuer un matching automatique."""
        try:
            match_type = request.data.get('type')
            item_id = request.data.get('item_id')
            auto_accept = request.data.get('auto_accept', False)
            limit = request.data.get('limit', 10)
            
            if not match_type or not item_id:
                return Response({
                    'success': False,
                    'message': 'Type et ID requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if match_type == 'shipment':
                try:
                    shipment = Shipment.objects.get(id=item_id, sender=request.user)
                    matches = AutomaticMatchingService.find_matches_for_shipment(shipment, limit)
                except Shipment.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Envoi non trouvé'
                    }, status=status.HTTP_404_NOT_FOUND)
            elif match_type == 'trip':
                try:
                    trip = Trip.objects.get(id=item_id, traveler=request.user)
                    matches = AutomaticMatchingService.find_matches_for_trip(trip, limit)
                except Trip.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Trajet non trouvé'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({
                    'success': False,
                    'message': 'Type invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Auto-accept si demandé
            if auto_accept and matches:
                for match in matches[:1]:  # Auto-accept seulement le premier match
                    if match.can_auto_accept:
                        match.auto_accept()
            
            serializer = MatchSerializer(matches, many=True)
            return Response({
                'success': True,
                'matches': serializer.data,
                'count': len(matches),
                'auto_accepted': auto_accept and bool(matches)
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur lors du matching automatique: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MatchingPreferencesView(APIView):
    """Vue pour la gestion des préférences de matching."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupérer les préférences de matching de l'utilisateur."""
        try:
            preferences = MatchingPreferences.objects.get(user=request.user)
            serializer = MatchingPreferencesSerializer(preferences)
            return Response({
                'success': True,
                'preferences': serializer.data
            })
        except MatchingPreferences.DoesNotExist:
            return Response({
                'success': True,
                'preferences': None,
                'message': 'Aucune préférence configurée'
            })
    
    def post(self, request):
        """Créer ou mettre à jour les préférences de matching."""
        try:
            preferences, created = MatchingPreferences.objects.get_or_create(
                user=request.user,
                defaults=request.data
            )
            
            if not created:
                for key, value in request.data.items():
                    setattr(preferences, key, value)
                preferences.save()
            
            serializer = MatchingPreferencesSerializer(preferences)
            return Response({
                'success': True,
                'preferences': serializer.data,
                'message': 'Préférences créées' if created else 'Préférences mises à jour'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur lors de la sauvegarde des préférences: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class MatchingAnalyticsView(APIView):
    """Vue pour les analytics de matching."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupérer les statistiques de matching."""
        try:
            from .services import MatchingAnalyticsService
            
            # Récupérer les paramètres de filtrage
            date_from = request.GET.get('date_from')
            date_to = request.GET.get('date_to')
            
            # Obtenir les statistiques
            analytics = MatchingAnalyticsService.get_matching_statistics(
                user=request.user,
                date_from=date_from,
                date_to=date_to
            )
            
            return Response({
                'success': True,
                'analytics': analytics
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur lors du calcul des analytics: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MatchingNotificationsView(APIView):
    """Vue pour les notifications de matching."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupérer les notifications de matching."""
        # Placeholder - à implémenter avec le module notifications
        return Response({
            'success': True,
            'notifications': [],
            'count': 0,
            'message': 'Module notifications à implémenter'
        })


# Views pour l'administration
class AdminMatchListView(APIView):
    """Vue admin pour la liste de tous les matches."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Liste de tous les matches."""
        matches = Match.objects.all().select_related('shipment', 'trip')
        serializer = MatchSerializer(matches, many=True)
        
        return Response({
            'success': True,
            'matches': serializer.data,
            'count': matches.count()
        })


class AdminMatchDetailView(APIView):
    """Vue admin pour les détails d'un match."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request, match_id):
        """Détails d'un match spécifique."""
        try:
            match = Match.objects.get(id=match_id)
            serializer = MatchSerializer(match)
            return Response({
                'success': True,
                'match': serializer.data
            })
        except Match.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Match non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class MatchingRulesView(APIView):
    """Vue pour la gestion des règles de matching configurables."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Récupérer les règles de matching actives."""
        rules = MatchingRule.objects.filter(is_active=True)
        
        rules_data = []
        for rule in rules:
            rules_data.append({
                'id': rule.id,
                'name': rule.name,
                'description': rule.description,
                'min_compatibility_score': float(rule.min_compatibility_score),
                'max_distance_km': rule.max_distance_km,
                'max_date_flexibility_days': rule.max_date_flexibility_days,
                'geographic_weight': float(rule.geographic_weight),
                'weight_weight': float(rule.weight_weight),
                'package_type_weight': float(rule.package_type_weight),
                'fragility_weight': float(rule.fragility_weight),
                'date_weight': float(rule.date_weight),
                'reputation_weight': float(rule.reputation_weight),
                'enable_auto_acceptance': rule.enable_auto_acceptance,
                'auto_accept_threshold': float(rule.auto_accept_threshold),
                'is_active': rule.is_active
            })
        
        return Response({
            'success': True,
            'rules': rules_data,
            'count': len(rules_data)
        })
    
    def post(self, request):
        """Créer une nouvelle règle de matching."""
        try:
            rule = MatchingRule.objects.create(
                name=request.data.get('name'),
                description=request.data.get('description'),
                min_compatibility_score=request.data.get('min_compatibility_score', 30.00),
                max_distance_km=request.data.get('max_distance_km', 100),
                max_date_flexibility_days=request.data.get('max_date_flexibility_days', 7),
                geographic_weight=request.data.get('geographic_weight', 35.00),
                weight_weight=request.data.get('weight_weight', 20.00),
                package_type_weight=request.data.get('package_type_weight', 15.00),
                fragility_weight=request.data.get('fragility_weight', 10.00),
                date_weight=request.data.get('date_weight', 15.00),
                reputation_weight=request.data.get('reputation_weight', 5.00),
                enable_auto_acceptance=request.data.get('enable_auto_acceptance', False),
                auto_accept_threshold=request.data.get('auto_accept_threshold', 90.00),
                is_active=request.data.get('is_active', True)
            )
            
            return Response({
                'success': True,
                'message': 'Règle de matching créée',
                'rule_id': rule.id
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur lors de la création de la règle: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
