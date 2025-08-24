"""
Serializers for admin_panel app - Dashboard and Analytics for Administrators
"""

from rest_framework import serializers
from .models import (
    DashboardMetric, AdminReport, AdminNotification, 
    SystemHealth, AdminAuditLog
)


class DashboardMetricSerializer(serializers.ModelSerializer):
    """Serializer pour les métriques du tableau de bord."""
    
    metric_type_display = serializers.CharField(source='get_metric_type_display', read_only=True)
    period_type_display = serializers.CharField(source='get_period_type_display', read_only=True)
    trend_direction = serializers.CharField(read_only=True)
    
    class Meta:
        model = DashboardMetric
        fields = [
            'id', 'metric_type', 'metric_type_display', 'period_type', 'period_type_display',
            'period_start', 'period_end', 'value', 'previous_value', 'change_percentage',
            'trend_direction', 'metadata', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AdminReportSerializer(serializers.ModelSerializer):
    """Serializer pour les rapports administratifs."""
    
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    format_display = serializers.CharField(source='get_format_display', read_only=True)
    generated_by_username = serializers.CharField(source='generated_by.username', read_only=True)
    
    class Meta:
        model = AdminReport
        fields = [
            'id', 'name', 'report_type', 'report_type_display', 'format', 'format_display',
            'parameters', 'filters', 'result_data', 'file_path', 'generated_by',
            'generated_by_username', 'generated_at', 'is_scheduled', 'schedule_cron'
        ]
        read_only_fields = ['id', 'generated_at']


class AdminNotificationSerializer(serializers.ModelSerializer):
    """Serializer pour les notifications administratives."""
    
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    recipients_count = serializers.SerializerMethodField()
    read_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminNotification
        fields = [
            'id', 'title', 'message', 'notification_type', 'notification_type_display',
            'priority', 'priority_display', 'recipients', 'recipients_count', 'is_broadcast',
            'is_read', 'read_by', 'read_count', 'read_at', 'action_url', 'action_text',
            'metadata', 'expires_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_recipients_count(self, obj):
        """Retourne le nombre de destinataires."""
        return obj.recipients.count()
    
    def get_read_count(self, obj):
        """Retourne le nombre de lecteurs."""
        return obj.read_by.count()


class SystemHealthSerializer(serializers.ModelSerializer):
    """Serializer pour la santé du système."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = SystemHealth
        fields = [
            'id', 'service_name', 'status', 'status_display', 'response_time',
            'uptime_percentage', 'error_count', 'last_check', 'details'
        ]
        read_only_fields = ['id', 'last_check']


class AdminAuditLogSerializer(serializers.ModelSerializer):
    """Serializer pour les logs d'audit administratifs."""
    
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AdminAuditLog
        fields = [
            'id', 'user', 'user_username', 'action', 'action_display', 'model_name',
            'object_id', 'changes', 'ip_address', 'user_agent', 'session_id',
            'metadata', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


# Sérialiseurs pour les métriques spécifiques
class ShipmentsSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé des envois."""
    
    total_shipments = serializers.IntegerField()
    pending_shipments = serializers.IntegerField()
    in_transit_shipments = serializers.IntegerField()
    delivered_shipments = serializers.IntegerField()
    cancelled_shipments = serializers.IntegerField()
    
    # Statistiques par période
    shipments_today = serializers.IntegerField()
    shipments_this_week = serializers.IntegerField()
    shipments_this_month = serializers.IntegerField()
    
    # Tendances
    growth_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_delivery_time = serializers.DurationField()
    success_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Top destinations
    top_destinations = serializers.ListField(child=serializers.DictField())
    
    # Répartition par type
    shipments_by_type = serializers.DictField()
    shipments_by_status = serializers.DictField()


class PaymentsSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé des paiements."""
    
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_transactions = serializers.IntegerField()
    successful_payments = serializers.IntegerField()
    failed_payments = serializers.IntegerField()
    
    # Statistiques par période
    revenue_today = serializers.DecimalField(max_digits=15, decimal_places=2)
    revenue_this_week = serializers.DecimalField(max_digits=15, decimal_places=2)
    revenue_this_month = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Méthodes de paiement
    payments_by_method = serializers.DictField()
    payments_by_status = serializers.DictField()
    
    # Tendances
    revenue_growth = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_transaction_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Top clients
    top_clients = serializers.ListField(child=serializers.DictField())


class CommissionsSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé des commissions."""
    
    total_commissions = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_commissionable_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    commission_rate_average = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Statistiques par période
    commissions_today = serializers.DecimalField(max_digits=15, decimal_places=2)
    commissions_this_week = serializers.DecimalField(max_digits=15, decimal_places=2)
    commissions_this_month = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Répartition des commissions
    commissions_by_type = serializers.DictField()
    commissions_by_status = serializers.DictField()
    
    # Top voyageurs (par commissions)
    top_travelers = serializers.ListField(child=serializers.DictField())
    
    # Tendances
    commission_growth = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_commission_per_shipment = serializers.DecimalField(max_digits=10, decimal_places=2)


class UsersSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé des utilisateurs."""
    
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    new_users_today = serializers.IntegerField()
    new_users_this_week = serializers.IntegerField()
    new_users_this_month = serializers.IntegerField()
    
    # Répartition par rôle
    users_by_role = serializers.DictField()
    users_by_status = serializers.DictField()
    users_by_verification = serializers.DictField()
    
    # Top utilisateurs
    top_senders = serializers.ListField(child=serializers.DictField())
    top_travelers = serializers.ListField(child=serializers.DictField())
    
    # Tendances
    user_growth_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    active_user_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Géographie
    users_by_country = serializers.DictField()
    users_by_city = serializers.DictField()


class FinancialSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé financier."""
    
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=15, decimal_places=2)
    net_profit = serializers.DecimalField(max_digits=15, decimal_places=2)
    profit_margin = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Revenus par source
    revenue_by_source = serializers.DictField()
    revenue_by_period = serializers.DictField()
    
    # Dépenses par catégorie
    expenses_by_category = serializers.DictField()
    expenses_by_period = serializers.DictField()
    
    # Trésorerie
    cash_flow = serializers.DictField()
    outstanding_payments = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Tendances
    revenue_trend = serializers.ListField(child=serializers.DictField())
    profit_trend = serializers.ListField(child=serializers.DictField())


class PerformanceSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé des performances."""
    
    # Métriques de performance
    system_uptime = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_response_time = serializers.DurationField()
    error_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Performance des envois
    delivery_success_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_delivery_time = serializers.DurationField()
    customer_satisfaction_score = serializers.DecimalField(max_digits=3, decimal_places=1)
    
    # Performance des utilisateurs
    user_engagement_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    user_retention_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Métriques techniques
    database_performance = serializers.DictField()
    api_performance = serializers.DictField()
    cache_performance = serializers.DictField()


class DashboardOverviewSerializer(serializers.Serializer):
    """Serializer pour la vue d'ensemble du tableau de bord."""
    
    # Résumés principaux
    shipments_summary = ShipmentsSummarySerializer()
    payments_summary = PaymentsSummarySerializer()
    commissions_summary = CommissionsSummarySerializer()
    users_summary = UsersSummarySerializer()
    financial_summary = FinancialSummarySerializer()
    performance_summary = PerformanceSummarySerializer()
    
    # Métriques en temps réel
    real_time_metrics = serializers.DictField()
    
    # Alertes et notifications
    active_alerts = serializers.ListField(child=serializers.DictField())
    recent_notifications = serializers.ListField(child=serializers.DictField())
    
    # Graphiques et visualisations
    charts_data = serializers.DictField()
    
    # Actions rapides
    quick_actions = serializers.ListField(child=serializers.DictField())


class ExportReportSerializer(serializers.Serializer):
    """Serializer pour l'export de rapports."""
    
    report_type = serializers.ChoiceField(choices=[
        ('shipments_summary', 'Résumé des envois'),
        ('payments_summary', 'Résumé des paiements'),
        ('commissions_summary', 'Résumé des commissions'),
        ('users_summary', 'Résumé des utilisateurs'),
        ('financial_summary', 'Résumé financier'),
        ('performance_summary', 'Résumé des performances'),
    ])
    
    format = serializers.ChoiceField(choices=[
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ])
    
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    
    filters = serializers.DictField(required=False)
    include_charts = serializers.BooleanField(default=False)
    include_metadata = serializers.BooleanField(default=True)


class ExportDataSerializer(serializers.Serializer):
    """Serializer pour l'export direct de données."""
    
    report_type = serializers.ChoiceField(choices=[
        # Types de rapports résumés
        ('shipments_summary', 'Résumé des envois'),
        ('payments_summary', 'Résumé des paiements'),
        ('commissions_summary', 'Résumé des commissions'),
        ('users_summary', 'Résumé des utilisateurs'),
        ('financial_summary', 'Résumé financier'),
        ('performance_summary', 'Résumé des performances'),
        # Types d'export direct de données
        ('shipments', 'Données des envois'),
        ('payments', 'Données des paiements'),
        ('commissions', 'Données des commissions'),
        ('users', 'Données des utilisateurs'),
        ('trips', 'Données des voyages'),
        ('matching', 'Données des correspondances'),
    ])
    
    format = serializers.ChoiceField(choices=[
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ])
    
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    
    filters = serializers.DictField(required=False)
    include_charts = serializers.BooleanField(default=False)
    include_metadata = serializers.BooleanField(default=True)


class SystemHealthCheckSerializer(serializers.Serializer):
    """Serializer pour la vérification de santé du système."""
    
    service_name = serializers.CharField(required=False)
    check_all = serializers.BooleanField(default=True)
    include_details = serializers.BooleanField(default=False)
    timeout = serializers.IntegerField(default=30, min_value=5, max_value=300)
