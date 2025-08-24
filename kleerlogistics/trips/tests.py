"""
Tests complets pour le module trips
"""

import json
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import datetime, timedelta

from .models import Trip, TripDocument
from .serializers import TripSerializer, TripCreateSerializer, TripDetailSerializer

User = get_user_model()


class TripModelTest(TestCase):
    """Tests pour le modèle Trip."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            username='testtraveler',
            email='traveler@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Traveler'
        )
        
        self.trip_data = {
            'traveler': self.user,
            'origin_city': 'Alger',
            'origin_country': 'Algeria',
            'destination_city': 'Paris',
            'destination_country': 'France',
            'departure_date': timezone.now() + timedelta(days=7),
            'arrival_date': timezone.now() + timedelta(days=8),
            'flexible_dates': False,
            'flexibility_days': 0,
            'max_weight': Decimal('20.00'),
            'max_packages': 5,
            'accepted_package_types': ['document', 'electronics'],
            'min_price_per_kg': Decimal('15.00'),
            'accepts_fragile': True,
            'notes': 'Voyage d\'affaires'
        }
    
    def test_create_trip(self):
        """Test de création d'un trajet."""
        trip = Trip.objects.create(**self.trip_data)
        
        self.assertEqual(trip.origin_city, 'Alger')
        self.assertEqual(trip.destination_city, 'Paris')
        self.assertEqual(trip.origin_country, 'Algeria')
        self.assertEqual(trip.destination_country, 'France')
        self.assertEqual(trip.status, 'draft')
        self.assertFalse(trip.is_verified)
        self.assertEqual(trip.remaining_weight, trip.max_weight)
        self.assertEqual(trip.remaining_packages, trip.max_packages)
    
    def test_trip_validation_origin_must_be_algeria(self):
        """Test que l'origine doit être en Algérie."""
        self.trip_data['origin_country'] = 'France'
        
        with self.assertRaises(Exception):
            trip = Trip.objects.create(**self.trip_data)
            trip.full_clean()
    
    def test_trip_validation_destination_cannot_be_algeria(self):
        """Test que la destination ne peut pas être en Algérie."""
        self.trip_data['destination_country'] = 'Algeria'
        
        with self.assertRaises(Exception):
            trip = Trip.objects.create(**self.trip_data)
            trip.full_clean()
    
    def test_trip_validation_departure_date_future(self):
        """Test que la date de départ doit être dans le futur."""
        self.trip_data['departure_date'] = timezone.now() - timedelta(days=1)
        
        with self.assertRaises(Exception):
            trip = Trip.objects.create(**self.trip_data)
            trip.full_clean()
    
    def test_trip_validation_arrival_after_departure(self):
        """Test que la date d'arrivée doit être après le départ."""
        self.trip_data['arrival_date'] = timezone.now() + timedelta(days=6)
        
        with self.assertRaises(Exception):
            trip = Trip.objects.create(**self.trip_data)
            trip.full_clean()
    
    def test_trip_validation_origin_destination_different(self):
        """Test que l'origine et la destination doivent être différentes."""
        self.trip_data['destination_city'] = 'Alger'
        self.trip_data['destination_country'] = 'Algeria'
        
        with self.assertRaises(Exception):
            trip = Trip.objects.create(**self.trip_data)
            trip.full_clean()
    
    def test_trip_validation_package_types(self):
        """Test de validation des types de colis acceptés."""
        self.trip_data['accepted_package_types'] = ['invalid_type']
        
        with self.assertRaises(Exception):
            trip = Trip.objects.create(**self.trip_data)
            trip.full_clean()
    
    def test_trip_validation_flexible_dates_consistency(self):
        """Test de cohérence entre dates flexibles et jours de flexibilité."""
        self.trip_data['flexible_dates'] = True
        self.trip_data['flexibility_days'] = 0
        
        with self.assertRaises(Exception):
            trip = Trip.objects.create(**self.trip_data)
            trip.full_clean()
    
    def test_trip_properties(self):
        """Test des propriétés calculées du trajet."""
        trip = Trip.objects.create(**self.trip_data)
        
        # Test is_active
        self.assertFalse(trip.is_active)  # Pas encore vérifié
        
        # Test days_until_departure
        self.assertIsNotNone(trip.days_until_departure)
        self.assertGreater(trip.days_until_departure, 0)
        
        # Test route_display
        self.assertEqual(trip.get_route_display(), 'Alger → Paris')
    
    def test_trip_status_transitions(self):
        """Test des transitions de statut valides."""
        trip = Trip.objects.create(**self.trip_data)
        
        # draft → active
        trip.update_status('active')
        self.assertEqual(trip.status, 'active')
        
        # active → in_progress
        trip.update_status('in_progress')
        self.assertEqual(trip.status, 'in_progress')
        
        # in_progress → completed
        trip.update_status('completed')
        self.assertEqual(trip.status, 'completed')
        
        # Test transition invalide
        with self.assertRaises(ValueError):
            trip.update_status('active')  # completed → active n'est pas valide
    
    def test_trip_capacity_management(self):
        """Test de la gestion de la capacité du trajet."""
        trip = Trip.objects.create(**self.trip_data)
        trip.update_status('active')
        trip.is_verified = True
        trip.save()
        
        # Simuler l'ajout d'un colis
        class MockShipment:
            def __init__(self, weight, package_type, is_fragile, preferred_pickup_date, max_delivery_date):
                self.weight = weight
                self.package_type = package_type
                self.is_fragile = is_fragile
                self.preferred_pickup_date = preferred_pickup_date
                self.max_delivery_date = max_delivery_date
        
        shipment = MockShipment(
            weight=Decimal('5.00'),
            package_type='document',
            is_fragile=False,
            preferred_pickup_date=trip.departure_date - timedelta(days=1),
            max_delivery_date=trip.arrival_date + timedelta(days=1)
        )
        
        # Vérifier que le trajet peut accepter le colis
        self.assertTrue(trip.can_accept_shipment(shipment))
        
        # Ajouter le colis
        trip.add_shipment(shipment)
        
        # Vérifier que la capacité a été mise à jour
        self.assertEqual(trip.remaining_weight, Decimal('15.00'))
        self.assertEqual(trip.remaining_packages, 4)
        
        # Retirer le colis
        trip.remove_shipment(shipment)
        
        # Vérifier que la capacité a été restaurée
        self.assertEqual(trip.remaining_weight, Decimal('20.00'))
        self.assertEqual(trip.remaining_packages, 5)


