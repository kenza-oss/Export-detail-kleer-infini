"""
Admin interface for admin_panel app - Dashboard and Analytics for Administrators
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import (
    DashboardMetric, AdminReport, AdminNotification, 
    SystemHealth, AdminAuditLog
)


@admin.register(DashboardMetric)
class DashboardMetricAdmin(admin.ModelAdmin):
    """Interface d'administration pour les métriques du tableau de bord."""
    
    list_display = [
        'metric_type', 'period_type', 'period_start', 'value', 
        'change_percentage', 'trend_direction', 'is_active', 'created_at'
    ]
    
    list_filter = [
        'metric_type', 'period_type', 'is_active', 'created_at'
    ]
    
    search_fields = ['metric_type', 'period_type']
    
    readonly_fields = ['created_at', 'updated_at', 'trend_direction']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('metric_type', 'period_type', 'period_start', 'period_end')
        }),
        ('Valeurs', {
            'fields': ('value', 'previous_value', 'change_percentage')
        }),
        ('Métadonnées', {
            'fields': ('metadata', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_metrics', 'deactivate_metrics', 'recalculate_percentages']
    
    def trend_direction(self, obj):
        """Affiche la direction de la tendance avec une icône."""
        if obj.trend_direction == 'up':
            return format_html('<span style="color: green;">↗</span> Hausse')
        elif obj.trend_direction == 'down':
            return format_html('<span style="color: red;">↘</span> Baisse')
        else:
            return format_html('<span style="color: gray;">→</span> Stable')
    
    trend_direction.short_description = 'Tendance'
    
    def activate_metrics(self, request, queryset):
        """Active les métriques sélectionnées."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} métriques ont été activées.')
    
    activate_metrics.short_description = "Activer les métriques sélectionnées"
    
    def deactivate_metrics(self, request, queryset):
        """Désactive les métriques sélectionnées."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} métriques ont été désactivées.')
    
    deactivate_metrics.short_description = "Désactiver les métriques sélectionnées"
    
    def recalculate_percentages(self, request, queryset):
        """Recalcule les pourcentages de changement."""
        for metric in queryset:
            if metric.previous_value and metric.previous_value > 0:
                metric.change_percentage = ((metric.value - metric.previous_value) / metric.previous_value) * 100
                metric.save()
        
        self.message_user(request, f'Pourcentages recalculés pour {queryset.count()} métriques.')
    
    recalculate_percentages.short_description = "Recalculer les pourcentages"


@admin.register(AdminReport)
class AdminReportAdmin(admin.ModelAdmin):
    """Interface d'administration pour les rapports administratifs."""
    
    list_display = [
        'name', 'report_type', 'format', 'generated_by', 
        'generated_at', 'is_scheduled', 'file_path'
    ]
    
    list_filter = [
        'report_type', 'format', 'is_scheduled', 'generated_at'
    ]
    
    search_fields = ['name', 'report_type', 'generated_by__username']
    
    readonly_fields = ['generated_at', 'file_path']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'report_type', 'format')
        }),
        ('Configuration', {
            'fields': ('parameters', 'filters', 'is_scheduled', 'schedule_cron')
        }),
        ('Résultats', {
            'fields': ('result_data', 'file_path')
        }),
        ('Métadonnées', {
            'fields': ('generated_by', 'generated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['schedule_reports', 'unschedule_reports', 'regenerate_reports']
    
    def schedule_reports(self, request, queryset):
        """Programme les rapports sélectionnés."""
        updated = queryset.update(is_scheduled=True)
        self.message_user(request, f'{updated} rapports ont été programmés.')
    
    schedule_reports.short_description = "Programmer les rapports sélectionnés"
    
    def unschedule_reports(self, request, queryset):
        """Désactive la programmation des rapports sélectionnés."""
        updated = queryset.update(is_scheduled=False)
        self.message_user(request, f'{updated} rapports ont été désactivés de la programmation.')
    
    unschedule_reports.short_description = "Désactiver la programmation des rapports sélectionnés"
    
    def regenerate_reports(self, request, queryset):
        """Régénère les rapports sélectionnés."""
        for report in queryset:
            # Ici, vous pouvez implémenter la logique de régénération
            pass
        
        self.message_user(request, f'Régénération lancée pour {queryset.count()} rapports.')
    
    regenerate_reports.short_description = "Régénérer les rapports sélectionnés"


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    """Interface d'administration pour les notifications administratives."""
    
    list_display = [
        'title', 'notification_type', 'priority', 'is_broadcast', 
        'is_read', 'recipients_count', 'created_at'
    ]
    
    list_filter = [
        'notification_type', 'priority', 'is_broadcast', 'is_read', 'created_at'
    ]
    
    search_fields = ['title', 'message', 'recipients__username']
    
    readonly_fields = ['created_at', 'updated_at', 'recipients_count', 'read_count']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('title', 'message', 'notification_type', 'priority')
        }),
        ('Destinataires', {
            'fields': ('recipients', 'is_broadcast')
        }),
        ('Actions', {
            'fields': ('action_url', 'action_text')
        }),
        ('Métadonnées', {
            'fields': ('metadata', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'send_notifications']
    
    def recipients_count(self, obj):
        """Affiche le nombre de destinataires."""
        return obj.recipients.count()
    
    recipients_count.short_description = 'Destinataires'
    
    def read_count(self, obj):
        """Affiche le nombre de lecteurs."""
        return obj.read_by.count()
    
    read_count.short_description = 'Lu par'
    
    def mark_as_read(self, request, queryset):
        """Marque les notifications sélectionnées comme lues."""
        for notification in queryset:
            notification.is_read = True
            notification.read_by.add(request.user)
            notification.save()
        
        self.message_user(request, f'{queryset.count()} notifications ont été marquées comme lues.')
    
    mark_as_read.short_description = "Marquer comme lues"
    
    def mark_as_unread(self, request, queryset):
        """Marque les notifications sélectionnées comme non lues."""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notifications ont été marquées comme non lues.')
    
    mark_as_unread.short_description = "Marquer comme non lues"
    
    def send_notifications(self, request, queryset):
        """Envoie les notifications sélectionnées."""
        # Ici, vous pouvez implémenter la logique d'envoi
        self.message_user(request, f'Envoi lancé pour {queryset.count()} notifications.')
    
    send_notifications.short_description = "Envoyer les notifications sélectionnées"


@admin.register(SystemHealth)
class SystemHealthAdmin(admin.ModelAdmin):
    """Interface d'administration pour la santé du système."""
    
    list_display = [
        'service_name', 'status', 'response_time', 'uptime_percentage', 
        'error_count', 'last_check'
    ]
    
    list_filter = ['status', 'last_check']
    
    search_fields = ['service_name']
    
    readonly_fields = ['last_check']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('service_name', 'status')
        }),
        ('Métriques de performance', {
            'fields': ('response_time', 'uptime_percentage', 'error_count')
        }),
        ('Détails', {
            'fields': ('details', 'last_check')
        }),
    )
    
    actions = ['check_health', 'reset_error_count', 'mark_as_healthy']
    
    def check_health(self, request, queryset):
        """Vérifie la santé des services sélectionnés."""
        # Ici, vous pouvez implémenter la logique de vérification
        self.message_user(request, f'Vérification de santé lancée pour {queryset.count()} services.')
    
    check_health.short_description = "Vérifier la santé des services sélectionnés"
    
    def reset_error_count(self, request, queryset):
        """Remet à zéro le compteur d'erreurs."""
        updated = queryset.update(error_count=0)
        self.message_user(request, f'Compteur d\'erreurs remis à zéro pour {updated} services.')
    
    reset_error_count.short_description = "Remettre à zéro le compteur d'erreurs"
    
    def mark_as_healthy(self, request, queryset):
        """Marque les services comme étant en bonne santé."""
        updated = queryset.update(status='healthy')
        self.message_user(request, f'{updated} services ont été marqués comme étant en bonne santé.')
    
    mark_as_healthy.short_description = "Marquer comme étant en bonne santé"


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    """Interface d'administration pour les logs d'audit administratifs."""
    
    list_display = [
        'user', 'action', 'model_name', 'object_id', 
        'ip_address', 'timestamp'
    ]
    
    list_filter = [
        'action', 'model_name', 'timestamp', 'user'
    ]
    
    search_fields = [
        'user__username', 'action', 'model_name', 'object_id', 'ip_address'
    ]
    
    readonly_fields = ['timestamp', 'ip_address', 'user_agent', 'session_id']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('user', 'action', 'model_name', 'object_id')
        }),
        ('Changements', {
            'fields': ('changes', 'metadata')
        }),
        ('Contexte', {
            'fields': ('ip_address', 'user_agent', 'session_id', 'timestamp')
        }),
    )
    
    actions = ['export_logs', 'cleanup_old_logs']
    
    def export_logs(self, request, queryset):
        """Exporte les logs sélectionnés."""
        # Ici, vous pouvez implémenter la logique d'export
        self.message_user(request, f'Export lancé pour {queryset.count()} logs.')
    
    export_logs.short_description = "Exporter les logs sélectionnés"
    
    def cleanup_old_logs(self, request, queryset):
        """Nettoie les anciens logs."""
        # Supprimer les logs de plus de 90 jours
        cutoff_date = timezone.now() - timedelta(days=90)
        old_logs = AdminAuditLog.objects.filter(timestamp__lt=cutoff_date)
        count = old_logs.count()
        old_logs.delete()
        
        self.message_user(request, f'{count} anciens logs ont été supprimés.')
    
    cleanup_old_logs.short_description = "Nettoyer les anciens logs"


