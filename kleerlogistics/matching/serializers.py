"""
Serializers for matching app - JSON serialization for matching data
"""

from rest_framework import serializers
from django.utils import timezone

from .models import Match, MatchingPreferences


class MatchSerializer(serializers.ModelSerializer):
    """Serializer pour les matches."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    shipment_summary = serializers.SerializerMethodField()
    trip_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Match
        fields = [
            'id', 'shipment', 'trip', 'compatibility_score',
            'status', 'status_display', 'created_at', 'accepted_at',
            'rejected_at', 'shipment_summary', 'trip_summary'
        ]
        read_only_fields = [
            'id', 'compatibility_score', 'created_at', 'accepted_at', 'rejected_at'
        ]
    
    def get_shipment_summary(self, obj):
        """Obtenir un résumé de l'envoi."""
        if obj.shipment:
            return {
                'id': obj.shipment.id,
                'tracking_number': obj.shipment.tracking_number,
                'origin': obj.shipment.origin,
                'destination': obj.shipment.destination,
                'weight': obj.shipment.weight,
                'status': obj.shipment.status
            }
        return None
    
    def get_trip_summary(self, obj):
        """Obtenir un résumé du trajet."""
        if obj.trip:
            return {
                'id': obj.trip.id,
                'origin': obj.trip.origin,
                'destination': obj.trip.destination,
                'departure_date': obj.trip.departure_date,
                'available_capacity': obj.trip.available_capacity,
                'status': obj.trip.status
            }
        return None


class MatchResultSerializer(serializers.Serializer):
    """Serializer pour les résultats de matching."""
    
    id = serializers.IntegerField()
    compatibility_score = serializers.FloatField()
    estimated_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    estimated_delivery = serializers.DateField()
    
    def to_representation(self, instance):
        """Formater les résultats de matching."""
        return {
            'id': instance.get('id'),
            'compatibility_score': instance.get('compatibility_score'),
            'estimated_cost': instance.get('estimated_cost'),
            'estimated_delivery': instance.get('estimated_delivery')
        }


class MatchingPreferencesSerializer(serializers.ModelSerializer):
    """Serializer pour les préférences de matching."""
    
    class Meta:
        model = MatchingPreferences
        fields = [
            'max_distance', 'min_rating', 'max_price_per_kg',
            'preferred_transport_types', 'flexible_dates',
            'accepts_fragile', 'accepts_urgent', 'notifications_enabled'
        ]
    
    def validate_max_distance(self, value):
        """Valider la distance maximale."""
        if value < 0:
            raise serializers.ValidationError("La distance ne peut pas être négative.")
        if value > 10000:  # 10,000 km max
            raise serializers.ValidationError("La distance maximale ne peut pas dépasser 10,000 km.")
        return value
    
    def validate_min_rating(self, value):
        """Valider la note minimale."""
        if value < 0 or value > 5:
            raise serializers.ValidationError("La note doit être entre 0 et 5.")
        return value
    
    def validate_max_price_per_kg(self, value):
        """Valider le prix maximum par kg."""
        if value < 0:
            raise serializers.ValidationError("Le prix ne peut pas être négatif.")
        return value


class MatchingAlgorithmSerializer(serializers.Serializer):
    """Serializer pour les paramètres de l'algorithme de matching."""
    
    type = serializers.ChoiceField(choices=['shipment', 'trip'])
    item_id = serializers.IntegerField()
    max_results = serializers.IntegerField(default=10, min_value=1, max_value=50)
    min_score = serializers.FloatField(default=0.5, min_value=0.0, max_value=1.0)
    
    def validate(self, attrs):
        """Validation globale."""
        if attrs['max_results'] > 50:
            raise serializers.ValidationError("Le nombre maximum de résultats ne peut pas dépasser 50.")
        return attrs


class MatchAcceptSerializer(serializers.Serializer):
    """Serializer pour accepter un match."""
    
    match_id = serializers.IntegerField()
    message = serializers.CharField(max_length=500, required=False)
    
    def validate_match_id(self, value):
        """Valider l'ID du match."""
        if value <= 0:
            raise serializers.ValidationError("ID de match invalide.")
        return value


class MatchRejectSerializer(serializers.Serializer):
    """Serializer pour rejeter un match."""
    
    match_id = serializers.IntegerField()
    reason = serializers.CharField(max_length=500, required=False)
    
    def validate_match_id(self, value):
        """Valider l'ID du match."""
        if value <= 0:
            raise serializers.ValidationError("ID de match invalide.")
        return value


class MatchingAnalyticsSerializer(serializers.Serializer):
    """Serializer pour les analytics de matching."""
    
    total_matches = serializers.IntegerField()
    accepted_matches = serializers.IntegerField()
    rejected_matches = serializers.IntegerField()
    pending_matches = serializers.IntegerField()
    average_compatibility_score = serializers.FloatField()
    success_rate = serializers.FloatField()
    
    def to_representation(self, instance):
        """Formater les analytics."""
        return {
            'success': True,
            'analytics': {
                'total_matches': instance.get('total_matches', 0),
                'accepted_matches': instance.get('accepted_matches', 0),
                'rejected_matches': instance.get('rejected_matches', 0),
                'pending_matches': instance.get('pending_matches', 0),
                'average_compatibility_score': instance.get('average_compatibility_score', 0),
                'success_rate': instance.get('success_rate', 0)
            }
        }


class MatchingNotificationSerializer(serializers.Serializer):
    """Serializer pour les notifications de matching."""
    
    id = serializers.IntegerField()
    type = serializers.CharField()
    title = serializers.CharField()
    message = serializers.CharField()
    created_at = serializers.DateTimeField()
    read = serializers.BooleanField()
    
    def to_representation(self, instance):
        """Formater les notifications."""
        return {
            'id': instance.get('id'),
            'type': instance.get('type'),
            'title': instance.get('title'),
            'message': instance.get('message'),
            'created_at': instance.get('created_at'),
            'read': instance.get('read', False)
        }


class MatchExportSerializer(serializers.ModelSerializer):
    """Serializer pour l'export des matches."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    shipment_tracking = serializers.CharField(source='shipment.tracking_number', read_only=True)
    trip_id = serializers.IntegerField(source='trip.id', read_only=True)
    
    class Meta:
        model = Match
        fields = [
            'id', 'compatibility_score', 'status', 'status_display',
            'created_at', 'accepted_at', 'rejected_at',
            'shipment_tracking', 'trip_id'
        ] 