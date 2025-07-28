"""
Serializers for payments app - JSON serialization for payment data
"""

from rest_framework import serializers
from django.utils import timezone

from .models import Wallet, Transaction, Commission


class WalletSerializer(serializers.ModelSerializer):
    """Serializer pour les portefeuilles."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'user', 'user_email', 'user_name', 'balance',
            'currency', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_user_name(self, obj):
        """Obtenir le nom de l'utilisateur."""
        return f"{obj.user.first_name} {obj.user.last_name}"


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer pour les transactions."""
    
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'transaction_type', 'transaction_type_display',
            'amount', 'payment_method', 'payment_method_display',
            'status', 'status_display', 'reference', 'description',
            'created_at'
        ]
        read_only_fields = [
            'id', 'user', 'reference', 'created_at'
        ]


class CommissionSerializer(serializers.ModelSerializer):
    """Serializer pour les commissions."""
    
    class Meta:
        model = Commission
        fields = [
            'id', 'transaction', 'amount', 'percentage',
            'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PaymentMethodSerializer(serializers.Serializer):
    """Serializer pour les méthodes de paiement."""
    
    method = serializers.ChoiceField(choices=[
        ('card', 'Carte bancaire'),
        ('edahabia', 'Edahabia'),
        ('cib', 'CIB'),
        ('baridi', 'Baridi Mob'),
        ('wallet', 'Portefeuille')
    ])
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    description = serializers.CharField(max_length=255, required=False)
    
    def validate_amount(self, value):
        """Valider le montant."""
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif.")
        return value


class ChargilyPaySerializer(serializers.Serializer):
    """Serializer pour les paiements Chargily."""
    
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=[
        ('edahabia', 'Edahabia'),
        ('cib', 'CIB'),
        ('baridi', 'Baridi Mob')
    ])
    client = serializers.CharField(max_length=255)
    client_email = serializers.EmailField()
    invoice_number = serializers.CharField(max_length=50, required=False)
    back_url = serializers.URLField(required=False)
    webhook_url = serializers.URLField(required=False)
    
    def validate_amount(self, value):
        """Valider le montant."""
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif.")
        return value


class DepositSerializer(serializers.Serializer):
    """Serializer pour les dépôts."""
    
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=[
        ('card', 'Carte bancaire'),
        ('edahabia', 'Edahabia'),
        ('cib', 'CIB'),
        ('baridi', 'Baridi Mob')
    ], default='card')
    
    def validate_amount(self, value):
        """Valider le montant."""
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif.")
        return value


class WithdrawalSerializer(serializers.Serializer):
    """Serializer pour les retraits."""
    
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    bank_account = serializers.CharField(max_length=255, required=False)
    payment_method = serializers.ChoiceField(choices=[
        ('bank_transfer', 'Virement bancaire'),
        ('mobile_money', 'Mobile Money')
    ], default='bank_transfer')
    
    def validate_amount(self, value):
        """Valider le montant."""
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif.")
        return value


class TransferSerializer(serializers.Serializer):
    """Serializer pour les transferts."""
    
    recipient_email = serializers.EmailField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    description = serializers.CharField(max_length=255, required=False)
    
    def validate_amount(self, value):
        """Valider le montant."""
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif.")
        return value
    
    def validate_recipient_email(self, value):
        """Valider l'email du destinataire."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Utilisateur non trouvé.")
        return value


class RefundSerializer(serializers.Serializer):
    """Serializer pour les remboursements."""
    
    reason = serializers.CharField(max_length=500)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    def validate_amount(self, value):
        """Valider le montant."""
        if value and value <= 0:
            raise serializers.ValidationError("Le montant doit être positif.")
        return value


class PaymentAnalyticsSerializer(serializers.Serializer):
    """Serializer pour les analytics de paiement."""
    
    total_transactions = serializers.IntegerField()
    total_volume = serializers.DecimalField(max_digits=10, decimal_places=2)
    deposits_count = serializers.IntegerField()
    withdrawals_count = serializers.IntegerField()
    transfers_count = serializers.IntegerField()
    monthly_stats = serializers.ListField()
    
    def to_representation(self, instance):
        """Formater les analytics."""
        return {
            'success': True,
            'analytics': {
                'total_transactions': instance.get('total_transactions', 0),
                'total_volume': instance.get('total_volume', 0),
                'deposits_count': instance.get('deposits_count', 0),
                'withdrawals_count': instance.get('withdrawals_count', 0),
                'transfers_count': instance.get('transfers_count', 0),
                'monthly_stats': instance.get('monthly_stats', [])
            }
        }


class TransactionSearchSerializer(serializers.ModelSerializer):
    """Serializer pour la recherche de transactions."""
    
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_type', 'transaction_type_display',
            'amount', 'payment_method', 'payment_method_display',
            'status', 'status_display', 'reference', 'created_at',
            'user_summary'
        ]
    
    def get_user_summary(self, obj):
        """Obtenir un résumé de l'utilisateur."""
        return {
            'id': obj.user.id,
            'name': f"{obj.user.first_name} {obj.user.last_name}",
            'email': obj.user.email
        }


class TransactionExportSerializer(serializers.ModelSerializer):
    """Serializer pour l'export des transactions."""
    
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'reference', 'transaction_type', 'transaction_type_display',
            'amount', 'payment_method', 'payment_method_display',
            'status', 'status_display', 'user_email', 'created_at'
        ] 