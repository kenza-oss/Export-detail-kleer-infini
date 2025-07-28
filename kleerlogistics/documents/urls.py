"""
URLs for documents app - PDF document generation
"""

from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Document Generation
    path('generate/invoice/', views.GenerateInvoiceView.as_view(), name='generate_invoice'),
    path('generate/receipt/', views.GenerateReceiptView.as_view(), name='generate_receipt'),
    path('generate/custom/', views.GenerateCustomDocumentView.as_view(), name='generate_custom'),
    
    # Document Management
    path('', views.DocumentListView.as_view(), name='document_list'),
    path('<int:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
    path('<int:pk>/download/', views.DocumentDownloadView.as_view(), name='document_download'),
    path('<int:pk>/preview/', views.DocumentPreviewView.as_view(), name='document_preview'),
    
    # Document Templates
    path('templates/', views.DocumentTemplateListView.as_view(), name='template_list'),
    
    # Admin endpoints
    path('admin/documents/', views.AdminDocumentListView.as_view(), name='admin_document_list'),
    path('admin/templates/', views.AdminDocumentTemplateListView.as_view(), name='admin_template_list'),
] 