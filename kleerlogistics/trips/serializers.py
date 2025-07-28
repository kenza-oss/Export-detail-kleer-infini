"""
Serializers for trips app - JSON serialization for trip data
"""

from rest_framework import serializers
from django.utils import timezone
from users.serializers import UserSerializer

from .models import Trip, TripDocument


class TripSerializer(serializers.ModelSerializer):
    """Serializer de base pour les trajets."""
    
    traveler = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    transport_type_display = serializers.CharField(source='get_transport_type_display', read_only=True)
    
    class Meta:
        model = Trip
        fields = [
            'id', 'traveler', 'origin', 'destination', 'departure_date',
            'arrival_date', 'transport_type', 'transport_type_display',
            'available_capacity', 'price_per_kg', 'status', 'status_display',
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'traveler', 'status', 'created_at', 'updated_at'
        ]


class TripCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de trajets."""
    
    class Meta:
        model = Trip
        fields = [
            'origin', 'destination', 'departure_date', 'arrival_date',
            'transport_type', 'available_capacity', 'price_per_kg',
            'description', 'special_requirements'
        ]
    
    def validate_departure_date(self, value):
        """Valider la date de départ."""
        if value < timezone.now().date():
            raise serializers.ValidationError("La date de départ ne peut pas être dans le passé.")
        return value
    
    def validate_arrival_date(self, value):
        """Valider la date d'arrivée."""
        departure_date = self.initial_data.get('departure_date')
        if departure_date and value <= departure_date:
            raise serializers.ValidationError("La date d'arrivée doit être après la date de départ.")
        return value
    
    def validate_available_capacity(self, value):
        """Valider la capacité disponible."""
        if value <= 0:
            raise serializers.ValidationError("La capacité disponible doit être supérieure à 0.")
        if value > 100:  # 100kg max
            raise serializers.ValidationError("La capacité ne peut pas dépasser 100kg.")
        return value
    
    def validate_price_per_kg(self, value):
        """Valider le prix par kg."""
        if value < 0:
            raise serializers.ValidationError("Le prix ne peut pas être négatif.")
        return value
    
    def validate(self, attrs):
        """Validation globale des données de trajet."""
        origin = attrs.get('origin')
        destination = attrs.get('destination')
        
        if origin == destination:
            raise serializers.ValidationError("L'origine et la destination ne peuvent pas être identiques.")
        
        return attrs


class TripDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour les trajets."""
    
    traveler = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    transport_type_display = serializers.CharField(source='get_transport_type_display', read_only=True)
    documents = serializers.SerializerMethodField()
    earnings = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Trip
        fields = [
            'id', 'traveler', 'origin', 'destination', 'departure_date',
            'arrival_date', 'transport_type', 'transport_type_display',
            'available_capacity', 'price_per_kg', 'status', 'status_display',
            'description', 'special_requirements', 'earnings', 'rating',
            'created_at', 'updated_at', 'documents'
        ]
        read_only_fields = [
            'id', 'traveler', 'status', 'earnings', 'rating',
            'created_at', 'updated_at'
        ]
    
    def get_documents(self, obj):
        """Récupérer les documents du trajet."""
        documents = TripDocument.objects.filter(trip=obj)
        return TripDocumentSerializer(documents, many=True).data


class TripStatusSerializer(serializers.ModelSerializer):
    """Serializer pour le statut des trajets."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    days_until_departure = serializers.SerializerMethodField()
    
    class Meta:
        model = Trip
        fields = [
            'id', 'origin', 'destination', 'departure_date', 'arrival_date',
            'status', 'status_display', 'available_capacity', 'days_until_departure'
        ]
        read_only_fields = [
            'id', 'departure_date', 'arrival_date', 'status'
        ]
    
    def get_days_until_departure(self, obj):
        """Calculer les jours jusqu'au départ."""
        if obj.departure_date:
            delta = obj.departure_date - timezone.now().date()
            return delta.days
        return None


class TripDocumentSerializer(serializers.ModelSerializer):
    """Serializer pour les documents de trajet."""
    
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = TripDocument
        fields = [
            'id', 'document_type', 'file', 'file_url', 'file_size',
            'upload_date', 'is_verified', 'verification_date',
            'verification_notes'
        ]
        read_only_fields = [
            'id', 'upload_date', 'is_verified', 'verification_date'
        ]
    
    def get_file_url(self, obj):
        """Obtenir l'URL du fichier."""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_file_size(self, obj):
        """Obtenir la taille du fichier en bytes."""
        if obj.file:
            try:
                return obj.file.size
            except:
                return 0
        return 0
    
    def validate_file(self, value):
        """Valider le fichier uploadé."""
        # Vérifier la taille du fichier (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Le fichier ne doit pas dépasser 10MB.")
        
        # Vérifier le type de fichier
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Type de fichier non autorisé. Utilisez JPEG, PNG, GIF ou PDF.")
        
        return value


