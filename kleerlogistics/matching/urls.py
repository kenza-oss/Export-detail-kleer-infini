"""
URLs for matching app - Intelligent matching algorithm
"""

from django.urls import path
from . import views

app_name = 'matching'

urlpatterns = [
    # Matching Engine
    path('find-matches/', views.MatchingEngineView.as_view(), name='find_matches'),
    
    # Match Management
    path('matches/', views.MatchListView.as_view(), name='match_list'),
    path('matches/<int:match_id>/accept/', views.AcceptMatchView.as_view(), name='accept_match'),
    path('matches/<int:match_id>/reject/', views.RejectMatchView.as_view(), name='reject_match'),
    
    # Matching Preferences
    path('preferences/', views.MatchingPreferencesView.as_view(), name='matching_preferences'),
    
    # Matching Analytics
    path('analytics/', views.MatchingAnalyticsView.as_view(), name='matching_analytics'),
    
    # Matching Notifications
    path('notifications/', views.MatchingNotificationsView.as_view(), name='matching_notifications'),
    
    # Admin endpoints
    path('admin/matches/', views.AdminMatchListView.as_view(), name='admin_match_list'),
    path('admin/matches/<int:match_id>/', views.AdminMatchDetailView.as_view(), name='admin_match_detail'),
] 