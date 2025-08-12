"""
URLs for shipments app - Core package shipping functionality
"""

from django.urls import path
from . import views

app_name = 'shipments'

urlpatterns = [
    # Shipment CRUD
    path('', views.ShipmentListView.as_view(), name='shipment_list'),
    path('create/', views.ShipmentCreateView.as_view(), name='create_shipment'),
    path('<str:tracking_number>/', views.ShipmentDetailView.as_view(), name='shipment_detail'),
    
    # Shipment Status
    path('<str:tracking_number>/status/', views.ShipmentStatusView.as_view(), name='shipment_status'),
    
    # Shipment Tracking
    path('<str:tracking_number>/tracking/', views.ShipmentTrackingView.as_view(), name='tracking_events'),
    path('<str:tracking_number>/tracking/add/', views.AddTrackingEventView.as_view(), name='add_tracking_event'),
    
    # Shipment Payment
    path('<str:tracking_number>/payment/', views.ShipmentPaymentView.as_view(), name='shipment_payment'),
    path('<str:tracking_number>/payment/process/', views.ProcessPaymentView.as_view(), name='process_payment'),
    
    # Shipment Delivery OTP System
    path('<str:tracking_number>/delivery/initiate/', views.InitiateDeliveryProcessView.as_view(), name='initiate_delivery_process'),
    path('<str:tracking_number>/delivery/otp/generate/', views.GenerateDeliveryOTPView.as_view(), name='generate_delivery_otp'),
    path('<str:tracking_number>/delivery/otp/verify/', views.VerifyDeliveryOTPView.as_view(), name='verify_delivery_otp'),
    path('<str:tracking_number>/delivery/otp/resend/', views.ResendDeliveryOTPView.as_view(), name='resend_delivery_otp'),
    path('<str:tracking_number>/delivery/otp/status/', views.DeliveryOTPStatusView.as_view(), name='delivery_otp_status'),
    
    # Package Details
    path('<int:shipment_id>/package/', views.PackageDetailView.as_view(), name='package_details'),
    
    # Shipment Ratings
    path('<int:shipment_id>/rating/', views.ShipmentRatingView.as_view(), name='shipment_rating'),
] 