class TripMatchSerializer(serializers.Serializer):
    """Serializer pour les matches de trajets."""
    
    id = serializers.IntegerField()
    shipment = serializers.DictField()
    sender = serializers.DictField()
    compatibility_score = serializers.FloatField()
    estimated_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    pickup_date = serializers.DateField()
    
    def to_representation(self, instance):
        """Formater les données de match."""
        return {
            'id': instance.get('id'),
            'shipment': {
                'tracking_number': instance.get('shipment', {}).get('tracking_number'),
                'origin': instance.get('shipment', {}).get('origin'),
                'destination': instance.get('shipment', {}).get('destination'),
                'weight': instance.get('shipment', {}).get('weight'),
                'description': instance.get('shipment', {}).get('description')
            },
            'sender': {
                'id': instance.get('sender', {}).get('id'),
                'name': instance.get('sender', {}).get('name'),
                'rating': instance.get('sender', {}).get('rating')
            },
            'compatibility_score': instance.get('compatibility_score'),
            'estimated_earnings': instance.get('estimated_earnings'),
            'pickup_date': instance.get('pickup_date')
        }


class TripSearchSerializer(serializers.ModelSerializer):
    """Serializer pour la recherche de trajets."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    traveler_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Trip
        fields = [
            'id', 'origin', 'destination', 'departure_date', 'arrival_date',
            'transport_type', 'available_capacity', 'price_per_kg',
            'status', 'status_display', 'traveler_summary'
        ]
    
    def get_traveler_summary(self, obj):
        """Obtenir un résumé du voyageur."""
        return {
            'id': obj.traveler.id,
            'name': f"{obj.traveler.first_name} {obj.traveler.last_name}",
            'rating': getattr(obj.traveler.userprofile, 'rating', 0),
            'total_trips': getattr(obj.traveler.userprofile, 'total_trips', 0)
        }


class TripAnalyticsSerializer(serializers.Serializer):
    """Serializer pour les analytics des trajets."""
    
    total_trips = serializers.IntegerField()
    active_trips = serializers.IntegerField()
    completed_trips = serializers.IntegerField()
    cancelled_trips = serializers.IntegerField()
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_rating = serializers.FloatField()
    total_distance = serializers.FloatField()
    favorite_routes = serializers.ListField()
    
    def to_representation(self, instance):
        """Formater les analytics."""
        return {
            'success': True,
            'analytics': {
                'total_trips': instance.get('total_trips', 0),
                'active_trips': instance.get('active_trips', 0),
                'completed_trips': instance.get('completed_trips', 0),
                'cancelled_trips': instance.get('cancelled_trips', 0),
                'total_earnings': instance.get('total_earnings', 0),
                'average_rating': instance.get('average_rating', 0),
                'total_distance': instance.get('total_distance', 0),
                'favorite_routes': instance.get('favorite_routes', [])
            }
        }


class TripCalendarSerializer(serializers.Serializer):
    """Serializer pour le calendrier des trajets."""
    
    id = serializers.IntegerField()
    title = serializers.CharField()
    date = serializers.DateField()
    status = serializers.CharField()
    available_capacity = serializers.FloatField()
    
    def to_representation(self, instance):
        """Formater les données du calendrier."""
        return {
            'id': instance.get('id'),
            'title': instance.get('title'),
            'date': instance.get('date'),
            'status': instance.get('status'),
            'available_capacity': instance.get('available_capacity')
        }


class TripExportSerializer(serializers.ModelSerializer):
    """Serializer pour l'export des trajets."""
    
    traveler_email = serializers.CharField(source='traveler.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    transport_type_display = serializers.CharField(source='get_transport_type_display', read_only=True)
    
    class Meta:
        model = Trip
        fields = [
            'id', 'traveler_email', 'origin', 'destination',
            'departure_date', 'arrival_date', 'transport_type',
            'transport_type_display', 'available_capacity',
            'price_per_kg', 'status', 'status_display',
            'earnings', 'rating', 'created_at'
        ] 