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
    path('<str:tracking_number>/delivery/confirm/', views.ConfirmDeliveryView.as_view(), name='confirm_delivery'),
    
    # Shipment Matching
    path('<str:tracking_number>/matches/', views.ShipmentMatchesView.as_view(), name='shipment_matches'),
    path('<str:tracking_number>/matches/<int:match_id>/accept/', views.AcceptMatchView.as_view(), name='accept_shipment_match'),
    
    # Package Details
    path('<int:shipment_id>/package/', views.PackageDetailView.as_view(), name='package_details'),
    
    # Shipment Documents
    path('<int:shipment_id>/documents/', views.ShipmentDocumentListView.as_view(), name='shipment_documents'),
    path('<int:shipment_id>/documents/<int:document_id>/', views.ShipmentDocumentDetailView.as_view(), name='shipment_document_detail'),
    
    # Shipment Ratings
    path('<int:shipment_id>/rating/', views.ShipmentRatingView.as_view(), name='shipment_rating'),
    
    # Shipment with all details
    path('<int:shipment_id>/details/', views.ShipmentWithAllDetailsView.as_view(), name='shipment_all_details'),
    
    # Admin endpoints
    path('admin/all/', views.AdminShipmentListView.as_view(), name='admin_shipment_list'),
    path('admin/<str:tracking_number>/', views.AdminShipmentDetailView.as_view(), name='admin_shipment_detail'),
    path('admin/packages/', views.AdminPackageListView.as_view(), name='admin_package_list'),
    path('admin/documents/', views.AdminDocumentListView.as_view(), name='admin_document_list'),
    path('admin/ratings/', views.AdminRatingListView.as_view(), name='admin_rating_list'),
] 