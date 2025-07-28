"""
Serializers for shipments app - JSON serialization for shipping data
"""

from rest_framework import serializers
from django.utils import timezone
from users.serializers import UserSerializer

from .models import Shipment, ShipmentTracking


class ShipmentSerializer(serializers.ModelSerializer):
    """Serializer de base pour les envois."""
    
    user = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
    class Meta:
        model = Shipment
        fields = [
            'id', 'tracking_number', 'user', 'origin', 'destination',
            'weight', 'dimensions', 'description', 'package_type',
            'shipping_cost', 'status', 'status_display', 'payment_status',
            'payment_status_display', 'payment_method', 'payment_date',
            'created_at', 'updated_at', 'delivery_date'
        ]
        read_only_fields = [
            'id', 'tracking_number', 'user', 'status', 'payment_status',
            'payment_date', 'created_at', 'updated_at', 'delivery_date'
        ]


class ShipmentCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'envois."""
    
    class Meta:
        model = Shipment
        fields = [
            'origin', 'destination', 'weight', 'dimensions',
            'description', 'package_type', 'shipping_cost',
            'recipient_name', 'recipient_phone', 'recipient_email',
            'special_instructions'
        ]
    
    def validate_weight(self, value):
        """Valider le poids du colis."""
        if value <= 0:
            raise serializers.ValidationError("Le poids doit être supérieur à 0.")
        if value > 50:  # 50kg max
            raise serializers.ValidationError("Le poids ne peut pas dépasser 50kg.")
        return value
    
    def validate_shipping_cost(self, value):
        """Valider le coût de livraison."""
        if value < 0:
            raise serializers.ValidationError("Le coût de livraison ne peut pas être négatif.")
        return value
    
    def validate(self, attrs):
        """Validation globale des données d'envoi."""
        origin = attrs.get('origin')
        destination = attrs.get('destination')
        
        if origin == destination:
            raise serializers.ValidationError("L'origine et la destination ne peuvent pas être identiques.")
        
        return attrs


class ShipmentDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour les envois."""
    
    user = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    package_type_display = serializers.CharField(source='get_package_type_display', read_only=True)
    tracking_events = serializers.SerializerMethodField()
    
    class Meta:
        model = Shipment
        fields = [
            'id', 'tracking_number', 'user', 'origin', 'destination',
            'weight', 'dimensions', 'description', 'package_type',
            'package_type_display', 'shipping_cost', 'status',
            'status_display', 'payment_status', 'payment_status_display',
            'payment_method', 'payment_date', 'recipient_name',
            'recipient_phone', 'recipient_email', 'special_instructions',
            'created_at', 'updated_at', 'delivery_date', 'tracking_events'
        ]
        read_only_fields = [
            'id', 'tracking_number', 'user', 'status', 'payment_status',
            'payment_date', 'created_at', 'updated_at', 'delivery_date'
        ]
    
    def get_tracking_events(self, obj):
        """Récupérer les événements de suivi."""
        events = ShipmentTracking.objects.filter(shipment=obj).order_by('-timestamp')
        return ShipmentTrackingSerializer(events, many=True).data


class ShipmentStatusSerializer(serializers.ModelSerializer):
    """Serializer pour le statut des envois."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    estimated_delivery = serializers.SerializerMethodField()
    
    class Meta:
        model = Shipment
        fields = [
            'tracking_number', 'status', 'status_display',
            'payment_status', 'payment_status_display',
            'created_at', 'updated_at', 'delivery_date',
            'estimated_delivery'
        ]
        read_only_fields = [
            'tracking_number', 'status', 'payment_status',
            'created_at', 'updated_at', 'delivery_date'
        ]
    
    def get_estimated_delivery(self, obj):
        """Calculer la date de livraison estimée."""
        if obj.status == 'delivered':
            return obj.delivery_date
        
        # En production, utiliser un algorithme plus sophistiqué
        if obj.created_at:
            return obj.created_at + timezone.timedelta(days=5)
        return None


