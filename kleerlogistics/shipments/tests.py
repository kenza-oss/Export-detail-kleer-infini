"""
Tests complets pour le module shipments
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import Shipment, Package, ShipmentDocument, ShipmentRating, ShipmentTracking

User = get_user_model()


class ShipmentModelTests(TestCase):
    """Tests unitaires pour les modèles Shipment."""
    
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            role='sender'
        )
        
        self.shipment = Shipment.objects.create(
            sender=self.user,
            package_type='electronics',
            description='Test shipment',
            weight=2.5,
            dimensions={'length': 30, 'width': 20, 'height': 15},
            origin_city='Alger',
            origin_address='123 Test Street, Alger',
            destination_city='Oran',
            destination_country='Algeria',
            destination_address='456 Test Street, Oran',
            recipient_name='John Doe',
            recipient_phone='+213123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7)
        )
    
    def test_shipment_creation(self):
        """Test de création d'un envoi."""
        self.assertEqual(self.shipment.sender, self.user)
        self.assertEqual(self.shipment.package_type, 'electronics')
        self.assertEqual(self.shipment.weight, 2.5)
        self.assertEqual(self.shipment.status, 'draft')
        self.assertFalse(self.shipment.is_paid)
        self.assertIsNotNone(self.shipment.tracking_number)
    
    def test_shipment_tracking_number_generation(self):
        """Test de génération automatique du numéro de suivi."""
        shipment = Shipment.objects.create(
            sender=self.user,
            package_type='document',
            description='Test shipment without tracking',
            weight=0.5,
            dimensions={'length': 20, 'width': 15, 'height': 5},
            origin_city='Alger',
            origin_address='123 Test Street, Alger',
            destination_city='Oran',
            destination_country='Algeria',
            destination_address='456 Test Street, Oran',
            recipient_name='Jane Doe',
            recipient_phone='+213123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7)
        )
        
        self.assertIsNotNone(shipment.tracking_number)
        self.assertTrue(len(shipment.tracking_number) > 0)
    
    def test_shipment_status_transitions(self):
        """Test des transitions de statut d'envoi."""
        # Test draft -> pending
        self.assertEqual(self.shipment.status, 'draft')
        
        self.shipment.status = 'pending'
        self.shipment.save()
        self.assertEqual(self.shipment.status, 'pending')
        
        # Test pending -> matched
        self.shipment.status = 'matched'
        self.shipment.save()
        self.assertEqual(self.shipment.status, 'matched')
        
        # Test matched -> in_transit
        self.shipment.status = 'in_transit'
        self.shipment.save()
        self.assertEqual(self.shipment.status, 'in_transit')
        
        # Test in_transit -> delivered
        self.shipment.status = 'delivered'
        self.shipment.save()
        self.assertEqual(self.shipment.status, 'delivered')
    
    def test_shipment_payment_operations(self):
        """Test des opérations de paiement."""
        # Test initial
        self.assertFalse(self.shipment.is_paid)
        self.assertEqual(self.shipment.payment_status, 'pending')
        
        # Test paiement
        self.shipment.price = 50.00
        self.shipment.is_paid = True
        self.shipment.payment_status = 'paid'
        self.shipment.payment_method = 'wallet'
        self.shipment.payment_date = timezone.now()
        self.shipment.save()
        
        self.assertTrue(self.shipment.is_paid)
        self.assertEqual(self.shipment.payment_status, 'paid')
        self.assertEqual(self.shipment.payment_method, 'wallet')
        self.assertIsNotNone(self.shipment.payment_date)
    
    def test_shipment_otp_operations(self):
        """Test des opérations OTP."""
        # Test génération OTP
        self.shipment.otp_code = '123456'
        self.shipment.otp_generated_at = timezone.now()
        self.shipment.save()
        
        self.assertEqual(self.shipment.otp_code, '123456')
        self.assertIsNotNone(self.shipment.otp_generated_at)
        
        # Test OTP de livraison
        self.shipment.delivery_otp = '654321'
        self.shipment.save()
        
        self.assertEqual(self.shipment.delivery_otp, '654321')
    
    def test_shipment_properties(self):
        """Test des propriétés calculées."""
        # Test destination
        self.assertEqual(self.shipment.destination, 'Oran, Algeria')
        
        # Test origin
        self.assertEqual(self.shipment.origin, 'Alger')
        
        # Test is_overdue (pas encore en retard)
        self.assertFalse(self.shipment.is_overdue)
        
        # Test can_be_matched
        self.assertTrue(self.shipment.can_be_matched)
    
    def test_shipment_validation(self):
        """Test de validation des données d'envoi."""
        # Test poids invalide
        self.shipment.weight = 0.00
        with self.assertRaises(ValidationError):
            self.shipment.full_clean()
        
        # Test poids négatif
        self.shipment.weight = -1.00
        with self.assertRaises(ValidationError):
            self.shipment.full_clean()
        
        # Test poids valide
        self.shipment.weight = 1.00
        self.shipment.full_clean()  # Ne devrait pas lever d'exception


