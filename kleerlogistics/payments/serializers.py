"""
Sérialiseurs pour la gestion des paiements algériens
Support pour CIB, Eddahabia et paiement en espèces au bureau
"""

from rest_framework import serializers
from decimal import Decimal
from .models import Transaction, PaymentMethod, Wallet, Commission


class WalletSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le portefeuille utilisateur."""
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'user', 'balance', 'pending_balance', 'available_balance',
            'total_earned', 'total_spent', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les méthodes de paiement."""
    
    method_type_display = serializers.CharField(source='get_method_type_display', read_only=True)
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'name', 'method_type', 'method_type_display', 'is_active', 'is_online',
            'min_amount', 'max_amount', 'processing_fee', 'fixed_fee',
            'office_locations', 'office_hours', 'office_instructions',
            'description', 'icon_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les transactions."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'user', 'user_email', 'user_full_name',
            'shipment', 'related_transaction', 'type', 'type_display',
            'amount', 'currency', 'status', 'status_display',
            'external_payment_id', 'payment_method', 'payment_method_display',
            'payment_gateway', 'card_type', 'card_last_four', 'card_holder_name',
            'cash_payment_reference', 'cash_payment_location', 'cash_payment_date',
            'cash_payment_confirmed_by', 'description', 'metadata',
            'created_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'transaction_id', 'user', 'user_email', 'user_full_name',
            'external_payment_id', 'cash_payment_confirmed_by', 'created_at', 'completed_at'
        ]


class CardPaymentSerializer(serializers.Serializer):
    """Sérialiseur pour les paiements par carte bancaire algérienne."""
    
    # Informations de base
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2,
        min_value=Decimal('0.01'),
        help_text="Montant du paiement en DA"
    )
    card_type = serializers.ChoiceField(
        choices=[('cib', 'CIB'), ('eddahabia', 'Eddahabia'), ('visa', 'Visa'), ('mastercard', 'Mastercard')],
        help_text="Type de carte bancaire"
    )
    
    # Informations de la carte (optionnelles pour les tests)
    card_number = serializers.CharField(
        max_length=19,
        min_length=13,
        required=False,
        help_text="Numéro de la carte bancaire"
    )
    card_last_four = serializers.CharField(
        max_length=4,
        required=False,
        help_text="4 derniers chiffres de la carte"
    )
    card_holder_name = serializers.CharField(
        max_length=100,
        required=False,
        help_text="Nom du titulaire de la carte"
    )
    cvv = serializers.CharField(
        max_length=4,
        min_length=3,
        required=False,
        help_text="Code de sécurité de la carte"
    )
    expiry_month = serializers.CharField(
        max_length=2,
        required=False,
        help_text="Mois d'expiration (MM)"
    )
    expiry_year = serializers.CharField(
        max_length=4,
        required=False,
        help_text="Année d'expiration (YYYY)"
    )
    
    # Informations optionnelles
    shipment_id = serializers.IntegerField(
        required=False,
        help_text="ID de l'envoi associé"
    )
    description = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Description du paiement"
    )
    
    def validate_card_number(self, value):
        """Valide le numéro de carte."""
        if not value:
            return value
            
        # Supprimer les espaces
        value = value.replace(' ', '')
        
        # Validation basique du format
        if not value.isdigit():
            raise serializers.ValidationError("Le numéro de carte ne doit contenir que des chiffres")
        
        # Validation de la longueur selon le type
        if len(value) < 13 or len(value) > 19:
            raise serializers.ValidationError("Numéro de carte invalide")
        
        return value
    
    def validate_expiry_month(self, value):
        """Valide le mois d'expiration."""
        if not value:
            return value
            
        try:
            month = int(value)
            if month < 1 or month > 12:
                raise serializers.ValidationError("Mois d'expiration invalide")
        except ValueError:
            raise serializers.ValidationError("Mois d'expiration invalide")
        
        return value
    
    def validate_expiry_year(self, value):
        """Valide l'année d'expiration."""
        if not value:
            return value
            
        try:
            year = int(value)
            if year < 2024 or year > 2030:
                raise serializers.ValidationError("Année d'expiration invalide")
        except ValueError:
            raise serializers.ValidationError("Année d'expiration invalide")
        
        return value


