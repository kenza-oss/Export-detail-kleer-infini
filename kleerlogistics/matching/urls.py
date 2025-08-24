"""
URLs for matching app - Conforme au dictionnaire des données
"""

from django.urls import path
from . import views

app_name = 'matching'

urlpatterns = [
    # Matching Engine
    path('engine/', views.MatchingEngineView.as_view(), name='engine'),
    path('find-matches/', views.MatchingEngineView.as_view(), name='find_matches'),
    
    # Match Management
    path('matches/', views.MatchListView.as_view(), name='match_list'),
    path('matches/<int:match_id>/', views.MatchDetailView.as_view(), name='match-detail'),
    path('matches/<int:match_id>/accept/', views.AcceptMatchView.as_view(), name='accept-match'),
    path('matches/<int:match_id>/reject/', views.RejectMatchView.as_view(), name='reject-match'),
    
    # OTP Delivery System
    path('matches/<int:match_id>/otp/', views.OTPDeliveryView.as_view(), name='otp-delivery'),
    
    # Chat Integration
    path('matches/<int:match_id>/chat/', views.ChatIntegrationView.as_view(), name='chat-integration'),
    
    # Automatic Matching
    path('automatic/', views.AutomaticMatchingView.as_view(), name='automatic-matching'),
    
    # Matching Preferences
    path('preferences/', views.MatchingPreferencesView.as_view(), name='preferences'),
    
    # Matching Analytics
    path('analytics/', views.MatchingAnalyticsView.as_view(), name='analytics'),
    
    # Matching Rules (Admin)
    path('rules/', views.MatchingRulesView.as_view(), name='rules'),
    
    # Notifications
    path('notifications/', views.MatchingNotificationsView.as_view(), name='notifications'),
    
    # Admin endpoints
    path('admin/matches/', views.AdminMatchListView.as_view(), name='admin_match_list'),
    path('admin/matches/<int:match_id>/', views.AdminMatchDetailView.as_view(), name='admin_match_detail'),
] 