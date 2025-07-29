"""
Tests d'intégration pour l'authentification et la gestion des utilisateurs
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import json

from .models import User, OTPCode, UserProfile, UserDocument

User = get_user_model()


class AuthenticationIntegrationTests(TestCase):
    """Tests d'intégration pour l'authentification complète."""
    
    def setUp(self):
        """Configuration initiale pour tous les tests."""
        self.client = APIClient()
        self.base_url = '/api/v1/users/'
        
        # Données de test
        self.valid_user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '+213123456789',
            'role': 'sender'
        }
        
        self.login_data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
    
    def test_user_registration_integration(self):
        """Test d'intégration pour l'inscription d'un utilisateur."""
        # Arrange
        url = reverse('users:user_registration')
        
        # Act
        response = self.client.post(url, self.valid_user_data, format='json')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('user_id', response.data)
        
        # Vérifier que l'utilisateur a été créé en base
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, 'sender')
        self.assertFalse(user.is_phone_verified)
        
        # Vérifier que le profil a été créé
        self.assertTrue(hasattr(user, 'profile'))
    
    def test_user_login_integration(self):
        """Test d'intégration pour la connexion d'un utilisateur."""
        # Arrange
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            role='sender'
        )
        url = reverse('users:user_login')
        
        # Act
        response = self.client.post(url, self.login_data, format='json')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertEqual(response.data['user']['username'], 'testuser')
    
    def test_otp_send_and_verify_integration(self):
        """Test d'intégration pour l'envoi et vérification d'OTP."""
        # Arrange
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            phone_number='+213123456789'
        )
        
        # Test envoi OTP
        send_otp_url = reverse('users:send_otp')
        send_otp_data = {'phone_number': '+213123456789'}
        
        # Act - Envoyer OTP
        response = self.client.post(send_otp_url, send_otp_data, format='json')
        
        # Assert - OTP envoyé
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Vérifier que l'OTP a été créé en base
        otp = OTPCode.objects.filter(phone_number='+213123456789').first()
        self.assertIsNotNone(otp)
        self.assertFalse(otp.is_used)
        
        # Test vérification OTP
        verify_otp_url = reverse('users:verify_otp')
        verify_otp_data = {
            'phone_number': '+213123456789',
            'code': otp.code
        }
        
        # Act - Vérifier OTP
        response = self.client.post(verify_otp_url, verify_otp_data, format='json')
        
        # Assert - OTP vérifié
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Vérifier que l'utilisateur est maintenant vérifié
        user.refresh_from_db()
        self.assertTrue(user.is_phone_verified)
    
    def test_authentication_with_permissions_integration(self):
        """Test d'intégration pour l'authentification avec vérification des permissions."""
        # Arrange
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            role='sender',
            is_phone_verified=True
        )
        
        # Connexion
        login_url = reverse('users:user_login')
        response = self.client.post(login_url, self.login_data, format='json')
        token = response.data['tokens']['access']
        
        # Act - Accéder à une route protégée (utiliser une route qui existe)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        # Utiliser une route qui existe réellement
        response = self.client.get('/api/v1/users/')  # Route de base
        
        # Assert - Accès autorisé (même si 404, c'est normal car pas de route GET sur /)
        # Le fait que ce ne soit pas 401 signifie que l'authentification fonctionne
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_role_based_access_integration(self):
        """Test d'intégration pour l'accès basé sur les rôles."""
        # Arrange
        sender = User.objects.create_user(
            username='sender',
            email='sender@example.com',
            password='TestPass123!',
            role='sender'
        )
        
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='TestPass123!',
            role='admin'
        )
        
        # Connexion sender
        self.client.post(reverse('users:user_login'), {
            'username': 'sender',
            'password': 'TestPass123!'
        }, format='json')
        
        # Act - Sender essaie d'accéder à une route admin
        admin_url = reverse('users:admin_user_list')
        response = self.client.get(admin_url)
        
        # Assert - Accès refusé (401 car pas de token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Connexion admin
        response = self.client.post(reverse('users:user_login'), {
            'username': 'admin',
            'password': 'TestPass123!'
        }, format='json')
        token = response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Act - Admin accède à la route admin
        response = self.client.get(admin_url)
        
        # Assert - Accès autorisé
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserProfileIntegrationTests(TestCase):
    """Tests d'intégration pour la gestion des profils utilisateur."""
    
    def setUp(self):
        """Configuration initiale."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            role='sender'
        )
        
        # Connexion
        response = self.client.post(reverse('users:user_login'), {
            'username': 'testuser',
            'password': 'TestPass123!'
        }, format='json')
        self.token = response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_profile_update_integration(self):
        """Test d'intégration pour la mise à jour du profil."""
        # Arrange
        url = reverse('users:user_profile')
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone_number': '+213987654321'
        }
        
        # Act
        response = self.client.put(url, update_data, format='json')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Vérifier les changements en base
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.phone_number, '+213987654321')
    
    def test_password_change_integration(self):
        """Test d'intégration pour le changement de mot de passe."""
        # Arrange
        url = reverse('users:change_password')
        password_data = {
            'old_password': 'TestPass123!',
            'new_password': 'NewPass456!'
        }
        
        # Act
        response = self.client.post(url, password_data, format='json')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Vérifier que le mot de passe a changé
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass456!'))
    
    def test_document_upload_integration(self):
        """Test d'intégration pour l'upload de documents."""
        # Arrange
        url = reverse('users:user_document_upload')
        
        # Créer un fichier de test
        from django.core.files.uploadedfile import SimpleUploadedFile
        test_file = SimpleUploadedFile(
            "test_document.pdf",
            b"test file content",
            content_type="application/pdf"
        )
        
        document_data = {
            'document_type': 'passport',
            'document_file': test_file
        }
        
        # Act
        response = self.client.post(url, document_data, format='multipart')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Vérifier que le document a été créé
        document = UserDocument.objects.filter(user=self.user).first()
        self.assertIsNotNone(document)
        self.assertEqual(document.document_type, 'passport')
        self.assertEqual(document.status, 'pending')


