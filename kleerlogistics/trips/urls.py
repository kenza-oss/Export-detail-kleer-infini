"""
URLs for trips app - Traveler trip management
"""

from django.urls import path
from . import views

app_name = 'trips'

urlpatterns = [
    # Trip CRUD
    path('', views.TripListView.as_view(), name='trip_list'),
    path('create/', views.TripCreateView.as_view(), name='trip_create'),
    path('<int:pk>/', views.TripDetailView.as_view(), name='trip_detail'),
    path('<int:pk>/update/', views.TripDetailView.as_view(), name='trip_update'),
    path('<int:pk>/delete/', views.TripDetailView.as_view(), name='trip_delete'),
    
    # Trip Status
    path('<int:pk>/status/', views.TripStatusView.as_view(), name='trip_status'),
    path('<int:pk>/status/update/', views.TripStatusView.as_view(), name='trip_status_update'),
    
    # Available Trips
    path('available/', views.AvailableTripsView.as_view(), name='available_trips'),
    
    # Trip Documents
    path('<int:trip_id>/documents/', views.TripDocumentView.as_view(), name='trip_documents'),
    path('<int:trip_id>/documents/upload/', views.TripDocumentView.as_view(), name='upload_trip_document'),
    
    # Trip Capacity
    path('<int:pk>/capacity/update/', views.UpdateCapacityView.as_view(), name='update_capacity'),
    
    # Trip Search
    path('search/', views.TripSearchView.as_view(), name='trip_search'),
    
    # Trip Matching
    path('<int:pk>/matches/', views.TripMatchesView.as_view(), name='trip_matches'),
    path('<int:pk>/matches/<int:shipment_id>/accept/', views.AcceptShipmentView.as_view(), name='accept_shipment'),
    
    # Trip Analytics
    path('analytics/', views.TripAnalyticsView.as_view(), name='trip_analytics'),
    
    # Trip Calendar
    path('calendar/', views.TripCalendarView.as_view(), name='trip_calendar'),
    
    # Admin endpoints
    path('admin/trips/', views.AdminTripListView.as_view(), name='admin_trip_list'),
    path('admin/trips/<int:pk>/', views.AdminTripDetailView.as_view(), name='admin_trip_detail'),
] 