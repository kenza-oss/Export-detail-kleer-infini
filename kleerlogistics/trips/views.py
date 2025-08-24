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
    TripUpdateSerializer, TripDocumentSerializer, TripStatusSerializer
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
                    'origin_city': trip.origin_city,
                    'origin_country': trip.origin_country,
                    'destination_city': trip.destination_city,
                    'destination_country': trip.destination_country,
                    'departure_date': trip.departure_date,
                    'arrival_date': trip.arrival_date,
                    'max_weight': trip.max_weight,
                    'max_packages': trip.max_packages,
                    'min_price_per_kg': trip.min_price_per_kg,
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
            serializer = TripUpdateSerializer(trip, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                # Re-serialize with detail serializer for response
                response_serializer = TripDetailSerializer(trip)
                return Response({
                    'success': True,
                    'message': 'Trajet mis à jour avec succès',
                    'trip': response_serializer.data
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
        return self._update_status(request, pk)
    
    def patch(self, request, pk):
        """Mettre à jour partiellement le statut d'un trajet."""
        return self._update_status(request, pk)
    
    def _update_status(self, request, pk):
        """Méthode commune pour mettre à jour le statut."""
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
        max_weight = request.query_params.get('max_weight')
        
        if origin:
            trips = trips.filter(origin_city__icontains=origin)
        if destination:
            trips = trips.filter(destination_city__icontains=destination)
        if departure_date:
            trips = trips.filter(departure_date=departure_date)
        if min_capacity:
            trips = trips.filter(remaining_weight__gte=float(min_capacity))
        if max_weight:
            trips = trips.filter(remaining_weight__lte=float(max_weight))
        
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
    
    @swagger_auto_schema(
        operation_description="Mettre à jour la capacité disponible d'un trajet",
        manual_parameters=[
            openapi.Parameter(
                'pk',
                openapi.IN_PATH,
                description="ID du trajet",
                type=openapi.TYPE_INTEGER
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'remaining_weight': openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description="Poids restant disponible en kg",
                    example=20.0
                ),
                'remaining_packages': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Nombre de colis restants",
                    example=2
                )
            },
            required=['remaining_weight', 'remaining_packages']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Capacité mise à jour avec succès",
                examples={"application/json": {
                    "success": True,
                    "message": "Capacité mise à jour avec succès",
                    "remaining_weight": 20.0,
                    "remaining_packages": 2,
                    "max_weight": 50.0,
                    "max_packages": 5,
                    "utilization_rate": 60.0
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "message": "Le poids restant ne peut pas dépasser le poids maximum (50.0 kg)"
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
    
    def put(self, request, pk):
        """Mettre à jour la capacité disponible (remplace complètement)."""
        return self._update_capacity(request, pk, is_partial=False)
    
    @swagger_auto_schema(
        operation_description="Mettre à jour partiellement la capacité disponible d'un trajet",
        manual_parameters=[
            openapi.Parameter(
                'pk',
                openapi.IN_PATH,
                description="ID du trajet",
                type=openapi.TYPE_INTEGER
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'remaining_weight': openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description="Poids restant disponible en kg (optionnel)",
                    example=20.0
                ),
                'remaining_packages': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Nombre de colis restants (optionnel)",
                    example=2
                )
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Capacité mise à jour avec succès",
                examples={"application/json": {
                    "success": True,
                    "message": "Capacité mise à jour avec succès",
                    "remaining_weight": 20.0,
                    "remaining_packages": 2,
                    "max_weight": 50.0,
                    "max_packages": 5,
                    "utilization_rate": 60.0
                }}
            )
        }
    )
    def patch(self, request, pk):
        """Mettre à jour partiellement la capacité disponible."""
        return self._update_capacity(request, pk, is_partial=True)
    
    def _update_capacity(self, request, pk, is_partial=False):
        """Méthode commune pour mettre à jour la capacité."""
        try:
            trip = Trip.objects.get(pk=pk, traveler=request.user)
            
            # Vérifier que le trajet peut être modifié
            if trip.status not in ['draft', 'active']:
                return Response({
                    'success': False,
                    'message': 'Seuls les trajets en brouillon ou actifs peuvent être modifiés'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer les nouvelles valeurs
            new_remaining_weight = request.data.get('remaining_weight')
            new_remaining_packages = request.data.get('remaining_packages')
            
            # Validation des données
            if new_remaining_weight is not None:
                if new_remaining_weight < 0:
                    return Response({
                        'success': False,
                        'message': 'Le poids restant ne peut pas être négatif'
                    }, status=status.HTTP_400_BAD_REQUEST)
                if new_remaining_weight > trip.max_weight:
                    return Response({
                        'success': False,
                        'message': f'Le poids restant ne peut pas dépasser le poids maximum ({trip.max_weight} kg)'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            if new_remaining_packages is not None:
                if new_remaining_packages < 0:
                    return Response({
                        'success': False,
                        'message': 'Le nombre de colis restants ne peut pas être négatif'
                    }, status=status.HTTP_400_BAD_REQUEST)
                if new_remaining_packages > trip.max_packages:
                    return Response({
                        'success': False,
                        'message': f'Le nombre de colis restants ne peut pas dépasser le maximum ({trip.max_packages})'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mettre à jour les champs
            if new_remaining_weight is not None:
                trip.remaining_weight = new_remaining_weight
            if new_remaining_packages is not None:
                trip.remaining_packages = new_remaining_packages
            
            # Si c'est une mise à jour complète (PUT), s'assurer que tous les champs sont définis
            if not is_partial:
                if new_remaining_weight is None or new_remaining_packages is None:
                    return Response({
                        'success': False,
                        'message': 'Les deux champs remaining_weight et remaining_packages sont requis pour une mise à jour complète'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            trip.save()
            
            # Recalculer le taux d'utilisation
            utilization_rate = trip.utilization_rate
            
            return Response({
                'success': True,
                'message': 'Capacité mise à jour avec succès',
                'remaining_weight': trip.remaining_weight,
                'remaining_packages': trip.remaining_packages,
                'max_weight': trip.max_weight,
                'max_packages': trip.max_packages,
                'utilization_rate': utilization_rate
            })
        except Trip.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Trajet non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class TripSearchView(APIView):
    """Vue pour la recherche de trajets."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Rechercher des trajets avec des paramètres de requête",
        manual_parameters=[
            openapi.Parameter(
                'q',
                openapi.IN_QUERY,
                description="Recherche textuelle générale",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'origin',
                openapi.IN_QUERY,
                description="Ville d'origine",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'destination',
                openapi.IN_QUERY,
                description="Ville de destination",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'date_from',
                openapi.IN_QUERY,
                description="Date de départ à partir de (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                required=False
            ),
            openapi.Parameter(
                'date_to',
                openapi.IN_QUERY,
                description="Date de départ jusqu'à (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                required=False
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Résultats de la recherche",
                examples={"application/json": {
                    "success": True,
                    "trips": [
                        {
                            "id": 1,
                            "origin": "Alger",
                            "destination": "Paris",
                            "departure_date": "2024-02-15T08:00:00Z",
                            "available_capacity": 100,
                            "price_per_kg": 15.00,
                            "status": "active"
                        }
                    ],
                    "count": 1
                }}
            )
        }
    )
    def get(self, request):
        """Rechercher des trajets avec des paramètres de requête."""
        return self._search_trips(request)
    
    @swagger_auto_schema(
        operation_description="Rechercher des trajets avec un corps de requête JSON",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'origin_city': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Ville d'origine",
                    example="Alger"
                ),
                'destination_city': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Ville de destination",
                    example="Paris"
                ),
                'date_from': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Date de départ à partir de (YYYY-MM-DD)",
                    example="2024-02-15"
                ),
                'date_to': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Date de départ jusqu'à (YYYY-MM-DD)",
                    example="2024-02-20"
                ),
                'max_weight': openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description="Poids maximum du colis en kg",
                    example=20.0
                ),
                'package_types': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Types de colis acceptés",
                    example=["document", "electronics"]
                ),
                'max_price_per_kg': openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description="Prix maximum par kg",
                    example=15.00
                ),
                'accepts_fragile': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Accepte les colis fragiles",
                    example=True
                )
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Résultats de la recherche",
                examples={"application/json": {
                    "success": True,
                    "trips": [
                        {
                            "id": 1,
                            "origin_city": "Alger",
                            "destination_city": "Paris",
                            "departure_date": "2024-02-15T08:00:00Z",
                            "remaining_weight": 100.0,
                            "remaining_packages": 5,
                            "min_price_per_kg": 15.00,
                            "status": "active"
                        }
                    ],
                    "count": 1
                }}
            )
        }
    )
    def post(self, request):
        """Rechercher des trajets avec un corps de requête JSON."""
        return self._search_trips(request)
    
    def _search_trips(self, request):
        """Méthode commune pour la recherche de trajets."""
        # Déterminer la source des paramètres
        if request.method == 'POST':
            # Paramètres du corps de la requête
            origin_city = request.data.get('origin_city', '')
            destination_city = request.data.get('destination_city', '')
            date_from = request.data.get('date_from', '')
            date_to = request.data.get('date_to', '')
            max_weight = request.data.get('max_weight')
            package_types = request.data.get('package_types', [])
            max_price_per_kg = request.data.get('max_price_per_kg')
            accepts_fragile = request.data.get('accepts_fragile')
        else:
            # Paramètres de requête GET
            origin_city = request.query_params.get('origin', '')
            destination_city = request.query_params.get('destination', '')
            date_from = request.query_params.get('date_from', '')
            date_to = request.query_params.get('date_to', '')
            max_weight = None
            package_types = []
            max_price_per_kg = None
            accepts_fragile = None
        
        # Commencer avec tous les trajets actifs
        trips = Trip.objects.filter(status='active')
        
        # Filtres de base
        if origin_city:
            trips = trips.filter(origin_city__icontains=origin_city)
        if destination_city:
            trips = trips.filter(destination_city__icontains=destination_city)
        if date_from:
            trips = trips.filter(departure_date__gte=date_from)
        if date_to:
            trips = trips.filter(departure_date__lte=date_to)
        
        # Filtres avancés (uniquement pour POST)
        if request.method == 'POST':
            if max_weight is not None:
                trips = trips.filter(remaining_weight__gte=max_weight)
            
            if package_types:
                # Filtrer par types de colis acceptés
                trips = trips.filter(accepted_package_types__overlap=package_types)
            
            if max_price_per_kg is not None:
                trips = trips.filter(min_price_per_kg__lte=max_price_per_kg)
            
            if accepts_fragile is not None:
                trips = trips.filter(accepts_fragile=accepts_fragile)
        
        # Exclure les trajets de l'utilisateur connecté
        trips = trips.exclude(traveler=request.user)
        
        # Trier par date de départ
        trips = trips.order_by('departure_date')
        
        # Limiter les résultats
        trips = trips[:50]
        
        # Utiliser le serializer approprié
        if request.method == 'POST':
            serializer = TripDetailSerializer(trips, many=True, context={'request': request})
        else:
            serializer = TripSerializer(trips, many=True)
        
        return Response({
            'success': True,
            'trips': serializer.data,
            'count': trips.count(),
            'filters_applied': {
                'origin_city': origin_city,
                'destination_city': destination_city,
                'date_from': date_from,
                'date_to': date_to,
                'max_weight': max_weight,
                'package_types': package_types,
                'max_price_per_kg': max_price_per_kg,
                'accepts_fragile': accepts_fragile
            }
        })


class TripMatchesView(APIView):
    """Vue pour les matches d'un trajet."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer les correspondances d'un trajet",
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
                description="Liste des correspondances",
                examples={"application/json": {
                    "success": True,
                    "matches": [
                        {
                            "id": 1,
                            "shipment": {
                                "tracking_number": "KL123456789",
                                "origin_city": "Alger",
                                "destination_city": "Paris",
                                "weight": 2.5,
                                "package_type": "document",
                                "description": "Colis fragile"
                            },
                            "sender": {
                                "id": 3,
                                "name": "Fatima Benali",
                                "rating": 4.6
                            },
                            "compatibility_score": 92.0,
                            "proposed_price": 120.00,
                            "status": "pending"
                        }
                    ],
                    "count": 1
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
        """Récupérer les matches pour un trajet."""
        try:
            trip = Trip.objects.get(pk=pk, traveler=request.user)
            
            # Récupérer les vrais matches depuis l'app matching
            from matching.models import Match
            matches = Match.objects.filter(
                trip=trip,
                status='pending'
            ).select_related('shipment', 'shipment__sender').order_by('-compatibility_score')
            
            # Formater les données des matches
            formatted_matches = []
            for match in matches:
                shipment = match.shipment
                sender = shipment.sender
                
                formatted_match = {
                    'id': match.id,
                    'shipment': {
                        'tracking_number': shipment.tracking_number,
                        'origin_city': shipment.origin_city,
                        'destination_city': shipment.destination_city,
                        'weight': float(shipment.weight),
                        'package_type': shipment.package_type,
                        'description': shipment.description,
                        'is_fragile': shipment.is_fragile,
                        'status': shipment.status
                    },
                    'sender': {
                        'id': sender.id,
                        'name': f"{sender.first_name} {sender.last_name}",
                        'rating': getattr(sender, 'rating', 0.0),
                        'email': sender.email
                    },
                    'compatibility_score': float(match.compatibility_score),
                    'proposed_price': float(match.proposed_price),
                    'status': match.status,
                    'created_at': match.created_at,
                    'expires_at': match.expires_at
                }
                formatted_matches.append(formatted_match)
            
            return Response({
                'success': True,
                'matches': formatted_matches,
                'count': len(formatted_matches),
                'trip_info': {
                    'id': trip.id,
                    'remaining_weight': float(trip.remaining_weight),
                    'remaining_packages': trip.remaining_packages,
                    'status': trip.status
                }
            })
        except Trip.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Trajet non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class AcceptShipmentView(APIView):
    """Vue pour accepter un envoi sur un trajet."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Accepter un envoi pour un trajet",
        manual_parameters=[
            openapi.Parameter(
                'pk',
                openapi.IN_PATH,
                description="ID du trajet",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'shipment_id',
                openapi.IN_PATH,
                description="ID de l'envoi",
                type=openapi.TYPE_INTEGER
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'accepted': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Confirmation d'acceptation",
                    example=True
                ),
                'notes': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Notes additionnelles",
                    example="Envoi accepté, prêt pour le transport"
                )
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Envoi accepté avec succès",
                examples={"application/json": {
                    "success": True,
                    "message": "Envoi accepté avec succès",
                    "trip_id": 11,
                    "shipment_id": 1,
                    "remaining_weight": 30.0,
                    "remaining_packages": 3
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "message": "L'envoi ne peut pas être accepté"
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Trajet ou envoi non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Trajet non trouvé"
                }}
            )
        }
    )
    def post(self, request, pk, shipment_id):
        """Accepter un envoi sur un trajet."""
        try:
            # Vérifier que le trajet existe et appartient à l'utilisateur
            trip = Trip.objects.get(pk=pk, traveler=request.user)
            
            # Vérifier que l'envoi existe
            from shipments.models import Shipment
            shipment = Shipment.objects.get(id=shipment_id)
            
            # Vérifier que l'envoi peut être accepté
            if shipment.status != 'pending':
                return Response({
                    'success': False,
                    'message': f'L\'envoi est dans un état invalide: {shipment.status}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier la compatibilité
            if not trip.can_accept_shipment(shipment):
                return Response({
                    'success': False,
                    'message': 'L\'envoi n\'est pas compatible avec ce trajet'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier la capacité
            if shipment.weight > trip.remaining_weight:
                return Response({
                    'success': False,
                    'message': f'Capacité insuffisante. Poids disponible: {trip.remaining_weight}kg, Poids requis: {shipment.weight}kg'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if trip.remaining_packages <= 0:
                return Response({
                    'success': False,
                    'message': 'Aucun emplacement disponible pour les colis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Accepter l'envoi
            with transaction.atomic():
                # Ajouter l'envoi au trajet
                trip.add_shipment(shipment)
                
                # Mettre à jour le statut de l'envoi
                shipment.status = 'matched'
                shipment.matched_trip = trip
                shipment.save()
                
                # Récupérer les données mises à jour
                trip.refresh_from_db()
            
            # Récupérer les notes si fournies
            notes = request.data.get('notes', '')
            
            return Response({
                'success': True,
                'message': 'Envoi accepté avec succès',
                'trip_id': trip.id,
                'shipment_id': shipment.id,
                'remaining_weight': float(trip.remaining_weight),
                'remaining_packages': trip.remaining_packages,
                'notes': notes
            })
            
        except Trip.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Trajet non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur lors de l\'acceptation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TripAnalyticsView(APIView):
    """Vue pour les analytics des trajets."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer les analytics des trajets de l'utilisateur",
        manual_parameters=[
            openapi.Parameter(
                'date_from',
                openapi.IN_QUERY,
                description="Date de début (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                required=False
            ),
            openapi.Parameter(
                'date_to',
                openapi.IN_QUERY,
                description="Date de fin (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                required=False
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Filtrer par statut",
                type=openapi.TYPE_STRING,
                enum=['active', 'completed', 'cancelled', 'draft'],
                required=False
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Analytics des trajets",
                examples={"application/json": {
                    "success": True,
                    "analytics": {
                        "total_trips": 15,
                        "active_trips": 3,
                        "completed_trips": 10,
                        "cancelled_trips": 2,
                        "total_earnings": 1250.00,
                        "total_weight_carried": 450.5,
                        "total_packages_carried": 25,
                        "average_utilization_rate": 78.5,
                        "favorite_routes": [
                            ["Alger → Paris", 5],
                            ["Oran → Lyon", 3]
                        ],
                        "monthly_stats": {
                            "2024-01": {"trips": 3, "earnings": 250.00},
                            "2024-02": {"trips": 4, "earnings": 400.00}
                        }
                    }
                }}
            )
        }
    )
    def get(self, request):
        """Récupérer les analytics des trajets de l'utilisateur."""
        # Récupérer les paramètres de filtrage
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        status_filter = request.query_params.get('status')
        
        # Filtrer les trajets
        user_trips = Trip.objects.filter(traveler=request.user)
        
        if date_from:
            user_trips = user_trips.filter(departure_date__gte=date_from)
        if date_to:
            user_trips = user_trips.filter(departure_date__lte=date_to)
        if status_filter:
            user_trips = user_trips.filter(status=status_filter)
        
        # Calculer les statistiques de base
        total_trips = user_trips.count()
        active_trips = user_trips.filter(status='active').count()
        completed_trips = user_trips.filter(status='completed').count()
        cancelled_trips = user_trips.filter(status='cancelled').count()
        draft_trips = user_trips.filter(status='draft').count()
        
        # Calculer les statistiques financières et de capacité
        total_earnings = sum(
            float(trip.estimated_earnings) for trip in user_trips 
            if hasattr(trip, 'estimated_earnings') and trip.estimated_earnings
        )
        
        total_weight_carried = sum(
            float(trip.total_weight_carried) for trip in user_trips 
            if hasattr(trip, 'total_weight_carried') and trip.total_weight_carried
        )
        
        total_packages_carried = sum(
            trip.total_packages_carried for trip in user_trips 
            if hasattr(trip, 'total_packages_carried') and trip.total_packages_carried
        )
        
        # Calculer le taux d'utilisation moyen
        utilization_rates = [
            trip.utilization_rate for trip in user_trips 
            if hasattr(trip, 'utilization_rate') and trip.utilization_rate is not None
        ]
        average_utilization_rate = sum(utilization_rates) / len(utilization_rates) if utilization_rates else 0
        
        # Obtenir les routes préférées
        favorite_routes = self.get_favorite_routes(user_trips)
        
        # Statistiques mensuelles
        monthly_stats = self.get_monthly_stats(user_trips)
        
        analytics = {
            'total_trips': total_trips,
            'active_trips': active_trips,
            'completed_trips': completed_trips,
            'cancelled_trips': cancelled_trips,
            'draft_trips': draft_trips,
            'total_earnings': round(total_earnings, 2),
            'total_weight_carried': round(total_weight_carried, 2),
            'total_packages_carried': total_packages_carried,
            'average_utilization_rate': round(average_utilization_rate, 1),
            'favorite_routes': favorite_routes,
            'monthly_stats': monthly_stats,
            'filters_applied': {
                'date_from': date_from,
                'date_to': date_to,
                'status': status_filter
            }
        }
        
        return Response({
            'success': True,
            'analytics': analytics
        })
    
    def get_favorite_routes(self, trips):
        """Obtenir les routes préférées."""
        routes = {}
        for trip in trips:
            route = f"{trip.origin_city} → {trip.destination_city}"
            routes[route] = routes.get(route, 0) + 1
        
        return sorted(routes.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def get_monthly_stats(self, trips):
        """Obtenir les statistiques mensuelles."""
        monthly_stats = {}
        for trip in trips:
            month_key = trip.departure_date.strftime('%Y-%m')
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {'trips': 0, 'earnings': 0.0}
            
            monthly_stats[month_key]['trips'] += 1
            if hasattr(trip, 'estimated_earnings') and trip.estimated_earnings:
                monthly_stats[month_key]['earnings'] += float(trip.estimated_earnings)
        
        return monthly_stats


class TripCalendarView(APIView):
    """Vue pour le calendrier des trajets."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer le calendrier des trajets",
        manual_parameters=[
            openapi.Parameter(
                'year',
                openapi.IN_QUERY,
                description="Année (YYYY)",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'month',
                openapi.IN_QUERY,
                description="Mois (1-12)",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Filtrer par statut",
                type=openapi.TYPE_STRING,
                enum=['active', 'completed', 'cancelled', 'draft'],
                required=False
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Calendrier des trajets",
                examples={"application/json": {
                    "success": True,
                    "calendar_data": [
                        {
                            "id": 11,
                            "title": "Alger → Paris",
                            "date": "2024-02-15T08:00:00Z",
                            "status": "active",
                            "remaining_weight": 30.0,
                            "remaining_packages": 3,
                            "origin_city": "Alger",
                            "destination_city": "Paris"
                        }
                    ],
                    "period": {
                        "year": 2024,
                        "month": 2
                    }
                }}
            )
        }
    )
    def get(self, request):
        """Récupérer les trajets pour un calendrier."""
        # Récupérer les paramètres
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        status_filter = request.query_params.get('status')
        
        # Utiliser l'année et le mois actuels si non spécifiés
        if not year:
            year = timezone.now().year
        if not month:
            month = timezone.now().month
        
        # Filtrer les trajets
        trips = Trip.objects.filter(
            traveler=request.user,
            departure_date__year=year,
            departure_date__month=month
        )
        
        if status_filter:
            trips = trips.filter(status=status_filter)
        
        trips = trips.order_by('departure_date')
        
        # Formater les données pour le calendrier
        calendar_data = []
        for trip in trips:
            calendar_data.append({
                'id': trip.id,
                'title': f"{trip.origin_city} → {trip.destination_city}",
                'date': trip.departure_date,
                'status': trip.status,
                'remaining_weight': float(trip.remaining_weight) if hasattr(trip, 'remaining_weight') else 0,
                'remaining_packages': trip.remaining_packages if hasattr(trip, 'remaining_packages') else 0,
                'origin_city': trip.origin_city,
                'destination_city': trip.destination_city,
                'departure_time': trip.departure_date.strftime('%H:%M') if trip.departure_date else None,
                'estimated_earnings': float(trip.estimated_earnings) if hasattr(trip, 'estimated_earnings') and trip.estimated_earnings else 0
            })
        
        return Response({
            'success': True,
            'calendar_data': calendar_data,
            'period': {
                'year': int(year),
                'month': int(month)
            },
            'count': len(calendar_data),
            'filters_applied': {
                'status': status_filter
            }
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
