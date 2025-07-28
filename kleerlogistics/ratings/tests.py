from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Rating

User = get_user_model()

class RatingModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123',
            phone_number='+213123456789'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123',
            phone_number='+213987654321'
        )
    
    def test_rating_creation(self):
        """Test de création d'une évaluation."""
        # Créer un shipment de test
        from shipments.models import Shipment
        from django.utils import timezone
        from datetime import timedelta
        
        shipment = Shipment.objects.create(
            sender=self.user1,
            package_type='document',
            description='Test shipment',
            weight=2.5,
            origin_city='Alger',
            origin_address='Test address',
            destination_city='Paris',
            destination_country='France',
            destination_address='Test destination',
            recipient_name='Test Recipient',
            recipient_phone='+33123456789',
            preferred_pickup_date=timezone.now(),
            max_delivery_date=timezone.now() + timedelta(days=7)
        )
        
        rating = Rating.objects.create(
            rater=self.user1,
            rated_user=self.user2,
            shipment=shipment,
            rating=5,
            comment='Excellent service'
        )
        self.assertEqual(rating.rating, 5)
        self.assertEqual(rating.comment, 'Excellent service')

class RatingAPITest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123',
            phone_number='+213111111111'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123',
            phone_number='+213222222222'
        )
    
    def test_create_rating(self):
        """Test de création d'évaluation via API."""
        # Créer un shipment de test
        from shipments.models import Shipment
        from django.utils import timezone
        from datetime import timedelta
        
        shipment = Shipment.objects.create(
            sender=self.user1,
            package_type='document',
            description='Test shipment',
            weight=2.5,
            origin_city='Alger',
            origin_address='Test address',
            destination_city='Paris',
            destination_country='France',
            destination_address='Test destination',
            recipient_name='Test Recipient',
            recipient_phone='+33123456789',
            preferred_pickup_date=timezone.now(),
            max_delivery_date=timezone.now() + timedelta(days=7)
        )
        
        self.client.force_authenticate(user=self.user1)
        data = {
            'rated_user': self.user2.id,
            'shipment': shipment.id,
            'rating': 5,
            'comment': 'Excellent service'
        }
        response = self.client.post('/api/v1/ratings/create/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED) 