class PackageModelTests(TestCase):
    """Tests unitaires pour le modèle Package."""
    
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            role='sender'
        )
        
        self.shipment = Shipment.objects.create(
            sender=self.user,
            package_type='electronics',
            description='Test shipment',
            weight=2.5,
            dimensions={'length': 30, 'width': 20, 'height': 15},
            origin_city='Alger',
            origin_address='123 Test Street, Alger',
            destination_city='Oran',
            destination_country='Algeria',
            destination_address='456 Test Street, Oran',
            recipient_name='John Doe',
            recipient_phone='+213123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7)
        )
    
        self.package = Package.objects.create(
            shipment=self.shipment,
            category='medium',
            length=30.0,
            width=20.0,
            height=15.0,
            requires_special_handling=False,
            is_hazardous=False,
            temperature_sensitive=False,
            handling_instructions='Handle with care',
            storage_requirements='Store in dry place'
        )
    
    def test_package_creation(self):
        """Test de création d'un colis."""
        self.assertEqual(self.package.shipment, self.shipment)
        self.assertEqual(self.package.category, 'medium')
        self.assertEqual(self.package.length, 30.0)
        self.assertEqual(self.package.width, 20.0)
        self.assertEqual(self.package.height, 15.0)
        self.assertFalse(self.package.requires_special_handling)
        self.assertFalse(self.package.is_hazardous)
        self.assertFalse(self.package.temperature_sensitive)
    
    def test_package_volume_calculation(self):
        """Test du calcul automatique du volume."""
        # Volume = 30 * 20 * 15 = 9000 cm³ = 9.0 dm³
        expected_volume = Decimal('9000.00')  # Corriger l'unité
        self.assertEqual(self.package.volume, expected_volume)
        
        # Test avec nouvelles dimensions
        self.package.length = 40.0
        self.package.width = 25.0
        self.package.height = 20.0
        self.package.save()
        
        # Volume = 40 * 25 * 20 = 20000 cm³ = 20.0 dm³
        expected_volume = Decimal('20000.00')  # Corriger l'unité
        self.assertEqual(self.package.volume, expected_volume)
    
    def test_package_temperature_handling(self):
        """Test de gestion des températures."""
        # Test colis sensible à la température
        self.package.temperature_sensitive = True
        self.package.min_temperature = 2.0
        self.package.max_temperature = 8.0
        self.package.save()
        
        self.assertTrue(self.package.temperature_sensitive)
        self.assertEqual(self.package.min_temperature, 2.0)
        self.assertEqual(self.package.max_temperature, 8.0)
    
    def test_package_validation(self):
        """Test de validation des dimensions."""
        # Test dimensions invalides
        self.package.length = 0.00
        with self.assertRaises(ValidationError):
            self.package.full_clean()
        
        # Test dimensions négatives
        self.package.length = -1.00
        with self.assertRaises(ValidationError):
            self.package.full_clean()
        
        # Test dimensions valides
        self.package.length = 1.00
        self.package.full_clean()  # Ne devrait pas lever d'exception


class ShipmentDocumentModelTests(TestCase):
    """Tests unitaires pour le modèle ShipmentDocument."""
    
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            role='sender'
        )
        
        self.shipment = Shipment.objects.create(
            sender=self.user,
            package_type='electronics',
            description='Test shipment',
            weight=2.5,
            dimensions={'length': 30, 'width': 20, 'height': 15},
            origin_city='Alger',
            origin_address='123 Test Street, Alger',
            destination_city='Oran',
            destination_country='Algeria',
            destination_address='456 Test Street, Oran',
            recipient_name='John Doe',
            recipient_phone='+213123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7)
        )
        
    def test_document_creation(self):
        """Test de création d'un document d'envoi."""
        test_file = SimpleUploadedFile(
            "test_document.pdf",
            b"test file content",
            content_type="application/pdf"
        )
        
        document = ShipmentDocument.objects.create(
            shipment=self.shipment,
            document_type='invoice',
            title='Test Invoice',
            file=test_file,
            description='Test document description',
            file_size=1024,
            mime_type='application/pdf'
        )
        
        self.assertEqual(document.shipment, self.shipment)
        self.assertEqual(document.document_type, 'invoice')
        self.assertEqual(document.title, 'Test Invoice')
        self.assertFalse(document.is_verified)
        self.assertIsNone(document.verified_by)
        self.assertIsNone(document.verified_at)
    
    def test_document_verification(self):
        """Test de vérification d'un document."""
        document = ShipmentDocument.objects.create(
            shipment=self.shipment,
            document_type='invoice',
            title='Test Invoice',
            file='test.pdf',
            description='Test document'
        )
        
        # Vérifier le document
        document.is_verified = True
        document.verified_by = self.user
        document.verified_at = timezone.now()
        document.save()
        
        self.assertTrue(document.is_verified)
        self.assertEqual(document.verified_by, self.user)
        self.assertIsNotNone(document.verified_at)


