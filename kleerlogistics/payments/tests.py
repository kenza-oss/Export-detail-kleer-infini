"""
Tests pour le module de paiements KleerLogistics
Tests unitaires et d'intégration pour tous les types de paiement algériens
"""

import json
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import Wallet, Transaction, PaymentMethod
from .services import AlgerianPaymentService, PaymentValidationService

User = get_user_model()


class WalletModelTest(TestCase):
    """Tests pour le modèle Wallet."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.wallet = Wallet.objects.create(user=self.user)
    
    def test_wallet_creation(self):
        """Test de création d'un portefeuille."""
        self.assertEqual(self.wallet.balance, Decimal('0.00'))
        self.assertEqual(self.wallet.available_balance, Decimal('0.00'))
    
    def test_add_funds(self):
        """Test d'ajout de fonds."""
        self.wallet.add_funds(Decimal('1000.00'))
        self.assertEqual(self.wallet.balance, Decimal('1000.00'))
    
    def test_deduct_funds(self):
        """Test de déduction de fonds."""
        self.wallet.add_funds(Decimal('1000.00'))
        self.wallet.deduct_funds(Decimal('500.00'))
        self.assertEqual(self.wallet.balance, Decimal('500.00'))


class TransactionModelTest(TestCase):
    """Tests pour le modèle Transaction."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_transaction_creation(self):
        """Test de création d'une transaction."""
        transaction = Transaction.objects.create(
            user=self.user,
            type='payment',
            amount=Decimal('1000.00'),
            currency='DZD',
            payment_method='cib',
            description='Test transaction'
        )
        
        self.assertEqual(transaction.amount, Decimal('1000.00'))
        self.assertEqual(transaction.currency, 'DZD')
        self.assertIsNotNone(transaction.transaction_id)


class PaymentMethodsAPITest(APITestCase):
    """Tests pour l'API des méthodes de paiement."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client.force_authenticate(user=self.user)
        
        PaymentMethod.objects.create(
            name='CIB',
            method_type='cib',
            is_active=True,
            min_amount=Decimal('100.00'),
            max_amount=Decimal('500000.00')
        )
    
    def test_get_payment_methods(self):
        """Test de récupération des méthodes de paiement."""
        url = reverse('payments:payment_methods')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('payment_methods', response.data)


class CardPaymentAPITest(APITestCase):
    """Tests pour l'API des paiements par carte."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_cib_payment(self):
        """Test de création d'un paiement CIB."""
        url = reverse('payments:card_payment')
        data = {
            'amount': '5000.00',
            'card_type': 'cib',
            'card_number': '1234567890123456',
            'card_holder_name': 'Ahmed Benali',
            'description': 'Paiement transport CIB'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('transaction', response.data)
        self.assertIn('transaction_id', response.data['transaction'])


class WalletAPITest(APITestCase):
    """Tests pour l'API des portefeuilles."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_wallet(self):
        """Test de récupération du portefeuille."""
        wallet = Wallet.objects.create(user=self.user)
        wallet.add_funds(Decimal('5000.00'))
        
        url = reverse('payments:wallet')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('wallet', response.data)
        self.assertIn('balance', response.data['wallet'])
    
    def test_wallet_deposit(self):
        """Test de dépôt sur le portefeuille."""
        Wallet.objects.create(user=self.user)
        
        url = reverse('payments:wallet_deposit')
        data = {
            'amount': '10000.00',
            'payment_method': 'chargily',
            'description': 'Dépôt initial sur le portefeuille'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('transaction_id', response.data)


class PaymentServicesTest(TestCase):
    """Tests pour les services de paiement."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_card_payment_validation(self):
        """Test de validation des paiements par carte."""
        result = PaymentValidationService.validate_card_payment(
            card_type='cib',
            card_number='1234567890123456',
            amount=Decimal('5000.00')
        )
        self.assertTrue(result['valid'])
        
        result = PaymentValidationService.validate_card_payment(
            card_type='cib',
            card_number='1234567890123456',
            amount=Decimal('-100.00')
        )
        self.assertFalse(result['valid'])
    
    def test_cash_payment_validation(self):
        """Test de validation des paiements en espèces."""
        result = PaymentValidationService.validate_cash_payment(
            amount=Decimal('5000.00'),
            office_location='Bureau Alger'
        )
        self.assertTrue(result['valid'])