class CashPaymentSerializer(serializers.Serializer):
    """Sérialiseur pour les paiements en espèces au bureau."""
    
    # Informations de base
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2,
        min_value=Decimal('0.01'),
        help_text="Montant du paiement en DA"
    )
    
    # Informations du bureau
    office_location = serializers.CharField(
        max_length=200,
        required=False,
        default="Bureau Kleer Infini - Alger Centre",
        help_text="Bureau de paiement"
    )
    
    # Informations optionnelles
    shipment = serializers.IntegerField(
        required=False,
        help_text="ID de l'envoi associé"
    )
    description = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Description du paiement"
    )
    contact_phone = serializers.CharField(
        max_length=20,
        required=False,
        help_text="Numéro de téléphone pour contact"
    )
    
    def validate_amount(self, value):
        """Valide le montant pour paiement en espèces."""
        # Limite pour paiement en espèces (50,000 DA)
        if value > 50000:
            raise serializers.ValidationError(
                "Le montant maximum pour paiement en espèces est de 50,000 DA"
            )
        return value


class PaymentValidationSerializer(serializers.Serializer):
    """Sérialiseur pour la validation des paiements."""
    
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2,
        min_value=Decimal('0.01'),
        help_text="Montant à valider"
    )
    payment_method = serializers.CharField(
        max_length=20,
        help_text="Méthode de paiement"
    )
    
    # Champs spécifiques selon la méthode
    card_number = serializers.CharField(
        max_length=19,
        required=False,
        help_text="Numéro de carte (pour paiement par carte)"
    )
    office_location = serializers.CharField(
        max_length=200,
        required=False,
        help_text="Bureau de paiement (pour paiement en espèces)"
    )


class PaymentConfirmationSerializer(serializers.Serializer):
    """Sérialiseur pour la confirmation de paiement en espèces."""
    
    payment_date = serializers.DateTimeField(
        required=False,
        help_text="Date de paiement (optionnel, utilise la date actuelle si non fournie)"
    )
    confirmation_notes = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Notes de confirmation"
    )
    receipt_number = serializers.CharField(
        max_length=50,
        required=False,
        help_text="Numéro de reçu"
    )


class PaymentFeesSerializer(serializers.Serializer):
    """Sérialiseur pour le calcul des frais de paiement."""
    
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2,
        min_value=Decimal('0.01'),
        help_text="Montant du paiement"
    )
    payment_method = serializers.CharField(
        max_length=20,
        help_text="Méthode de paiement"
    )


class CommissionSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les commissions."""
    
    shipment_tracking = serializers.CharField(source='shipment.tracking_number', read_only=True)
    sender_email = serializers.CharField(source='shipment.sender.email', read_only=True)
    traveler_email = serializers.CharField(source='shipment.matched_trip.traveler.email', read_only=True)
    
    class Meta:
        model = Commission
        fields = [
            'id', 'shipment', 'shipment_tracking', 'sender_email', 'traveler_email',
            'platform_commission', 'traveler_earning', 'total_amount',
            'commission_rate', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PaymentStatisticsSerializer(serializers.Serializer):
    """Sérialiseur pour les statistiques de paiement."""
    
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    
    def validate(self, data):
        """Valide les dates."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                "La date de début ne peut pas être postérieure à la date de fin"
            )
        
        return data


class TransactionListSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la liste des transactions."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'user_email', 'type', 'amount', 'currency',
            'status', 'status_display', 'payment_method', 'payment_method_display',
            'created_at'
        ]
        read_only_fields = ['id', 'transaction_id', 'user_email', 'created_at']


class PaymentMethodCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour créer une méthode de paiement (admin)."""
    
    class Meta:
        model = PaymentMethod
        fields = [
            'name', 'method_type', 'is_active', 'is_online',
            'min_amount', 'max_amount', 'processing_fee', 'fixed_fee',
            'office_locations', 'office_hours', 'office_instructions',
            'description', 'icon_url'
        ]
    
    def validate_name(self, value):
        """Valide le nom de la méthode de paiement."""
        if PaymentMethod.objects.filter(name=value).exists():
            raise serializers.ValidationError("Une méthode de paiement avec ce nom existe déjà")
        return value
    
    def validate(self, data):
        """Validation globale."""
        # Vérifier que les frais ne sont pas négatifs
        if data.get('processing_fee', 0) < 0:
            raise serializers.ValidationError("Les frais de traitement ne peuvent pas être négatifs")
        
        if data.get('fixed_fee', 0) < 0:
            raise serializers.ValidationError("Les frais fixes ne peuvent pas être négatifs")
        
        # Vérifier que le montant minimum est inférieur au maximum
        min_amount = data.get('min_amount', 0)
        max_amount = data.get('max_amount', 100000)
        
        if min_amount >= max_amount:
            raise serializers.ValidationError(
                "Le montant minimum doit être inférieur au montant maximum"
            )
        
        return data 


class ChargilyPaymentSerializer(serializers.Serializer):
    """Sérialiseur pour les paiements Chargily."""
    
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2,
        min_value=Decimal('0.01'),
        help_text="Montant du paiement en DA"
    )
    payment_mode = serializers.ChoiceField(
        choices=[('edahabia', 'Edahabia'), ('cib', 'CIB'), ('baridi_mob', 'Baridi Mob')],
        help_text="Mode de paiement Chargily"
    )
    shipment_id = serializers.IntegerField(
        help_text="ID de l'envoi associé"
    )
    description = serializers.CharField(
        max_length=200,
        required=False,
        help_text="Description du paiement"
    )
    back_url = serializers.URLField(
        required=False,
        help_text="URL de retour après paiement"
    )
    webhook_url = serializers.URLField(
        required=False,
        help_text="URL webhook pour les notifications"
    )


class ChargilyWebhookSerializer(serializers.Serializer):
    """Sérialiseur pour les webhooks Chargily."""
    
    id = serializers.CharField(help_text="ID du paiement Chargily")
    order_id = serializers.CharField(help_text="ID de la commande")
    status = serializers.CharField(help_text="Statut du paiement")
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, help_text="Montant")
    currency = serializers.CharField(help_text="Devise")
    payment_mode = serializers.CharField(help_text="Mode de paiement")
    created_at = serializers.DateTimeField(help_text="Date de création")


class CommissionCalculateSerializer(serializers.Serializer):
    """Sérialiseur pour le calcul des commissions."""
    
    shipment_id = serializers.IntegerField(help_text="ID de l'envoi")
    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2,
        min_value=Decimal('0.01'),
        help_text="Montant total"
    )
    commission_rate = serializers.DecimalField(
        max_digits=5, decimal_places=2,
        min_value=0,
        max_value=100,
        default=25.0,
        help_text="Taux de commission en pourcentage"
    )


class CommissionApplySerializer(serializers.Serializer):
    """Sérialiseur pour l'application des commissions."""
    
    shipment_id = serializers.IntegerField(help_text="ID de l'envoi")
    commission_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2,
        min_value=0,
        help_text="Montant de la commission"
    )
    traveler_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2,
        min_value=0,
        help_text="Montant pour le voyageur"
    )
    description = serializers.CharField(
        max_length=200,
        required=False,
        help_text="Description de la commission"
    )


class BankTransferRequestSerializer(serializers.Serializer):
    """Sérialiseur pour les demandes de virement bancaire."""
    
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2,
        min_value=Decimal('0.01'),
        help_text="Montant du virement"
    )
    bank_name = serializers.CharField(
        max_length=100,
        help_text="Nom de la banque"
    )
    account_number = serializers.CharField(
        max_length=50,
        help_text="Numéro de compte"
    )
    account_holder = serializers.CharField(
        max_length=100,
        help_text="Nom du titulaire du compte"
    )
    description = serializers.CharField(
        max_length=200,
        required=False,
        help_text="Description du virement"
    )


class BankTransferConfirmSerializer(serializers.Serializer):
    """Sérialiseur pour la confirmation des virements bancaires."""
    
    transfer_id = serializers.CharField(help_text="ID de la transaction de virement")
    bank_reference = serializers.CharField(
        max_length=100,
        help_text="Référence bancaire"
    )
    confirmation_date = serializers.DateField(
        required=False,
        help_text="Date de confirmation"
    )
    notes = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Notes de confirmation"
    )


class CashPaymentOfficeSerializer(serializers.Serializer):
    """Sérialiseur pour les bureaux de paiement en espèces."""
    
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(help_text="Nom du bureau")
    address = serializers.CharField(help_text="Adresse du bureau")
    phone = serializers.CharField(help_text="Téléphone du bureau")
    hours = serializers.CharField(help_text="Heures d'ouverture")
    coordinates = serializers.DictField(
        child=serializers.FloatField(),
        help_text="Coordonnées GPS"
    )


class PaymentMethodDetailSerializer(serializers.ModelSerializer):
    """Sérialiseur détaillé pour les méthodes de paiement."""
    
    method_type_display = serializers.CharField(source='get_method_type_display', read_only=True)
    is_available = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'name', 'method_type', 'method_type_display', 'is_active', 'is_online',
            'min_amount', 'max_amount', 'processing_fee', 'fixed_fee',
            'office_locations', 'office_hours', 'office_instructions',
            'description', 'icon_url', 'is_available', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_available(self, obj):
        """Détermine si la méthode est disponible pour le montant donné."""
        amount = self.context.get('amount')
        if amount is None:
            return obj.is_active
        
        return (obj.is_active and 
                obj.min_amount <= amount <= obj.max_amount) 