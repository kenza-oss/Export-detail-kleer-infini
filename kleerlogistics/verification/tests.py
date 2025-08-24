"""
Tests for verification app - Document verification and validation
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
import tempfile
import os
import shutil

from .models import (
    DocumentVerification, DocumentValidationRule, 
    VerificationWorkflow, VerificationLog, DocumentTemplate
)
from users.models import UserDocument

User = get_user_model()


class DocumentVerificationModelTests(TestCase):
    """Tests unitaires pour le modèle DocumentVerification."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        # Créer un document utilisateur de test
        self.document = UserDocument.objects.create(
            user=self.user,
            document_type='passport',
            document_file=SimpleUploadedFile(
                'test_passport.jpg',
                b'fake-image-content',
                content_type='image/jpeg'
            ),
            status='pending'
        )
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        # Supprimer les fichiers de test
        if hasattr(self, 'document') and self.document.document_file:
            try:
                if os.path.exists(self.document.document_file.path):
                    os.unlink(self.document.document_file.path)
            except (OSError, ValueError):
                pass  # Ignorer les erreurs de suppression de fichier
    
    def test_verification_creation(self):
        """Test de création d'une vérification de document."""
        verification = DocumentVerification.objects.create(
            user=self.user,
            document=self.document,
            verification_method='automatic',
            status='pending'
        )
        
        self.assertEqual(verification.user, self.user)
        self.assertEqual(verification.document, self.document)
        self.assertEqual(verification.verification_method, 'automatic')
        self.assertEqual(verification.status, 'pending')
        self.assertIsNotNone(verification.id)
    
    def test_verification_status_properties(self):
        """Test des propriétés de statut de vérification."""
        verification = DocumentVerification.objects.create(
            user=self.user,
            document=self.document,
            verification_method='automatic',
            status='approved'
        )
        
        self.assertTrue(verification.is_approved)
        self.assertFalse(verification.is_rejected)
        self.assertFalse(verification.is_pending)
        self.assertFalse(verification.requires_manual_review)
    
    def test_verification_string_representation(self):
        """Test de la représentation string du modèle."""
        verification = DocumentVerification.objects.create(
            user=self.user,
            document=self.document,
            verification_method='automatic',
            status='pending'
        )
        
        expected_string = f"Vérification {verification.id} - {self.document.document_type} - pending"
        self.assertEqual(str(verification), expected_string)


class DocumentValidationRuleModelTests(TestCase):
    """Tests unitaires pour le modèle DocumentValidationRule."""
    
    def test_validation_rule_creation(self):
        """Test de création d'une règle de validation."""
        rule = DocumentValidationRule.objects.create(
            name='Test Rule',
            document_type='passport',
            validation_type='ocr_extraction',
            is_active=True,
            priority=1,
            threshold_score=85.00,
            description='Règle de test pour l\'extraction OCR'
        )
        
        self.assertEqual(rule.name, 'Test Rule')
        self.assertEqual(rule.document_type, 'passport')
        self.assertEqual(rule.validation_type, 'ocr_extraction')
        self.assertTrue(rule.is_active)
        self.assertEqual(rule.priority, 1)
        self.assertEqual(rule.threshold_score, 85.00)
    
    def test_validation_rule_string_representation(self):
        """Test de la représentation string du modèle."""
        rule = DocumentValidationRule.objects.create(
            name='Test Rule',
            document_type='passport',
            validation_type='ocr_extraction',
            is_active=True,
            priority=1
        )
        
        expected_string = "Test Rule - Passeport - Extraction OCR"
        self.assertEqual(str(rule), expected_string)


class VerificationWorkflowModelTests(TestCase):
    """Tests unitaires pour le modèle VerificationWorkflow."""
    
    def test_workflow_creation(self):
        """Test de création d'un workflow de vérification."""
        workflow = VerificationWorkflow.objects.create(
            name='Test Workflow',
            workflow_type='standard',
            is_active=True,
            auto_approval_threshold=90.00,
            requires_manual_review=False
        )
        
        self.assertEqual(workflow.name, 'Test Workflow')
        self.assertEqual(workflow.workflow_type, 'standard')
        self.assertTrue(workflow.is_active)
        self.assertEqual(workflow.auto_approval_threshold, 90.00)
        self.assertFalse(workflow.requires_manual_review)
    
    def test_workflow_string_representation(self):
        """Test de la représentation string du modèle."""
        workflow = VerificationWorkflow.objects.create(
            name='Test Workflow',
            workflow_type='standard',
            is_active=True
        )
        
        expected_string = "Test Workflow (Workflow standard)"
        self.assertEqual(str(workflow), expected_string)


