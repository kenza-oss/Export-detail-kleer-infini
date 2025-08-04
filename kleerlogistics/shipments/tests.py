"""
Tests for shipments app - Core functionality testing
"""

import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import datetime, timedelta

from .models import Shipment, Package, ShipmentDocument, ShipmentRating, ShipmentTracking
from .serializers import ShipmentCreateSerializer, ShipmentDetailSerializer

User = get_user_model()


class ShipmentModelTest(TestCase):
    """Tests unitaires pour le modèle Shipment."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.shipment_data = {
            'origin_city': 'Alger',
            'destination_city': 'Paris',
            'destination_country': 'France',
            'weight': Decimal('2.5'),
            'description': 'Documents importants',
            'package_type': 'document',
            'origin_address': '123 Rue de la Paix, Alger',
            'destination_address': '456 Avenue des Champs, Paris',
            'recipient_name': 'Jean Dupont',
            'recipient_phone': '+33123456789',
            'recipient_email': 'jean.dupont@example.com',
            'preferred_pickup_date': timezone.now() + timedelta(days=1),
            'max_delivery_date': timezone.now() + timedelta(days=7),
            'urgency': 'medium',
            'value': Decimal('100.00'),
            'is_fragile': False,
            'special_instructions': 'Livraison à domicile',
            'insurance_requested': True,
            'payment_method': 'card'
        }
    
    def test_shipment_creation(self):
        """Test de création d'un envoi."""
        shipment = Shipment.objects.create(
            sender=self.user,
            **self.shipment_data
        )
        
        self.assertIsNotNone(shipment.tracking_number)
        self.assertTrue(shipment.tracking_number.startswith('KL'))
        self.assertEqual(shipment.status, 'draft')
        self.assertEqual(shipment.sender, self.user)
        self.assertEqual(shipment.origin_city, 'Alger')
        self.assertEqual(shipment.destination_city, 'Paris')
    
    def test_shipment_str_representation(self):
        """Test de la représentation string d'un envoi."""
        shipment = Shipment.objects.create(
            sender=self.user,
            **self.shipment_data
        )
        
        expected_str = f"Shipment {shipment.tracking_number} - Alger to Paris"
        self.assertEqual(str(shipment), expected_str)
    
    def test_shipment_is_overdue(self):
        """Test de la propriété is_overdue."""
        # Créer une copie des données sans max_delivery_date
        overdue_data = {k: v for k, v in self.shipment_data.items() if k != 'max_delivery_date'}
        normal_data = {k: v for k, v in self.shipment_data.items() if k != 'max_delivery_date'}
        
        # Envoi en retard - créer d'abord avec des dates valides, puis modifier
        overdue_shipment = Shipment.objects.create(
            sender=self.user,
            **overdue_data,
            status='in_transit',
            max_delivery_date=timezone.now() + timedelta(days=1)  # Date valide pour la création
        )
        # Modifier la date après création pour éviter la validation
        Shipment.objects.filter(id=overdue_shipment.id).update(
            max_delivery_date=timezone.now() - timedelta(days=1)
        )
        overdue_shipment.refresh_from_db()
        
        # Envoi normal
        normal_shipment = Shipment.objects.create(
            sender=self.user,
            **normal_data,
            status='in_transit',
            max_delivery_date=timezone.now() + timedelta(days=1)
        )
        
        self.assertTrue(overdue_shipment.is_overdue)
        self.assertFalse(normal_shipment.is_overdue)
    
    def test_shipment_can_be_matched(self):
        """Test de la propriété can_be_matched."""
        shipment = Shipment.objects.create(
            sender=self.user,
            **self.shipment_data
        )
        
        # Envoi en brouillon peut être associé
        self.assertTrue(shipment.can_be_matched)
        
        # Envoi déjà associé ne peut plus être associé
        shipment.status = 'matched'
        shipment.save()
        self.assertFalse(shipment.can_be_matched)


