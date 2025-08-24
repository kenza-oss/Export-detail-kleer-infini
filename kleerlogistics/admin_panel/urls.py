"""
URLs for admin_panel app - Dashboard and Analytics for Administrators
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'admin_panel'

# Configuration du routeur pour les vues basées sur les vues
router = DefaultRouter()

urlpatterns = [
    # Tableau de bord principal
    path('dashboard/overview/', views.DashboardOverviewView.as_view(), name='dashboard_overview'),
    path('dashboard/metrics/', views.DashboardMetricsView.as_view(), name='dashboard_metrics'),
    
    # Rapports
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('reports/<uuid:report_id>/', views.ReportDetailView.as_view(), name='report_detail'),
    
    # Notifications
    path('notifications/', views.NotificationsView.as_view(), name='notifications'),
    path('notifications/<uuid:notification_id>/', views.NotificationDetailView.as_view(), name='notification_detail'),
    path('notifications/<uuid:notification_id>/mark-read/', views.NotificationDetailView.as_view(), name='mark_notification_read'),
    
    # Santé du système
    path('system/health/', views.SystemHealthView.as_view(), name='system_health'),
    
    # Logs d'audit
    path('audit/logs/', views.AuditLogsView.as_view(), name='audit_logs'),
    path('audit/logs/<uuid:log_id>/', views.AuditLogsView.as_view(), name='audit_log_detail'),
    
    # Actions rapides
    path('quick-actions/', views.QuickActionsView.as_view(), name='quick_actions'),
    
    # Export de données
    path('export/', views.ExportDataView.as_view(), name='export_data'),
    
    # Inclure les URLs du routeur
    path('', include(router.urls)),
] 