class VerificationLogModelTests(TestCase):
    """Tests unitaires pour le modèle VerificationLog."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        self.document = UserDocument.objects.create(
            user=self.user,
            document_type='passport',
            document_file=SimpleUploadedFile(
                'test_passport.jpg',
                b'fake-image-content',
                content_type='image/jpeg'
            ),
            status='pending'
        )
        
        self.verification = DocumentVerification.objects.create(
            user=self.user,
            document=self.document,
            verification_method='automatic',
            status='pending'
        )
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        # Supprimer les fichiers de test
        if hasattr(self, 'document') and self.document.document_file:
            try:
                if os.path.exists(self.document.document_file.path):
                    os.unlink(self.document.document_file.path)
            except (OSError, ValueError):
                pass  # Ignorer les erreurs de suppression de fichier
    
    def test_log_creation(self):
        """Test de création d'un log de vérification."""
        log = VerificationLog.objects.create(
            verification=self.verification,
            log_level='info',
            message='Test log message',
            details={'test': 'data'}
        )
        
        self.assertEqual(log.verification, self.verification)
        self.assertEqual(log.log_level, 'info')
        self.assertEqual(log.message, 'Test log message')
        self.assertEqual(log.details, {'test': 'data'})
    
    def test_log_string_representation(self):
        """Test de la représentation string du modèle."""
        log = VerificationLog.objects.create(
            verification=self.verification,
            log_level='info',
            message='Test log message'
        )
        
        expected_string = f"{log.timestamp} - Information - Test log message"
        self.assertEqual(str(log), expected_string)


class DocumentTemplateModelTests(TestCase):
    """Tests unitaires pour le modèle DocumentTemplate."""
    
    def test_template_creation(self):
        """Test de création d'un template de document."""
        template = DocumentTemplate.objects.create(
            name='Test Template',
            document_type='passport',
            country='DZ',
            is_active=True,
            validation_zones={'zone1': [100, 100, 200, 200]},
            required_fields=['name', 'date_of_birth', 'passport_number']
        )
        
        self.assertEqual(template.name, 'Test Template')
        self.assertEqual(template.document_type, 'passport')
        self.assertEqual(template.country, 'DZ')
        self.assertTrue(template.is_active)
        self.assertEqual(template.validation_zones, {'zone1': [100, 100, 200, 200]})
        self.assertEqual(template.required_fields, ['name', 'date_of_birth', 'passport_number'])
    
    def test_template_string_representation(self):
        """Test de la représentation string du modèle."""
        template = DocumentTemplate.objects.create(
            name='Test Template',
            document_type='passport',
            country='DZ',
            is_active=True
        )
        
        expected_string = "Test Template - Passeport (Algérie)"
        self.assertEqual(str(template), expected_string)


