"""
Serializers for trips app - JSON serialization for trip data according to data dictionary
"""

from rest_framework import serializers
from django.utils import timezone
from django_countries import countries
from users.serializers import UserSerializer
from django.core.validators import MinValueValidator

from .models import Trip, TripDocument


class TripSerializer(serializers.ModelSerializer):
    """Serializer de base pour les trajets."""
    
    traveler = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    origin_country_display = serializers.CharField(source='get_origin_country_display', read_only=True)
    destination_country_display = serializers.CharField(source='get_destination_country_display', read_only=True)
    days_until_departure = serializers.SerializerMethodField()
    route_display = serializers.CharField(source='get_route_display', read_only=True)
    
    class Meta:
        model = Trip
        fields = [
            'id', 'traveler', 'origin_city', 'origin_country', 'origin_country_display',
            'destination_city', 'destination_country', 'destination_country_display',
            'departure_date', 'arrival_date', 'flexible_dates', 'flexibility_days',
            'max_weight', 'remaining_weight', 'max_packages', 'remaining_packages',
            'accepted_package_types', 'min_price_per_kg', 'accepts_fragile',
            'status', 'status_display', 'is_verified', 'notes', 'route_display',
            'days_until_departure', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'traveler', 'status', 'is_verified', 'created_at', 'updated_at',
            'remaining_weight', 'remaining_packages'
        ]
    
    def get_days_until_departure(self, obj):
        """Calculer les jours jusqu'au départ."""
        return obj.days_until_departure


class TripCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de trajets."""
    
    # Champs avec valeurs par défaut
    max_packages = serializers.IntegerField(default=1, required=False)
    accepted_package_types = serializers.ListField(
        child=serializers.ChoiceField(choices=Trip.PACKAGE_TYPE_CHOICES),
        default=['document', 'electronics', 'clothing'],
        required=False
    )
    accepts_fragile = serializers.BooleanField(default=False, required=False)
    flexible_dates = serializers.BooleanField(default=False, required=False)
    flexibility_days = serializers.IntegerField(default=0, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Trip
        fields = [
            'origin_city', 'origin_country', 'destination_city', 'destination_country',
            'departure_date', 'arrival_date', 'flexible_dates', 'flexibility_days',
            'max_weight', 'max_packages', 'accepted_package_types', 'min_price_per_kg',
            'accepts_fragile', 'notes'
        ]
    
    def validate_origin_country(self, value):
        """Valider que l'origine est en Algérie."""
        if value != 'Algeria':
            raise serializers.ValidationError("L'origine doit être en Algérie.")
        return value
    
    def validate_destination_country(self, value):
        """Valider que la destination n'est pas en Algérie."""
        if value == 'Algeria':
            raise serializers.ValidationError("La destination ne peut pas être en Algérie.")
        return value
    
    def validate_departure_date(self, value):
        """Valider la date de départ."""
        if value <= timezone.now():
            raise serializers.ValidationError("La date de départ doit être dans le futur.")
        return value
    
    def validate_arrival_date(self, value):
        """Valider la date d'arrivée."""
        # La validation de la relation entre dates se fait dans validate()
        return value
    
    def validate_max_weight(self, value):
        """Valider le poids maximum."""
        if value <= 0:
            raise serializers.ValidationError("Le poids maximum doit être supérieur à 0.")
        if value > 100:  # 100kg max
            raise serializers.ValidationError("Le poids maximum ne peut pas dépasser 100kg.")
        return value
    
    def validate_max_packages(self, value):
        """Valider le nombre maximum de colis."""
        if value <= 0:
            raise serializers.ValidationError("Le nombre maximum de colis doit être supérieur à 0.")
        if value > 50:  # Limite raisonnable
            raise serializers.ValidationError("Le nombre maximum de colis ne peut pas dépasser 50.")
        return value
    
    def validate_accepted_package_types(self, value):
        """Valider les types de colis acceptés."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Les types de colis acceptés doivent être une liste.")
        
        valid_types = [choice[0] for choice in Trip.PACKAGE_TYPE_CHOICES]
        for package_type in value:
            if package_type not in valid_types:
                raise serializers.ValidationError(f"Type de colis invalide: {package_type}")
        
        return value
    
    def validate_min_price_per_kg(self, value):
        """Valider le prix minimum par kg."""
        if value <= 0:
            raise serializers.ValidationError("Le prix minimum par kg doit être supérieur à 0.")
        if value > 1000:  # Limite raisonnable en DA
            raise serializers.ValidationError("Le prix minimum par kg ne peut pas dépasser 1000 DA.")
        return value
    
    def validate_flexibility_days(self, value):
        """Valider les jours de flexibilité."""
        if value < 0:
            raise serializers.ValidationError("Les jours de flexibilité ne peuvent pas être négatifs.")
        if value > 30:
            raise serializers.ValidationError("Les jours de flexibilité ne peuvent pas dépasser 30.")
        return value
    
    def validate(self, attrs):
        """Validation globale des données de trajet."""
        origin_city = attrs.get('origin_city')
        destination_city = attrs.get('destination_city')
        origin_country = attrs.get('origin_country')
        destination_country = attrs.get('destination_country')
        
        # Vérifier que l'origine et la destination sont différentes
        if origin_city == destination_city and origin_country == destination_country:
            raise serializers.ValidationError("L'origine et la destination ne peuvent pas être identiques.")
        
        # Vérifier la relation entre les dates
        departure_date = attrs.get('departure_date')
        arrival_date = attrs.get('arrival_date')
        
        if departure_date and arrival_date and arrival_date <= departure_date:
            raise serializers.ValidationError("La date d'arrivée doit être après la date de départ.")
        
        # Vérifier que les dates flexibles sont cohérentes
        flexible_dates = attrs.get('flexible_dates', False)
        flexibility_days = attrs.get('flexibility_days', 0)
        
        if flexible_dates and flexibility_days == 0:
            raise serializers.ValidationError("Si les dates sont flexibles, les jours de flexibilité doivent être supérieurs à 0.")
        
        if not flexible_dates and flexibility_days > 0:
            raise serializers.ValidationError("Si les dates ne sont pas flexibles, les jours de flexibilité doivent être 0.")
        
        # Initialiser les champs calculés
        max_weight = attrs.get('max_weight')
        max_packages = attrs.get('max_packages', 1)
        
        if max_weight:
            attrs['remaining_weight'] = max_weight
        if max_packages:
            attrs['remaining_packages'] = max_packages
        
        return attrs


class TripUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour des trajets."""
    
    class Meta:
        model = Trip
        fields = [
            'origin_city', 'origin_country', 'destination_city', 'destination_country',
            'departure_date', 'arrival_date', 'flexible_dates', 'flexibility_days',
            'max_weight', 'max_packages', 'accepted_package_types', 'min_price_per_kg',
            'accepts_fragile', 'notes'
        ]
    
    def validate(self, attrs):
        """Validation pour la mise à jour."""
        # Vérifier que le trajet peut être modifié
        instance = self.instance
        if instance.status not in ['draft', 'active']:
            raise serializers.ValidationError("Seuls les trajets en brouillon ou actifs peuvent être modifiés.")
        
        # Validation spécifique pour la mise à jour
        # Vérifier que l'origine et la destination sont différentes seulement si elles sont modifiées
        origin_city = attrs.get('origin_city', instance.origin_city)
        origin_country = attrs.get('origin_country', instance.origin_country)
        destination_city = attrs.get('destination_city', instance.destination_city)
        destination_country = attrs.get('destination_country', instance.destination_country)
        
        if origin_city == destination_city and origin_country == destination_country:
            raise serializers.ValidationError("L'origine et la destination ne peuvent pas être identiques.")
        
        # Vérifier la relation entre les dates
        departure_date = attrs.get('departure_date', instance.departure_date)
        arrival_date = attrs.get('arrival_date', instance.arrival_date)
        
        if departure_date and arrival_date and arrival_date <= departure_date:
            raise serializers.ValidationError("La date d'arrivée doit être après la date de départ.")
        
        # Vérifier que les dates flexibles sont cohérentes
        flexible_dates = attrs.get('flexible_dates', instance.flexible_dates)
        flexibility_days = attrs.get('flexibility_days', instance.flexibility_days)
        
        if flexible_dates and flexibility_days == 0:
            raise serializers.ValidationError("Si les dates sont flexibles, les jours de flexibilité doivent être supérieurs à 0.")
        
        if not flexible_dates and flexibility_days > 0:
            raise serializers.ValidationError("Si les dates ne sont pas flexibles, les jours de flexibilité doivent être 0.")
        
        return attrs


class TripDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour les trajets."""
    
    traveler = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    origin_country_display = serializers.CharField(source='get_origin_country_display', read_only=True)
    destination_country_display = serializers.CharField(source='get_destination_country_display', read_only=True)
    documents = serializers.SerializerMethodField()
    days_until_departure = serializers.SerializerMethodField()
    route_display = serializers.CharField(source='get_route_display', read_only=True)
    utilization_rate = serializers.FloatField(read_only=True)
    total_weight_carried = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    total_packages_carried = serializers.IntegerField(min_value=0, read_only=True)
    estimated_earnings = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Trip
        fields = [
            'id', 'traveler', 'origin_city', 'origin_country', 'origin_country_display',
            'destination_city', 'destination_country', 'destination_country_display',
            'departure_date', 'arrival_date', 'flexible_dates', 'flexibility_days',
            'max_weight', 'remaining_weight', 'max_packages', 'remaining_packages',
            'accepted_package_types', 'min_price_per_kg', 'accepts_fragile',
            'status', 'status_display', 'is_verified', 'notes', 'route_display',
            'days_until_departure', 'utilization_rate', 'total_weight_carried',
            'total_packages_carried', 'estimated_earnings', 'documents',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'traveler', 'status', 'is_verified', 'created_at', 'updated_at',
            'remaining_weight', 'remaining_packages'
        ]
    
    def get_documents(self, obj):
        """Récupérer les documents du trajet."""
        documents = TripDocument.objects.filter(trip=obj)
        return TripDocumentSerializer(documents, many=True, context=self.context).data
    
    def get_days_until_departure(self, obj):
        """Calculer les jours jusqu'au départ."""
        return obj.days_until_departure


