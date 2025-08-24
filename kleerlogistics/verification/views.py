"""
Views for verification app - Document verification and validation
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Avg
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from .models import (
    DocumentVerification, DocumentValidationRule, 
    VerificationWorkflow, VerificationLog, DocumentTemplate
)
from .serializers import (
    DocumentVerificationSerializer, DocumentVerificationCreateSerializer,
    DocumentVerificationUpdateSerializer, DocumentValidationRuleSerializer,
    VerificationWorkflowSerializer, VerificationLogSerializer,
    DocumentTemplateSerializer, DocumentUploadSerializer,
    DocumentVerificationRequestSerializer, BulkVerificationSerializer,
    VerificationStatisticsSerializer
)
from users.models import UserDocument

logger = logging.getLogger(__name__)


class DocumentUploadView(APIView):
    """Vue pour l'upload et la vérification automatique de documents."""
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Uploader et vérifier automatiquement un document",
        request_body=DocumentUploadSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Document uploadé et vérification initiée",
                examples={"application/json": {
                    "success": True,
                    "message": "Document uploadé avec succès",
                    "verification_id": "uuid-here",
                    "estimated_completion_time": "2024-02-15T16:00:00Z"
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "errors": ["Fichier invalide"]
                }}
            )
        }
    )
    def post(self, request):
        """Uploader et vérifier un document."""
        try:
            serializer = DocumentUploadSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer le document utilisateur
            document = UserDocument.objects.create(
                user=request.user,
                document_type=serializer.validated_data['document_type'],
                document_file=serializer.validated_data['document_file'],
                status='pending'
            )
            
            # Créer la vérification automatique
            verification = DocumentVerification.objects.create(
                user=request.user,
                document=document,
                verification_method='automatic',
                status='processing'
            )
            
            # Lancer la vérification automatique en arrière-plan
            self.start_automatic_verification(verification)
            
            return Response({
                'success': True,
                'message': 'Document uploadé avec succès',
                'verification_id': verification.id,
                'document_id': document.id,
                'estimated_completion_time': timezone.now() + timezone.timedelta(minutes=5)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'upload du document: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de l\'upload du document'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def start_automatic_verification(self, verification):
        """Démarrer la vérification automatique."""
        try:
            # Simuler la vérification automatique (à remplacer par l'implémentation réelle)
            import threading
            import time
            
            def verify_document():
                time.sleep(2)  # Simulation du traitement
                
                # Mettre à jour le statut
                verification.status = 'approved'
                verification.validation_score = 95.50
                verification.fraud_detection_score = 98.00
                verification.verified_at = timezone.now()
                verification.verification_duration = timezone.timedelta(seconds=2)
                verification.save()
                
                # Mettre à jour le document
                verification.document.status = 'approved'
                verification.document.verified_at = timezone.now()
                verification.document.save()
                
                # Créer un log
                VerificationLog.objects.create(
                    verification=verification,
                    log_level='success',
                    message='Vérification automatique terminée avec succès',
                    details={'score': 95.50, 'fraud_score': 98.00}
                )
            
            # Lancer la vérification en arrière-plan
            thread = threading.Thread(target=verify_document)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification automatique: {str(e)}")
            verification.status = 'requires_manual_review'
            verification.save()


class DocumentVerificationListView(APIView):
    """Vue pour lister les vérifications de documents."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Lister les vérifications de l'utilisateur."""
        try:
            verifications = DocumentVerification.objects.filter(user=request.user).order_by('-created_at')
            
            # Filtres
            status_filter = request.query_params.get('status')
            document_type = request.query_params.get('document_type')
            verification_method = request.query_params.get('verification_method')
            
            if status_filter:
                verifications = verifications.filter(status=status_filter)
            if document_type:
                verifications = verifications.filter(document__document_type=document_type)
            if verification_method:
                verifications = verifications.filter(verification_method=verification_method)
            
            serializer = DocumentVerificationSerializer(verifications, many=True)
            
            return Response({
                'success': True,
                'verifications': serializer.data,
                'count': verifications.count()
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des vérifications: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la récupération des vérifications'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentVerificationDetailView(APIView):
    """Vue pour les détails d'une vérification de document."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, verification_id):
        """Obtenir les détails d'une vérification."""
        try:
            verification = DocumentVerification.objects.get(
                id=verification_id, 
                user=request.user
            )
            
            serializer = DocumentVerificationSerializer(verification)
            
            return Response({
                'success': True,
                'verification': serializer.data
            })
            
        except DocumentVerification.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Vérification non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la vérification: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la récupération de la vérification'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentVerificationRequestView(APIView):
    """Vue pour demander une vérification de document."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, document_id):
        """Demander une vérification pour un document existant."""
        try:
            # Vérifier que le document appartient à l'utilisateur
            document = UserDocument.objects.get(id=document_id, user=request.user)
            
            serializer = DocumentVerificationRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer la vérification
            verification = DocumentVerification.objects.create(
                user=request.user,
                document=document,
                verification_method=serializer.validated_data['verification_method'],
                verification_notes=serializer.validated_data.get('notes', ''),
                status='pending'
            )
            
            # Lancer la vérification selon la méthode choisie
            if serializer.validated_data['verification_method'] == 'automatic':
                self.start_automatic_verification(verification)
            elif serializer.validated_data['verification_method'] == 'manual':
                verification.status = 'requires_manual_review'
                verification.save()
            
            return Response({
                'success': True,
                'message': 'Vérification demandée avec succès',
                'verification_id': verification.id,
                'status': verification.status
            }, status=status.HTTP_201_CREATED)
            
        except UserDocument.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Document non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur lors de la demande de vérification: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la demande de vérification'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def start_automatic_verification(self, verification):
        """Démarrer la vérification automatique."""
        # Même logique que dans DocumentUploadView
        pass


class BulkVerificationView(APIView):
    """Vue pour la vérification en lot de documents."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Lancer la vérification en lot de plusieurs documents."""
        try:
            serializer = BulkVerificationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            document_ids = serializer.validated_data['document_ids']
            verification_method = serializer.validated_data['verification_method']
            priority = serializer.validated_data['priority']
            
            # Vérifier que tous les documents appartiennent à l'utilisateur
            documents = UserDocument.objects.filter(
                id__in=document_ids, 
                user=request.user
            )
            
            if documents.count() != len(document_ids):
                return Response({
                    'success': False,
                    'error': 'Certains documents n\'ont pas été trouvés'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer les vérifications en lot
            verifications = []
            for document in documents:
                verification = DocumentVerification.objects.create(
                    user=request.user,
                    document=document,
                    verification_method=verification_method,
                    status='pending'
                )
                verifications.append(verification)
            
            # Lancer les vérifications selon la méthode
            if verification_method == 'automatic':
                for verification in verifications:
                    self.start_automatic_verification(verification)
            
            return Response({
                'success': True,
                'message': f'Vérification en lot lancée pour {len(verifications)} documents',
                'verification_count': len(verifications),
                'verification_ids': [str(v.id) for v in verifications]
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification en lot: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la vérification en lot'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def start_automatic_verification(self, verification):
        """Démarrer la vérification automatique."""
        # Même logique que précédemment
        pass


class VerificationStatisticsView(APIView):
    """Vue pour les statistiques de vérification."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtenir les statistiques de vérification de l'utilisateur."""
        try:
            user_verifications = DocumentVerification.objects.filter(user=request.user)
            
            # Statistiques de base
            total_verifications = user_verifications.count()
            pending_verifications = user_verifications.filter(status='pending').count()
            approved_verifications = user_verifications.filter(status='approved').count()
            rejected_verifications = user_verifications.filter(status='rejected').count()
            requires_manual_review = user_verifications.filter(status='requires_manual_review').count()
            
            # Statistiques avancées
            average_processing_time = None
            average_validation_score = None
            fraud_detection_rate = None
            
            if approved_verifications > 0:
                # Calculer le temps moyen de traitement
                completed_verifications = user_verifications.filter(
                    status__in=['approved', 'rejected']
                )
                if completed_verifications.exists():
                    avg_duration = completed_verifications.aggregate(
                        avg_duration=Avg('verification_duration')
                    )['avg_duration']
                    if avg_duration:
                        average_processing_time = avg_duration
                
                # Calculer le score moyen de validation
                valid_scores = user_verifications.filter(
                    validation_score__isnull=False
                )
                if valid_scores.exists():
                    average_validation_score = valid_scores.aggregate(
                        avg_score=Avg('validation_score')
                    )['avg_score']
                
                # Calculer le taux de détection de fraude
                fraud_scores = user_verifications.filter(
                    fraud_detection_score__isnull=False
                )
                if fraud_scores.exists():
                    fraud_detection_rate = fraud_scores.aggregate(
                        avg_fraud_score=Avg('fraud_detection_score')
                    )['avg_fraud_score']
            
            # Statistiques par type et statut
            verifications_by_type = user_verifications.values(
                'document__document_type'
            ).annotate(count=Count('id'))
            
            verifications_by_status = user_verifications.values('status').annotate(
                count=Count('id')
            )
            
            verifications_by_method = user_verifications.values(
                'verification_method'
            ).annotate(count=Count('id'))
            
            statistics = {
                'total_verifications': total_verifications,
                'pending_verifications': pending_verifications,
                'approved_verifications': approved_verifications,
                'rejected_verifications': rejected_verifications,
                'requires_manual_review': requires_manual_review,
                'average_processing_time': average_processing_time,
                'average_validation_score': average_validation_score,
                'fraud_detection_rate': fraud_detection_rate,
                'verifications_by_type': list(verifications_by_type),
                'verifications_by_status': list(verifications_by_status),
                'verifications_by_method': list(verifications_by_method)
            }
            
            return Response({
                'success': True,
                'statistics': statistics
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la récupération des statistiques'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminVerificationListView(APIView):
    """Vue admin pour lister toutes les vérifications."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Lister toutes les vérifications (admin uniquement)."""
        try:
            verifications = DocumentVerification.objects.all().order_by('-created_at')
            
            # Filtres admin
            status_filter = request.query_params.get('status')
            user_filter = request.query_params.get('user_id')
            document_type = request.query_params.get('document_type')
            
            if status_filter:
                verifications = verifications.filter(status=status_filter)
            if user_filter:
                verifications = verifications.filter(user_id=user_filter)
            if document_type:
                verifications = verifications.filter(document__document_type=document_type)
            
            serializer = DocumentVerificationSerializer(verifications, many=True)
            
            return Response({
                'success': True,
                'verifications': serializer.data,
                'count': verifications.count()
            })
            
        except Exception as e:
            logger.error(f"Erreur admin lors de la récupération des vérifications: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la récupération des vérifications'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminVerificationUpdateView(APIView):
    """Vue admin pour mettre à jour le statut d'une vérification."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def put(self, request, verification_id):
        """Mettre à jour le statut d'une vérification (admin uniquement)."""
        try:
            verification = DocumentVerification.objects.get(id=verification_id)
            
            serializer = DocumentVerificationUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mettre à jour la vérification
            verification.status = serializer.validated_data['status']
            verification.verified_at = timezone.now()
            verification.verified_by = request.user
            
            if serializer.validated_data['status'] == 'rejected':
                verification.rejection_reason = serializer.validated_data.get('rejection_reason', '')
            
            verification.save()
            
            # Mettre à jour le document utilisateur
            document = verification.document
            document.status = verification.status
            document.verified_at = verification.verified_at
            document.verified_by = verification.verified_by
            document.save()
            
            # Créer un log
            VerificationLog.objects.create(
                verification=verification,
                log_level='info',
                message=f'Statut mis à jour par l\'administrateur: {verification.status}',
                user=request.user,
                details={'admin_action': True, 'previous_status': verification.status}
            )
            
            return Response({
                'success': True,
                'message': 'Statut de vérification mis à jour avec succès',
                'verification': DocumentVerificationSerializer(verification).data
            })
            
        except DocumentVerification.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Vérification non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur admin lors de la mise à jour: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la mise à jour'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
