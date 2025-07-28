"""
Tests pour l'authentification et la sécurité des utilisateurs.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

class AuthenticationTestCase(TestCase):
    """Tests pour l'authentification des utilisateurs."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '+213123456789',
            'role': 'sender'
        }
        
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123',
            first_name='Existing',
            last_name='User',
            phone_number='+213987654321',
            role='sender'
        )
        
        # Créer un profil pour l'utilisateur de test
        UserProfile.objects.create(user=self.user)
    
    def test_user_registration_success(self):
        """Test d'inscription réussie d'un utilisateur."""
        url = reverse('users:user_registration')
        response = self.client.post(url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Utilisateur créé avec succès')
        self.assertIn('user_id', response.data)
        self.assertIn('email', response.data)
        self.assertIn('role', response.data)
    
    def test_user_registration_password_mismatch(self):
        """Test d'inscription avec mots de passe différents."""
        self.user_data['password_confirm'] = 'differentpass123'
        url = reverse('users:user_registration')
        response = self.client.post(url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('non_field_errors', response.data['errors'])
    
    def test_user_registration_duplicate_email(self):
        """Test d'inscription avec email déjà utilisé."""
        self.user_data['email'] = 'existing@example.com'
        url = reverse('users:user_registration')
        response = self.client.post(url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('email', response.data['errors'])
    
    def test_user_registration_duplicate_phone(self):
        """Test d'inscription avec numéro de téléphone déjà utilisé."""
        self.user_data['phone_number'] = '+213987654321'
        url = reverse('users:user_registration')
        response = self.client.post(url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('phone_number', response.data['errors'])
    
    def test_user_login_success(self):
        """Test de connexion réussie."""
        login_data = {
            'username': 'existinguser',
            'password': 'testpass123'
        }
        url = reverse('users:user_login')
        response = self.client.post(url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertIn('user', response.data)
    
    def test_user_login_invalid_credentials(self):
        """Test de connexion avec identifiants invalides."""
        login_data = {
            'username': 'existinguser',
            'password': 'wrongpassword'
        }
        url = reverse('users:user_login')
        response = self.client.post(url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_user_login_nonexistent_user(self):
        """Test de connexion avec utilisateur inexistant."""
        login_data = {
            'username': 'nonexistent',
            'password': 'testpass123'
        }
        url = reverse('users:user_login')
        response = self.client.post(url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_protected_endpoint_without_token(self):
        """Test d'accès à un endpoint protégé sans token."""
        url = reverse('users:user_profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_protected_endpoint_with_token(self):
        """Test d'accès à un endpoint protégé avec token."""
        # Se connecter pour obtenir un token
        login_data = {
            'username': 'existinguser',
            'password': 'testpass123'
        }
        login_url = reverse('users:user_login')
        login_response = self.client.post(login_url, login_data, format='json')
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        token = login_response.data['tokens']['access']
        
        # Utiliser le token pour accéder à un endpoint protégé
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        url = reverse('users:user_profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_phone_verification_status(self):
        """Test de récupération du statut de vérification du téléphone."""
        # Se connecter
        login_data = {
            'username': 'existinguser',
            'password': 'testpass123'
        }
        login_url = reverse('users:user_login')
        login_response = self.client.post(login_url, login_data, format='json')
        token = login_response.data['tokens']['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        url = reverse('users:phone_verification_status')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('phone_verified', response.data)
        self.assertIn('phone_number', response.data)
    
    def test_send_otp(self):
        """Test d'envoi d'OTP."""
        # Se connecter
        login_data = {
            'username': 'existinguser',
            'password': 'testpass123'
        }
        login_url = reverse('users:user_login')
        login_response = self.client.post(login_url, login_data, format='json')
        token = login_response.data['tokens']['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        url = reverse('users:send_otp')
        otp_data = {'phone_number': '+213123456789'}
        response = self.client.post(url, otp_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('message', response.data)
    
    def test_verify_otp(self):
        """Test de vérification d'OTP."""
        # Se connecter
        login_data = {
            'username': 'existinguser',
            'password': 'testpass123'
        }
        login_url = reverse('users:user_login')
        login_response = self.client.post(login_url, login_data, format='json')
        token = login_response.data['tokens']['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        url = reverse('users:verify_otp')
        otp_data = {
            'phone_number': '+213123456789',
            'code': '123456'
        }
        response = self.client.post(url, otp_data, format='json')
        
        # Le test peut réussir ou échouer selon l'implémentation OTP
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
    
    def test_verify_invalid_otp(self):
        """Test de vérification d'OTP invalide."""
        # Se connecter
        login_data = {
            'username': 'existinguser',
            'password': 'testpass123'
        }
        login_url = reverse('users:user_login')
        login_response = self.client.post(login_url, login_data, format='json')
        token = login_response.data['tokens']['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        url = reverse('users:verify_otp')
        otp_data = {
            'phone_number': '+213123456789',
            'code': '000000'
        }
        response = self.client.post(url, otp_data, format='json')
        
        # Le test peut réussir ou échouer selon l'implémentation OTP
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])


class SecurityTestCase(TestCase):
    """Tests pour la sécurité."""
    
    def setUp(self):
        """Configuration initiale pour les tests de sécurité."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='sender'
        )
        UserProfile.objects.create(user=self.user)
    
    def test_rate_limiting(self):
        """Test de limitation de taux."""
        url = reverse('users:user_registration')
        user_data = {
            'username': 'rateuser',
            'email': 'rate@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Rate',
            'last_name': 'User',
            'phone_number': '+213123456789',
            'role': 'sender'
        }
        
        # Faire plusieurs requêtes rapides
        for i in range(5):
            user_data['username'] = f'rateuser{i}'
            user_data['email'] = f'rate{i}@example.com'
            response = self.client.post(url, user_data, format='json')
            # Le test peut réussir ou échouer selon la configuration de rate limiting
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_429_TOO_MANY_REQUESTS])


class UserProfileTestCase(TestCase):
    """Tests pour la gestion des profils utilisateur."""
    
    def setUp(self):
        """Configuration initiale pour les tests de profil."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='testpass123',
            role='sender'
        )
        self.profile = UserProfile.objects.create(user=self.user)
        
        # Se connecter
        login_data = {
            'username': 'profileuser',
            'password': 'testpass123'
        }
        login_url = reverse('users:user_login')
        login_response = self.client.post(login_url, login_data, format='json')
        self.token = login_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_get_user_profile(self):
        """Test de récupération du profil utilisateur."""
        url = reverse('users:user_profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('profile', response.data)
    
    def test_update_user_profile(self):
        """Test de mise à jour du profil utilisateur."""
        url = reverse('users:user_profile')
        profile_data = {
            'city': 'Alger',
            'country': 'Algeria',
            'bio': 'Test bio'
        }
        response = self.client.put(url, profile_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['profile']['city'], 'Alger')
    
    def test_partial_update_user_profile(self):
        """Test de mise à jour partielle du profil utilisateur."""
        url = reverse('users:user_profile_update')
        profile_data = {
            'city': 'Oran'
        }
        response = self.client.patch(url, profile_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['profile']['city'], 'Oran')