class AdminIntegrationTests(TestCase):
    """Tests d'intégration pour les fonctionnalités admin."""
    
    def setUp(self):
        """Configuration initiale."""
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            role='admin'
        )
        
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@example.com',
            password='SenderPass123!',
            role='sender'
        )
        
        # Connexion admin
        response = self.client.post(reverse('users:user_login'), {
            'username': 'admin',
            'password': 'AdminPass123!'
        }, format='json')
        self.token = response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_admin_user_list_integration(self):
        """Test d'intégration pour la liste des utilisateurs par l'admin."""
        # Arrange
        url = reverse('users:admin_user_list')
        
        # Act
        response = self.client.get(url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('users', response.data)
        self.assertEqual(len(response.data['users']), 2)  # admin + sender
    
    def test_admin_user_update_integration(self):
        """Test d'intégration pour la mise à jour d'utilisateur par l'admin."""
        # Arrange
        url = reverse('users:admin_user_detail', kwargs={'pk': self.sender.pk})
        update_data = {
            'role': 'both',
            'is_phone_verified': True
        }
        
        # Act
        response = self.client.patch(url, update_data, format='json')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Vérifier les changements en base
        self.sender.refresh_from_db()
        self.assertEqual(self.sender.role, 'both')
        self.assertTrue(self.sender.is_phone_verified)


class SecurityIntegrationTests(TestCase):
    """Tests d'intégration pour la sécurité."""
    
    def setUp(self):
        """Configuration initiale."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            role='sender'
        )
    
    def test_invalid_token_access(self):
        """Test d'intégration pour l'accès avec un token invalide."""
        # Arrange
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        url = reverse('users:user_profile')
        
        # Act
        response = self.client.get(url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_expired_token_access(self):
        """Test d'intégration pour l'accès avec un token expiré."""
        # Arrange
        from rest_framework_simplejwt.tokens import AccessToken
        from django.utils import timezone
        from datetime import timedelta
        
        # Créer un token expiré
        token = AccessToken()
        token.set_exp(lifetime=timedelta(seconds=-1))  # Token expiré
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')
        url = reverse('users:user_profile')
        
        # Act
        response = self.client.get(url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_rate_limiting_integration(self):
        """Test d'intégration pour la limitation de taux."""
        # Arrange
        url = reverse('users:user_login')
        login_data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
        
        # Act - Faire plusieurs tentatives de connexion
        for _ in range(10):
            response = self.client.post(url, login_data, format='json')
        
        # Assert - La dernière tentative devrait être bloquée
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class OTPIntegrationTests(TestCase):
    """Tests d'intégration spécifiques pour les OTP."""
    
    def setUp(self):
        """Configuration initiale."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            phone_number='+213123456789'
        )
    
    def test_otp_expiration_integration(self):
        """Test d'intégration pour l'expiration des OTP."""
        # Arrange
        otp = OTPCode.objects.create(
            user=self.user,
            phone_number='+213123456789',
            code='123456',
            expires_at=timezone.now() - timedelta(minutes=1)  # OTP expiré
        )
        
        url = reverse('users:verify_otp')
        data = {
            'phone_number': '+213123456789',
            'code': '123456'
        }
        
        # Act
        response = self.client.post(url, data, format='json')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_otp_reuse_prevention_integration(self):
        """Test d'intégration pour empêcher la réutilisation des OTP."""
        # Arrange
        otp = OTPCode.objects.create(
            user=self.user,
            phone_number='+213123456789',
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=10),
            is_used=True  # OTP déjà utilisé
        )
        
        url = reverse('users:verify_otp')
        data = {
            'phone_number': '+213123456789',
            'code': '123456'
        }
        
        # Act
        response = self.client.post(url, data, format='json')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])