class DocumentUploadAPITests(APITestCase):
    """Tests d'API pour l'upload de documents."""
    
    def setUp(self):
        """Configuration initiale pour les tests d'upload."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Créer un dossier temporaire pour les tests
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        # Supprimer le dossier temporaire et son contenu
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, shutil.Error):
            pass  # Ignorer les erreurs de suppression
    
    def test_document_upload_endpoint(self):
        """Test de l'endpoint d'upload de document."""
        # Créer un fichier temporaire
        temp_file_path = os.path.join(self.temp_dir, 'test_passport.jpg')
        with open(temp_file_path, 'wb') as f:
            f.write(b'fake-image-content')
        
        # Ouvrir le fichier pour l'upload
        with open(temp_file_path, 'rb') as file:
            data = {
                'document_type': 'passport',
                'country': 'DZ',
                'description': 'Test passport upload',
                'document_file': file
            }
            
            response = self.client.post('/api/v1/verification/upload/', data, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('verification_id', response.data)
            self.assertIn('document_id', response.data)
    
    def test_document_upload_validation(self):
        """Test de validation de l'upload de document."""
        # Test sans fichier
        data = {
            'document_type': 'passport',
            'country': 'DZ'
        }
        
        response = self.client.post('/api/v1/verification/upload/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_document_upload_unauthorized(self):
        """Test d'upload sans authentification."""
        self.client.force_authenticate(user=None)
        
        # Créer un fichier temporaire
        temp_file_path = os.path.join(self.temp_dir, 'test_passport.jpg')
        with open(temp_file_path, 'wb') as f:
            f.write(b'fake-image-content')
        
        # Ouvrir le fichier pour l'upload
        with open(temp_file_path, 'rb') as file:
            data = {
                'document_type': 'passport',
                'country': 'DZ',
                'document_file': file
            }
            
            response = self.client.post('/api/v1/verification/upload/', data, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BulkVerificationAPITests(APITestCase):
    """Tests d'API pour la vérification en lot."""
    
    def setUp(self):
        """Configuration initiale pour les tests de vérification en lot."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Créer des documents de test
        self.documents = []
        for i in range(3):
            document = UserDocument.objects.create(
                user=self.user,
                document_type='passport',
                document_file=SimpleUploadedFile(
                    f'test_passport_{i}.jpg',
                    b'fake-image-content',
                    content_type='image/jpeg'
                ),
                status='pending'
            )
            self.documents.append(document)
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        # Supprimer les fichiers de test
        for document in self.documents:
            try:
                if document.document_file and os.path.exists(document.document_file.path):
                    os.unlink(document.document_file.path)
            except (OSError, ValueError):
                pass  # Ignorer les erreurs de suppression de fichier
    
    def test_bulk_verification_endpoint(self):
        """Test de l'endpoint de vérification en lot."""
        data = {
            'document_ids': [doc.id for doc in self.documents],
            'verification_method': 'automatic',
            'priority': 'normal'
        }
        
        response = self.client.post('/api/v1/verification/bulk-verify/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('verification_count', response.data)
        self.assertIn('verification_ids', response.data)
    
    def test_bulk_verification_validation(self):
        """Test de validation de la vérification en lot."""
        # Test avec document inexistant
        data = {
            'document_ids': [999, 998, 997],
            'verification_method': 'automatic',
            'priority': 'normal'
        }
        
        response = self.client.post('/api/v1/verification/bulk-verify/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_bulk_verification_empty_list(self):
        """Test de vérification en lot avec liste vide."""
        data = {
            'document_ids': [],
            'verification_method': 'automatic',
            'priority': 'normal'
        }
        
        response = self.client.post('/api/v1/verification/bulk-verify/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class VerificationListAPITests(APITestCase):
    """Tests d'API pour la liste des vérifications."""
    
    def setUp(self):
        """Configuration initiale pour les tests de liste."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Créer des documents et vérifications de test
        self.documents = []
        self.verifications = []
        
        for i in range(3):
            document = UserDocument.objects.create(
                user=self.user,
                document_type='passport',
                document_file=SimpleUploadedFile(
                    f'test_passport_{i}.jpg',
                    b'fake-image-content',
                    content_type='image/jpeg'
                ),
                status='pending'
            )
            self.documents.append(document)
            
            verification = DocumentVerification.objects.create(
                user=self.user,
                document=document,
                verification_method='automatic',
                status='pending'
            )
            self.verifications.append(verification)
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        # Supprimer les fichiers de test
        for document in self.documents:
            try:
                if document.document_file and os.path.exists(document.document_file.path):
                    os.unlink(document.document_file.path)
            except (OSError, ValueError):
                pass  # Ignorer les erreurs de suppression de fichier
    
    def test_verification_list_endpoint(self):
        """Test de l'endpoint de liste des vérifications."""
        response = self.client.get('/api/v1/verification/verifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('verifications', response.data)
        self.assertEqual(len(response.data['verifications']), 3)
    
    def test_verification_list_filtered(self):
        """Test de l'endpoint de liste avec filtres."""
        response = self.client.get('/api/v1/verification/verifications/?status=pending')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('verifications', response.data)
        self.assertEqual(len(response.data['verifications']), 3)


class VerificationDetailAPITests(APITestCase):
    """Tests d'API pour les détails des vérifications."""
    
    def setUp(self):
        """Configuration initiale pour les tests de détail."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Créer un document et une vérification de test
        self.document = UserDocument.objects.create(
            user=self.user,
            document_type='passport',
            document_file=SimpleUploadedFile(
                'test_passport.jpg',
                b'fake-image-content',
                content_type='image/jpeg'
            ),
            status='pending'
        )
        
        self.verification = DocumentVerification.objects.create(
            user=self.user,
            document=self.document,
            verification_method='automatic',
            status='pending'
        )
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        # Supprimer les fichiers de test
        if hasattr(self, 'document') and self.document.document_file:
            try:
                if os.path.exists(self.document.document_file.path):
                    os.unlink(self.document.document_file.path)
            except (OSError, ValueError):
                pass  # Ignorer les erreurs de suppression de fichier
    
    def test_verification_detail_endpoint(self):
        """Test de l'endpoint de détail des vérifications."""
        response = self.client.get(f'/api/v1/verification/verifications/{self.verification.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('verification', response.data)
        self.assertEqual(response.data['verification']['id'], str(self.verification.id))
    
    def test_verification_detail_not_found(self):
        """Test de l'endpoint de détail avec ID inexistant."""
        response = self.client.get('/api/v1/verification/verifications/99999999-9999-9999-9999-999999999999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class VerificationStatisticsAPITests(APITestCase):
    """Tests d'API pour les statistiques de vérification."""
    
    def setUp(self):
        """Configuration initiale pour les tests de statistiques."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Créer des documents et vérifications de test
        self.documents = []
        self.verifications = []
        
        for i in range(3):
            document = UserDocument.objects.create(
                user=self.user,
                document_type='passport',
                document_file=SimpleUploadedFile(
                    f'test_passport_{i}.jpg',
                    b'fake-image-content',
                    content_type='image/jpeg'
                ),
                status='pending'
            )
            self.documents.append(document)
            
            verification = DocumentVerification.objects.create(
                user=self.user,
                document=document,
                verification_method='automatic',
                status='pending'
            )
            self.verifications.append(verification)
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        # Supprimer les fichiers de test
        for document in self.documents:
            try:
                if document.document_file and os.path.exists(document.document_file.path):
                    os.unlink(document.document_file.path)
            except (OSError, ValueError):
                pass  # Ignorer les erreurs de suppression de fichier
    
    def test_verification_statistics_endpoint(self):
        """Test de l'endpoint de statistiques des vérifications."""
        response = self.client.get('/api/v1/verification/statistics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('statistics', response.data)
        self.assertEqual(response.data['statistics']['total_verifications'], 3)
        self.assertEqual(response.data['statistics']['pending_verifications'], 3)


class AdminVerificationAPITests(APITestCase):
    """Tests d'API pour les fonctionnalités admin des vérifications."""
    
    def setUp(self):
        """Configuration initiale pour les tests admin."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
        
        self.regular_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Créer un document et une vérification de test
        self.document = UserDocument.objects.create(
            user=self.regular_user,
            document_type='passport',
            document_file=SimpleUploadedFile(
                'test_passport.jpg',
                b'fake-image-content',
                content_type='image/jpeg'
            ),
            status='pending'
        )
        
        self.verification = DocumentVerification.objects.create(
            user=self.regular_user,
            document=self.document,
            verification_method='automatic',
            status='pending'
        )
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        # Supprimer les fichiers de test
        if hasattr(self, 'document') and self.document.document_file:
            try:
                if os.path.exists(self.document.document_file.path):
                    os.unlink(self.document.document_file.path)
            except (OSError, ValueError):
                pass  # Ignorer les erreurs de suppression de fichier
    
    def test_admin_verification_list_endpoint(self):
        """Test de l'endpoint admin de liste des vérifications."""
        response = self.client.get('/api/v1/verification/admin/verifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('verifications', response.data)
    
    def test_admin_verification_update_endpoint(self):
        """Test de l'endpoint admin de mise à jour des vérifications."""
        data = {
            'status': 'approved',
            'verification_notes': 'Document approuvé par l\'administrateur'
        }
        
        response = self.client.put(
            f'/api/v1/verification/admin/verifications/{self.verification.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('verification', response.data)
        
        # Vérifier que le statut a été mis à jour
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, 'approved')
    
    def test_admin_verification_update_unauthorized(self):
        """Test de mise à jour admin sans privilèges."""
        self.client.force_authenticate(user=self.regular_user)
        
        data = {
            'status': 'approved',
            'verification_notes': 'Tentative d\'accès non autorisé'
        }
        
        response = self.client.put(
            f'/api/v1/verification/admin/verifications/{self.verification.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
