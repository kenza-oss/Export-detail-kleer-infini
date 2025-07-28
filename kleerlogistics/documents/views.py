"""
Views for documents app - PDF document generation
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
import io
import random
import string
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Document, DocumentTemplate
from .serializers import (
    DocumentSerializer, DocumentTemplateSerializer,
    InvoiceSerializer, ReceiptSerializer
)
from config.swagger_config import (
    document_upload_schema, document_list_schema, document_verify_schema
)
from config.swagger_examples import (
    DOCUMENT_UPLOAD_EXAMPLE, DOCUMENT_LIST_EXAMPLE, DOCUMENT_VERIFY_EXAMPLE
)


class GenerateInvoiceView(APIView):
    """Vue pour générer une facture PDF."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Générer une facture PDF",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'shipment_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            },
            required=['shipment_id']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Facture générée avec succès",
                examples={"application/json": {
                    "success": True,
                    "message": "Facture générée avec succès",
                    "document": {
                        "id": 1,
                        "invoice_number": "INV12345678",
                        "download_url": "/api/v1/documents/1/download/",
                        "preview_url": "/api/v1/documents/1/preview/"
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "message": "ID d'envoi requis"
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Envoi non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Envoi non trouvé"
                }}
            )
        }
    )
    def post(self, request):
        """Générer une facture PDF."""
        shipment_id = request.data.get('shipment_id')
        
        if not shipment_id:
            return Response({
                'success': False,
                'message': 'ID d\'envoi requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from shipments.models import Shipment
            shipment = Shipment.objects.get(id=shipment_id, user=request.user)
            
            # Générer le numéro de facture
            invoice_number = self.generate_invoice_number()
            
            # Créer le document
            document = Document.objects.create(
                user=request.user,
                document_type='invoice',
                reference=invoice_number,
                title=f'Facture {invoice_number}',
                content=self.generate_invoice_content(shipment, invoice_number),
                status='generated'
            )
            
            return Response({
                'success': True,
                'message': 'Facture générée avec succès',
                'document': {
                    'id': document.id,
                    'invoice_number': invoice_number,
                    'download_url': f'/api/v1/documents/{document.id}/download/',
                    'preview_url': f'/api/v1/documents/{document.id}/preview/'
                }
            })
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def generate_invoice_number(self):
        """Générer un numéro de facture unique."""
        while True:
            number = ''.join(random.choices(string.digits, k=8))
            invoice_number = f"INV{number}"
            
            if not Document.objects.filter(reference=invoice_number).exists():
                return invoice_number
    
    def generate_invoice_content(self, shipment, invoice_number):
        """Générer le contenu de la facture."""
        return {
            'invoice_number': invoice_number,
            'date': timezone.now().strftime('%d/%m/%Y'),
            'shipment': {
                'tracking_number': shipment.tracking_number,
                'origin': shipment.origin,
                'destination': shipment.destination,
                'weight': shipment.weight,
                'shipping_cost': shipment.shipping_cost
            },
            'customer': {
                'name': f"{shipment.user.first_name} {shipment.user.last_name}",
                'email': shipment.user.email
            }
        }


class GenerateReceiptView(APIView):
    """Vue pour générer un reçu PDF."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Générer un reçu PDF",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'transaction_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            },
            required=['transaction_id']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Reçu généré avec succès",
                examples={"application/json": {
                    "success": True,
                    "message": "Reçu généré avec succès",
                    "document": {
                        "id": 2,
                        "receipt_number": "RCP87654321",
                        "download_url": "/api/v1/documents/2/download/",
                        "preview_url": "/api/v1/documents/2/preview/"
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "message": "ID de transaction requis"
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Transaction non trouvée",
                examples={"application/json": {
                    "success": False,
                    "message": "Transaction non trouvée"
                }}
            )
        }
    )
    def post(self, request):
        """Générer un reçu PDF."""
        transaction_id = request.data.get('transaction_id')
        
        if not transaction_id:
            return Response({
                'success': False,
                'message': 'ID de transaction requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from payments.models import Transaction
            transaction = Transaction.objects.get(id=transaction_id, user=request.user)
            
            # Générer le numéro de reçu
            receipt_number = self.generate_receipt_number()
            
            # Créer le document
            document = Document.objects.create(
                user=request.user,
                document_type='receipt',
                reference=receipt_number,
                title=f'Reçu {receipt_number}',
                content=self.generate_receipt_content(transaction, receipt_number),
                status='generated'
            )
            
            return Response({
                'success': True,
                'message': 'Reçu généré avec succès',
                'document': {
                    'id': document.id,
                    'receipt_number': receipt_number,
                    'download_url': f'/api/v1/documents/{document.id}/download/',
                    'preview_url': f'/api/v1/documents/{document.id}/preview/'
                }
            })
        except Transaction.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Transaction non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def generate_receipt_number(self):
        """Générer un numéro de reçu unique."""
        while True:
            number = ''.join(random.choices(string.digits, k=8))
            receipt_number = f"RCP{number}"
            
            if not Document.objects.filter(reference=receipt_number).exists():
                return receipt_number
    
    def generate_receipt_content(self, transaction, receipt_number):
        """Générer le contenu du reçu."""
        return {
            'receipt_number': receipt_number,
            'date': transaction.created_at.strftime('%d/%m/%Y'),
            'transaction': {
                'reference': transaction.reference,
                'amount': transaction.amount,
                'type': transaction.get_transaction_type_display(),
                'method': transaction.get_payment_method_display()
            },
            'customer': {
                'name': f"{transaction.user.first_name} {transaction.user.last_name}",
                'email': transaction.user.email
            }
        }


class DocumentListView(APIView):
    """Vue pour la liste des documents."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Lister les documents de l'utilisateur",
        manual_parameters=[
            openapi.Parameter(
                'document_type',
                openapi.IN_QUERY,
                description="Type de document",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Statut du document",
                type=openapi.TYPE_STRING,
                enum=['generated', 'pending', 'completed']
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des documents",
                examples={"application/json": DOCUMENT_LIST_EXAMPLE["response"]}
            )
        }
    )
    def get(self, request):
        """Récupérer la liste des documents de l'utilisateur."""
        documents = Document.objects.filter(user=request.user).order_by('-created_at')
        serializer = DocumentSerializer(documents, many=True)
        
        return Response({
            'success': True,
            'documents': serializer.data,
            'count': documents.count()
        })


class DocumentDetailView(APIView):
    """Vue pour les détails d'un document."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer les détails d'un document",
        manual_parameters=[
            openapi.Parameter(
                'pk',
                openapi.IN_PATH,
                description="ID du document",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Détails du document",
                examples={"application/json": {
                    "success": True,
                    "document": {
                        "id": 1,
                        "document_type": "invoice",
                        "reference": "INV12345678",
                        "title": "Facture INV12345678",
                        "status": "generated",
                        "created_at": "2024-01-15T10:30:00Z",
                        "download_url": "/api/v1/documents/1/download/",
                        "preview_url": "/api/v1/documents/1/preview/"
                    }
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Document non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Document non trouvé"
                }}
            )
        }
    )
    def get(self, request, pk):
        """Récupérer les détails d'un document."""
        try:
            document = Document.objects.get(pk=pk, user=request.user)
            serializer = DocumentSerializer(document)
            
            return Response({
                'success': True,
                'document': serializer.data
            })
        except Document.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Document non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class DocumentDownloadView(APIView):
    """Vue pour télécharger un document PDF."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Télécharger un document PDF",
        manual_parameters=[
            openapi.Parameter(
                'pk',
                openapi.IN_PATH,
                description="ID du document",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Document PDF téléchargé",
                content_type='application/pdf'
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Document non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Document non trouvé"
                }}
            )
        }
    )
    def get(self, request, pk):
        """Télécharger un document PDF."""
        try:
            document = Document.objects.get(pk=pk, user=request.user)
            
            # En production, générer le PDF réel
            # Pour la démonstration, on simule
            pdf_content = self.generate_pdf_content(document)
            
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{document.reference}.pdf"'
            
            return response
        except Document.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Document non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def generate_pdf_content(self, document):
        """Générer le contenu PDF (simulation)."""
        # En production, utiliser une bibliothèque comme ReportLab
        return f"PDF content for {document.reference}".encode('utf-8')


class DocumentPreviewView(APIView):
    """Vue pour prévisualiser un document."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Prévisualiser un document",
        manual_parameters=[
            openapi.Parameter(
                'pk',
                openapi.IN_PATH,
                description="ID du document",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Prévisualisation du document",
                examples={"application/json": {
                    "success": True,
                    "document": {
                        "id": 1,
                        "title": "Facture INV12345678",
                        "reference": "INV12345678",
                        "document_type": "invoice",
                        "status": "generated",
                        "preview_url": "/api/v1/documents/1/preview/",
                        "download_url": "/api/v1/documents/1/download/"
                    }
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Document non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Document non trouvé"
                }}
            )
        }
    )
    def get(self, request, pk):
        """Prévisualiser un document."""
        try:
            document = Document.objects.get(pk=pk, user=request.user)
            
            return Response({
                'success': True,
                'document': {
                    'id': document.id,
                    'title': document.title,
                    'reference': document.reference,
                    'type': document.document_type,
                    'content': document.content,
                    'created_at': document.created_at
                }
            })
        except Document.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Document non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class DocumentTemplateListView(APIView):
    """Vue pour la liste des modèles de documents."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupérer la liste des modèles."""
        templates = DocumentTemplate.objects.filter(is_active=True)
        serializer = DocumentTemplateSerializer(templates, many=True)
        
        return Response({
            'success': True,
            'templates': serializer.data,
            'count': templates.count()
        })


