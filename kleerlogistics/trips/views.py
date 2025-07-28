"""
Views for trips app - Traveler trip management with JSON responses
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
import random
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Trip, TripDocument
from .serializers import (
    TripSerializer, TripCreateSerializer, TripDetailSerializer,
    TripDocumentSerializer, TripStatusSerializer
)
from config.swagger_examples import (
    TRIP_CREATE_EXAMPLE, TRIP_SEARCH_EXAMPLE, ERROR_EXAMPLES
)
from config.swagger_config import (
    trip_create_schema, trip_search_schema
)


class TripListView(APIView):
    """Vue pour la liste des trajets."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Lister les trajets de l'utilisateur",
        manual_parameters=[
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Statut du trajet",
                type=openapi.TYPE_STRING,
                enum=['active', 'completed', 'cancelled']
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
                description="Liste des trajets",
                examples={"application/json": {
                    "success": True,
                    "trips": [
                        {
                            "id": 1,
                            "origin": "Alger",
                            "destination": "Oran",
                            "departure_date": "2024-01-25T08:00:00Z",
                            "arrival_date": "2024-01-25T12:00:00Z",
                            "available_capacity": 100,
                            "price_per_kg": 15.00,
                            "status": "active",
                            "created_at": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "count": 1
                }}
            )
        }
    )
    def get(self, request):
        """Liste des trajets de l'utilisateur connecté."""
        trips = Trip.objects.filter(traveler=request.user).order_by('-created_at')
        serializer = TripSerializer(trips, many=True)
        
        return Response({
            'success': True,
            'trips': serializer.data,
            'count': trips.count()
        })


