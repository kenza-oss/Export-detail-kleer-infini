"""
URLs for analytics app - Dashboard analytics and statistics
"""

from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Dashboard Analytics
    path('dashboard/', views.DashboardAnalyticsView.as_view(), name='dashboard_analytics'),
    
    # Specific Analytics
    path('shipments/', views.ShipmentAnalyticsView.as_view(), name='shipment_analytics'),
    path('trips/', views.TripAnalyticsView.as_view(), name='trip_analytics'),
    path('financial/', views.FinancialAnalyticsView.as_view(), name='financial_analytics'),
    
    # Analytics Events
    path('events/', views.AnalyticsEventView.as_view(), name='analytics_events'),
    
    # Admin Analytics
    path('admin/', views.AdminAnalyticsView.as_view(), name='admin_analytics'),
] 