class ShipmentRatingModelTests(TestCase):
    """Tests unitaires pour le modèle ShipmentRating."""
    
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            role='sender'
        )
        
        self.rater = User.objects.create_user(
            username='rater',
            email='rater@example.com',
            password='TestPass123!',
            role='traveler'
        )
        
        self.shipment = Shipment.objects.create(
            sender=self.user,
            package_type='electronics',
            description='Test shipment',
            weight=2.5,
            dimensions={'length': 30, 'width': 20, 'height': 15},
            origin_city='Alger',
            origin_address='123 Test Street, Alger',
            destination_city='Oran',
            destination_country='Algeria',
            destination_address='456 Test Street, Oran',
            recipient_name='John Doe',
            recipient_phone='+213123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7)
        )
    
    def test_rating_creation(self):
        """Test de création d'une évaluation."""
        rating = ShipmentRating.objects.create(
            shipment=self.shipment,
            rater=self.rater,
            overall_rating=4,
            delivery_speed=5,
            package_condition=4,
            communication=3,
            comment='Great service!',
            is_public=True
        )
        
        self.assertEqual(rating.shipment, self.shipment)
        self.assertEqual(rating.rater, self.rater)
        self.assertEqual(rating.overall_rating, 4)
        self.assertEqual(rating.delivery_speed, 5)
        self.assertEqual(rating.package_condition, 4)
        self.assertEqual(rating.communication, 3)
        self.assertEqual(rating.comment, 'Great service!')
        self.assertTrue(rating.is_public)
    
    def test_rating_average_calculation(self):
        """Test du calcul de la note moyenne."""
        rating = ShipmentRating.objects.create(
            shipment=self.shipment,
            rater=self.rater,
            overall_rating=4,
            delivery_speed=5,
            package_condition=4,
            communication=3,
            comment='Test rating'
        )
        
        # Moyenne = (4 + 5 + 4 + 3) / 4 = 4.0
        expected_average = 4.0
        self.assertEqual(rating.average_rating, expected_average)
    
    def test_rating_validation(self):
        """Test de validation des notes."""
        # Test note invalide (trop élevée)
        rating = ShipmentRating(
            shipment=self.shipment,
            rater=self.rater,
            overall_rating=6,  # Trop élevé
            delivery_speed=5,
            package_condition=4,
            communication=3
        )
        with self.assertRaises(ValidationError):
            rating.full_clean()
        
        # Test note invalide (trop basse)
        rating = ShipmentRating(
            shipment=self.shipment,
            rater=self.rater,
            overall_rating=0,  # Trop bas
            delivery_speed=5,
            package_condition=4,
            communication=3
        )
        with self.assertRaises(ValidationError):
            rating.full_clean()


class ShipmentTrackingModelTests(TestCase):
    """Tests unitaires pour le modèle ShipmentTracking."""
    
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            role='sender'
        )
        
        self.shipment = Shipment.objects.create(
            sender=self.user,
            package_type='electronics',
            description='Test shipment',
            weight=2.5,
            dimensions={'length': 30, 'width': 20, 'height': 15},
            origin_city='Alger',
            origin_address='123 Test Street, Alger',
            destination_city='Oran',
            destination_country='Algeria',
            destination_address='456 Test Street, Oran',
            recipient_name='John Doe',
            recipient_phone='+213123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7)
        )
    
    def test_tracking_event_creation(self):
        """Test de création d'un événement de suivi."""
        event = ShipmentTracking.objects.create(
            shipment=self.shipment,
            status='created',
            event_type='created',
            description='Shipment created',
            location='Alger',
            created_by=self.user
        )
        
        self.assertEqual(event.shipment, self.shipment)
        self.assertEqual(event.status, 'created')
        self.assertEqual(event.event_type, 'created')
        self.assertEqual(event.description, 'Shipment created')
        self.assertEqual(event.location, 'Alger')
        self.assertEqual(event.created_by, self.user)
    
    def test_tracking_event_shipment_status_update(self):
        """Test de mise à jour du statut du shipment lors de la création d'un événement."""
        # Créer un événement de livraison
        event = ShipmentTracking.objects.create(
            shipment=self.shipment,
            status='delivered',
            event_type='delivered',
            description='Shipment delivered',
            location='Oran',
            created_by=self.user
        )
        
        # Vérifier que le statut du shipment a été mis à jour
        self.shipment.refresh_from_db()
        self.assertEqual(self.shipment.status, 'delivered')


