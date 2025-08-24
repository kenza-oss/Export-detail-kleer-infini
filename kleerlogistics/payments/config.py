"""
Configuration pour le module de paiements KleerLogistics
Paramètres pour les différents types de paiement algériens
"""

from decimal import Decimal

# Configuration générale des paiements
PAYMENT_CONFIG = {
    'default_currency': 'DZD',
    'min_transaction_amount': Decimal('100.00'),
    'max_transaction_amount': Decimal('1000000.00'),
    'transaction_timeout_hours': 24,
}

# Configuration des cartes bancaires algériennes
CARD_PAYMENT_CONFIG = {
    'cib': {
        'name': 'CIB (Carte Interbancaire)',
        'is_active': True,
        'min_amount': Decimal('100.00'),
        'max_amount': Decimal('500000.00'),
        'processing_fee': Decimal('0.00'),
        'fixed_fee': Decimal('0.00'),
        'description': 'Paiement par carte CIB algérienne',
        'icon_url': '/static/images/payment/cib.png',
    },
    'eddahabia': {
        'name': 'Edahabia',
        'is_active': True,
        'min_amount': Decimal('100.00'),
        'max_amount': Decimal('500000.00'),
        'processing_fee': Decimal('0.00'),
        'fixed_fee': Decimal('0.00'),
        'description': 'Paiement par carte Edahabia',
        'icon_url': '/static/images/payment/eddahabia.png',
    },
    'visa': {
        'name': 'Visa',
        'is_active': True,
        'min_amount': Decimal('100.00'),
        'max_amount': Decimal('1000000.00'),
        'processing_fee': Decimal('2.5'),
        'fixed_fee': Decimal('50.00'),
        'description': 'Paiement par carte Visa',
        'icon_url': '/static/images/payment/visa.png',
    },
    'mastercard': {
        'name': 'Mastercard',
        'is_active': True,
        'min_amount': Decimal('100.00'),
        'max_amount': Decimal('1000000.00'),
        'processing_fee': Decimal('2.5'),
        'fixed_fee': Decimal('50.00'),
        'description': 'Paiement par carte Mastercard',
        'icon_url': '/static/images/payment/mastercard.png',
    },
}

# Configuration des paiements en espèces
CASH_PAYMENT_CONFIG = {
    'is_active': True,
    'min_amount': Decimal('100.00'),
    'max_amount': Decimal('50000.00'),
    'processing_fee': Decimal('0.00'),
    'fixed_fee': Decimal('0.00'),
    'description': 'Paiement en espèces au bureau',
    'icon_url': '/static/images/payment/cash.png',
    'offices': [
        {
            'id': 1,
            'name': 'Bureau Kleer Infini - Alger Centre',
            'address': '123 Rue Didouche Mourad, Alger',
            'phone': '+213 21 123 456',
            'email': 'alger@kleerinfini.com',
            'hours': 'Lun-Ven: 9h-17h, Sam: 9h-12h',
            'coordinates': {'lat': 36.7538, 'lng': 3.0588},
            'is_active': True,
        },
        {
            'id': 2,
            'name': 'Bureau Kleer Infini - Oran',
            'address': '456 Boulevard de l\'ALN, Oran',
            'phone': '+213 41 789 012',
            'email': 'oran@kleerinfini.com',
            'hours': 'Lun-Ven: 8h-16h, Sam: 8h-11h',
            'coordinates': {'lat': 35.6971, 'lng': -0.6337},
            'is_active': True,
        },
        {
            'id': 3,
            'name': 'Bureau Kleer Infini - Constantine',
            'address': '789 Rue Larbi Ben M\'Hidi, Constantine',
            'phone': '+213 31 345 678',
            'email': 'constantine@kleerinfini.com',
            'hours': 'Lun-Ven: 9h-17h, Sam: 9h-12h',
            'coordinates': {'lat': 36.3650, 'lng': 6.6147},
            'is_active': True,
        },
    ],
}

