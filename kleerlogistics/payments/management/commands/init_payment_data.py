"""
Commande de management pour initialiser les données de paiement de test
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from payments.models import PaymentMethod
from decimal import Decimal


class Command(BaseCommand):
    help = 'Initialise les données de paiement de test'

    def handle(self, *args, **options):
        self.stdout.write('Initialisation des données de paiement...')
        
        with transaction.atomic():
            # Créer les méthodes de paiement
            payment_methods = [
                {
                    'name': 'CIB',
                    'method_type': 'cib',
                    'is_active': True,
                    'is_online': True,
                    'min_amount': Decimal('100.00'),
                    'max_amount': Decimal('500000.00'),
                    'processing_fee': Decimal('0.00'),
                    'fixed_fee': Decimal('0.00'),
                    'description': 'Paiement par carte CIB algérienne',
                    'icon_url': '/static/images/payment/cib.png',
                },
                {
                    'name': 'Eddahabia',
                    'method_type': 'eddahabia',
                    'is_active': True,
                    'is_online': True,
                    'min_amount': Decimal('100.00'),
                    'max_amount': Decimal('500000.00'),
                    'processing_fee': Decimal('0.00'),
                    'fixed_fee': Decimal('0.00'),
                    'description': 'Paiement par carte Eddahabia',
                    'icon_url': '/static/images/payment/eddahabia.png',
                },
                {
                    'name': 'Visa',
                    'method_type': 'card',
                    'is_active': True,
                    'is_online': True,
                    'min_amount': Decimal('100.00'),
                    'max_amount': Decimal('1000000.00'),
                    'processing_fee': Decimal('2.5'),
                    'fixed_fee': Decimal('50.00'),
                    'description': 'Paiement par carte Visa',
                    'icon_url': '/static/images/payment/visa.png',
                },
                {
                    'name': 'Mastercard',
                    'method_type': 'card',
                    'is_active': True,
                    'is_online': True,
                    'min_amount': Decimal('100.00'),
                    'max_amount': Decimal('1000000.00'),
                    'processing_fee': Decimal('2.5'),
                    'fixed_fee': Decimal('50.00'),
                    'description': 'Paiement par carte Mastercard',
                    'icon_url': '/static/images/payment/mastercard.png',
                },
                {
                    'name': 'Espèces',
                    'method_type': 'cash',
                    'is_active': True,
                    'is_online': False,
                    'min_amount': Decimal('100.00'),
                    'max_amount': Decimal('50000.00'),
                    'processing_fee': Decimal('0.00'),
                    'fixed_fee': Decimal('0.00'),
                    'description': 'Paiement en espèces au bureau',
                    'icon_url': '/static/images/payment/cash.png',
                    'office_locations': [
                        {
                            'id': 1,
                            'name': 'Bureau Kleer Infini - Alger Centre',
                            'address': '123 Rue Didouche Mourad, Alger',
                            'phone': '+213 21 123 456',
                            'hours': 'Lun-Ven: 9h-17h, Sam: 9h-12h',
                        },
                        {
                            'id': 2,
                            'name': 'Bureau Kleer Infini - Oran',
                            'address': '456 Boulevard de l\'ALN, Oran',
                            'phone': '+213 41 789 012',
                            'hours': 'Lun-Ven: 8h-16h, Sam: 8h-11h',
                        }
                    ],
                    'office_hours': 'Lun-Ven: 9h-17h, Sam: 9h-12h',
                    'office_instructions': 'Présentez-vous au bureau avec votre pièce d\'identité et le montant exact.',
                },
                {
                    'name': 'Virement Bancaire',
                    'method_type': 'bank_transfer',
                    'is_active': True,
                    'is_online': True,
                    'min_amount': Decimal('1000.00'),
                    'max_amount': Decimal('100000.00'),
                    'processing_fee': Decimal('0.00'),
                    'fixed_fee': Decimal('0.00'),
                    'description': 'Virement bancaire',
                    'icon_url': '/static/images/payment/bank_transfer.png',
                },
                {
                    'name': 'Chargily Pay',
                    'method_type': 'chargily',
                    'is_active': True,
                    'is_online': True,
                    'min_amount': Decimal('100.00'),
                    'max_amount': Decimal('500000.00'),
                    'processing_fee': Decimal('0.00'),
                    'fixed_fee': Decimal('0.00'),
                    'description': 'Paiement via Chargily Pay',
                    'icon_url': '/static/images/payment/chargily.png',
                },
                {
                    'name': 'Portefeuille Virtuel',
                    'method_type': 'wallet',
                    'is_active': True,
                    'is_online': True,
                    'min_amount': Decimal('100.00'),
                    'max_amount': Decimal('100000.00'),
                    'processing_fee': Decimal('0.00'),
                    'fixed_fee': Decimal('0.00'),
                    'description': 'Paiement via portefeuille virtuel',
                    'icon_url': '/static/images/payment/wallet.png',
                },
            ]
            
            for method_data in payment_methods:
                PaymentMethod.objects.get_or_create(
                    name=method_data['name'],
                    defaults=method_data
                )
                self.stdout.write(f'✓ Méthode de paiement créée: {method_data["name"]}')
        
        self.stdout.write(
            self.style.SUCCESS('Données de paiement initialisées avec succès!')
        )