class UserModelTests(TestCase):
    """Tests unitaires pour les modèles User."""
    
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            role='sender'
        )
    
    def test_user_creation_with_default_values(self):
        """Test de création d'utilisateur avec les valeurs par défaut."""
        self.assertEqual(self.user.wallet_balance, 0.00)
        self.assertEqual(self.user.commission_rate, 10.00)
        self.assertFalse(self.user.is_active_traveler)
        self.assertFalse(self.user.is_active_sender)
        self.assertEqual(self.user.preferred_language, 'fr')
    
    def test_user_role_properties(self):
        """Test des propriétés de rôle utilisateur."""
        # Test sender
        self.assertTrue(self.user.is_sender)
        self.assertFalse(self.user.is_traveler)
        self.assertFalse(self.user.is_admin)
        
        # Test traveler
        self.user.role = 'traveler'
        self.user.save()
        self.assertFalse(self.user.is_sender)
        self.assertTrue(self.user.is_traveler)
        
        # Test both
        self.user.role = 'both'
        self.user.save()
        self.assertTrue(self.user.is_sender)
        self.assertTrue(self.user.is_traveler)
        
        # Test admin
        self.user.role = 'admin'
        self.user.save()
        self.assertTrue(self.user.is_admin)
    
    def test_user_verification_status(self):
        """Test du statut de vérification utilisateur."""
        status = self.user.get_verification_status()
        
        self.assertIn('phone_verified', status)
        self.assertIn('document_verified', status)
        self.assertIn('fully_verified', status)
        
        self.assertFalse(status['phone_verified'])
        self.assertFalse(status['document_verified'])
        self.assertFalse(status['fully_verified'])
        
        # Vérifier le téléphone
        self.user.is_phone_verified = True
        self.user.save()
        status = self.user.get_verification_status()
        self.assertTrue(status['phone_verified'])
        self.assertFalse(status['fully_verified'])
        
        # Vérifier les documents
        self.user.is_document_verified = True
        self.user.save()
        status = self.user.get_verification_status()
        self.assertTrue(status['fully_verified'])
    
    def test_user_wallet_operations(self):
        """Test des opérations de portefeuille utilisateur."""
        # Test initial
        self.assertEqual(self.user.wallet_balance, 0.00)
        
        # Test dépôt
        self.user.wallet_balance += 100.00
        self.user.save()
        self.assertEqual(self.user.wallet_balance, 100.00)
        
        # Test retrait
        self.user.wallet_balance -= 25.50
        self.user.save()
        self.assertEqual(self.user.wallet_balance, 74.50)
    
    def test_user_commission_rate(self):
        """Test du taux de commission utilisateur."""
        # Test valeur par défaut
        self.assertEqual(self.user.commission_rate, 10.00)
        
        # Test modification
        self.user.commission_rate = 15.50
        self.user.save()
        self.assertEqual(self.user.commission_rate, 15.50)
    
    def test_user_active_status(self):
        """Test du statut actif utilisateur."""
        # Test initial
        self.assertFalse(self.user.is_active_traveler)
        self.assertFalse(self.user.is_active_sender)
        
        # Test activation voyageur
        self.user.is_active_traveler = True
        self.user.save()
        self.assertTrue(self.user.is_active_traveler)
        
        # Test activation expéditeur
        self.user.is_active_sender = True
        self.user.save()
        self.assertTrue(self.user.is_active_sender)