class GenerateCustomDocumentView(APIView):
    """Vue pour générer un document personnalisé."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Générer un document personnalisé",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'template_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'data': openapi.Schema(type=openapi.TYPE_OBJECT)
            },
            required=['template_id']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Document généré avec succès",
                examples={"application/json": {
                    "success": True,
                    "message": "Document généré avec succès",
                    "document": {
                        "id": 3,
                        "reference": "CUSTOM12345678",
                        "download_url": "/api/v1/documents/3/download/",
                        "preview_url": "/api/v1/documents/3/preview/"
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "message": "ID de modèle requis"
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Modèle non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Modèle non trouvé"
                }}
            )
        }
    )
    def post(self, request):
        """Générer un document personnalisé."""
        template_id = request.data.get('template_id')
        data = request.data.get('data', {})
        
        if not template_id:
            return Response({
                'success': False,
                'message': 'ID de modèle requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            template = DocumentTemplate.objects.get(id=template_id, is_active=True)
            
            # Générer le numéro de document
            document_number = self.generate_document_number(template.document_type)
            
            # Créer le document
            document = Document.objects.create(
                user=request.user,
                document_type=template.document_type,
                reference=document_number,
                title=f'{template.name} {document_number}',
                content=data,
                status='generated'
            )
            
            return Response({
                'success': True,
                'message': 'Document généré avec succès',
                'document': {
                    'id': document.id,
                    'reference': document_number,
                    'download_url': f'/api/v1/documents/{document.id}/download/',
                    'preview_url': f'/api/v1/documents/{document.id}/preview/'
                }
            })
        except DocumentTemplate.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Modèle non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def generate_document_number(self, document_type):
        """Générer un numéro de document unique."""
        while True:
            number = ''.join(random.choices(string.digits, k=8))
            document_number = f"{document_type.upper()}{number}"
            
            if not Document.objects.filter(reference=document_number).exists():
                return document_number


# Views pour l'administration
class AdminDocumentListView(APIView):
    """Vue admin pour la liste de tous les documents."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Liste de tous les documents."""
        documents = Document.objects.all().select_related('user')
        serializer = DocumentSerializer(documents, many=True)
        
        return Response({
            'success': True,
            'documents': serializer.data,
            'count': documents.count()
        })


class AdminDocumentTemplateListView(APIView):
    """Vue admin pour la liste de tous les modèles."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Liste de tous les modèles."""
        templates = DocumentTemplate.objects.all()
        serializer = DocumentTemplateSerializer(templates, many=True)
        
        return Response({
            'success': True,
            'templates': serializer.data,
            'count': templates.count()
        })
    
    def post(self, request):
        """Créer un nouveau modèle."""
        serializer = DocumentTemplateSerializer(data=request.data)
        if serializer.is_valid():
            template = serializer.save()
            return Response({
                'success': True,
                'message': 'Modèle créé avec succès',
                'template': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