class TripCreateView(APIView):
    """Vue pour la création de trajets."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Créer un nouveau trajet",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'origin': openapi.Schema(type=openapi.TYPE_STRING),
                'destination': openapi.Schema(type=openapi.TYPE_STRING),
                'departure_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'arrival_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'available_capacity': openapi.Schema(type=openapi.TYPE_NUMBER),
                'price_per_kg': openapi.Schema(type=openapi.TYPE_NUMBER),
                'vehicle_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['car', 'van', 'truck', 'motorcycle']
                ),
                'description': openapi.Schema(type=openapi.TYPE_STRING),
                'flexible_dates': openapi.Schema(type=openapi.TYPE_BOOLEAN)
            },
            required=['origin', 'destination', 'departure_date', 'available_capacity', 'price_per_kg']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Trajet créé",
                examples={"application/json": {
                    "success": True,
                    "message": "Trajet créé avec succès",
                    "trip": {
                        "id": 1,
                        "origin": "Alger",
                        "destination": "Oran",
                        "status": "active"
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "errors": {
                        "origin": ["Ce champ est requis."],
                        "departure_date": ["Cette date doit être dans le futur."]
                    }
                }}
            )
        }
    )
    def post(self, request):
        """Créer un nouveau trajet."""
        serializer = TripCreateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                trip = serializer.save(
                    traveler=request.user,
                    status='active'
                )
            
            return Response({
                'success': True,
                'message': 'Trajet créé avec succès',
                'trip': {
                    'id': trip.id,
                    'origin': trip.origin,
                    'destination': trip.destination,
                    'status': trip.status
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TripDetailView(APIView):
    """Vue pour les détails d'un trajet."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer les détails d'un trajet",
        manual_parameters=[
            openapi.Parameter(
                'pk',
                openapi.IN_PATH,
                description="ID du trajet",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Détails du trajet",
                examples={"application/json": {
                    "success": True,
                    "trip": {
                        "id": 1,
                        "origin": "Alger",
                        "destination": "Oran",
                        "departure_date": "2024-01-25T08:00:00Z",
                        "arrival_date": "2024-01-25T12:00:00Z",
                        "available_capacity": 100,
                        "price_per_kg": 15.00,
                        "vehicle_type": "car",
                        "description": "Voyage d'affaires",
                        "status": "active",
                        "flexible_dates": False,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Trajet non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Trajet non trouvé"
                }}
            )
        }
    )
    def get(self, request, pk):
        """Récupérer les détails d'un trajet."""
        try:
            trip = Trip.objects.get(pk=pk, traveler=request.user)
            serializer = TripDetailSerializer(trip)
            
            return Response({
                'success': True,
                'trip': serializer.data
            })
        except Trip.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Trajet non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, pk):
        """Mettre à jour un trajet."""
        try:
            trip = Trip.objects.get(pk=pk, traveler=request.user)
            serializer = TripCreateSerializer(trip, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Trajet mis à jour avec succès',
                    'trip': serializer.data
                })
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Trip.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Trajet non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, pk):
        """Supprimer un trajet."""
        try:
            trip = Trip.objects.get(pk=pk, traveler=request.user)
            
            # Vérifier que le trajet peut être supprimé
            if trip.status not in ['active', 'draft']:
                return Response({
                    'success': False,
                    'message': 'Impossible de supprimer un trajet en cours ou terminé'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            trip.delete()
            
            return Response({
                'success': True,
                'message': 'Trajet supprimé avec succès'
            })
        except Trip.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Trajet non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class TripStatusView(APIView):
    """Vue pour la gestion du statut des trajets."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        """Récupérer le statut d'un trajet."""
        try:
            trip = Trip.objects.get(pk=pk, traveler=request.user)
            serializer = TripStatusSerializer(trip)
            
            return Response({
                'success': True,
                'status': serializer.data
            })
        except Trip.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Trajet non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, pk):
        """Mettre à jour le statut d'un trajet."""
        try:
            trip = Trip.objects.get(pk=pk, traveler=request.user)
            new_status = request.data.get('status')
            
            if new_status not in ['active', 'in_progress', 'completed', 'cancelled']:
                return Response({
                    'success': False,
                    'message': 'Statut invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            trip.status = new_status
            trip.save()
            
            return Response({
                'success': True,
                'message': f'Statut mis à jour vers {new_status}',
                'status': new_status
            })
        except Trip.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Trajet non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class AvailableTripsView(APIView):
    """Vue pour les trajets disponibles."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Liste des trajets disponibles pour le matching."""
        # Filtrer les trajets actifs d'autres voyageurs
        trips = Trip.objects.filter(
            status='active',
            departure_date__gte=timezone.now().date()
        ).exclude(traveler=request.user)
        
        # Filtres optionnels
        origin = request.query_params.get('origin')
        destination = request.query_params.get('destination')
        departure_date = request.query_params.get('departure_date')
        min_capacity = request.query_params.get('min_capacity')
        
        if origin:
            trips = trips.filter(origin__icontains=origin)
        if destination:
            trips = trips.filter(destination__icontains=destination)
        if departure_date:
            trips = trips.filter(departure_date=departure_date)
        if min_capacity:
            trips = trips.filter(available_capacity__gte=float(min_capacity))
        
        serializer = TripSerializer(trips, many=True)
        
        return Response({
            'success': True,
            'trips': serializer.data,
            'count': trips.count()
        })


class TripDocumentView(APIView):
    """Vue pour la gestion des documents de trajet."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, trip_id):
        """Liste des documents d'un trajet."""
        try:
            trip = Trip.objects.get(pk=trip_id, traveler=request.user)
            documents = TripDocument.objects.filter(trip=trip)
            serializer = TripDocumentSerializer(documents, many=True)
            
            return Response({
                'success': True,
                'documents': serializer.data,
                'count': documents.count()
            })
        except Trip.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Trajet non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request, trip_id):
        """Ajouter un document à un trajet."""
        try:
            trip = Trip.objects.get(pk=trip_id, traveler=request.user)
            serializer = TripDocumentSerializer(data=request.data)
            
            if serializer.is_valid():
                document = serializer.save(trip=trip)
                return Response({
                    'success': True,
                    'message': 'Document ajouté avec succès',
                    'document': serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Trip.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Trajet non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class UpdateCapacityView(APIView):
    """Vue pour mettre à jour la capacité d'un trajet."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request, pk):
        """Mettre à jour la capacité disponible."""
        try:
            trip = Trip.objects.get(pk=pk, traveler=request.user)
            new_capacity = request.data.get('available_capacity')
            
            if new_capacity is None:
                return Response({
                    'success': False,
                    'message': 'Capacité requise'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if new_capacity < 0:
                return Response({
                    'success': False,
                    'message': 'La capacité ne peut pas être négative'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            trip.available_capacity = new_capacity
            trip.save()
            
            return Response({
                'success': True,
                'message': 'Capacité mise à jour avec succès',
                'available_capacity': new_capacity
            })
        except Trip.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Trajet non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class TripSearchView(APIView):
    """Vue pour la recherche de trajets."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @trip_search_schema()
    def get(self, request):
        """Rechercher des trajets."""
        query = request.query_params.get('q', '')
        origin = request.query_params.get('origin', '')
        destination = request.query_params.get('destination', '')
        date_from = request.query_params.get('date_from', '')
        date_to = request.query_params.get('date_to', '')
        
        trips = Trip.objects.filter(status='active')
        
        if query:
            trips = trips.filter(
                Q(origin__icontains=query) |
                Q(destination__icontains=query) |
                Q(description__icontains=query)
            )
        
        if origin:
            trips = trips.filter(origin__icontains=origin)
        if destination:
            trips = trips.filter(destination__icontains=destination)
        if date_from:
            trips = trips.filter(departure_date__gte=date_from)
        if date_to:
            trips = trips.filter(departure_date__lte=date_to)
        
        # Exclure les trajets de l'utilisateur connecté
        trips = trips.exclude(traveler=request.user)
        
        serializer = TripSerializer(trips[:20], many=True)
        
        return Response({
            'success': True,
            'trips': serializer.data,
            'count': trips.count()
        })


class TripMatchesView(APIView):
    """Vue pour les matches d'un trajet."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        """Récupérer les matches pour un trajet."""
        try:
            trip = Trip.objects.get(pk=pk, traveler=request.user)
            
            # Simuler des matches (en production, utiliser l'algorithme de matching)
            matches = []
            if trip.status == 'active':
                # Créer des matches fictifs pour la démonstration
                matches = [
                    {
                        'id': 1,
                        'shipment': {
                            'tracking_number': 'KL123456789',
                            'origin': trip.origin,
                            'destination': trip.destination,
                            'weight': 2.5,
                            'description': 'Colis fragile'
                        },
                        'sender': {
                            'id': 3,
                            'name': 'Fatima Benali',
                            'rating': 4.6
                        },
                        'compatibility_score': 0.92,
                        'estimated_earnings': 120.00,
                        'pickup_date': '2024-02-15'
                    }
                ]
            
            return Response({
                'success': True,
                'matches': matches,
                'count': len(matches)
            })
        except Trip.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Trajet non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class AcceptShipmentView(APIView):
    """Vue pour accepter un envoi sur un trajet."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk, shipment_id):
        """Accepter un envoi sur un trajet."""
        try:
            trip = Trip.objects.get(pk=pk, traveler=request.user)
            
            # En production, vérifier que l'envoi existe et est compatible
            # Pour la démonstration, on simule l'acceptation
            
            # Mettre à jour la capacité du trajet
            shipment_weight = float(request.data.get('weight', 0))
            if trip.available_capacity >= shipment_weight:
                trip.available_capacity -= shipment_weight
                trip.save()
                
                return Response({
                    'success': True,
                    'message': 'Envoi accepté avec succès',
                    'remaining_capacity': trip.available_capacity
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Capacité insuffisante'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Trip.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Trajet non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class TripAnalyticsView(APIView):
    """Vue pour les analytics des trajets."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupérer les analytics des trajets de l'utilisateur."""
        user_trips = Trip.objects.filter(traveler=request.user)
        
        analytics = {
            'total_trips': user_trips.count(),
            'active_trips': user_trips.filter(status='active').count(),
            'completed_trips': user_trips.filter(status='completed').count(),
            'cancelled_trips': user_trips.filter(status='cancelled').count(),
            'total_earnings': sum(trip.earnings for trip in user_trips if trip.earnings),
            'average_rating': user_trips.aggregate(avg_rating=models.Avg('rating'))['avg_rating'] or 0,
            'total_distance': sum(trip.distance for trip in user_trips if trip.distance),
            'favorite_routes': self.get_favorite_routes(user_trips)
        }
        
        return Response({
            'success': True,
            'analytics': analytics
        })
    
    def get_favorite_routes(self, trips):
        """Obtenir les routes préférées."""
        routes = {}
        for trip in trips:
            route = f"{trip.origin} → {trip.destination}"
            routes[route] = routes.get(route, 0) + 1
        
        return sorted(routes.items(), key=lambda x: x[1], reverse=True)[:5]


class TripCalendarView(APIView):
    """Vue pour le calendrier des trajets."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupérer les trajets pour un calendrier."""
        year = request.query_params.get('year', timezone.now().year)
        month = request.query_params.get('month', timezone.now().month)
        
        trips = Trip.objects.filter(
            traveler=request.user,
            departure_date__year=year,
            departure_date__month=month
        ).order_by('departure_date')
        
        calendar_data = []
        for trip in trips:
            calendar_data.append({
                'id': trip.id,
                'title': f"{trip.origin} → {trip.destination}",
                'date': trip.departure_date,
                'status': trip.status,
                'available_capacity': trip.available_capacity
            })
        
        return Response({
            'success': True,
            'calendar_data': calendar_data
        })


# Views pour l'administration
class AdminTripListView(APIView):
    """Vue admin pour la liste de tous les trajets."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Liste de tous les trajets."""
        trips = Trip.objects.all().select_related('traveler')
        serializer = TripSerializer(trips, many=True)
        
        return Response({
            'success': True,
            'trips': serializer.data,
            'count': trips.count()
        })


class AdminTripDetailView(APIView):
    """Vue admin pour les détails d'un trajet."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request, pk):
        """Détails d'un trajet spécifique."""
        try:
            trip = Trip.objects.get(pk=pk)
            serializer = TripDetailSerializer(trip)
            return Response({
                'success': True,
                'trip': serializer.data
            })
        except Trip.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Trajet non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
