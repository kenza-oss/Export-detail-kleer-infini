"""
URLs for verification app - Document verification and validation
"""

from django.urls import path
from . import views

app_name = 'verification'

urlpatterns = [
    # Upload et vérification de documents
    path('upload/', views.DocumentUploadView.as_view(), name='document_upload'),
    path('verifications/', views.DocumentVerificationListView.as_view(), name='verification_list'),
    path('verifications/<uuid:verification_id>/', views.DocumentVerificationDetailView.as_view(), name='verification_detail'),
    path('documents/<int:document_id>/verify/', views.DocumentVerificationRequestView.as_view(), name='request_verification'),
    
    # Vérification en lot
    path('bulk-verify/', views.BulkVerificationView.as_view(), name='bulk_verification'),
    
    # Statistiques
    path('statistics/', views.VerificationStatisticsView.as_view(), name='verification_statistics'),
    
    # Endpoints administrateur
    path('admin/verifications/', views.AdminVerificationListView.as_view(), name='admin_verification_list'),
    path('admin/verifications/<uuid:verification_id>/', views.AdminVerificationUpdateView.as_view(), name='admin_verification_update'),
] 