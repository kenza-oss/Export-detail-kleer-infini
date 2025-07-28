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
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123'
        )
    
    def test_rating_creation(self):
        """Test de création d'une évaluation."""
        rating = Rating.objects.create(
            rater=self.user1,
            rated_user=self.user2,
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
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123'
        )
    
    def test_create_rating(self):
        """Test de création d'évaluation via API."""
        self.client.force_authenticate(user=self.user1)
        data = {
            'rated_user': self.user2.id,
            'rating': 5,
            'comment': 'Excellent service'
        }
        response = self.client.post('/api/ratings/create/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED) 