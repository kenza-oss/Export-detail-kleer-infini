"""
URLs for notifications app - Email and SMS notifications
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Email Notifications
    path('email/send/', views.EmailNotificationView.as_view(), name='send_email'),
    path('email/templates/', views.EmailTemplateListView.as_view(), name='email_templates'),
    
    # SMS Notifications
    path('sms/send/', views.SMSNotificationView.as_view(), name='send_sms'),
    path('sms/templates/', views.SMSTemplateListView.as_view(), name='sms_templates'),
    
    # Notification Management
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification_detail'),
    path('<int:pk>/mark-read/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark_all_read'),
    
    # Shipment Notifications
    path('shipment/send/', views.SendShipmentNotificationView.as_view(), name='send_shipment_notification'),
    
    # Notification Analytics
    path('analytics/', views.NotificationAnalyticsView.as_view(), name='notification_analytics'),
    
    # Admin endpoints
    path('admin/notifications/', views.AdminNotificationListView.as_view(), name='admin_notification_list'),
    path('admin/email-templates/', views.AdminEmailTemplateListView.as_view(), name='admin_email_templates'),
    path('admin/sms-templates/', views.AdminSMSTemplateListView.as_view(), name='admin_sms_templates'),
] 