"""
Serializers for matching app - JSON serialization for matching data
Conforme au dictionnaire des données
"""

from rest_framework import serializers
from django.utils import timezone

from .models import Match, MatchingPreferences, MatchingRule


class MatchSerializer(serializers.ModelSerializer):
    """Serializer pour les matches - Conforme au dictionnaire des données."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    shipment_summary = serializers.SerializerMethodField()
    trip_summary = serializers.SerializerMethodField()
    economic_breakdown = serializers.SerializerMethodField()
    otp_info = serializers.SerializerMethodField()
    chat_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Match
        fields = [
            'id', 'shipment', 'trip', 'compatibility_score',
            'proposed_price', 'traveler_earnings', 'commission_amount',
            'packaging_fee', 'service_fee', 'status', 'status_display', 
            'created_at', 'expires_at', 'responded_at', 'accepted_at', 'rejected_at',
            'algorithm_version', 'matching_factors', 'shipment_summary', 'trip_summary',
            'economic_breakdown', 'otp_info', 'chat_info', 'auto_accepted',
            'notification_sent', 'notification_sent_at'
        ]
        read_only_fields = [
            'id', 'compatibility_score', 'created_at', 'responded_at',
            'algorithm_version', 'matching_factors', 'traveler_earnings',
            'commission_amount', 'packaging_fee', 'service_fee', 'accepted_at',
            'rejected_at', 'otp_info', 'chat_info', 'auto_accepted',
            'notification_sent', 'notification_sent_at'
        ]
    
    def get_shipment_summary(self, obj):
        """Obtenir un résumé de l'envoi."""
        if obj.shipment:
            return {
                'id': obj.shipment.id,
                'tracking_number': obj.shipment.tracking_number,
                'origin_city': obj.shipment.origin_city,
                'destination_city': obj.shipment.destination_city,
                'weight': obj.shipment.weight,
                'package_type': obj.shipment.package_type,
                'is_fragile': obj.shipment.is_fragile,
                'urgency': obj.shipment.urgency,
                'status': obj.shipment.status
            }
        return None
    
    def get_trip_summary(self, obj):
        """Obtenir un résumé du trajet."""
        if obj.trip:
            return {
                'id': obj.trip.id,
                'origin_city': obj.trip.origin_city,
                'destination_city': obj.trip.destination_city,
                'departure_date': obj.trip.departure_date,
                'arrival_date': obj.trip.arrival_date,
                'remaining_weight': obj.trip.remaining_weight,
                'remaining_packages': obj.trip.remaining_packages,
                'min_price_per_kg': obj.trip.min_price_per_kg,
                'accepts_fragile': obj.trip.accepts_fragile,
                'accepted_package_types': obj.trip.accepted_package_types,
                'status': obj.trip.status
            }
        return None
    
    def get_economic_breakdown(self, obj):
        """Obtenir la répartition économique."""
        return {
            'total_price': float(obj.proposed_price),
            'traveler_earnings': float(obj.traveler_earnings) if obj.traveler_earnings else 0,
            'commission_amount': float(obj.commission_amount) if obj.commission_amount else 0,
            'packaging_fee': float(obj.packaging_fee),
            'service_fee': float(obj.service_fee),
            'commission_percentage': 25.0,  # 25% par défaut
            'traveler_percentage': 75.0  # 75% par défaut
        }
    
    def get_otp_info(self, obj):
        """Obtenir les informations OTP."""
        if obj.status == 'accepted' and obj.delivery_otp:
            return {
                'otp_code': obj.delivery_otp,
                'generated_at': obj.otp_generated_at,
                'expires_at': obj.otp_expires_at,
                'is_valid': obj.otp_is_valid,
                'delivery_confirmed': obj.delivery_confirmed,
                'delivery_confirmed_at': obj.delivery_confirmed_at
            }
        return None
    
    def get_chat_info(self, obj):
        """Obtenir les informations de chat."""
        if obj.chat_activated:
            return {
                'chat_room_id': str(obj.chat_room_id),
                'activated_at': obj.chat_activated_at,
                'is_active': obj.chat_activated
            }
        return None


class MatchResultSerializer(serializers.Serializer):
    """Serializer pour les résultats de matching."""
    
    id = serializers.IntegerField()
    compatibility_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    proposed_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    traveler_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    commission_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    estimated_delivery = serializers.DateField()
    can_auto_accept = serializers.BooleanField()
    
    def to_representation(self, instance):
        """Formater les résultats de matching."""
        return {
            'id': instance.get('id'),
            'compatibility_score': instance.get('compatibility_score'),
            'proposed_price': instance.get('proposed_price'),
            'traveler_earnings': instance.get('traveler_earnings'),
            'commission_amount': instance.get('commission_amount'),
            'estimated_delivery': instance.get('estimated_delivery'),
            'can_auto_accept': instance.get('can_auto_accept', False)
        }