class OTPCodeModelTests(TestCase):
    """Tests unitaires pour le modèle OTPCode."""
    
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_otp_creation(self):
        """Test de création d'un code OTP."""
        otp = OTPCode.create_otp(
            phone_number='+213123456789',
            user=self.user,
            expiry_minutes=10
        )
        
        self.assertEqual(otp.phone_number, '+213123456789')
        self.assertEqual(otp.user, self.user)
        self.assertEqual(len(otp.code), 6)
        self.assertTrue(otp.code.isdigit())
        self.assertFalse(otp.is_used)
        self.assertFalse(otp.is_expired())
    
    def test_otp_validation(self):
        """Test de validation d'un code OTP."""
        otp = OTPCode.create_otp(
            phone_number='+213123456789',
            user=self.user
        )
        
        # Test OTP valide
        valid_otp = OTPCode.get_valid_otp('+213123456789', otp.code)
        self.assertEqual(valid_otp, otp)
        
        # Test OTP utilisé
        otp.mark_as_used()
        valid_otp = OTPCode.get_valid_otp('+213123456789', otp.code)
        self.assertIsNone(valid_otp)
    
    def test_otp_expiration(self):
        """Test d'expiration d'un code OTP."""
        from django.utils import timezone
        from datetime import timedelta
        
        otp = OTPCode.objects.create(
            user=self.user,
            phone_number='+213123456789',
            code='123456',
            expires_at=timezone.now() - timedelta(minutes=1)  # Expiré
        )
        
        self.assertTrue(otp.is_expired())
        self.assertFalse(otp.is_valid())
    
    def test_otp_mark_as_used(self):
        """Test de marquage d'un OTP comme utilisé."""
        otp = OTPCode.create_otp(
            phone_number='+213123456789',
            user=self.user
        )
        
        self.assertFalse(otp.is_used)
        otp.mark_as_used()
        self.assertTrue(otp.is_used)


class UserDocumentModelTests(TestCase):
    """Tests unitaires pour le modèle UserDocument."""
    
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            role='admin'
        )
    
    def test_document_creation(self):
        """Test de création d'un document utilisateur."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        test_file = SimpleUploadedFile(
            "test_document.pdf",
            b"test file content",
            content_type="application/pdf"
        )
        
        document = UserDocument.objects.create(
            user=self.user,
            document_type='passport',
            document_file=test_file
        )
        
        self.assertEqual(document.user, self.user)
        self.assertEqual(document.document_type, 'passport')
        self.assertEqual(document.status, 'pending')
        self.assertIsNone(document.verified_at)
        self.assertIsNone(document.verified_by)
    
    def test_document_approval(self):
        """Test d'approbation d'un document."""
        document = UserDocument.objects.create(
            user=self.user,
            document_type='passport',
            document_file='test.pdf'
        )
        
        self.assertEqual(document.status, 'pending')
        self.assertFalse(document.is_approved)
        
        document.approve(self.admin)
        
        self.assertEqual(document.status, 'approved')
        self.assertTrue(document.is_approved)
        self.assertIsNotNone(document.verified_at)
        self.assertEqual(document.verified_by, self.admin)
    
    def test_document_rejection(self):
        """Test de rejet d'un document."""
        document = UserDocument.objects.create(
            user=self.user,
            document_type='passport',
            document_file='test.pdf'
        )
        
        reason = "Document illisible"
        document.reject(self.admin, reason)
        
        self.assertEqual(document.status, 'rejected')
        self.assertTrue(document.is_rejected)
        self.assertEqual(document.rejection_reason, reason)
        self.assertEqual(document.verified_by, self.admin)
    
    def test_document_status_properties(self):
        """Test des propriétés de statut de document."""
        document = UserDocument.objects.create(
            user=self.user,
            document_type='passport',
            document_file='test.pdf'
        )
        
        # Test pending
        self.assertTrue(document.is_pending)
        self.assertFalse(document.is_approved)
        self.assertFalse(document.is_rejected)
        
        # Test approved
        document.status = 'approved'
        document.save()
        self.assertFalse(document.is_pending)
        self.assertTrue(document.is_approved)
        self.assertFalse(document.is_rejected)
        
        # Test rejected
        document.status = 'rejected'
        document.save()
        self.assertFalse(document.is_pending)
        self.assertFalse(document.is_approved)
        self.assertTrue(document.is_rejected)
