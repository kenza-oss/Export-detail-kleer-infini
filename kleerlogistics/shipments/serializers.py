"""
Serializers for shipments app - JSON serialization for shipping data
"""

from rest_framework import serializers
from django.utils import timezone
from users.serializers import UserSerializer

from .models import Shipment, ShipmentTracking, Package, ShipmentDocument, ShipmentRating
from .models import DeliveryOTP


class ShipmentSerializer(serializers.ModelSerializer):
    """Serializer de base pour les envois."""
    
    sender = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    package_type_display = serializers.CharField(source='get_package_type_display', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = Shipment
        fields = [
            'id', 'tracking_number', 'sender', 'origin_city', 'destination_city',
            'weight', 'dimensions', 'description', 'package_type', 'package_type_display',
            'price', 'status', 'status_display', 'urgency', 'urgency_display',
            'payment_method', 'payment_method_display', 'is_paid',
            'created_at', 'updated_at', 'preferred_pickup_date', 'max_delivery_date'
        ]
        read_only_fields = [
            'id', 'tracking_number', 'sender', 'status', 'is_paid',
            'created_at', 'updated_at'
        ]


class ShipmentCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'envois."""
    
    class Meta:
        model = Shipment
        fields = [
            'origin_city', 'destination_city', 'weight', 'dimensions',
            'description', 'package_type', 'price', 'value', 'is_fragile',
            'origin_address', 'destination_country', 'destination_address',
            'recipient_name', 'recipient_phone', 'recipient_email',
            'preferred_pickup_date', 'max_delivery_date', 'urgency',
            'special_instructions', 'insurance_requested', 'payment_method'
        ]
    
    def validate_weight(self, value):
        """Valider le poids du colis."""
        if value <= 0:
            raise serializers.ValidationError("Le poids doit être supérieur à 0.")
        if value > 50:  # 50kg max
            raise serializers.ValidationError("Le poids ne peut pas dépasser 50kg.")
        return value
    
    def validate_price(self, value):
        """Valider le prix de livraison."""
        if value and value < 0:
            raise serializers.ValidationError("Le prix de livraison ne peut pas être négatif.")
        return value
    
    def validate(self, attrs):
        """Validation globale des données d'envoi."""
        origin_city = attrs.get('origin_city')
        destination_city = attrs.get('destination_city')
        
        if origin_city == destination_city:
            raise serializers.ValidationError("L'origine et la destination ne peuvent pas être identiques.")
        
        return attrs


class ShipmentDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour les envois."""
    
    sender = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    package_type_display = serializers.CharField(source='get_package_type_display', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    tracking_events = serializers.SerializerMethodField()
    
    class Meta:
        model = Shipment
        fields = [
            'id', 'tracking_number', 'sender', 'origin_city', 'origin_address',
            'destination_city', 'destination_country', 'destination_address',
            'weight', 'dimensions', 'description', 'package_type',
            'package_type_display', 'value', 'is_fragile', 'price', 'status',
            'status_display', 'urgency', 'urgency_display', 'is_paid',
            'payment_method', 'payment_method_display', 'recipient_name',
            'recipient_phone', 'recipient_email', 'preferred_pickup_date',
            'max_delivery_date', 'special_instructions', 'insurance_requested',
            'otp_code', 'otp_generated_at', 'created_at', 'updated_at',
            'tracking_events'
        ]
        read_only_fields = [
            'id', 'tracking_number', 'sender', 'status', 'is_paid',
            'otp_code', 'otp_generated_at', 'created_at', 'updated_at'
        ]
    
    def get_tracking_events(self, obj):
        """Récupérer les événements de suivi."""
        events = ShipmentTracking.objects.filter(shipment=obj).order_by('-timestamp')
        return ShipmentTrackingSerializer(events, many=True).data


class ShipmentStatusSerializer(serializers.ModelSerializer):
    """Serializer pour le statut des envois."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    package_type_display = serializers.CharField(source='get_package_type_display', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    estimated_delivery = serializers.SerializerMethodField()
    
    class Meta:
        model = Shipment
        fields = [
            'tracking_number', 'status', 'status_display', 'package_type',
            'package_type_display', 'urgency', 'urgency_display',
            'created_at', 'updated_at', 'max_delivery_date',
            'estimated_delivery'
        ]
        read_only_fields = [
            'tracking_number', 'status', 'created_at', 'updated_at'
        ]
    
    def get_estimated_delivery(self, obj):
        """Calculer la date de livraison estimée."""
        if obj.max_delivery_date:
            return obj.max_delivery_date.strftime('%Y-%m-%d')
        return None


class ShipmentTrackingSerializer(serializers.ModelSerializer):
    """Serializer pour les événements de suivi."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    
    class Meta:
        model = ShipmentTracking
        fields = [
            'id', 'status', 'status_display', 'event_type', 'event_type_display', 'description',
            'location', 'timestamp', 'created_by'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def validate_status(self, value):
        """Valider le statut de suivi."""
        valid_statuses = [choice[0] for choice in ShipmentTracking.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError("Statut de suivi invalide.")
        return value
    
    def validate_event_type(self, value):
        """Valider le type d'événement."""
        valid_event_types = [choice[0] for choice in ShipmentTracking.EVENT_TYPE_CHOICES]
        if value not in valid_event_types:
            raise serializers.ValidationError("Type d'événement invalide.")
        return value


class ShipmentMatchSerializer(serializers.Serializer):
    """Serializer pour les matches d'envois."""
    
    id = serializers.IntegerField()
    traveler = serializers.DictField()
    trip = serializers.DictField()
    compatibility_score = serializers.FloatField()
    estimated_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    estimated_delivery = serializers.DateField()
    match_factors = serializers.DictField()
    
    def to_representation(self, instance):
        """Représentation personnalisée du match."""
        return {
            'id': instance.id,
            'traveler': {
                'id': instance.trip.traveler.id,
                'name': f"{instance.trip.traveler.first_name} {instance.trip.traveler.last_name}",
                'rating': instance.trip.traveler.rating,
                'total_trips': instance.trip.traveler.total_trips
            },
            'trip': {
                'id': instance.trip.id,
                'origin': instance.trip.origin_city,
                'destination': instance.trip.destination_city,
                'departure_date': instance.trip.departure_date.strftime('%Y-%m-%d'),
                'arrival_date': instance.trip.arrival_date.strftime('%Y-%m-%d'),
                'remaining_weight': instance.trip.remaining_weight
            },
            'compatibility_score': instance.compatibility_score,
            'estimated_cost': instance.proposed_price,
            'estimated_delivery': instance.trip.arrival_date.strftime('%Y-%m-%d'),
            'match_factors': instance.matching_factors
        }


class ShipmentPaymentSerializer(serializers.ModelSerializer):
    """Serializer pour les informations de paiement."""
    
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = Shipment
        fields = [
            'tracking_number', 'price', 'is_paid',
            'payment_method', 'payment_method_display'
        ]
        read_only_fields = ['tracking_number']
    
    def to_representation(self, instance):
        """Représentation personnalisée du paiement."""
        return {
            'tracking_number': instance.tracking_number,
            'price': instance.price,
            'is_paid': instance.is_paid,
            'payment_method': instance.payment_method,
            'payment_method_display': instance.get_payment_method_display() if instance.payment_method else None,
            'payment_status': 'paid' if instance.is_paid else 'pending'
        }


class ShipmentOTPSerializer(serializers.Serializer):
    """Serializer pour la gestion des OTP de livraison."""
    
    otp = serializers.CharField(max_length=6, min_length=6)
    
    def validate_otp(self, value):
        """Valider le format de l'OTP."""
        if not value.isdigit():
            raise serializers.ValidationError("L'OTP doit contenir uniquement des chiffres.")
        return value


class ShipmentSearchSerializer(serializers.ModelSerializer):
    """Serializer pour la recherche d'envois."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    package_type_display = serializers.CharField(source='get_package_type_display', read_only=True)
    sender_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Shipment
        fields = [
            'id', 'tracking_number', 'origin_city', 'destination_city',
            'status', 'status_display', 'package_type', 'package_type_display',
            'weight', 'price', 'created_at', 'sender_summary'
        ]
    
    def get_sender_summary(self, obj):
        """Résumé de l'expéditeur."""
        return {
            'id': obj.sender.id,
            'name': f"{obj.sender.first_name} {obj.sender.last_name}",
            'rating': obj.sender.rating
        }


class ShipmentAnalyticsSerializer(serializers.Serializer):
    """Serializer pour les analytics des envois."""
    
    total_shipments = serializers.IntegerField()
    pending_shipments = serializers.IntegerField()
    in_transit_shipments = serializers.IntegerField()
    delivered_shipments = serializers.IntegerField()
    cancelled_shipments = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_delivery_time = serializers.FloatField()
    
    def to_representation(self, instance):
        """Représentation personnalisée des analytics."""
        return {
            'total_shipments': instance.get('total_shipments', 0),
            'pending_shipments': instance.get('pending_shipments', 0),
            'in_transit_shipments': instance.get('in_transit_shipments', 0),
            'delivered_shipments': instance.get('delivered_shipments', 0),
            'cancelled_shipments': instance.get('cancelled_shipments', 0),
            'total_revenue': instance.get('total_revenue', 0.00),
            'average_delivery_time': instance.get('average_delivery_time', 0.0),
            'delivery_success_rate': (
                instance.get('delivered_shipments', 0) / 
                max(instance.get('total_shipments', 1), 1) * 100
            )
        }


class ShipmentExportSerializer(serializers.ModelSerializer):
    """Serializer pour l'export des envois."""
    
    sender_email = serializers.CharField(source='sender.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    package_type_display = serializers.CharField(source='get_package_type_display', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = Shipment
        fields = [
            'tracking_number', 'sender_email', 'origin_city', 'destination_city',
            'status', 'status_display', 'package_type', 'package_type_display',
            'weight', 'price', 'urgency', 'urgency_display', 'is_paid',
            'payment_method', 'payment_method_display', 'created_at',
            'preferred_pickup_date', 'max_delivery_date'
        ]


class PackageSerializer(serializers.ModelSerializer):
    """Serializer pour les détails des colis."""
    
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    volume_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Package
        fields = [
            'id', 'category', 'category_display', 'length', 'width', 'height',
            'volume', 'volume_formatted', 'requires_special_handling',
            'is_hazardous', 'temperature_sensitive', 'min_temperature',
            'max_temperature', 'handling_instructions', 'storage_requirements',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'volume', 'created_at', 'updated_at']
    
    def get_volume_formatted(self, obj):
        """Formater le volume pour l'affichage."""
        if obj.volume:
            return f"{obj.volume:.2f} cm³"
        return None
    
    def validate(self, attrs):
        """Validation des dimensions du colis."""
        length = attrs.get('length', 0)
        width = attrs.get('width', 0)
        height = attrs.get('height', 0)
        
        if length <= 0 or width <= 0 or height <= 0:
            raise serializers.ValidationError("Toutes les dimensions doivent être positives.")
        
        # Vérifier les limites maximales
        max_dimension = 200  # 200cm max
        if length > max_dimension or width > max_dimension or height > max_dimension:
            raise serializers.ValidationError(f"Aucune dimension ne peut dépasser {max_dimension}cm.")
        
        return attrs


class PackageCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de détails de colis."""
    
    class Meta:
        model = Package
        fields = [
            'category', 'length', 'width', 'height', 'requires_special_handling',
            'is_hazardous', 'temperature_sensitive', 'min_temperature',
            'max_temperature', 'handling_instructions', 'storage_requirements'
        ]
    
    def validate_temperature_range(self, attrs):
        """Valider la plage de température."""
        min_temp = attrs.get('min_temperature')
        max_temp = attrs.get('max_temperature')
        
        if min_temp and max_temp and min_temp >= max_temp:
            raise serializers.ValidationError("La température minimale doit être inférieure à la température maximale.")
        
        return attrs


class ShipmentDocumentSerializer(serializers.ModelSerializer):
    """Serializer pour les documents d'envoi."""
    
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    file_size_formatted = serializers.SerializerMethodField()
    verified_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ShipmentDocument
        fields = [
            'id', 'document_type', 'document_type_display', 'title', 'file',
            'description', 'file_size', 'file_size_formatted', 'mime_type',
            'is_verified', 'verified_by', 'verified_by_name', 'verified_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_size', 'mime_type', 'is_verified', 'verified_by',
            'verified_at', 'created_at', 'updated_at'
        ]
    
    def get_file_size_formatted(self, obj):
        """Formater la taille du fichier."""
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return None
    
    def get_verified_by_name(self, obj):
        """Nom de l'utilisateur qui a vérifié le document."""
        if obj.verified_by:
            return f"{obj.verified_by.first_name} {obj.verified_by.last_name}"
        return None


class ShipmentDocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de documents d'envoi."""
    
    class Meta:
        model = ShipmentDocument
        fields = [
            'document_type', 'title', 'file', 'description'
        ]
    
    def validate_file(self, value):
        """Valider le fichier uploadé."""
        # Vérifier la taille du fichier (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError("Le fichier ne peut pas dépasser 10MB.")
        
        # Vérifier le type de fichier
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
        file_extension = value.name.lower().split('.')[-1]
        if file_extension not in [ext[1:] for ext in allowed_extensions]:
            raise serializers.ValidationError(
                f"Type de fichier non autorisé. Types acceptés: {', '.join(allowed_extensions)}"
            )
        
        return value


class ShipmentRatingSerializer(serializers.ModelSerializer):
    """Serializer pour les évaluations d'envois."""
    
    rater_name = serializers.SerializerMethodField()
    average_rating = serializers.FloatField(read_only=True)
    
    class Meta:
        model = ShipmentRating
        fields = [
            'id', 'rater', 'rater_name', 'overall_rating', 'delivery_speed',
            'package_condition', 'communication', 'comment', 'is_public',
            'average_rating', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'rater', 'created_at', 'updated_at']
    
    def get_rater_name(self, obj):
        """Nom de l'évaluateur."""
        return f"{obj.rater.first_name} {obj.rater.last_name}"
    
    def validate_overall_rating(self, value):
        """Valider la note globale."""
        if value < 1 or value > 5:
            raise serializers.ValidationError("La note globale doit être entre 1 et 5.")
        return value
    
    def validate(self, attrs):
        """Validation globale de l'évaluation."""
        # Vérifier que toutes les notes sont cohérentes
        ratings = [
            attrs.get('overall_rating', 0),
            attrs.get('delivery_speed', 0),
            attrs.get('package_condition', 0),
            attrs.get('communication', 0)
        ]
        
        if any(rating < 1 or rating > 5 for rating in ratings):
            raise serializers.ValidationError("Toutes les notes doivent être entre 1 et 5.")
        
        return attrs


class ShipmentRatingCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'évaluations d'envois."""
    
    class Meta:
        model = ShipmentRating
        fields = [
            'overall_rating', 'delivery_speed', 'package_condition',
            'communication', 'comment', 'is_public'
        ]
    
    def validate(self, attrs):
        """Validation de l'évaluation."""
        # Vérifier que l'utilisateur n'a pas déjà évalué cet envoi
        request = self.context.get('request')
        if request and request.user:
            shipment_id = self.context.get('shipment_id')
            if ShipmentRating.objects.filter(
                shipment_id=shipment_id, 
                rater=request.user
            ).exists():
                raise serializers.ValidationError("Vous avez déjà évalué cet envoi.")
        
        return attrs


class ShipmentWithDetailsSerializer(ShipmentDetailSerializer):
    """Serializer complet avec tous les détails de l'envoi."""
    
    package_details = PackageSerializer(source='package_details', read_only=True)
    documents = ShipmentDocumentSerializer(source='documents', many=True, read_only=True)
    rating = ShipmentRatingSerializer(source='rating', read_only=True)
    
    class Meta(ShipmentDetailSerializer.Meta):
        fields = ShipmentDetailSerializer.Meta.fields + [
            'package_details', 'documents', 'rating'
        ] 


class DeliveryOTPSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les OTP de livraison."""
    
    time_remaining_minutes = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = DeliveryOTP
        fields = [
            'id', 'shipment', 'otp_code', 'recipient_phone', 'recipient_name',
            'generated_by', 'created_at', 'expires_at', 'is_used', 'verified_at',
            'verified_by', 'sms_sent', 'sms_sent_at', 'sms_delivery_status',
            'time_remaining_minutes', 'is_valid'
        ]
        read_only_fields = [
            'id', 'shipment', 'otp_code', 'recipient_phone', 'recipient_name',
            'generated_by', 'created_at', 'expires_at', 'verified_at', 'verified_by',
            'sms_sent', 'sms_sent_at', 'sms_delivery_status', 'time_remaining_minutes', 'is_valid'
        ]
    
    def get_time_remaining_minutes(self, obj):
        """Retourne le temps restant en minutes."""
        return obj.time_remaining
    
    def get_is_valid(self, obj):
        """Retourne si l'OTP est valide."""
        return obj.is_valid


class DeliveryOTPStatusSerializer(serializers.Serializer):
    """Sérialiseur pour le statut de l'OTP de livraison."""
    
    has_active_otp = serializers.BooleanField()
    has_used_otp = serializers.BooleanField()
    otp_generated_at = serializers.DateTimeField(allow_null=True)
    otp_expires_at = serializers.DateTimeField(allow_null=True)
    otp_verified_at = serializers.DateTimeField(allow_null=True)
    time_remaining_minutes = serializers.IntegerField(allow_null=True)
    recipient_name = serializers.CharField()
    recipient_phone = serializers.CharField()


class DeliveryOTPVerifySerializer(serializers.Serializer):
    """Sérialiseur pour la vérification de l'OTP de livraison."""
    
    otp_code = serializers.CharField(
        max_length=6,
        min_length=6,
        help_text="Code OTP à 6 chiffres fourni par le destinataire"
    )
    
    def validate_otp_code(self, value):
        """Valider le format de l'OTP."""
        if not value.isdigit():
            raise serializers.ValidationError("Le code OTP doit contenir uniquement des chiffres.")
        if len(value) != 6:
            raise serializers.ValidationError("Le code OTP doit contenir exactement 6 chiffres.")
        return value


class DeliveryInfoSerializer(serializers.Serializer):
    """Sérialiseur pour les informations de livraison."""
    
    delivery_date = serializers.DateTimeField()
    recipient_name = serializers.CharField()
    payment_released = serializers.BooleanField()
    amount_released = serializers.DecimalField(max_digits=10, decimal_places=2)


class InitiateDeliverySerializer(serializers.Serializer):
    """Sérialiseur pour l'initiation du processus de livraison."""
    
    # Aucun champ requis, juste une confirmation
    pass


class ResendDeliveryOTPSerializer(serializers.Serializer):
    """Sérialiseur pour le renvoi de l'OTP de livraison."""
    
    # Aucun champ requis, juste une demande de renvoi
    pass 