# Configuration Chargily Pay
CHARGILY_CONFIG = {
    'is_active': True,
    'api_key': None,  # À configurer en production
    'api_secret': None,  # À configurer en production
    'webhook_secret': None,  # À configurer en production
    'base_url': 'https://pay.chargily.com',
    'modes': {
        'edahabia': {
            'name': 'Edahabia',
            'is_active': True,
            'min_amount': Decimal('100.00'),
            'max_amount': Decimal('500000.00'),
            'processing_fee': Decimal('0.00'),
            'fixed_fee': Decimal('0.00'),
            'description': 'Paiement via Edahabia',
            'icon_url': '/static/images/payment/edahabia.png',
        },
        'cib': {
            'name': 'CIB',
            'is_active': True,
            'min_amount': Decimal('100.00'),
            'max_amount': Decimal('500000.00'),
            'processing_fee': Decimal('0.00'),
            'fixed_fee': Decimal('0.00'),
            'description': 'Paiement via CIB',
            'icon_url': '/static/images/payment/cib.png',
        },
        'baridi_mob': {
            'name': 'Baridi Mob',
            'is_active': True,
            'min_amount': Decimal('100.00'),
            'max_amount': Decimal('100000.00'),
            'processing_fee': Decimal('0.00'),
            'fixed_fee': Decimal('0.00'),
            'description': 'Paiement via Baridi Mob',
            'icon_url': '/static/images/payment/baridi_mob.png',
        },
    },
}

# Configuration des commissions
COMMISSION_CONFIG = {
    'default_rate': Decimal('25.0'),  # 25%
    'min_rate': Decimal('0.0'),
    'max_rate': Decimal('50.0'),
    'min_commission': Decimal('500.00'),
    'max_commission': Decimal('5000.00'),
    'description': 'Commission standard Kleer Logistics',
}

# Configuration des virements bancaires
BANK_TRANSFER_CONFIG = {
    'is_active': True,
    'min_amount': Decimal('1000.00'),
    'max_amount': Decimal('100000.00'),
    'processing_fee': Decimal('0.00'),
    'fixed_fee': Decimal('0.00'),
    'processing_days': 3,  # Jours ouvrables
    'description': 'Virement bancaire',
    'icon_url': '/static/images/payment/bank_transfer.png',
    'supported_banks': [
        'BNA', 'BNP Paribas El Djazaïr', 'Société Générale Algérie',
        'Crédit Populaire d\'Algérie', 'Banque de l\'Agriculture et du Développement Rural',
        'Banque de Développement Local', 'Banque Extérieure d\'Algérie'
    ],
}

# Configuration des portefeuilles virtuels
WALLET_CONFIG = {
    'is_active': True,
    'min_deposit': Decimal('100.00'),
    'max_deposit': Decimal('100000.00'),
    'min_withdrawal': Decimal('500.00'),
    'max_withdrawal': Decimal('50000.00'),
    'min_transfer': Decimal('100.00'),
    'max_transfer': Decimal('10000.00'),
    'daily_transfer_limit': Decimal('50000.00'),
    'description': 'Portefeuille virtuel Kleer Logistics',
    'icon_url': '/static/images/payment/wallet.png',
}

# Configuration des notifications
NOTIFICATION_CONFIG = {
    'payment_confirmation': True,
    'low_balance_alert': True,
    'transaction_alerts': True,
    'email_notifications': True,
    'sms_notifications': True,
    'push_notifications': True,
    'low_balance_threshold': Decimal('1000.00'),
}

# Configuration des rapports
REPORTING_CONFIG = {
    'default_period_days': 30,
    'max_period_days': 365,
    'export_formats': ['csv', 'xlsx', 'pdf'],
    'auto_generate_reports': True,
    'report_retention_days': 1095,  # 3 ans
}

# Configuration de sécurité
SECURITY_CONFIG = {
    'max_failed_attempts': 3,
    'lockout_duration_minutes': 30,
    'require_2fa_for_large_amounts': True,
    'large_amount_threshold': Decimal('10000.00'),
    'session_timeout_minutes': 60,
    'webhook_signature_required': True,
}

# Configuration des frais
FEES_CONFIG = {
    'packaging_fees': {
        'small': Decimal('200.00'),
        'medium': Decimal('500.00'),
        'large': Decimal('1000.00'),
        'extra_large': Decimal('2000.00'),
    },
    'insurance_fees': {
        'basic': Decimal('100.00'),
        'premium': Decimal('500.00'),
        'full_coverage': Decimal('1000.00'),
    },
    'urgent_delivery_fee': Decimal('1000.00'),
    'weekend_delivery_fee': Decimal('500.00'),
    'remote_area_fee': Decimal('300.00'),
}