# Configuration personnalisée de l'admin
admin.site.site_header = "KleerLogistics - Administration"
admin.site.site_title = "KleerLogistics Admin"
admin.site.index_title = "Tableau de bord administratif"

# Ajouter des statistiques au tableau de bord principal
class AdminDashboard:
    """Tableau de bord personnalisé pour l'administration."""
    
    def changelist_view(self, request, extra_context=None):
        """Ajoute des statistiques au tableau de bord."""
        extra_context = extra_context or {}
        
        # Statistiques des envois
        extra_context['shipments_stats'] = {
            'total': Shipment.objects.count(),
            'pending': Shipment.objects.filter(status='pending').count(),
            'in_transit': Shipment.objects.filter(status='in_transit').count(),
            'delivered': Shipment.objects.filter(status='delivered').count(),
        }
        
        # Statistiques des paiements
        extra_context['payments_stats'] = {
            'total_revenue': Transaction.objects.filter(
                transaction_type='payment',
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'total_commissions': Transaction.objects.filter(
                transaction_type='commission',
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0,
        }
        
        # Statistiques des utilisateurs
        extra_context['users_stats'] = {
            'total': User.objects.count(),
            'active': User.objects.filter(is_active=True).count(),
            'new_today': User.objects.filter(
                date_joined__date=timezone.now().date()
            ).count(),
        }
        
        # Santé du système
        extra_context['system_health'] = {
            'healthy_services': SystemHealth.objects.filter(status='healthy').count(),
            'warning_services': SystemHealth.objects.filter(status='warning').count(),
            'critical_services': SystemHealth.objects.filter(status='critical').count(),
        }
        
        return super().changelist_view(request, extra_context)
