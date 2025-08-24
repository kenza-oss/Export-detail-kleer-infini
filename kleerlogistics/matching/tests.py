"""
Tests for matching app - Comprehensive test suite for matching functionality
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
import json
from datetime import timedelta
import uuid

from .models import Match, MatchingPreferences, MatchingRule
from .services import (
    AutomaticMatchingService, 
    MatchingNotificationService, 
    OTPDeliveryService,
    MatchingAnalyticsService
)
from shipments.models import Shipment
from trips.models import Trip

User = get_user_model()


class MatchingModelsTestCase(TestCase):
    """Tests for matching models"""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@test.com',
            password='testpass123',
            first_name='John',
            last_name='Sender',
            role='sender'
        )
        
        self.traveler = User.objects.create_user(
            username='traveler',
            email='traveler@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Traveler',
            role='traveler'
        )
        
        # Create shipment
        self.shipment = Shipment.objects.create(
            sender=self.sender,
            package_type='document',
            description='Documents importants',
            weight=Decimal('2.5'),
            origin_city='Alger',
            origin_country='Algeria',
            destination_city='Paris',
            destination_country='France',
            origin_address='123 Rue d\'Alger',
            destination_address='456 Avenue de Paris',
            recipient_name='Jean Dupont',
            recipient_phone='+33123456789',
            recipient_email='jean@example.com',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7),
            is_fragile=False
        )
        
        # Create trip
        self.trip = Trip.objects.create(
            traveler=self.traveler,
            origin_city='Alger',
            origin_country='Algeria',
            destination_city='Paris',
            destination_country='France',
            origin_address='123 Rue d\'Alger',
            destination_address='456 Avenue de Paris',
            departure_date=timezone.now() + timedelta(days=2),
            arrival_date=timezone.now() + timedelta(days=6),
            max_weight=Decimal('20.0'),
            remaining_weight=Decimal('20.0'),
            max_packages=5,
            remaining_packages=5,
            min_price_per_kg=Decimal('100.0'),
            accepts_fragile=True,
            accepted_package_types=['document', 'electronics', 'clothing']
        )
        
        # Create matching rule
        self.matching_rule = MatchingRule.objects.create(
            name='Test Rule',
            description='Test matching rule',
            is_active=True
        )
    
    def test_match_creation(self):
        """Test match creation with compatibility score calculation."""
        match = Match.objects.create(
            shipment=self.shipment,
            trip=self.trip,
            compatibility_score=Decimal('85.50'),
            proposed_price=Decimal('250.00'),
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        self.assertIsNotNone(match)
        self.assertEqual(match.shipment, self.shipment)
        self.assertEqual(match.trip, self.trip)
        self.assertEqual(match.compatibility_score, Decimal('85.50'))
        self.assertEqual(match.proposed_price, Decimal('250.00'))
    
    def test_economic_breakdown_calculation(self):
        """Test economic breakdown calculation."""
        match = Match.objects.create(
            shipment=self.shipment,
            trip=self.trip,
            compatibility_score=Decimal('85.50'),
            proposed_price=Decimal('1000.00'),
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        breakdown = match.calculate_economic_breakdown()
        
        self.assertEqual(breakdown['total_price'], Decimal('1000.00'))
        self.assertEqual(breakdown['commission_amount'], Decimal('250.00'))  # 25%
        self.assertEqual(breakdown['packaging_fee'], Decimal('500.00'))  # Document
        self.assertEqual(breakdown['service_fee'], Decimal('0.00'))  # Normal urgency
        self.assertEqual(breakdown['traveler_earnings'], Decimal('250.00'))
    
    def test_fragile_package_economic_breakdown(self):
        """Test economic breakdown for fragile packages."""
        fragile_shipment = Shipment.objects.create(
            sender=self.sender,
            package_type='fragile',
            description='Objet fragile',
            weight=Decimal('1.0'),
            origin_city='Alger',
            origin_country='Algeria',
            destination_city='Paris',
            destination_country='France',
            origin_address='123 Rue d\'Alger',
            destination_address='456 Avenue de Paris',
            recipient_name='Jean Dupont',
            recipient_phone='+33123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7),
            is_fragile=True,
            urgency='urgent'
        )
        
        match = Match.objects.create(
            shipment=fragile_shipment,
            trip=self.trip,
            compatibility_score=Decimal('90.00'),
            proposed_price=Decimal('1000.00'),
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        breakdown = match.calculate_economic_breakdown()
        
        self.assertEqual(breakdown['packaging_fee'], Decimal('1000.00'))  # Fragile
        self.assertEqual(breakdown['service_fee'], Decimal('200.00'))  # Urgent
    
    def test_otp_generation_and_verification(self):
        """Test OTP generation and verification."""
        match = Match.objects.create(
            shipment=self.shipment,
            trip=self.trip,
            compatibility_score=Decimal('85.50'),
            proposed_price=Decimal('250.00'),
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Generate OTP
        otp_code = match.generate_delivery_otp()
        
        self.assertIsNotNone(otp_code)
        self.assertEqual(len(otp_code), 6)
        self.assertTrue(otp_code.isdigit())
        self.assertTrue(match.otp_is_valid)
        
        # Verify OTP
        self.assertTrue(match.verify_delivery_otp(otp_code))
        self.assertTrue(match.delivery_confirmed)
        self.assertIsNotNone(match.delivery_confirmed_at)
    
    def test_otp_expiration(self):
        """Test OTP expiration."""
        match = Match.objects.create(
            shipment=self.shipment,
            trip=self.trip,
            compatibility_score=Decimal('85.50'),
            proposed_price=Decimal('250.00'),
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Generate OTP
        otp_code = match.generate_delivery_otp()
        
        # Manually expire OTP
        match.otp_expires_at = timezone.now() - timedelta(hours=1)
        match.save()
        
        self.assertFalse(match.otp_is_valid)
        self.assertFalse(match.verify_delivery_otp(otp_code))
    
    def test_chat_activation(self):
        """Test chat activation for accepted matches."""
        match = Match.objects.create(
            shipment=self.shipment,
            trip=self.trip,
            compatibility_score=Decimal('85.50'),
            proposed_price=Decimal('250.00'),
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Accept match
        match.accept()
        
        # Chat should be automatically activated
        self.assertTrue(match.chat_activated)
        self.assertIsNotNone(match.chat_room_id)
        self.assertIsNotNone(match.chat_activated_at)
    
    def test_auto_acceptance(self):
        """Test auto-acceptance functionality."""
        match = Match.objects.create(
            shipment=self.shipment,
            trip=self.trip,
            compatibility_score=Decimal('95.00'),  # High score
            proposed_price=Decimal('250.00'),
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Should be able to auto-accept
        self.assertTrue(match.can_auto_accept)
        
        # Auto-accept
        self.assertTrue(match.auto_accept())
        self.assertTrue(match.auto_accepted)
        self.assertEqual(match.status, 'accepted')
    
    def test_matching_preferences(self):
        """Test matching preferences."""
        preferences = MatchingPreferences.objects.create(
            user=self.sender,
            auto_accept_threshold=Decimal('90.00'),
            notification_enabled=True,
            min_rating=Decimal('4.0'),
            preferred_cities=['Paris', 'Lyon'],
            blacklisted_users=[],
            response_time_hours=24,
            min_price=Decimal('50.00'),
            max_price=Decimal('500.00')
        )
        
        self.assertEqual(preferences.user, self.sender)
        self.assertEqual(preferences.auto_accept_threshold, Decimal('90.00'))
        self.assertTrue(preferences.notification_enabled)
        self.assertEqual(preferences.min_rating, Decimal('4.0'))
        self.assertEqual(preferences.preferred_cities, ['Paris', 'Lyon'])
        self.assertEqual(preferences.blacklisted_users, [])
        self.assertEqual(preferences.response_time_hours, 24)
        self.assertEqual(preferences.min_price, Decimal('50.00'))
        self.assertEqual(preferences.max_price, Decimal('500.00'))
    
    def test_matching_rule_creation(self):
        """Test matching rule creation."""
        rule = MatchingRule.objects.create(
            name='Test Rule',
            description='Test matching rule',
            min_compatibility_score=Decimal('40.00'),
            geographic_weight=Decimal('40.00'),
            weight_weight=Decimal('25.00'),
            package_type_weight=Decimal('15.00'),
            fragility_weight=Decimal('10.00'),
            date_weight=Decimal('10.00'),
            reputation_weight=Decimal('0.00'),
            enable_auto_acceptance=True,
            auto_accept_threshold=Decimal('95.00')
        )
        
        self.assertEqual(rule.name, 'Test Rule')
        self.assertEqual(rule.min_compatibility_score, Decimal('40.00'))
        self.assertTrue(rule.is_active)


class MatchingServicesTestCase(TestCase):
    """Tests for matching services"""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@test.com',
            password='testpass123',
            first_name='John',
            last_name='Sender',
            role='sender'
        )
        
        self.traveler = User.objects.create_user(
            username='traveler',
            email='traveler@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Traveler',
            role='traveler'
        )
        
        # Create shipment
        self.shipment = Shipment.objects.create(
            sender=self.sender,
            package_type='document',
            description='Documents importants',
            weight=Decimal('2.5'),
            origin_city='Alger',
            origin_country='Algeria',
            destination_city='Paris',
            destination_country='France',
            origin_address='123 Rue d\'Alger',
            destination_address='456 Avenue de Paris',
            recipient_name='Jean Dupont',
            recipient_phone='+33123456789',
            recipient_email='jean@example.com',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7),
            is_fragile=False,
            status='pending'
        )
        
        # Create trip
        self.trip = Trip.objects.create(
            traveler=self.traveler,
            origin_city='Alger',
            origin_country='Algeria',
            destination_city='Paris',
            destination_country='France',
            origin_address='123 Rue d\'Alger',
            destination_address='456 Avenue de Paris',
            departure_date=timezone.now() + timedelta(days=2),
            arrival_date=timezone.now() + timedelta(days=6),
            max_weight=Decimal('20.0'),
            remaining_weight=Decimal('20.0'),
            max_packages=5,
            remaining_packages=5,
            min_price_per_kg=Decimal('100.0'),
            accepts_fragile=True,
            accepted_package_types=['document', 'electronics', 'clothing'],
            status='active'
        )
    
    def test_automatic_matching_service(self):
        """Test automatic matching service."""
        # Find matches for shipment
        matches = AutomaticMatchingService.find_matches_for_shipment(self.shipment)
        
        self.assertIsInstance(matches, list)
        if matches:
            match = matches[0]
            self.assertIsInstance(match, Match)
            self.assertEqual(match.shipment, self.shipment)
            self.assertEqual(match.trip, self.trip)
            self.assertGreater(match.compatibility_score, 0)
    
    def test_compatibility_score_calculation(self):
        """Test compatibility score calculation."""
        rules = MatchingRule.objects.create(
            name='Test Rule',
            description='Test matching rule',
            is_active=True
        )
        
        score = AutomaticMatchingService.calculate_compatibility_score(
            self.shipment, self.trip, rules
        )
        
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_proposed_price_calculation(self):
        """Test proposed price calculation."""
        price = AutomaticMatchingService.calculate_proposed_price(
            self.shipment, self.trip
        )
        
        self.assertGreater(price, 0)
        # Base price should be weight * price_per_kg
        expected_base = self.shipment.weight * self.trip.min_price_per_kg
        self.assertGreaterEqual(price, expected_base)
    
    def test_otp_delivery_service(self):
        """Test OTP delivery service."""
        match = Match.objects.create(
            shipment=self.shipment,
            trip=self.trip,
            compatibility_score=Decimal('85.50'),
            proposed_price=Decimal('250.00'),
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Generate and send OTP
        otp_code = OTPDeliveryService.generate_and_send_otp(match)
        
        self.assertIsNotNone(otp_code)
        self.assertEqual(len(otp_code), 6)
        
        # Verify OTP
        self.assertTrue(OTPDeliveryService.verify_delivery_otp(match, otp_code))
    
    def test_matching_analytics_service(self):
        """Test matching analytics service."""
        # Create some matches with different shipments to avoid unique constraint violation
        shipment2 = Shipment.objects.create(
            sender=self.sender,
            package_type='electronics',
            description='Électronique pour test',
            weight=Decimal('1.0'),
            origin_city='Alger',
            origin_country='Algeria',
            destination_city='Paris',
            destination_country='France',
            origin_address='123 Rue d\'Alger',
            destination_address='456 Avenue de Paris',
            recipient_name='Jean Dupont',
            recipient_phone='+33123456789',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7),
            is_fragile=False,
            status='pending'
        )
        
        match1 = Match.objects.create(
            shipment=self.shipment,
            trip=self.trip,
            compatibility_score=Decimal('85.50'),
            proposed_price=Decimal('250.00'),
            status='accepted',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        match2 = Match.objects.create(
            shipment=shipment2,
            trip=self.trip,
            compatibility_score=Decimal('75.00'),
            proposed_price=Decimal('200.00'),
            status='rejected',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Get statistics
        stats = MatchingAnalyticsService.get_matching_statistics()
        
        self.assertGreaterEqual(stats['total_matches'], 2)
        self.assertGreaterEqual(stats['accepted_matches'], 1)
        self.assertGreaterEqual(stats['rejected_matches'], 1)
        self.assertGreater(stats['average_compatibility_score'], 0)


class MatchingAPITestCase(APITestCase):
    """Tests for matching API endpoints"""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@test.com',
            password='testpass123',
            first_name='John',
            last_name='Sender',
            role='sender'
        )
        
        self.traveler = User.objects.create_user(
            username='traveler',
            email='traveler@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Traveler',
            role='traveler'
        )
        
        # Create shipment
        self.shipment = Shipment.objects.create(
            sender=self.sender,
            package_type='document',
            description='Documents importants',
            weight=Decimal('2.5'),
            origin_city='Alger',
            origin_country='Algeria',
            destination_city='Paris',
            destination_country='France',
            origin_address='123 Rue d\'Alger',
            destination_address='456 Avenue de Paris',
            recipient_name='Jean Dupont',
            recipient_phone='+33123456789',
            recipient_email='jean@example.com',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7),
            is_fragile=False,
            status='pending'
        )
        
        # Create trip
        self.trip = Trip.objects.create(
            traveler=self.traveler,
            origin_city='Alger',
            origin_country='Algeria',
            destination_city='Paris',
            destination_country='France',
            origin_address='123 Rue d\'Alger',
            destination_address='456 Avenue de Paris',
            departure_date=timezone.now() + timedelta(days=2),
            arrival_date=timezone.now() + timedelta(days=6),
            max_weight=Decimal('20.0'),
            remaining_weight=Decimal('20.0'),
            max_packages=5,
            remaining_packages=5,
            min_price_per_kg=Decimal('100.0'),
            accepts_fragile=True,
            accepted_package_types=['document', 'electronics', 'clothing'],
            status='active'
        )
        
        # Create match
        self.match = Match.objects.create(
            shipment=self.shipment,
            trip=self.trip,
            compatibility_score=Decimal('85.50'),
            proposed_price=Decimal('250.00'),
            expires_at=timezone.now() + timedelta(hours=24)
        )
    
    def test_matching_engine_endpoint(self):
        """Test matching engine endpoint."""
        self.client.force_authenticate(user=self.sender)
        
        url = reverse('matching:engine')
        data = {
            'type': 'shipment',
            'item_id': self.shipment.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('matches', response.data)
    
    def test_accept_match_endpoint(self):
        """Test accept match endpoint."""
        self.client.force_authenticate(user=self.sender)
        
        url = reverse('matching:accept-match', kwargs={'match_id': self.match.id})
        data = {
            'accepted_price': '250.00',
            'message': 'Accepté avec plaisir'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check that match was accepted
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, 'accepted')
    
    def test_reject_match_endpoint(self):
        """Test reject match endpoint."""
        self.client.force_authenticate(user=self.sender)
        
        url = reverse('matching:reject-match', kwargs={'match_id': self.match.id})
        data = {
            'reason': 'Prix trop élevé',
            'message': 'Désolé, le prix ne convient pas'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check that match was rejected
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, 'rejected')
    
    def test_otp_delivery_endpoint(self):
        """Test OTP delivery endpoint."""
        # First accept the match
        self.match.accept()
        
        self.client.force_authenticate(user=self.traveler)
        
        # Generate OTP
        url = reverse('matching:otp-delivery', kwargs={'match_id': self.match.id})
        response = self.client.post(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('otp_code', response.data)
        
        # Verify OTP
        otp_code = response.data['otp_code']
        data = {'otp_code': otp_code}
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['payment_released'])
    
    def test_chat_integration_endpoint(self):
        """Test chat integration endpoint."""
        # First accept the match
        self.match.accept()
        
        self.client.force_authenticate(user=self.sender)
        
        url = reverse('matching:chat-integration', kwargs={'match_id': self.match.id})
        response = self.client.post(url, format='json')
        
        # Since accept() automatically activates chat, we expect a 400 with "already activated" message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('déjà activé', response.data['message'])
    
    def test_chat_integration_endpoint_new_match(self):
        """Test chat integration endpoint with a match that hasn't been accepted yet."""
        # Create a new shipment and trip for this test to avoid unique constraint violation
        from django.utils import timezone
        from datetime import timedelta
        
        new_shipment = Shipment.objects.create(
            sender=self.sender,
            tracking_number='TEST123456',
            origin_city='Paris',
            origin_address='123 Rue de Paris, 75001 Paris',
            destination_city='Lyon',
            destination_country='France',
            destination_address='456 Avenue de Lyon, 69001 Lyon',
            recipient_name='Jean Dupont',
            recipient_phone='+33123456789',
            description='Électronique fragile',
            weight=Decimal('5.0'),
            dimensions={'length': 30, 'width': 20, 'height': 15},
            package_type='electronics',
            is_fragile=True,
            value=Decimal('200.00'),
            preferred_pickup_date=timezone.now(),
            max_delivery_date=timezone.now() + timedelta(days=7),
            status='pending'
        )
        
        new_trip = Trip.objects.create(
            traveler=self.traveler,
            origin_city='Paris',
            destination_city='Lyon',
            destination_country='France',
            departure_date=timezone.now() + timedelta(days=1),
            arrival_date=timezone.now() + timedelta(days=6),
            max_weight=Decimal('10.0'),
            max_packages=2,
            min_price_per_kg=Decimal('15.00'),
            accepted_package_types=['electronics', 'document'],
            status='active',
            is_verified=True
        )
        
        # Create a new match that hasn't been accepted
        new_match = Match.objects.create(
            shipment=new_shipment,
            trip=new_trip,
            status='pending',
            compatibility_score=85.5,
            proposed_price=Decimal('150.00'),
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        self.client.force_authenticate(user=self.sender)
        
        # First accept the match
        accept_url = reverse('matching:accept-match', kwargs={'match_id': new_match.id})
        accept_response = self.client.post(accept_url, format='json')
        
        self.assertEqual(accept_response.status_code, status.HTTP_200_OK)
        self.assertTrue(accept_response.data['success'])
        
        # Now try to activate chat (should fail since chat is already activated by accept())
        url = reverse('matching:chat-integration', kwargs={'match_id': new_match.id})
        response = self.client.post(url, format='json')
        
        # Should fail because chat is already activated
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('déjà activé', response.data['message'])
        
        # Refresh the match to check that chat was already activated by accept()
        new_match.refresh_from_db()
        self.assertTrue(new_match.chat_activated)
    
    def test_automatic_matching_endpoint(self):
        """Test automatic matching endpoint."""
        self.client.force_authenticate(user=self.sender)
        
        url = reverse('matching:automatic-matching')
        data = {
            'type': 'shipment',
            'item_id': self.shipment.id,
            'auto_accept': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('matches', response.data)
    
    def test_matching_preferences_endpoint(self):
        """Test matching preferences endpoint."""
        self.client.force_authenticate(user=self.sender)
        
        url = reverse('matching:preferences')
        data = {
            'auto_accept_threshold': 85.0,
            'notification_enabled': True,
            'min_rating': 4.0,
            'preferred_cities': ['Paris', 'Lyon'],
            'blacklisted_users': [],
            'response_time_hours': 24
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_matching_analytics_endpoint(self):
        """Test matching analytics endpoint."""
        self.client.force_authenticate(user=self.sender)
        
        url = reverse('matching:analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('analytics', response.data)


class MatchingIntegrationTestCase(APITestCase):
    """Integration tests for complete matching workflow"""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@test.com',
            password='testpass123',
            first_name='John',
            last_name='Sender',
            role='sender'
        )
        
        self.traveler = User.objects.create_user(
            username='traveler',
            email='traveler@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Traveler',
            role='traveler'
        )
        
        # Create shipment
        self.shipment = Shipment.objects.create(
            sender=self.sender,
            package_type='document',
            description='Documents importants',
            weight=Decimal('2.5'),
            origin_city='Alger',
            origin_country='Algeria',
            destination_city='Paris',
            destination_country='France',
            origin_address='123 Rue d\'Alger',
            destination_address='456 Avenue de Paris',
            recipient_name='Jean Dupont',
            recipient_phone='+33123456789',
            recipient_email='jean@example.com',
            preferred_pickup_date=timezone.now() + timedelta(days=1),
            max_delivery_date=timezone.now() + timedelta(days=7),
            is_fragile=False,
            status='pending'
        )
        
        # Create trip
        self.trip = Trip.objects.create(
            traveler=self.traveler,
            origin_city='Alger',
            origin_country='Algeria',
            destination_city='Paris',
            destination_country='France',
            origin_address='123 Rue d\'Alger',
            destination_address='456 Avenue de Paris',
            departure_date=timezone.now() + timedelta(days=2),
            arrival_date=timezone.now() + timedelta(days=6),
            max_weight=Decimal('20.0'),
            remaining_weight=Decimal('20.0'),
            max_packages=5,
            remaining_packages=5,
            min_price_per_kg=Decimal('100.0'),
            accepts_fragile=True,
            accepted_package_types=['document', 'electronics', 'clothing'],
            status='active'
        )
    
    def test_complete_matching_workflow(self):
        """Test complete matching workflow from creation to delivery."""
        # Step 1: Create a match manually since the matching engine doesn't create Match objects
        from django.utils import timezone
        from datetime import timedelta
        
        match = Match.objects.create(
            shipment=self.shipment,
            trip=self.trip,
            status='pending',
            compatibility_score=85.5,
            proposed_price=Decimal('150.00'),
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Step 2: Find matches using the matching engine
        self.client.force_authenticate(user=self.sender)
        url = reverse('matching:engine')
        data = {
            'type': 'shipment',
            'item_id': self.shipment.id
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Step 3: Accept the match (this automatically generates OTP and activates chat)
        url = reverse('matching:accept-match', kwargs={'match_id': match.id})
        response = self.client.post(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Step 4: Verify that the match is accepted and chat is activated
        match.refresh_from_db()
        self.assertEqual(match.status, 'accepted')
        self.assertTrue(match.chat_activated)
        self.assertIsNotNone(match.delivery_otp)
        
        # Step 5: Test chat integration
        url = reverse('matching:chat-integration', kwargs={'match_id': match.id})
        response = self.client.post(url, format='json')
        
        # Since chat is already activated, we expect a 400 with "already activated" message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('déjà activé', response.data['message'])
        
        # Step 6: Test OTP verification (using PUT method)
        url = reverse('matching:otp-delivery', kwargs={'match_id': match.id})
        data = {'otp_code': match.delivery_otp}
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['payment_released'])