class ShipmentValidationTests(TestCase):
    """Tests de validation pour les envois."""
    
    def test_shipment_weight_validation(self):
        """Test de validation du poids."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            role='sender'
        )
        
        # Test poids valide
        shipment = Shipment(
            sender=user,
            package_type='electronics',
            description='Test shipment',
            weight=1.00,
            dimensions={'length': 30, 'width': 20, 'height': 15},
            origin_city='Alger',
            origin_address='123 Test Street, Alger',
            destination_city='Oran',
            destination_country='Algeria',
            destination_address='456 Test Street, Oran',
            recipient_name='John Doe',
            recipient_phone='+213123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7)
        )
        shipment.full_clean()  # Ne devrait pas lever d'exception
        
        # Test poids invalide
        shipment.weight = 0.00
        with self.assertRaises(ValidationError):
            shipment.full_clean()
    
    def test_shipment_date_validation(self):
        """Test de validation des dates."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            role='sender'
        )
        
        # Test dates valides
        shipment = Shipment(
            sender=user,
            package_type='electronics',
            description='Test shipment',
            weight=1.00,
            dimensions={'length': 30, 'width': 20, 'height': 15},
            origin_city='Alger',
            origin_address='123 Test Street, Alger',
            destination_city='Oran',
            destination_country='Algeria',
            destination_address='456 Test Street, Oran',
            recipient_name='John Doe',
            recipient_phone='+213123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7)
        )
        shipment.full_clean()  # Ne devrait pas lever d'exception


class ShipmentPerformanceTests(TestCase):
    """Tests de performance pour les envois."""
    
    def test_bulk_shipment_creation(self):
        """Test de création en masse d'envois."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            role='sender'
        )
    
        start_time = timezone.now()
        
        # Créer 100 envois
        for i in range(100):
            Shipment.objects.create(
                sender=user,
                package_type='electronics',
                description=f'Test shipment {i}',
                weight=1.00,
                dimensions={'length': 30, 'width': 20, 'height': 15},
                origin_city='Alger',
                origin_address='123 Test Street, Alger',
                destination_city='Oran',
                destination_country='Algeria',
                destination_address='456 Test Street, Oran',
                recipient_name=f'Recipient {i}',
                recipient_phone='+213123456789',
                preferred_pickup_date=timezone.now() + timedelta(days=1),
                max_delivery_date=timezone.now() + timedelta(days=7)
            )
        
        end_time = timezone.now()
        creation_time = (end_time - start_time).total_seconds()
        
        # Vérifier que la création en masse est rapide (< 10 secondes)
        self.assertLess(creation_time, 10.0)
        self.assertEqual(Shipment.objects.count(), 100)
    
    def test_shipment_query_performance(self):
        """Test de performance des requêtes d'envoi."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            role='sender'
        )
        
        # Créer des envois avec différents statuts
        statuses = ['draft', 'pending', 'matched', 'in_transit', 'delivered']
        for i, status in enumerate(statuses):
            for j in range(20):  # 20 envois par statut
                Shipment.objects.create(
                    sender=user,
                    package_type='electronics',
                    description=f'Test shipment {status}_{j}',
                    weight=1.00,
                    dimensions={'length': 30, 'width': 20, 'height': 15},
                    origin_city='Alger',
                    origin_address='123 Test Street, Alger',
                    destination_city='Oran',
                    destination_country='Algeria',
                    destination_address='456 Test Street, Oran',
                    recipient_name=f'Recipient {status}_{j}',
                    recipient_phone='+213123456789',
                    preferred_pickup_date=timezone.now() + timedelta(days=1),
                    max_delivery_date=timezone.now() + timedelta(days=7),
                    status=status
                )
        
        # Test de requête avec filtres
        start_time = timezone.now()
        
        # Requête avec filtre par statut
        pending_shipments = Shipment.objects.filter(status='pending')
        delivered_shipments = Shipment.objects.filter(status='delivered')
        draft_shipments = Shipment.objects.filter(status='draft')
        
        end_time = timezone.now()
        query_time = (end_time - start_time).total_seconds()
        
        # Vérifier que les requêtes sont rapides (< 1 seconde)
        self.assertLess(query_time, 1.0)
        self.assertEqual(pending_shipments.count(), 20)
        self.assertEqual(delivered_shipments.count(), 20)
        self.assertEqual(draft_shipments.count(), 20)


# Tests d'intégration et API conservés...