class PackageModelTest(TestCase):
    """Tests unitaires pour le modèle Package."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.shipment = Shipment.objects.create(
            sender=self.user,
            origin_city='Alger',
            destination_city='Paris',
            destination_country='France',
            weight=Decimal('2.5'),
            description='Test shipment',
            package_type='document',
            origin_address='Test origin',
            destination_address='Test destination',
            recipient_name='Test Recipient',
            recipient_phone='+33123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7)
        )
    
    def test_package_creation(self):
        """Test de création d'un colis."""
        package = Package.objects.create(
            shipment=self.shipment,
            category='small',
            length=Decimal('20.0'),
            width=Decimal('15.0'),
            height=Decimal('10.0'),
            requires_special_handling=False,
            is_hazardous=False,
            temperature_sensitive=False,
            handling_instructions='Manipuler avec soin',
            storage_requirements='Température ambiante'
        )
        
        self.assertEqual(package.shipment, self.shipment)
        self.assertEqual(package.category, 'small')
        self.assertIsNotNone(package.volume)
    
    def test_package_volume_calculation(self):
        """Test du calcul automatique du volume."""
        package = Package.objects.create(
            shipment=self.shipment,
            category='small',
            length=Decimal('20.0'),
            width=Decimal('15.0'),
            height=Decimal('10.0')
        )
        
        expected_volume = Decimal('20.0') * Decimal('15.0') * Decimal('10.0')
        self.assertEqual(package.volume, expected_volume)