class TripDocumentModelTest(TestCase):
    """Tests pour le modèle TripDocument."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            username='testtraveler',
            email='traveler@test.com',
            password='testpass123'
        )
        
        self.trip = Trip.objects.create(
            traveler=self.user,
            origin_city='Alger',
            origin_country='Algeria',
            destination_city='Paris',
            destination_country='France',
            departure_date=timezone.now() + timedelta(days=7),
            arrival_date=timezone.now() + timedelta(days=8),
            max_weight=Decimal('20.00'),
            max_packages=5,
            accepted_package_types=['document'],
            min_price_per_kg=Decimal('15.00')
        )
    
    def test_create_trip_document(self):
        """Test de création d'un document de trajet."""
        document = TripDocument.objects.create(
            trip=self.trip,
            document_type='flight_ticket',
            file=SimpleUploadedFile('ticket.pdf', b'fake pdf content', content_type='application/pdf')
        )
        
        self.assertEqual(document.document_type, 'flight_ticket')
        self.assertEqual(document.trip, self.trip)
        self.assertFalse(document.is_verified)
        self.assertIsNone(document.verification_date)
    
    def test_document_verification(self):
        """Test de vérification d'un document."""
        document = TripDocument.objects.create(
            trip=self.trip,
            document_type='passport_copy',
            file=SimpleUploadedFile('passport.pdf', b'fake pdf content', content_type='application/pdf')
        )
        
        # Vérifier le document
        document.is_verified = True
        document.verification_date = timezone.now()
        document.verification_notes = 'Document valide'
        document.save()
        
        self.assertTrue(document.is_verified)
        self.assertIsNotNone(document.verification_date)
        self.assertEqual(document.verification_notes, 'Document valide')
    
    def test_document_completeness(self):
        """Test de la complétude d'un document."""
        document = TripDocument.objects.create(
            trip=self.trip,
            document_type='flight_ticket',
            file=SimpleUploadedFile('ticket.pdf', b'fake pdf content', content_type='application/pdf')
        )
        
        # Document non vérifié
        self.assertFalse(document.is_complete)
        
        # Document vérifié
        document.is_verified = True
        document.save()
        self.assertTrue(document.is_complete)


