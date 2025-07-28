"""
Serializers for analytics app - JSON serialization for analytics data
"""

from rest_framework import serializers
from django.utils import timezone

from .models import AnalyticsEvent, DashboardMetric


class AnalyticsEventSerializer(serializers.ModelSerializer):
    """Serializer pour les événements d'analytics."""
    
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    
    class Meta:
        model = AnalyticsEvent
        fields = [
            'id', 'user', 'event_type', 'event_type_display',
            'event_data', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class DashboardMetricSerializer(serializers.ModelSerializer):
    """Serializer pour les métriques du tableau de bord."""
    
    class Meta:
        model = DashboardMetric
        fields = [
            'id', 'metric_name', 'metric_value', 'metric_type',
            'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DashboardAnalyticsSerializer(serializers.Serializer):
    """Serializer pour les analytics du tableau de bord."""
    
    general = serializers.DictField()
    shipments = serializers.DictField()
    trips = serializers.DictField()
    financial = serializers.DictField()
    charts = serializers.DictField()
    
    def to_representation(self, instance):
        """Formater les analytics du tableau de bord."""
        return {
            'success': True,
            'analytics': {
                'general': instance.get('general', {}),
                'shipments': instance.get('shipments', {}),
                'trips': instance.get('trips', {}),
                'financial': instance.get('financial', {}),
                'charts': instance.get('charts', {})
            }
        }


class ShipmentAnalyticsSerializer(serializers.Serializer):
    """Serializer pour les analytics des envois."""
    
    total_shipments = serializers.IntegerField()
    shipments_by_status = serializers.ListField()
    shipments_by_month = serializers.ListField()
    top_destinations = serializers.ListField()
    revenue_analysis = serializers.DictField()
    delivery_performance = serializers.DictField()
    
    def to_representation(self, instance):
        """Formater les analytics des envois."""
        return {
            'success': True,
            'analytics': {
                'total_shipments': instance.get('total_shipments', 0),
                'shipments_by_status': instance.get('shipments_by_status', []),
                'shipments_by_month': instance.get('shipments_by_month', []),
                'top_destinations': instance.get('top_destinations', []),
                'revenue_analysis': instance.get('revenue_analysis', {}),
                'delivery_performance': instance.get('delivery_performance', {})
            }
        }


class TripAnalyticsSerializer(serializers.Serializer):
    """Serializer pour les analytics des trajets."""
    
    total_trips = serializers.IntegerField()
    trips_by_status = serializers.ListField()
    trips_by_month = serializers.ListField()
    top_routes = serializers.ListField()
    earnings_analysis = serializers.DictField()
    performance_metrics = serializers.DictField()
    
    def to_representation(self, instance):
        """Formater les analytics des trajets."""
        return {
            'success': True,
            'analytics': {
                'total_trips': instance.get('total_trips', 0),
                'trips_by_status': instance.get('trips_by_status', []),
                'trips_by_month': instance.get('trips_by_month', []),
                'top_routes': instance.get('top_routes', []),
                'earnings_analysis': instance.get('earnings_analysis', {}),
                'performance_metrics': instance.get('performance_metrics', {})
            }
        }


class FinancialAnalyticsSerializer(serializers.Serializer):
    """Serializer pour les analytics financiers."""
    
    current_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    transaction_summary = serializers.DictField()
    monthly_transactions = serializers.ListField()
    payment_methods = serializers.ListField()
    cash_flow = serializers.DictField()
    
    def to_representation(self, instance):
        """Formater les analytics financiers."""
        return {
            'success': True,
            'analytics': {
                'current_balance': instance.get('current_balance', 0),
                'transaction_summary': instance.get('transaction_summary', {}),
                'monthly_transactions': instance.get('monthly_transactions', []),
                'payment_methods': instance.get('payment_methods', []),
                'cash_flow': instance.get('cash_flow', {})
            }
        }


class AnalyticsEventCreateSerializer(serializers.Serializer):
    """Serializer pour créer un événement d'analytics."""
    
    event_type = serializers.CharField(max_length=50)
    event_data = serializers.DictField(required=False, default=dict)
    
    def validate_event_type(self, value):
        """Valider le type d'événement."""
        valid_types = [
            'page_view', 'button_click', 'form_submit', 'api_call',
            'shipment_created', 'trip_created', 'payment_made',
            'user_login', 'user_logout'
        ]
        if value not in valid_types:
            raise serializers.ValidationError(f"Type d'événement invalide. Types autorisés: {valid_types}")
        return value


class AnalyticsSearchSerializer(serializers.Serializer):
    """Serializer pour la recherche d'analytics."""
    
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    event_type = serializers.CharField(max_length=50, required=False)
    user_id = serializers.IntegerField(required=False)
    
    def validate(self, attrs):
        """Validation globale."""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("La date de début doit être antérieure à la date de fin.")
        
        return attrs


class AnalyticsExportSerializer(serializers.Serializer):
    """Serializer pour l'export des analytics."""
    
    format = serializers.ChoiceField(choices=['json', 'csv', 'xlsx'], default='json')
    date_range = serializers.CharField(max_length=20, required=False)
    metrics = serializers.ListField(child=serializers.CharField(), required=False)
    
    def validate_format(self, value):
        """Valider le format d'export."""
        if value not in ['json', 'csv', 'xlsx']:
            raise serializers.ValidationError("Format d'export non supporté.")
        return value


class AdminAnalyticsSerializer(serializers.Serializer):
    """Serializer pour les analytics admin."""
    
    users = serializers.DictField()
    shipments = serializers.DictField()
    trips = serializers.DictField()
    transactions = serializers.DictField()
    
    def to_representation(self, instance):
        """Formater les analytics admin."""
        return {
            'success': True,
            'analytics': {
                'users': instance.get('users', {}),
                'shipments': instance.get('shipments', {}),
                'trips': instance.get('trips', {}),
                'transactions': instance.get('transactions', {})
            }
        }


class ChartDataSerializer(serializers.Serializer):
    """Serializer pour les données de graphiques."""
    
    labels = serializers.ListField(child=serializers.CharField())
    datasets = serializers.ListField(child=serializers.DictField())
    
    def to_representation(self, instance):
        """Formater les données de graphiques."""
        return {
            'labels': instance.get('labels', []),
            'datasets': instance.get('datasets', [])
        }


class MetricSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé des métriques."""
    
    metric_name = serializers.CharField()
    current_value = serializers.FloatField()
    previous_value = serializers.FloatField()
    change_percentage = serializers.FloatField()
    trend = serializers.CharField()  # 'up', 'down', 'stable'
    
    def to_representation(self, instance):
        """Formater le résumé des métriques."""
        return {
            'metric_name': instance.get('metric_name'),
            'current_value': instance.get('current_value', 0),
            'previous_value': instance.get('previous_value', 0),
            'change_percentage': instance.get('change_percentage', 0),
            'trend': instance.get('trend', 'stable')
        } 