class ShipmentSerializerTest(TestCase):
    """Tests pour les serializers."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.valid_data = {
            'origin_city': 'Alger',
            'destination_city': 'Paris',
            'destination_country': 'France',
            'weight': Decimal('2.5'),
            'description': 'Documents importants',
            'package_type': 'document',
            'origin_address': '123 Rue de la Paix, Alger',
            'destination_address': '456 Avenue des Champs, Paris',
            'recipient_name': 'Jean Dupont',
            'recipient_phone': '+33123456789',
            'preferred_pickup_date': timezone.now() + timedelta(days=1),
            'max_delivery_date': timezone.now() + timedelta(days=7)
        }
    
    def test_shipment_create_serializer_valid(self):
        """Test du serializer de création avec données valides."""
        serializer = ShipmentCreateSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
    
    def test_shipment_create_serializer_invalid_weight(self):
        """Test du serializer avec poids invalide."""
        invalid_data = self.valid_data.copy()
        invalid_data['weight'] = Decimal('-1.0')
        
        serializer = ShipmentCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('weight', serializer.errors)
    
    def test_shipment_create_serializer_same_origin_destination(self):
        """Test de validation avec origine et destination identiques."""
        invalid_data = self.valid_data.copy()
        invalid_data['destination_city'] = 'Alger'
        
        serializer = ShipmentCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)


class ShipmentAPITest(APITestCase):
    """Tests pour les vues API des envois."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=self.user)
        
        self.shipment = Shipment.objects.create(
            sender=self.user,
            origin_city='Alger',
            destination_city='Paris',
            destination_country='France',
            weight=Decimal('2.5'),
            description='Test shipment',
            package_type='document',
            origin_address='Test origin',
            destination_address='Test destination',
            recipient_name='Test Recipient',
            recipient_phone='+33123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7)
        )
        
        self.package_data = {
            'category': 'small',
            'length': Decimal('20.0'),
            'width': Decimal('15.0'),
            'height': Decimal('10.0'),
            'requires_special_handling': False,
            'is_hazardous': False,
            'temperature_sensitive': False,
            'handling_instructions': 'Manipuler avec soin',
            'storage_requirements': 'Température ambiante'
        }
    
    def test_create_shipment_success(self):
        """Test de création d'envoi réussie."""
        url = reverse('shipments:create_shipment')
        data = {
            'origin_city': 'Alger',
            'destination_city': 'Paris',
            'destination_country': 'France',
            'weight': '2.5',
            'description': 'Test shipment',
            'package_type': 'document',
            'origin_address': 'Test origin',
            'destination_address': 'Test destination',
            'recipient_name': 'Test Recipient',
            'recipient_phone': '+33123456789',
            'preferred_pickup_date': (timezone.now() + timedelta(days=1)).isoformat(),
            'max_delivery_date': (timezone.now() + timedelta(days=7)).isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
    
    def test_create_shipment_invalid_data(self):
        """Test de création d'envoi avec données invalides."""
        url = reverse('shipments:create_shipment')
        data = {
            'origin_city': 'Alger',
            'destination_city': 'Paris',
            'weight': '-1.0',  # Poids invalide
            'description': 'Test shipment'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_list_shipments(self):
        """Test de liste des envois."""
        url = reverse('shipments:shipment_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['shipments']), 1)
    
    def test_shipment_detail(self):
        """Test de détails d'un envoi."""
        url = reverse('shipments:shipment_detail', kwargs={'tracking_number': self.shipment.tracking_number})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['shipment']['tracking_number'], self.shipment.tracking_number)
    
    def test_shipment_not_found(self):
        """Test d'envoi non trouvé."""
        url = reverse('shipments:shipment_detail', kwargs={'tracking_number': 'INVALID123'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ShipmentTrackingTest(APITestCase):
    """Tests pour le suivi des envois."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=self.user)
        
        self.shipment = Shipment.objects.create(
            sender=self.user,
            origin_city='Alger',
            destination_city='Paris',
            destination_country='France',
            weight=Decimal('2.5'),
            description='Test shipment',
            package_type='document',
            origin_address='Test origin',
            destination_address='Test destination',
            recipient_name='Test Recipient',
            recipient_phone='+33123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7)
        )
    
    def test_add_tracking_event(self):
        """Test d'ajout d'un événement de suivi."""
        tracking_data = {
            'status': 'picked_up',
            'event_type': 'picked_up',
            'description': 'Colis ramassé par le voyageur',
            'location': 'Bureau Alger Centre'
        }
        
        url = reverse('shipments:add_tracking_event', kwargs={'tracking_number': self.shipment.tracking_number})
        response = self.client.post(url, tracking_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Vérifier que le statut de l'envoi a été mis à jour
        self.shipment.refresh_from_db()
        self.assertEqual(self.shipment.status, 'in_transit')
    
    def test_get_tracking_events(self):
        """Test de récupération des événements de suivi."""
        # Créer un événement de suivi
        ShipmentTracking.objects.create(
            shipment=self.shipment,
            status='picked_up',
            event_type='picked_up',
            description='Colis ramassé',
            location='Alger Centre'
        )
        
        url = reverse('shipments:tracking_events', kwargs={'tracking_number': self.shipment.tracking_number})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['tracking_events']), 1)


class ShipmentPaymentTest(APITestCase):
    """Tests pour les paiements d'envois."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=self.user)
        
        self.shipment = Shipment.objects.create(
            sender=self.user,
            origin_city='Alger',
            destination_city='Paris',
            destination_country='France',
            weight=Decimal('2.5'),
            description='Test shipment',
            package_type='document',
            origin_address='Test origin',
            destination_address='Test destination',
            recipient_name='Test Recipient',
            recipient_phone='+33123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7),
            price=Decimal('150.00'),
            shipping_cost=Decimal('150.00')
        )
    
    def test_get_payment_info(self):
        """Test de récupération des informations de paiement."""
        url = reverse('shipments:shipment_payment', kwargs={'tracking_number': self.shipment.tracking_number})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['payment_info']['amount'], Decimal('150.00'))
        self.assertEqual(response.data['payment_info']['currency'], 'EUR')
        self.assertEqual(response.data['payment_info']['status'], 'pending')
    
    def test_process_payment(self):
        """Test de traitement de paiement."""
        payment_data = {
            'payment_method': 'card',
            'amount': '150.00'
        }
        
        url = reverse('shipments:process_payment', kwargs={'tracking_number': self.shipment.tracking_number})
        response = self.client.post(url, payment_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Vérifier que le paiement a été traité
        self.shipment.refresh_from_db()
        self.assertTrue(self.shipment.is_paid)
        self.assertEqual(self.shipment.payment_status, 'paid')


class ShipmentDeliveryTest(APITestCase):
    """Tests pour la livraison des envois."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=self.user)
        
        self.shipment = Shipment.objects.create(
            sender=self.user,
            origin_city='Alger',
            destination_city='Paris',
            destination_country='France',
            weight=Decimal('2.5'),
            description='Test shipment',
            package_type='document',
            origin_address='Test origin',
            destination_address='Test destination',
            recipient_name='Test Recipient',
            recipient_phone='+33123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7)
        )
    
    def test_generate_delivery_otp(self):
        """Test de génération d'OTP de livraison."""
        url = reverse('shipments:generate_delivery_otp', kwargs={'tracking_number': self.shipment.tracking_number})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Vérifier que l'OTP a été généré
        self.shipment.refresh_from_db()
        self.assertIsNotNone(self.shipment.delivery_otp)
    
    def test_verify_delivery_otp(self):
        """Test de vérification d'OTP de livraison."""
        # Générer un OTP d'abord
        self.shipment.delivery_otp = '123456'
        self.shipment.save()
        
        verify_data = {
            'otp': '123456'
        }
        
        url = reverse('shipments:verify_delivery_otp', kwargs={'tracking_number': self.shipment.tracking_number})
        response = self.client.post(url, verify_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_verify_delivery_otp_invalid(self):
        """Test de vérification d'OTP invalide."""
        # Générer un OTP d'abord
        self.shipment.delivery_otp = '123456'
        self.shipment.save()
        
        verify_data = {
            'otp': '000000'
        }
        
        url = reverse('shipments:verify_delivery_otp', kwargs={'tracking_number': self.shipment.tracking_number})
        response = self.client.post(url, verify_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_confirm_delivery(self):
        """Test de confirmation de livraison."""
        url = reverse('shipments:confirm_delivery', kwargs={'tracking_number': self.shipment.tracking_number})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Vérifier que la livraison a été confirmée
        self.shipment.refresh_from_db()
        self.assertEqual(self.shipment.status, 'delivered')
        self.assertIsNotNone(self.shipment.delivery_date)


class PackageAPITest(APITestCase):
    """Tests pour les API de colis."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=self.user)
        
        self.shipment = Shipment.objects.create(
            sender=self.user,
            origin_city='Alger',
            destination_city='Paris',
            destination_country='France',
            weight=Decimal('2.5'),
            description='Test shipment',
            package_type='document',
            origin_address='Test origin',
            destination_address='Test destination',
            recipient_name='Test Recipient',
            recipient_phone='+33123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7)
        )
        
        self.package_data = {
            'category': 'small',
            'length': Decimal('20.0'),
            'width': Decimal('15.0'),
            'height': Decimal('10.0'),
            'requires_special_handling': False,
            'is_hazardous': False,
            'temperature_sensitive': False,
            'handling_instructions': 'Manipuler avec soin',
            'storage_requirements': 'Température ambiante'
        }
    
    def test_create_package_details(self):
        """Test de création de détails de colis."""
        url = reverse('shipments:package_details', kwargs={'shipment_id': self.shipment.id})
        response = self.client.post(url, self.package_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
    
    def test_get_package_details(self):
        """Test de récupération de détails de colis."""
        # Créer d'abord un colis
        Package.objects.create(
            shipment=self.shipment,
            **self.package_data
        )
        
        url = reverse('shipments:package_details', kwargs={'shipment_id': self.shipment.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])


class ShipmentRatingTest(APITestCase):
    """Tests pour les évaluations d'envois."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=self.user)
        
        self.shipment = Shipment.objects.create(
            sender=self.user,
            origin_city='Alger',
            destination_city='Paris',
            destination_country='France',
            weight=Decimal('2.5'),
            description='Test shipment',
            package_type='document',
            origin_address='Test origin',
            destination_address='Test destination',
            recipient_name='Test Recipient',
            recipient_phone='+33123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7),
            status='delivered',
            delivery_date=timezone.now()
        )
    
    def test_create_shipment_rating(self):
        """Test de création d'évaluation d'envoi."""
        rating_data = {
            'overall_rating': 5,
            'delivery_speed': 4,
            'package_condition': 5,
            'communication': 4,
            'comment': 'Excellent service !'
        }
        
        url = reverse('shipments:shipment_rating', kwargs={'shipment_id': self.shipment.id})
        response = self.client.post(url, rating_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
    
    def test_create_rating_for_non_delivered_shipment(self):
        """Test d'évaluation d'un envoi non livré."""
        # Créer un envoi non livré
        non_delivered_shipment = Shipment.objects.create(
            sender=self.user,
            origin_city='Alger',
            destination_city='Paris',
            destination_country='France',
            weight=Decimal('2.5'),
            description='Test shipment',
            package_type='document',
            origin_address='Test origin',
            destination_address='Test destination',
            recipient_name='Test Recipient',
            recipient_phone='+33123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7),
            status='in_transit'
        )
        
        rating_data = {
            'overall_rating': 5,
            'delivery_speed': 4,
            'package_condition': 5,
            'communication': 4,
            'comment': 'Excellent service !'
        }
        
        url = reverse('shipments:shipment_rating', kwargs={'shipment_id': non_delivered_shipment.id})
        response = self.client.post(url, rating_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_shipment_rating(self):
        """Test de récupération d'évaluation d'envoi."""
        # Créer d'abord une évaluation
        ShipmentRating.objects.create(
            shipment=self.shipment,
            rater=self.user,
            overall_rating=5,
            delivery_speed=4,
            package_condition=5,
            communication=4,
            comment='Excellent service !'
        )
        
        url = reverse('shipments:shipment_rating', kwargs={'shipment_id': self.shipment.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['rating']['overall_rating'], 5)


class ShipmentValidationTest(TestCase):
    """Tests de validation des données d'envoi."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_shipment_weight_validation(self):
        """Test de validation du poids du colis."""
        # Test poids négatif
        with self.assertRaises(Exception):
            Shipment.objects.create(
                sender=self.user,
                origin_city='Alger',
                destination_city='Paris',
                destination_country='France',
                weight=Decimal('-1.0'),
                description='Test shipment',
                package_type='document',
                origin_address='Test origin',
                destination_address='Test destination',
                recipient_name='Test Recipient',
                recipient_phone='+33123456789',
                preferred_pickup_date=timezone.now() + timedelta(days=1),
                max_delivery_date=timezone.now() + timedelta(days=7)
            )
        
        # Test poids trop élevé
        with self.assertRaises(Exception):
            Shipment.objects.create(
                sender=self.user,
                origin_city='Alger',
                destination_city='Paris',
                destination_country='France',
                weight=Decimal('100.0'),  # Plus de 50kg
                description='Test shipment',
                package_type='document',
                origin_address='Test origin',
                destination_address='Test destination',
                recipient_name='Test Recipient',
                recipient_phone='+33123456789',
                preferred_pickup_date=timezone.now() + timedelta(days=1),
                max_delivery_date=timezone.now() + timedelta(days=7)
            )
    
    def test_shipment_dates_validation(self):
        """Test de validation des dates d'envoi."""
        # Test date de livraison antérieure à la date de ramassage
        with self.assertRaises(Exception):
            Shipment.objects.create(
                sender=self.user,
                origin_city='Alger',
                destination_city='Paris',
                destination_country='France',
                weight=Decimal('2.5'),
                description='Test shipment',
                package_type='document',
                origin_address='Test origin',
                destination_address='Test destination',
                recipient_name='Test Recipient',
                recipient_phone='+33123456789',
                preferred_pickup_date=timezone.now() + timedelta(days=7),
                max_delivery_date=timezone.now() + timedelta(days=1)  # Date antérieure
            )


class ShipmentPerformanceTest(TestCase):
    """Tests de performance pour les envois."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_bulk_shipment_creation(self):
        """Test de création en masse d'envois."""
        start_time = timezone.now()
        
        # Créer 100 envois
        for i in range(100):
            Shipment.objects.create(
                sender=self.user,
                origin_city=f'City{i}',
                destination_city=f'DestCity{i}',
                destination_country='France',
                weight=Decimal('2.5'),
                description=f'Test shipment {i}',
                package_type='document',
                origin_address=f'Address {i}',
                destination_address=f'DestAddress {i}',
                recipient_name=f'Recipient {i}',
                recipient_phone=f'+3312345678{i:02d}',
                preferred_pickup_date=timezone.now() + timedelta(days=1),
                max_delivery_date=timezone.now() + timedelta(days=7)
            )
        
        end_time = timezone.now()
        creation_time = (end_time - start_time).total_seconds()
        
        # Vérifier que la création en masse est rapide (< 5 secondes)
        self.assertLess(creation_time, 5.0)
        self.assertEqual(Shipment.objects.count(), 100)
    
    def test_shipment_query_performance(self):
        """Test de performance des requêtes d'envois."""
        # Créer des envois avec différents statuts
        statuses = ['pending', 'in_transit', 'delivered', 'cancelled']
        for i, status in enumerate(statuses):
            for j in range(25):  # 25 envois par statut
                Shipment.objects.create(
                    sender=self.user,
                    origin_city=f'City{i}_{j}',
                    destination_city=f'DestCity{i}_{j}',
                    destination_country='France',
                    weight=Decimal('2.5'),
                    description=f'Test shipment {i}_{j}',
                    package_type='document',
                    origin_address=f'Address {i}_{j}',
                    destination_address=f'DestAddress {i}_{j}',
                    recipient_name=f'Recipient {i}_{j}',
                    recipient_phone=f'+3312345678{i:02d}{j:02d}',
                    preferred_pickup_date=timezone.now() + timedelta(days=1),
                    max_delivery_date=timezone.now() + timedelta(days=7),
                    status=status
                )
        
        # Test de requête avec filtres
        start_time = timezone.now()
        
        # Requête avec filtre par statut
        pending_shipments = Shipment.objects.filter(status='pending')
        in_transit_shipments = Shipment.objects.filter(status='in_transit')
        delivered_shipments = Shipment.objects.filter(status='delivered')
        
        end_time = timezone.now()
        query_time = (end_time - start_time).total_seconds()
        
        # Vérifier que les requêtes sont rapides (< 1 seconde)
        self.assertLess(query_time, 1.0)
        self.assertEqual(pending_shipments.count(), 25)
        self.assertEqual(in_transit_shipments.count(), 25)
        self.assertEqual(delivered_shipments.count(), 25)