class ShipmentTrackingSerializer(serializers.ModelSerializer):
    """Serializer pour les événements de suivi."""
    
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    
    class Meta:
        model = ShipmentTracking
        fields = [
            'id', 'event_type', 'event_type_display', 'description',
            'location', 'timestamp', 'additional_info'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def validate_event_type(self, value):
        """Valider le type d'événement."""
        valid_events = [
            'created', 'picked_up', 'in_transit', 'out_for_delivery',
            'delivered', 'failed_delivery', 'returned', 'cancelled'
        ]
        if value not in valid_events:
            raise serializers.ValidationError(f"Type d'événement invalide. Valeurs autorisées: {valid_events}")
        return value


class ShipmentMatchSerializer(serializers.Serializer):
    """Serializer pour les matches d'envois."""
    
    id = serializers.IntegerField()
    traveler = serializers.DictField()
    trip = serializers.DictField()
    compatibility_score = serializers.FloatField()
    estimated_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    estimated_delivery = serializers.DateField()
    
    def to_representation(self, instance):
        """Formater les données de match."""
        return {
            'id': instance.get('id'),
            'traveler': {
                'id': instance.get('traveler', {}).get('id'),
                'name': instance.get('traveler', {}).get('name'),
                'rating': instance.get('traveler', {}).get('rating'),
                'total_trips': instance.get('traveler', {}).get('total_trips')
            },
            'trip': {
                'id': instance.get('trip', {}).get('id'),
                'origin': instance.get('trip', {}).get('origin'),
                'destination': instance.get('trip', {}).get('destination'),
                'departure_date': instance.get('trip', {}).get('departure_date'),
                'available_capacity': instance.get('trip', {}).get('available_capacity')
            },
            'compatibility_score': instance.get('compatibility_score'),
            'estimated_cost': instance.get('estimated_cost'),
            'estimated_delivery': instance.get('estimated_delivery')
        }


class ShipmentPaymentSerializer(serializers.ModelSerializer):
    """Serializer pour les informations de paiement."""
    
    class Meta:
        model = Shipment
        fields = [
            'tracking_number', 'shipping_cost', 'payment_status',
            'payment_method', 'payment_date'
        ]
        read_only_fields = ['tracking_number', 'payment_date']
    
    def to_representation(self, instance):
        """Formater les informations de paiement."""
        return {
            'shipment_id': instance.id,
            'tracking_number': instance.tracking_number,
            'amount': instance.shipping_cost,
            'currency': 'EUR',
            'status': instance.payment_status,
            'payment_method': instance.payment_method,
            'payment_date': instance.payment_date
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
    user_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Shipment
        fields = [
            'id', 'tracking_number', 'origin', 'destination',
            'weight', 'status', 'status_display', 'created_at',
            'user_summary'
        ]
    
    def get_user_summary(self, obj):
        """Obtenir un résumé de l'utilisateur."""
        return {
            'id': obj.user.id,
            'name': f"{obj.user.first_name} {obj.user.last_name}",
            'email': obj.user.email
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
        """Formater les analytics."""
        return {
            'success': True,
            'analytics': {
                'total_shipments': instance.get('total_shipments', 0),
                'pending_shipments': instance.get('pending_shipments', 0),
                'in_transit_shipments': instance.get('in_transit_shipments', 0),
                'delivered_shipments': instance.get('delivered_shipments', 0),
                'cancelled_shipments': instance.get('cancelled_shipments', 0),
                'total_revenue': instance.get('total_revenue', 0),
                'average_delivery_time': instance.get('average_delivery_time', 0)
            }
        }


class ShipmentExportSerializer(serializers.ModelSerializer):
    """Serializer pour l'export des envois."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
    class Meta:
        model = Shipment
        fields = [
            'tracking_number', 'user_email', 'origin', 'destination',
            'weight', 'dimensions', 'description', 'package_type',
            'shipping_cost', 'status', 'status_display',
            'payment_status', 'payment_status_display',
            'created_at', 'delivery_date'
        ] 