class TripSerializerTest(TestCase):
    """Tests pour les sérialiseurs de trajets."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            username='testtraveler',
            email='traveler@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Traveler'
        )
        
        self.trip_data = {
            'origin_city': 'Alger',
            'origin_country': 'Algeria',
            'destination_city': 'Paris',
            'destination_country': 'France',
            'departure_date': timezone.now() + timedelta(days=7),
            'arrival_date': timezone.now() + timedelta(days=8),
            'flexible_dates': False,
            'flexibility_days': 0,
            'max_weight': Decimal('20.00'),
            'max_packages': 5,
            'accepted_package_types': ['document', 'electronics'],
            'min_price_per_kg': Decimal('15.00'),
            'accepts_fragile': True,
            'notes': 'Voyage d\'affaires'
        }
    
    def test_trip_create_serializer_valid(self):
        """Test de validation du sérialiseur de création."""
        serializer = TripCreateSerializer(data=self.trip_data)
        self.assertTrue(serializer.is_valid())
    
    def test_trip_create_serializer_invalid_origin_country(self):
        """Test de validation du pays d'origine."""
        self.trip_data['origin_country'] = 'FR'
        serializer = TripCreateSerializer(data=self.trip_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('origin_country', serializer.errors)
    
    def test_trip_create_serializer_invalid_destination_country(self):
        """Test de validation du pays de destination."""
        self.trip_data['destination_country'] = 'Algeria'
        serializer = TripCreateSerializer(data=self.trip_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('destination_country', serializer.errors)
    
    def test_trip_create_serializer_invalid_dates(self):
        """Test de validation des dates."""
        self.trip_data['departure_date'] = timezone.now() - timedelta(days=1)
        serializer = TripCreateSerializer(data=self.trip_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('departure_date', serializer.errors)
    
    def test_trip_create_serializer_invalid_package_types(self):
        """Test de validation des types de colis."""
        self.trip_data['accepted_package_types'] = ['invalid_type']
        serializer = TripCreateSerializer(data=self.trip_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('accepted_package_types', serializer.errors)
    
    def test_trip_create_serializer_flexible_dates_validation(self):
        """Test de validation des dates flexibles."""
        self.trip_data['flexible_dates'] = True
        self.trip_data['flexibility_days'] = 0
        serializer = TripCreateSerializer(data=self.trip_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)


class TripAPITest(APITestCase):
    """Tests pour l'API des trajets."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testtraveler',
            email='traveler@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Traveler'
        )
        self.client.force_authenticate(user=self.user)
        
        self.trip_data = {
            'origin_city': 'Alger',
            'origin_country': 'Algeria',
            'destination_city': 'Paris',
            'destination_country': 'France',
            'departure_date': (timezone.now() + timedelta(days=7)).isoformat(),
            'arrival_date': (timezone.now() + timedelta(days=8)).isoformat(),
            'flexible_dates': False,
            'flexibility_days': 0,
            'max_weight': '20.00',
            'max_packages': 5,
            'accepted_package_types': ['document', 'electronics'],
            'min_price_per_kg': '15.00',
            'accepts_fragile': True,
            'notes': 'Voyage d\'affaires'
        }
        
        # Data for direct object creation (with proper types)
        self.trip_object_data = {
            'origin_city': 'Alger',
            'origin_country': 'Algeria',
            'destination_city': 'Paris',
            'destination_country': 'France',
            'flexible_dates': False,
            'flexibility_days': 0,
            'max_weight': Decimal('20.00'),
            'max_packages': 5,
            'accepted_package_types': ['document', 'electronics'],
            'min_price_per_kg': Decimal('15.00'),
            'accepts_fragile': True,
            'notes': 'Voyage d\'affaires'
        }
    
    def test_create_trip_api(self):
        """Test de création d'un trajet via l'API."""
        url = reverse('trips:trip_create')
        response = self.client.post(url, self.trip_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('trip', response.data)
        
        # Vérifier que le trajet a été créé en base
        trip_id = response.data['trip']['id']
        trip = Trip.objects.get(id=trip_id)
        self.assertEqual(trip.origin_city, 'Alger')
        self.assertEqual(trip.destination_city, 'Paris')
        self.assertEqual(trip.traveler, self.user)
    
    def test_create_trip_api_invalid_data(self):
        """Test de création d'un trajet avec des données invalides."""
        self.trip_data['origin_country'] = 'France'  # Doit être Algeria
        
        url = reverse('trips:trip_create')
        response = self.client.post(url, self.trip_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('origin_country', response.data['errors'])
    
    def test_list_trips_api(self):
        """Test de récupération de la liste des trajets."""
        # Créer un trajet
        trip = Trip.objects.create(
            traveler=self.user,
            **self.trip_object_data,
            departure_date=timezone.now() + timedelta(days=7),
            arrival_date=timezone.now() + timedelta(days=8)
        )
        
        url = reverse('trips:trip_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['trips']), 1)
    
    def test_trip_detail_api(self):
        """Test de récupération des détails d'un trajet."""
        trip = Trip.objects.create(
            traveler=self.user,
            **self.trip_object_data,
            departure_date=timezone.now() + timedelta(days=7),
            arrival_date=timezone.now() + timedelta(days=8)
        )
        
        url = reverse('trips:trip_detail', kwargs={'pk': trip.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('trip', response.data)
        self.assertEqual(response.data['trip']['id'], trip.id)
    
    def test_trip_update_api(self):
        """Test de mise à jour d'un trajet."""
        trip = Trip.objects.create(
            traveler=self.user,
            **self.trip_object_data,
            departure_date=timezone.now() + timedelta(days=7),
            arrival_date=timezone.now() + timedelta(days=8)
        )
        
        update_data = {'notes': 'Notes mises à jour'}
        url = reverse('trips:trip_update', kwargs={'pk': trip.id})
        response = self.client.put(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Vérifier que le trajet a été mis à jour
        trip.refresh_from_db()
        self.assertEqual(trip.notes, 'Notes mises à jour')
    
    def test_trip_delete_api(self):
        """Test de suppression d'un trajet."""
        trip = Trip.objects.create(
            traveler=self.user,
            **self.trip_object_data,
            departure_date=timezone.now() + timedelta(days=7),
            arrival_date=timezone.now() + timedelta(days=8)
        )
        
        url = reverse('trips:trip_delete', kwargs={'pk': trip.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Vérifier que le trajet a été supprimé
        self.assertFalse(Trip.objects.filter(id=trip.id).exists())
    
    def test_trip_status_update_api(self):
        """Test de mise à jour du statut d'un trajet."""
        trip = Trip.objects.create(
            traveler=self.user,
            **self.trip_object_data,
            departure_date=timezone.now() + timedelta(days=7),
            arrival_date=timezone.now() + timedelta(days=8)
        )
        
        url = reverse('trips:trip_status_update', kwargs={'pk': trip.id})
        response = self.client.put(url, {'status': 'active'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Vérifier que le statut a été mis à jour
        trip.refresh_from_db()
        self.assertEqual(trip.status, 'active')
    
    def test_available_trips_api(self):
        """Test de récupération des trajets disponibles."""
        # Créer un autre utilisateur et un trajet
        other_user = User.objects.create_user(
            username='othertraveler',
            email='other@test.com',
            password='testpass123'
        )
        
        trip = Trip.objects.create(
            traveler=other_user,
            **self.trip_object_data,
            departure_date=timezone.now() + timedelta(days=7),
            arrival_date=timezone.now() + timedelta(days=8),
            status='active',
            is_verified=True
        )
        
        url = reverse('trips:available_trips')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['trips']), 1)
    
    def test_trip_search_api(self):
        """Test de recherche de trajets."""
        # Créer un autre utilisateur et un trajet
        other_user = User.objects.create_user(
            username='othertraveler',
            email='other@test.com',
            password='testpass123'
        )
        
        trip = Trip.objects.create(
            traveler=other_user,
            **self.trip_object_data,
            departure_date=timezone.now() + timedelta(days=7),
            arrival_date=timezone.now() + timedelta(days=8),
            status='active',
            is_verified=True
        )
        
        url = reverse('trips:trip_search')
        response = self.client.get(url, {'q': 'Paris'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 1)
    
    def test_trip_analytics_api(self):
        """Test de récupération des analytics des trajets."""
        # Créer plusieurs trajets
        for i in range(3):
            Trip.objects.create(
                traveler=self.user,
                **self.trip_object_data,
                departure_date=timezone.now() + timedelta(days=7+i),
                arrival_date=timezone.now() + timedelta(days=8+i),
                status='active' if i == 0 else 'completed' if i == 1 else 'cancelled'
            )
        
        url = reverse('trips:trip_analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('analytics', response.data)
        self.assertEqual(response.data['analytics']['total_trips'], 3)
        self.assertEqual(response.data['analytics']['active_trips'], 1)
        self.assertEqual(response.data['analytics']['completed_trips'], 1)
        self.assertEqual(response.data['analytics']['cancelled_trips'], 1)
    
    def test_trip_calendar_api(self):
        """Test de récupération du calendrier des trajets."""
        # Créer un trajet
        trip = Trip.objects.create(
            traveler=self.user,
            **self.trip_object_data,
            departure_date=timezone.now() + timedelta(days=7),
            arrival_date=timezone.now() + timedelta(days=8)
        )
        
        url = reverse('trips:trip_calendar')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('calendar_data', response.data)
        self.assertEqual(len(response.data['calendar_data']), 1)
        self.assertEqual(response.data['calendar_data'][0]['id'], trip.id)


class TripDocumentAPITest(APITestCase):
    """Tests pour l'API des documents de trajet."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testtraveler',
            email='traveler@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.trip = Trip.objects.create(
            traveler=self.user,
            origin_city='Alger',
            origin_country='Algeria',
            destination_city='Paris',
            destination_country='France',
            departure_date=timezone.now() + timedelta(days=7),
            arrival_date=timezone.now() + timedelta(days=8),
            max_weight=Decimal('20.00'),
            max_packages=5,
            accepted_package_types=['document'],
            min_price_per_kg=Decimal('15.00')
        )
    
    def test_upload_trip_document(self):
        """Test d'upload d'un document de trajet."""
        url = reverse('trips:upload_trip_document', kwargs={'trip_id': self.trip.id})
        
        file_content = b'fake pdf content'
        file = SimpleUploadedFile('ticket.pdf', file_content, content_type='application/pdf')
        
        data = {
            'document_type': 'flight_ticket',
            'file': file
        }
        
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('document', response.data)
        
        # Vérifier que le document a été créé en base
        document_id = response.data['document']['id']
        document = TripDocument.objects.get(id=document_id)
        self.assertEqual(document.document_type, 'flight_ticket')
        self.assertEqual(document.trip, self.trip)
    
    def test_list_trip_documents(self):
        """Test de récupération de la liste des documents d'un trajet."""
        # Créer un document
        document = TripDocument.objects.create(
            trip=self.trip,
            document_type='flight_ticket',
            file=SimpleUploadedFile('ticket.pdf', b'fake pdf content', content_type='application/pdf')
        )
        
        url = reverse('trips:trip_documents', kwargs={'trip_id': self.trip.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['documents']), 1)
        self.assertEqual(response.data['documents'][0]['id'], document.id)


class TripPermissionTest(APITestCase):
    """Tests pour les permissions des trajets."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testtraveler',
            email='traveler@test.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='othertraveler',
            email='other@test.com',
            password='testpass123'
        )
        
        self.trip = Trip.objects.create(
            traveler=self.user,
            origin_city='Alger',
            origin_country='Algeria',
            destination_city='Paris',
            destination_country='France',
            departure_date=timezone.now() + timedelta(days=7),
            arrival_date=timezone.now() + timedelta(days=8),
            max_weight=Decimal('20.00'),
            max_packages=5,
            accepted_package_types=['document'],
            min_price_per_kg=Decimal('15.00')
        )
    
    def test_unauthorized_access(self):
        """Test d'accès non autorisé."""
        # Désauthentifier le client
        self.client.force_authenticate(user=None)
        
        url = reverse('trips:trip_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_access_other_user_trip(self):
        """Test d'accès au trajet d'un autre utilisateur."""
        self.client.force_authenticate(user=self.other_user)
        
        url = reverse('trips:trip_detail', kwargs={'pk': self.trip.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
    
    def test_modify_other_user_trip(self):
        """Test de modification du trajet d'un autre utilisateur."""
        self.client.force_authenticate(user=self.other_user)
        
        url = reverse('trips:trip_update', kwargs={'pk': self.trip.id})
        response = self.client.put(url, {'notes': 'Hack attempt'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        
        # Vérifier que le trajet n'a pas été modifié
        self.trip.refresh_from_db()
        self.assertNotEqual(self.trip.notes, 'Hack attempt')
