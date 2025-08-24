from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
import json

from .models import (
    TranslationCategory, TranslationKey, Translation, 
    UserLanguagePreference, TranslationTemplate, 
    TranslationTemplateContent
)
from .utils import TranslationService

User = get_user_model()

class TranslationModelTests(TestCase):
    """Tests pour les modèles de traduction"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = TranslationCategory.objects.create(
            name='Interface utilisateur',
            code='ui',
            description='Traductions pour l\'interface utilisateur'
        )
        
        self.translation_key = TranslationKey.objects.create(
            key='welcome_message',
            category=self.category,
            description='Message de bienvenue',
            context='Page d\'accueil'
        )
    
    def test_translation_category_creation(self):
        """Test de création d'une catégorie de traduction"""
        self.assertEqual(self.category.name, 'Interface utilisateur')
        self.assertEqual(self.category.code, 'ui')
        self.assertTrue(self.category.is_active)
    
    def test_translation_key_creation(self):
        """Test de création d'une clé de traduction"""
        self.assertEqual(self.translation_key.key, 'welcome_message')
        self.assertEqual(self.translation_key.category, self.category)
        self.assertTrue(self.translation_key.is_active)
    
    def test_translation_creation(self):
        """Test de création d'une traduction"""
        translation = Translation.objects.create(
            key=self.translation_key,
            language_code='fr',
            text='Bienvenue sur KleerLogistics',
            is_approved=True,
            approved_by=self.user
        )
        
        self.assertEqual(translation.language_code, 'fr')
        self.assertEqual(translation.text, 'Bienvenue sur KleerLogistics')
        self.assertTrue(translation.is_approved)
        self.assertEqual(translation.approved_by, self.user)
    
    def test_get_translation_method(self):
        """Test de la méthode get_translation"""
        Translation.objects.create(
            key=self.translation_key,
            language_code='fr',
            text='Bienvenue sur KleerLogistics',
            is_approved=True
        )
        
        Translation.objects.create(
            key=self.translation_key,
            language_code='en',
            text='Welcome to KleerLogistics',
            is_approved=True
        )
        
        # Test avec langue française
        result = self.translation_key.get_translation('fr')
        self.assertEqual(result, 'Bienvenue sur KleerLogistics')
        
        # Test avec langue anglaise
        result = self.translation_key.get_translation('en')
        self.assertEqual(result, 'Welcome to KleerLogistics')
        
        # Test avec langue inexistante
        result = self.translation_key.get_translation('ar')
        self.assertEqual(result, 'welcome_message')  # Retourne la clé
    
    def test_user_language_preference(self):
        """Test des préférences de langue utilisateur"""
        preference = UserLanguagePreference.objects.create(
            user=self.user,
            preferred_language='fr',
            fallback_language='en'
        )
        
        self.assertEqual(preference.preferred_language, 'fr')
        self.assertEqual(preference.fallback_language, 'en')
    
    def test_translation_template(self):
        """Test des modèles de traduction"""
        template = TranslationTemplate.objects.create(
            name='Email de confirmation',
            template_type='email',
            key='email_confirmation',
            variables=['user_name', 'confirmation_link'],
            category=self.category
        )
        
        content = TranslationTemplateContent.objects.create(
            template=template,
            language_code='fr',
            subject='Confirmation de votre compte',
            content='Bonjour {{user_name}}, veuillez confirmer votre compte en cliquant sur {{confirmation_link}}',
            is_approved=True,
            approved_by=self.user
        )
        
        self.assertEqual(template.name, 'Email de confirmation')
        self.assertEqual(template.template_type, 'email')
        self.assertEqual(len(template.variables), 2)
        self.assertEqual(content.language_code, 'fr')
        self.assertTrue(content.is_approved)

