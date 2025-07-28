"""
URLs for shipments app - Package shipping management
"""

from django.urls import path
from . import views

app_name = 'shipments'

urlpatterns = [
    # Shipment CRUD
    path('', views.ShipmentListView.as_view(), name='shipment_list'),
    path('create/', views.ShipmentCreateView.as_view(), name='shipment_create'),
    path('<str:tracking_number>/', views.ShipmentDetailView.as_view(), name='shipment_detail'),
    path('<str:tracking_number>/update/', views.ShipmentDetailView.as_view(), name='shipment_update'),
    path('<str:tracking_number>/delete/', views.ShipmentDetailView.as_view(), name='shipment_delete'),
    
    # Shipment Status
    path('<str:tracking_number>/status/', views.ShipmentStatusView.as_view(), name='shipment_status'),
    
    # Shipment Tracking
    path('<str:tracking_number>/tracking/', views.ShipmentTrackingView.as_view(), name='shipment_tracking'),
    path('<str:tracking_number>/tracking/add/', views.AddTrackingEventView.as_view(), name='add_tracking_event'),
    
    # Shipment Matching
    path('<str:tracking_number>/matches/', views.ShipmentMatchesView.as_view(), name='shipment_matches'),
    path('<str:tracking_number>/matches/<int:match_id>/accept/', views.AcceptMatchView.as_view(), name='accept_match'),
    
    # Shipment Payment
    path('<str:tracking_number>/payment/', views.ShipmentPaymentView.as_view(), name='shipment_payment'),
    path('<str:tracking_number>/payment/process/', views.ProcessPaymentView.as_view(), name='process_payment'),
    
    # Shipment Delivery
    path('<str:tracking_number>/delivery/otp/generate/', views.GenerateDeliveryOTPView.as_view(), name='generate_delivery_otp'),
    path('<str:tracking_number>/delivery/otp/verify/', views.VerifyDeliveryOTPView.as_view(), name='verify_delivery_otp'),
    path('<str:tracking_number>/delivery/confirm/', views.ConfirmDeliveryView.as_view(), name='confirm_delivery'),
    
    # Admin endpoints
    path('admin/shipments/', views.AdminShipmentListView.as_view(), name='admin_shipment_list'),
    path('admin/shipments/<str:tracking_number>/', views.AdminShipmentDetailView.as_view(), name='admin_shipment_detail'),
] 