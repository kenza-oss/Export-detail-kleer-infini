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

from .models import Match, MatchingPreferences
from .serializers import (
    MatchSerializer, MatchingPreferencesSerializer,
    MatchResultSerializer, MatchingAlgorithmSerializer
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
            shipment = Shipment.objects.get(id=shipment_id, user=request.user)
            
            # Algorithme de matching
            matches = self.calculate_shipment_matches(shipment)
            
            return Response({
                'success': True,
                'matches': matches,
                'count': len(matches),
                'shipment_id': shipment_id
            })
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def find_trip_matches(self, request, trip_id):
        """Trouver des envois pour un trajet."""
        try:
            trip = Trip.objects.get(id=trip_id, traveler=request.user)
            
            # Algorithme de matching
            matches = self.calculate_trip_matches(trip)
            
            return Response({
                'success': True,
                'matches': matches,
                'count': len(matches),
                'trip_id': trip_id
            })
        except Trip.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Trajet non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def calculate_shipment_matches(self, shipment):
        """Calculer les matches pour un envoi."""
        # Critères de matching
        compatible_trips = Trip.objects.filter(
            status='active',
            origin__icontains=shipment.origin,
            destination__icontains=shipment.destination,
            available_capacity__gte=shipment.weight,
            departure_date__gte=timezone.now().date()
        ).exclude(traveler=shipment.user)
        
        matches = []
        for trip in compatible_trips[:10]:  # Limiter à 10 résultats
            score = self.calculate_compatibility_score(shipment, trip)
            
            if score > 0.5:  # Seuil minimum de compatibilité
                matches.append({
                    'id': len(matches) + 1,
                    'trip': {
                        'id': trip.id,
                        'traveler': {
                            'id': trip.traveler.id,
                            'name': f"{trip.traveler.first_name} {trip.traveler.last_name}",
                            'rating': getattr(trip.traveler.userprofile, 'rating', 0),
                            'total_trips': getattr(trip.traveler.userprofile, 'total_trips', 0)
                        },
                        'origin': trip.origin,
                        'destination': trip.destination,
                        'departure_date': trip.departure_date,
                        'available_capacity': trip.available_capacity,
                        'price_per_kg': trip.price_per_kg
                    },
                    'compatibility_score': score,
                    'estimated_cost': shipment.weight * trip.price_per_kg,
                    'estimated_delivery': trip.arrival_date
                })
        
        # Trier par score de compatibilité
        matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
        return matches
    
    def calculate_trip_matches(self, trip):
        """Calculer les matches pour un trajet."""
        # Critères de matching
        compatible_shipments = Shipment.objects.filter(
            status='pending',
            origin__icontains=trip.origin,
            destination__icontains=trip.destination,
            weight__lte=trip.available_capacity
        ).exclude(user=trip.traveler)
        
        matches = []
        for shipment in compatible_shipments[:10]:  # Limiter à 10 résultats
            score = self.calculate_compatibility_score(shipment, trip)
            
            if score > 0.5:  # Seuil minimum de compatibilité
                matches.append({
                    'id': len(matches) + 1,
                    'shipment': {
                        'id': shipment.id,
                        'tracking_number': shipment.tracking_number,
                        'sender': {
                            'id': shipment.user.id,
                            'name': f"{shipment.user.first_name} {shipment.user.last_name}",
                            'rating': getattr(shipment.user.userprofile, 'rating', 0)
                        },
                        'origin': shipment.origin,
                        'destination': shipment.destination,
                        'weight': shipment.weight,
                        'description': shipment.description
                    },
                    'compatibility_score': score,
                    'estimated_earnings': shipment.weight * trip.price_per_kg,
                    'pickup_date': trip.departure_date
                })
        
        # Trier par score de compatibilité
        matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
        return matches
    
    def calculate_compatibility_score(self, shipment, trip):
        """Calculer le score de compatibilité entre un envoi et un trajet."""
        score = 0.0
        
        # 1. Compatibilité géographique (40%)
        if shipment.origin.lower() in trip.origin.lower() or trip.origin.lower() in shipment.origin.lower():
            score += 0.4
        elif shipment.origin.lower()[:3] == trip.origin.lower()[:3]:
            score += 0.3
        
        if shipment.destination.lower() in trip.destination.lower() or trip.destination.lower() in shipment.destination.lower():
            score += 0.4
        elif shipment.destination.lower()[:3] == trip.destination.lower()[:3]:
            score += 0.3
        
        # 2. Compatibilité de capacité (30%)
        capacity_ratio = shipment.weight / trip.available_capacity
        if capacity_ratio <= 1.0:
            score += 0.3 * (1 - capacity_ratio)
        
        # 3. Compatibilité temporelle (20%)
        if trip.departure_date >= timezone.now().date():
            days_diff = (trip.departure_date - timezone.now().date()).days
            if days_diff <= 7:
                score += 0.2
            elif days_diff <= 14:
                score += 0.1
        
        # 4. Historique utilisateur (10%)
        user_rating = getattr(trip.traveler.userprofile, 'rating', 0)
        score += (user_rating / 5.0) * 0.1
        
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
                examples={"application/json": MATCHING_LIST_EXAMPLE["response"]}
            )
        }
    )
    def get(self, request):
        """Récupérer les matches de l'utilisateur."""
        user_matches = Match.objects.filter(
            Q(shipment__user=request.user) | Q(trip__traveler=request.user)
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
                examples={"application/json": MATCHING_ACCEPT_EXAMPLE["response"]}
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
            if match.shipment and match.shipment.user != request.user:
                return Response({
                    'success': False,
                    'message': 'Non autorisé'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if match.trip and match.trip.traveler != request.user:
                return Response({
                    'success': False,
                    'message': 'Non autorisé'
                }, status=status.HTTP_403_FORBIDDEN)
            
            with transaction.atomic():
                match.status = 'accepted'
                match.accepted_at = timezone.now()
                match.accepted_by = request.user
                match.save()
                
                # Mettre à jour les statuts
                if match.shipment:
                    match.shipment.status = 'matched'
                    match.shipment.save()
                
                if match.trip:
                    # Réduire la capacité disponible
                    if match.shipment:
                        match.trip.available_capacity -= match.shipment.weight
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
                examples={"application/json": MATCHING_REJECT_EXAMPLE["response"]}
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
            if match.shipment and match.shipment.user != request.user:
                return Response({
                    'success': False,
                    'message': 'Non autorisé'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if match.trip and match.trip.traveler != request.user:
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


class MatchingPreferencesView(APIView):
    """Vue pour les préférences de matching."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer les préférences de matching",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Préférences de matching",
                examples={"application/json": {
                    "success": True,
                    "preferences": {
                        "id": 1,
                        "max_distance": 100,
                        "min_rating": 4.0,
                        "preferred_vehicle_types": ["car", "van"],
                        "price_range": {
                            "min": 50,
                            "max": 200
                        },
                        "notification_settings": {
                            "email": True,
                            "push": True,
                            "sms": False
                        }
                    }
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Préférences non trouvées",
                examples={"application/json": {
                    "success": False,
                    "message": "Préférences non trouvées"
                }}
            )
        }
    )
    def get(self, request):
        """Récupérer les préférences de matching."""
        try:
            preferences = MatchingPreferences.objects.get(user=request.user)
            serializer = MatchingPreferencesSerializer(preferences)
            return Response({
                'success': True,
                'preferences': serializer.data
            })
        except MatchingPreferences.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Préférences non trouvées'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_description="Créer ou mettre à jour les préférences de matching",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'max_distance': openapi.Schema(type=openapi.TYPE_INTEGER),
                'min_rating': openapi.Schema(type=openapi.TYPE_NUMBER),
                'preferred_vehicle_types': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING)
                ),
                'price_range': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'min': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'max': openapi.Schema(type=openapi.TYPE_NUMBER)
                    }
                ),
                'notification_settings': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'email': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'push': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'sms': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                    }
                )
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Préférences mises à jour",
                examples={"application/json": {
                    "success": True,
                    "message": "Préférences mises à jour",
                    "preferences": {
                        "id": 1,
                        "max_distance": 100,
                        "min_rating": 4.0,
                        "preferred_vehicle_types": ["car", "van"],
                        "price_range": {
                            "min": 50,
                            "max": 200
                        },
                        "notification_settings": {
                            "email": True,
                            "push": True,
                            "sms": False
                        }
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "errors": {
                        "max_distance": ["Ce champ est requis."]
                    }
                }}
            )
        }
    )
    def post(self, request):
        """Créer ou mettre à jour les préférences de matching."""
        try:
            preferences = MatchingPreferences.objects.get(user=request.user)
            serializer = MatchingPreferencesSerializer(preferences, data=request.data)
        except MatchingPreferences.DoesNotExist:
            serializer = MatchingPreferencesSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                'success': True,
                'message': 'Préférences mises à jour',
                'preferences': serializer.data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class MatchingAnalyticsView(APIView):
    """Vue pour les analytics de matching."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupérer les statistiques de matching."""
        user_matches = Match.objects.filter(
            Q(shipment__user=request.user) | Q(trip__traveler=request.user)
        )
        
        analytics = {
            'total_matches': user_matches.count(),
            'accepted_matches': user_matches.filter(status='accepted').count(),
            'rejected_matches': user_matches.filter(status='rejected').count(),
            'pending_matches': user_matches.filter(status='pending').count(),
            'average_compatibility_score': user_matches.aggregate(
                avg_score=models.Avg('compatibility_score')
            )['avg_score'] or 0,
            'success_rate': (user_matches.filter(status='accepted').count() / 
                           max(user_matches.count(), 1)) * 100
        }
        
        return Response({
            'success': True,
            'analytics': analytics
        })


class MatchingNotificationsView(APIView):
    """Vue pour les notifications de matching."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupérer les notifications de matching."""
        # En production, intégrer avec le système de notifications
        notifications = [
            {
                'id': 1,
                'type': 'new_match',
                'title': 'Nouveau match disponible',
                'message': 'Un nouveau trajet correspond à votre envoi',
                'created_at': timezone.now(),
                'read': False
            }
        ]
        
        return Response({
            'success': True,
            'notifications': notifications,
            'count': len(notifications)
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