class MatchAcceptSerializer(serializers.Serializer):
    """Serializer pour accepter un match."""
    
    accepted_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    message = serializers.CharField(max_length=500, required=False)
    auto_accept = serializers.BooleanField(default=False)
    
    def validate_accepted_price(self, value):
        """Valider le prix accepté."""
        if value and value <= 0:
            raise serializers.ValidationError("Le prix doit être positif.")
        return value


class MatchRejectSerializer(serializers.Serializer):
    """Serializer pour rejeter un match."""
    
    reason = serializers.CharField(max_length=200, required=False)
    message = serializers.CharField(max_length=500, required=False)


class MatchingPreferencesSerializer(serializers.ModelSerializer):
    """Serializer pour les préférences de matching."""
    
    class Meta:
        model = MatchingPreferences
        fields = [
            'id', 'auto_accept_threshold', 'notification_enabled', 'min_rating',
            'preferred_cities', 'blacklisted_users', 'response_time_hours',
            'min_price', 'max_price', 'accepts_fragile', 'accepts_urgent',
            'max_distance_km', 'max_price_per_kg', 'preferred_package_types',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MatchingRuleSerializer(serializers.ModelSerializer):
    """Serializer pour les règles de matching."""
    
    class Meta:
        model = MatchingRule
        fields = [
            'id', 'name', 'description', 'min_compatibility_score', 'max_distance_km',
            'max_date_flexibility_days', 'geographic_weight', 'weight_weight',
            'package_type_weight', 'fragility_weight', 'date_weight', 'reputation_weight',
            'enable_auto_acceptance', 'auto_accept_threshold', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MatchingAnalyticsSerializer(serializers.Serializer):
    """Serializer pour les analytics de matching."""
    
    total_matches = serializers.IntegerField()
    accepted_matches = serializers.IntegerField()
    rejected_matches = serializers.IntegerField()
    pending_matches = serializers.IntegerField()
    expired_matches = serializers.IntegerField()
    average_compatibility_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    success_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_commission = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    def to_representation(self, instance):
        """Formater les analytics."""
        return {
            'total_matches': instance.get('total_matches', 0),
            'accepted_matches': instance.get('accepted_matches', 0),
            'rejected_matches': instance.get('rejected_matches', 0),
            'pending_matches': instance.get('pending_matches', 0),
            'expired_matches': instance.get('expired_matches', 0),
            'average_compatibility_score': instance.get('average_compatibility_score', 0),
            'success_rate': instance.get('success_rate', 0),
            'total_earnings': instance.get('total_earnings', 0),
            'total_commission': instance.get('total_commission', 0)
        }


class OTPVerificationSerializer(serializers.Serializer):
    """Serializer pour la vérification OTP."""
    
    otp_code = serializers.CharField(
        max_length=6, 
        min_length=6,
        help_text="Code OTP à 6 chiffres"
    )
    
    def validate_otp_code(self, value):
        """Valider le code OTP."""
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("Le code OTP doit contenir exactement 6 chiffres.")
        return value


class MatchExportSerializer(serializers.ModelSerializer):
    """Serializer pour l'export des matches."""
    
    class Meta:
        model = Match
        fields = [
            'id', 'shipment', 'trip', 'compatibility_score',
            'proposed_price', 'traveler_earnings', 'commission_amount',
            'packaging_fee', 'service_fee', 'status', 'created_at', 
            'expires_at', 'responded_at', 'algorithm_version',
            'delivery_confirmed', 'delivery_confirmed_at'
        ]


class AutomaticMatchingSerializer(serializers.Serializer):
    """Serializer pour le matching automatique."""
    
    type = serializers.ChoiceField(choices=['shipment', 'trip'])
    item_id = serializers.IntegerField()
    auto_accept = serializers.BooleanField(default=False)
    limit = serializers.IntegerField(default=10, min_value=1, max_value=50)
    
    def validate_item_id(self, value):
        """Valider l'ID de l'élément."""
        if value <= 0:
            raise serializers.ValidationError("L'ID doit être positif.")
        return value


class MatchingAlgorithmSerializer(serializers.Serializer):
    """Serializer pour la configuration de l'algorithme de matching."""
    
    geographic_weight = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        min_value=0, 
        max_value=100,
        default=35.00
    )
    weight_weight = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        min_value=0, 
        max_value=100,
        default=20.00
    )
    package_type_weight = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        min_value=0, 
        max_value=100,
        default=15.00
    )
    fragility_weight = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        min_value=0, 
        max_value=100,
        default=10.00
    )
    date_weight = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        min_value=0, 
        max_value=100,
        default=15.00
    )
    reputation_weight = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        min_value=0, 
        max_value=100,
        default=5.00
    )
    
    def validate(self, data):
        """Valider que la somme des poids est égale à 100."""
        total_weight = sum(data.values())
        if abs(total_weight - 100) > 0.01:  # Tolérance pour les erreurs de précision
            raise serializers.ValidationError(
                "La somme des poids doit être égale à 100."
            )
        return data 