class TripStatusSerializer(serializers.ModelSerializer):
    """Serializer pour le statut des trajets."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    days_until_departure = serializers.SerializerMethodField()
    route_display = serializers.CharField(source='get_route_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Trip
        fields = [
            'id', 'origin_city', 'destination_city', 'route_display',
            'departure_date', 'arrival_date', 'status', 'status_display', 
            'remaining_weight', 'remaining_packages', 'days_until_departure',
            'is_active', 'is_verified'
        ]
        read_only_fields = [
            'id', 'departure_date', 'arrival_date', 'status', 'is_verified'
        ]
    
    def get_days_until_departure(self, obj):
        """Calculer les jours jusqu'au départ."""
        return obj.days_until_departure


class TripDocumentSerializer(serializers.ModelSerializer):
    """Serializer pour les documents de trajet."""
    
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    
    class Meta:
        model = TripDocument
        fields = [
            'id', 'document_type', 'document_type_display', 'file', 'file_url', 'file_size',
            'is_verified', 'verification_date', 'verification_notes', 'uploaded_at'
        ]
        read_only_fields = [
            'id', 'uploaded_at', 'is_verified', 'verification_date'
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


class TripDocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de documents de trajet."""
    
    class Meta:
        model = TripDocument
        fields = ['document_type', 'file']
    
    def validate_file(self, value):
        """Valider le fichier uploadé."""
        # Vérifier la taille du fichier (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Le fichier ne doit pas dépasser 10MB.")
        
        # Vérifier le type de fichier
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
        if hasattr(value, 'content_type') and value.content_type not in allowed_types:
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
                'origin_city': instance.get('shipment', {}).get('origin_city'),
                'destination_city': instance.get('shipment', {}).get('destination_city'),
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
    route_display = serializers.CharField(source='get_route_display', read_only=True)
    days_until_departure = serializers.SerializerMethodField()
    
    class Meta:
        model = Trip
        fields = [
            'id', 'origin_city', 'destination_city', 'route_display',
            'departure_date', 'arrival_date', 'remaining_weight', 'remaining_packages',
            'min_price_per_kg', 'status', 'status_display', 'traveler_summary',
            'days_until_departure', 'accepts_fragile', 'accepted_package_types'
        ]
    
    def get_traveler_summary(self, obj):
        """Obtenir un résumé du voyageur."""
        return {
            'id': obj.traveler.id,
            'name': f"{obj.traveler.first_name} {obj.traveler.last_name}",
            'rating': getattr(obj.traveler, 'rating', 0),
            'total_trips': getattr(obj.traveler, 'total_trips', 0)
        }
    
    def get_days_until_departure(self, obj):
        """Calculer les jours jusqu'au départ."""
        return obj.days_until_departure


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
    remaining_weight = serializers.FloatField()
    remaining_packages = serializers.IntegerField()
    
    def to_representation(self, instance):
        """Formater les données du calendrier."""
        return {
            'id': instance.get('id'),
            'title': instance.get('title'),
            'date': instance.get('date'),
            'status': instance.get('status'),
            'remaining_weight': instance.get('remaining_weight'),
            'remaining_packages': instance.get('remaining_packages')
        }


class TripExportSerializer(serializers.ModelSerializer):
    """Serializer pour l'export des trajets."""
    
    traveler_email = serializers.CharField(source='traveler.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    origin_country_display = serializers.CharField(source='get_origin_country_display', read_only=True)
    destination_country_display = serializers.CharField(source='get_destination_country_display', read_only=True)
    route_display = serializers.CharField(source='get_route_display', read_only=True)
    
    class Meta:
        model = Trip
        fields = [
            'id', 'traveler_email', 'origin_city', 'origin_country', 'origin_country_display',
            'destination_city', 'destination_country', 'destination_country_display',
            'route_display', 'departure_date', 'arrival_date', 'flexible_dates',
            'flexibility_days', 'max_weight', 'remaining_weight', 'max_packages',
            'remaining_packages', 'accepted_package_types', 'min_price_per_kg',
            'accepts_fragile', 'status', 'status_display', 'is_verified',
            'estimated_earnings', 'notes', 'created_at'
        ]


class TripCapacityUpdateSerializer(serializers.Serializer):
    """Serializer pour la mise à jour de la capacité d'un trajet."""
    
    remaining_weight = serializers.DecimalField(
        max_digits=8, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    remaining_packages = serializers.IntegerField(
        validators=[MinValueValidator(1)]
    )
    
    def validate(self, attrs):
        """Validation de la capacité."""
        instance = self.instance
        if instance:
            # Vérifier que la nouvelle capacité ne dépasse pas le maximum
            if attrs.get('remaining_weight', 0) > instance.max_weight:
                raise serializers.ValidationError(
                    f"Le poids restant ne peut pas dépasser {instance.max_weight} kg."
                )
            
            if attrs.get('remaining_packages', 0) > instance.max_packages:
                raise serializers.ValidationError(
                    f"Le nombre de colis restants ne peut pas dépasser {instance.max_packages}."
                )
        
        return attrs 