class TranslationServiceTests(TestCase):
    """Tests pour le service de traduction"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = TranslationCategory.objects.create(
            name='Interface utilisateur',
            code='ui'
        )
        
        self.translation_key = TranslationKey.objects.create(
            key='welcome_message',
            category=self.category
        )
        
        # Créer des traductions
        Translation.objects.create(
            key=self.translation_key,
            language_code='fr',
            text='Bienvenue sur KleerLogistics',
            is_approved=True
        )
        
        Translation.objects.create(
            key=self.translation_key,
            language_code='en',
            text='Welcome to KleerLogistics',
            is_approved=True
        )
    
    def test_get_translation_service(self):
        """Test du service de récupération de traduction"""
        # Test avec langue française
        result = TranslationService.get_translation('welcome_message', 'fr')
        self.assertEqual(result, 'Bienvenue sur KleerLogistics')
        
        # Test avec langue anglaise
        result = TranslationService.get_translation('welcome_message', 'en')
        self.assertEqual(result, 'Welcome to KleerLogistics')
        
        # Test avec clé inexistante
        result = TranslationService.get_translation('nonexistent_key', 'fr')
        self.assertEqual(result, 'nonexistent_key')
    
    def test_get_multiple_translations(self):
        """Test de récupération de plusieurs traductions"""
        # Créer une deuxième clé
        key2 = TranslationKey.objects.create(
            key='login_button',
            category=self.category
        )
        
        Translation.objects.create(
            key=key2,
            language_code='fr',
            text='Se connecter',
            is_approved=True
        )
        
        keys = ['welcome_message', 'login_button']
        result = TranslationService.get_multiple_translations(keys, 'fr')
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result['welcome_message'], 'Bienvenue sur KleerLogistics')
        self.assertEqual(result['login_button'], 'Se connecter')
    
    def test_render_template(self):
        """Test du rendu de modèle avec variables"""
        template_content = "Bonjour {{user_name}}, votre commande {{order_id}} a été confirmée."
        variables = {
            'user_name': 'Ahmed',
            'order_id': 'KL123456'
        }
        
        result = TranslationService.render_template(template_content, variables)
        expected = "Bonjour Ahmed, votre commande KL123456 a été confirmée."
        self.assertEqual(result, expected)
    
    def test_get_user_language(self):
        """Test de récupération de la langue utilisateur"""
        # Test sans préférence
        result = TranslationService.get_user_language(self.user)
        self.assertEqual(result, 'fr')  # Langue par défaut
        
        # Test avec préférence
        UserLanguagePreference.objects.create(
            user=self.user,
            preferred_language='en',
            fallback_language='fr'
        )
        
        result = TranslationService.get_user_language(self.user)
        self.assertEqual(result, 'en')
    
    def test_detect_language_from_request(self):
        """Test de détection de langue depuis une requête"""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        
        # Test avec paramètre de langue
        request = factory.get('/?lang=en')
        result = TranslationService.detect_language_from_request(request)
        self.assertEqual(result, 'en')
        
        # Test avec en-tête Accept-Language
        request = factory.get('/', HTTP_ACCEPT_LANGUAGE='ar,en;q=0.9,fr;q=0.8')
        result = TranslationService.detect_language_from_request(request)
        self.assertEqual(result, 'ar')
        
        # Test sans paramètres
        request = factory.get('/')
        result = TranslationService.detect_language_from_request(request)
        self.assertEqual(result, 'fr')  # Langue par défaut

class TranslationAPITests(APITestCase):
    """Tests pour l'API de traduction"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.category = TranslationCategory.objects.create(
            name='Interface utilisateur',
            code='ui'
        )
        
        self.translation_key = TranslationKey.objects.create(
            key='welcome_message',
            category=self.category
        )
        
        self.client.force_authenticate(user=self.user)
    
    def test_create_translation_category(self):
        """Test de création d'une catégorie via API"""
        url = reverse('translationcategory-list')
        data = {
            'name': 'Test Category',
            'code': 'test',
            'description': 'Test category for testing'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TranslationCategory.objects.count(), 2)  # +1 pour celle créée dans setUp
    
    def test_create_translation_key(self):
        """Test de création d'une clé de traduction via API"""
        url = reverse('translationkey-list')
        data = {
            'key': 'test_key',
            'category': self.category.id,
            'description': 'Test key',
            'context': 'Test context'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TranslationKey.objects.count(), 2)  # +1 pour celle créée dans setUp
    
    def test_create_translation(self):
        """Test de création d'une traduction via API"""
        # First, create a translation in setUp to have a baseline
        initial_translation = Translation.objects.create(
            key=self.translation_key,
            language_code='fr',
            text='Bienvenue sur KleerLogistics',
            is_approved=True
        )
        
        url = reverse('translation-list')
        data = {
            'key': self.translation_key.id,
            'language_code': 'en',
            'text': 'Test translation'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Translation.objects.count(), 2)  # 1 from setUp + 1 newly created
    
    def test_get_translation_service_api(self):
        """Test de l'API de service de traduction"""
        url = reverse('get-translation')
        response = self.client.get(url, {'key': 'welcome_message', 'language_code': 'fr'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('text', response.data)
    
    def test_bulk_translation_operations(self):
        """Test des opérations en lot sur les traductions"""
        url = reverse('bulk-operations')
        data = {
            'action': 'create',
            'language_code': 'en',
            'translations': [
                {'key': 'welcome_message', 'text': 'Welcome to KleerLogistics'}
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_translation_search(self):
        """Test de recherche de traductions"""
        url = reverse('search-keys')
        response = self.client.get(url, {'query': 'welcome'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
    
    def test_translation_statistics(self):
        """Test des statistiques de traduction"""
        url = reverse('translation-statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_translations', response.data)
    
    def test_user_language_preferences_api(self):
        """Test de l'API des préférences de langue"""
        # Create user language preference first
        UserLanguagePreference.objects.create(
            user=self.user,
            preferred_language='en',
            fallback_language='fr'
        )
        
        url = reverse('my-preferences')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('preferred_language', response.data)

class TranslationIntegrationTests(TestCase):
    """Tests d'intégration pour l'internationalisation"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = TranslationCategory.objects.create(
            name='Interface utilisateur',
            code='ui'
        )
        
        self.translation_key = TranslationKey.objects.create(
            key='welcome_message',
            category=self.category
        )
        
        Translation.objects.create(
            key=self.translation_key,
            language_code='fr',
            text='Bienvenue sur KleerLogistics',
            is_approved=True
        )
        
        Translation.objects.create(
            key=self.translation_key,
            language_code='en',
            text='Welcome to KleerLogistics',
            is_approved=True
        )
    
    def test_translation_cache(self):
        """Test du cache des traductions"""
        # Premier appel - pas en cache
        result1 = TranslationService.get_translation('welcome_message', 'fr')
        self.assertEqual(result1, 'Bienvenue sur KleerLogistics')
        
        # Deuxième appel - devrait être en cache
        result2 = TranslationService.get_translation('welcome_message', 'fr')
        self.assertEqual(result2, 'Bienvenue sur KleerLogistics')
        
        # Vérifier que les résultats sont identiques
        self.assertEqual(result1, result2)
    
    def test_translation_fallback(self):
        """Test du système de fallback de langue"""
        # Créer des traductions en français et anglais
        Translation.objects.get_or_create(
            key=self.translation_key,
            language_code='fr',
            defaults={
                'text': 'Bienvenue sur KleerLogistics',
                'is_approved': True
            }
        )
        
        Translation.objects.get_or_create(
            key=self.translation_key,
            language_code='en',
            defaults={
                'text': 'Welcome to KleerLogistics',
                'is_approved': True
            }
        )
        
        # Créer des préférences utilisateur avec français comme langue principale et anglais comme fallback
        UserLanguagePreference.objects.get_or_create(
            user=self.user,
            defaults={
                'preferred_language': 'fr',
                'fallback_language': 'en'
            }
        )
        
        # Clear cache to ensure fresh results
        from django.core.cache import cache
        cache.clear()
        
        # Tester la récupération en arabe (langue inexistante) - devrait retourner la langue de fallback (anglais)
        result = TranslationService.get_translation('welcome_message', 'ar', self.user)
        self.assertEqual(result, 'Welcome to KleerLogistics')  # Fallback vers l'anglais
    
    def test_translation_approval_workflow(self):
        """Test du workflow d'approbation des traductions"""
        # Créer une traduction non approuvée
        translation = Translation.objects.create(
            key=self.translation_key,
            language_code='ar',
            text='مرحباً بك في KleerLogistics',
            is_approved=False
        )
        
        # Vérifier qu'elle n'est pas retournée par le service (désactiver le fallback)
        result = TranslationService.get_translation('welcome_message', 'ar', allow_fallback=False)
        self.assertEqual(result, 'welcome_message')  # Retourne la clé
        
        # Approuver la traduction
        translation.is_approved = True
        translation.approved_by = self.user
        translation.approved_at = timezone.now()
        translation.save()
        
        # Vérifier qu'elle est maintenant retournée
        result = TranslationService.get_translation('welcome_message', 'ar', allow_fallback=False)
        self.assertEqual(result, 'مرحباً بك في KleerLogistics')
    
    def test_translation_template_rendering(self):
        """Test du rendu de modèles de traduction"""
        template = TranslationTemplate.objects.create(
            name='Email de confirmation',
            template_type='email',
            key='email_confirmation',
            variables=['user_name', 'confirmation_link'],
            category=self.category
        )
        
        content = TranslationTemplateContent.objects.create(
            template=template,
            language_code='fr',
            subject='Confirmation de votre compte',
            content='Bonjour {{user_name}}, veuillez confirmer votre compte en cliquant sur {{confirmation_link}}',
            is_approved=True
        )
        
        # Test du rendu avec variables
        variables = {
            'user_name': 'Ahmed',
            'confirmation_link': 'https://example.com/confirm'
        }
        
        result = TranslationService.render_template(content.content, variables)
        expected = 'Bonjour Ahmed, veuillez confirmer votre compte en cliquant sur https://example.com/confirm'
        self.assertEqual(result, expected)
    
    def test_translation_statistics_calculation(self):
        """Test du calcul des statistiques de traduction"""
        # Créer plusieurs traductions
        Translation.objects.create(
            key=self.translation_key,
            language_code='ar',
            text='مرحباً بك في KleerLogistics',
            is_approved=False
        )
        
        stats = TranslationService.get_translation_statistics()
        
        self.assertEqual(stats['total_translations'], 3)
        self.assertEqual(stats['approved_translations'], 2)
        self.assertEqual(stats['pending_translations'], 1)
        
        # Vérifier les statistiques par langue
        self.assertEqual(stats['by_language']['fr']['total'], 1)
        self.assertEqual(stats['by_language']['en']['total'], 1)
        self.assertEqual(stats['by_language']['ar']['total'], 1)
        
        # Vérifier les statistiques par catégorie
        self.assertEqual(stats['by_category']['Interface utilisateur']['total'], 3)
        self.assertEqual(stats['by_category']['Interface utilisateur']['approved'], 2)
