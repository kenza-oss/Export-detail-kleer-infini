from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

User = get_user_model()


class Wallet(models.Model):
    """Modèle pour les portefeuilles virtuels des utilisateurs."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    
    # Soldes
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    pending_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    
    # Statistiques
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['balance']),
        ]
    
    def __str__(self):
        return f"Wallet for {self.user.username} - Balance: {self.balance}"
    
    @property
    def available_balance(self):
        """Solde disponible (balance - pending)."""
        # S'assurer que les deux valeurs sont des Decimal
        balance = Decimal(str(self.balance))
        pending_balance = Decimal(str(self.pending_balance))
        return balance - pending_balance
    
    def can_withdraw(self, amount):
        """Vérifie si le retrait est possible."""
        # Convertir amount en Decimal si ce n'est pas déjà le cas
        amount = Decimal(str(amount))
        return self.available_balance >= amount
    
    def add_funds(self, amount, transaction_type='credit'):
        """Ajoute des fonds au portefeuille."""
        if amount <= 0:
            raise ValueError("Le montant doit être positif")
        
        # Convertir en Decimal pour éviter les problèmes de type
        amount = Decimal(str(amount))
        
        # S'assurer que balance est aussi un Decimal
        self.balance = Decimal(str(self.balance))
        self.balance += amount
        
        if transaction_type == 'earning':
            self.total_earned = Decimal(str(self.total_earned)) + amount
        elif transaction_type == 'refund':
            self.total_spent = Decimal(str(self.total_spent)) - amount
        
        self.save()
    
    def deduct_funds(self, amount, transaction_type='debit'):
        """Déduit des fonds du portefeuille."""
        if amount <= 0:
            raise ValueError("Le montant doit être positif")
        
        # Convertir en Decimal pour éviter les problèmes de type
        amount = Decimal(str(amount))
        
        if not self.can_withdraw(amount):
            raise ValueError("Solde insuffisant")
        
        # S'assurer que balance est aussi un Decimal
        self.balance = Decimal(str(self.balance))
        self.balance -= amount
        
        if transaction_type == 'payment':
            self.total_spent = Decimal(str(self.total_spent)) + amount
        
        self.save()
    
    def hold_funds(self, amount):
        """Met en attente des fonds pour une transaction."""
        if amount <= 0:
            raise ValueError("Le montant doit être positif")
        
        # Convertir en Decimal pour éviter les problèmes de type
        amount = Decimal(str(amount))
        
        if not self.can_withdraw(amount):
            raise ValueError("Solde insuffisant")
        
        # S'assurer que pending_balance est aussi un Decimal
        self.pending_balance = Decimal(str(self.pending_balance))
        self.pending_balance += amount
        self.save()
    
    def release_hold(self, amount):
        """Libère les fonds en attente."""
        if amount <= 0:
            raise ValueError("Le montant doit être positif")
        
        # Convertir en Decimal pour éviter les problèmes de type
        amount = Decimal(str(amount))
        
        # S'assurer que pending_balance est aussi un Decimal
        self.pending_balance = Decimal(str(self.pending_balance))
        
        if self.pending_balance < amount:
            raise ValueError("Montant en attente insuffisant")
        
        self.pending_balance -= amount
        self.save()
    
    def confirm_hold(self, amount):
        """Confirme une mise en attente (déduit du solde principal)."""
        if amount <= 0:
            raise ValueError("Le montant doit être positif")
        
        # Convertir en Decimal pour éviter les problèmes de type
        amount = Decimal(str(amount))
        
        # S'assurer que les balances sont aussi des Decimal
        self.pending_balance = Decimal(str(self.pending_balance))
        self.balance = Decimal(str(self.balance))
        
        if self.pending_balance < amount:
            raise ValueError("Montant en attente insuffisant")
        
        self.pending_balance -= amount
        self.balance -= amount
        self.save()


class Transaction(models.Model):
    """Modèle pour les transactions financières."""
    
    TRANSACTION_TYPES = [
        ('deposit', 'Dépôt'),
        ('withdrawal', 'Retrait'),
        ('payment', 'Paiement'),
        ('refund', 'Remboursement'),
        ('commission', 'Commission'),
        ('earning', 'Gains'),
        ('transfer', 'Transfert'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
        ('refunded', 'Remboursé'),
    ]
    
    # Méthodes de paiement
    PAYMENT_METHODS = [
        ('wallet', 'Portefeuille'),
        ('card', 'Carte bancaire'),
        ('cib', 'CIB'),
        ('eddahabia', 'Eddahabia'),
        ('cash', 'Espèces'),
        ('bank_transfer', 'Virement bancaire'),
        ('chargily', 'Chargily Pay'),
    ]
    
    # Passerelles de paiement
    PAYMENT_GATEWAYS = [
        ('cib', 'CIB'),
        ('eddahabia', 'Eddahabia'),
        ('chargily', 'Chargily Pay'),
        ('stripe', 'Stripe'),
        ('manual', 'Manuel (Bureau)'),
    ]
    
    # Identifiant unique
    transaction_id = models.CharField(max_length=50, unique=True, blank=True)
    
    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    shipment = models.ForeignKey('shipments.Shipment', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    related_transaction = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='related_transactions')
    
    # Détails de la transaction
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    currency = models.CharField(max_length=3, default='DZD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Informations de paiement externe
    external_payment_id = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, blank=True)
    payment_gateway = models.CharField(max_length=20, choices=PAYMENT_GATEWAYS, blank=True)
    
    # Informations spécifiques aux cartes algériennes
    card_type = models.CharField(max_length=20, blank=True, choices=[
        ('cib', 'CIB'),
        ('eddahabia', 'Eddahabia'),
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
    ])
    card_last_four = models.CharField(max_length=4, blank=True)
    card_holder_name = models.CharField(max_length=100, blank=True)
    
    # Informations pour paiement en espèces
    cash_payment_reference = models.CharField(max_length=50, blank=True, help_text="Référence de paiement en espèces")
    cash_payment_location = models.CharField(max_length=200, blank=True, help_text="Bureau de paiement")
    cash_payment_date = models.DateTimeField(null=True, blank=True, help_text="Date de paiement en espèces")
    cash_payment_confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cash_payments_confirmed')
    
    # Description et métadonnées
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'type']),
            models.Index(fields=['shipment']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['card_type']),
        ]
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.type} {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"TXN{uuid.uuid4().hex[:12].upper()}"
        
        # Définir automatiquement le type de carte basé sur la méthode de paiement
        if self.payment_method in ['cib', 'eddahabia']:
            self.card_type = self.payment_method
        
        super().save(*args, **kwargs)
    
    def complete(self):
        """Marque la transaction comme terminée."""
        from django.utils import timezone
        
        if self.status not in ['pending', 'processing']:
            raise ValueError("Seules les transactions en attente ou en cours peuvent être terminées")
        
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Mettre à jour le portefeuille si nécessaire
        wallet, created = Wallet.objects.get_or_create(user=self.user)
        if self.type in ['deposit', 'earning', 'refund']:
            wallet.add_funds(self.amount, self.type)
        elif self.type == 'withdrawal':
            wallet.deduct_funds(self.amount, self.type)
        elif self.type == 'payment':
            # Pour les paiements par carte, on ajoute les fonds au portefeuille
            # car c'est un paiement entrant (l'utilisateur paie pour un service)
            if self.payment_method in ['cib', 'eddahabia', 'card', 'chargily']:
                wallet.add_funds(self.amount, 'payment')
            else:
                # Pour les autres méthodes (espèces, etc.), on déduit
                wallet.deduct_funds(self.amount, self.type)
    
    def fail(self, reason=""):
        """Marque la transaction comme échouée."""
        if self.status not in ['pending', 'processing']:
            raise ValueError("Seules les transactions en attente ou en cours peuvent échouer")
        
        self.status = 'failed'
        self.metadata['failure_reason'] = reason
        self.save()
    
    def cancel(self):
        """Annule la transaction."""
        if self.status not in ['pending', 'processing']:
            raise ValueError("Seules les transactions en attente ou en cours peuvent être annulées")
        
        self.status = 'cancelled'
        self.save()
    
    def refund(self, amount=None):
        """Rembourse la transaction."""
        if self.status != 'completed':
            raise ValueError("Seules les transactions terminées peuvent être remboursées")
        
        refund_amount = amount or self.amount
        
        # Créer une transaction de remboursement
        refund_transaction = Transaction.objects.create(
            user=self.user,
            shipment=self.shipment,
            related_transaction=self,
            type='refund',
            amount=refund_amount,
            currency=self.currency,
            payment_method=self.payment_method,
            payment_gateway=self.payment_gateway,
            description=f"Remboursement de {self.transaction_id}",
            metadata={'original_transaction': self.transaction_id}
        )
        
        self.status = 'refunded'
        self.save()
        
        return refund_transaction
    
    @property
    def is_cash_payment(self):
        """Vérifie si c'est un paiement en espèces."""
        return self.payment_method == 'cash'
    
    @property
    def is_card_payment(self):
        """Vérifie si c'est un paiement par carte."""
        return self.payment_method in ['card', 'cib', 'eddahabia']
    
    @property
    def is_algerian_card(self):
        """Vérifie si c'est une carte bancaire algérienne."""
        return self.card_type in ['cib', 'eddahabia']
    
    def confirm_cash_payment(self, confirmed_by_user, payment_date=None):
        """Confirme un paiement en espèces."""
        from django.utils import timezone
        
        if not self.is_cash_payment:
            raise ValueError("Cette transaction n'est pas un paiement en espèces")
        
        if self.status != 'pending':
            raise ValueError("Seule une transaction en attente peut être confirmée")
        
        self.cash_payment_confirmed_by = confirmed_by_user
        self.cash_payment_date = payment_date or timezone.now()
        self.cash_payment_reference = f"CASH-{self.transaction_id}"
        self.complete()


class Commission(models.Model):
    """Modèle pour les commissions de la plateforme."""
    
    shipment = models.OneToOneField('shipments.Shipment', on_delete=models.CASCADE, related_name='commission')
    
    # Montants
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    traveler_earning = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Taux de commission (pourcentage)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['shipment']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Commission for Shipment {self.shipment.tracking_number} - {self.platform_commission}"
    
    def save(self, *args, **kwargs):
        # Calculer automatiquement les montants si pas fournis
        if not self.total_amount and self.shipment.price:
            self.total_amount = self.shipment.price
        
        if not self.commission_rate:
            # Taux de commission par défaut (10%)
            self.commission_rate = 10.00
        
        if self.total_amount and not self.platform_commission:
            self.platform_commission = (self.total_amount * self.commission_rate) / 100
        
        if self.total_amount and not self.traveler_earning:
            self.traveler_earning = self.total_amount - self.platform_commission
        
        super().save(*args, **kwargs)
    
    def distribute_commission(self):
        """Distribue la commission aux parties concernées."""
        if not self.shipment.matched_trip:
            raise ValueError("Le shipment doit être associé à un trajet")
        
        traveler = self.shipment.matched_trip.traveler
        
        # Créer les transactions
        # Commission pour la plateforme
        platform_transaction = Transaction.objects.create(
            user=self.shipment.sender,
            shipment=self.shipment,
            type='payment',
            amount=self.platform_commission,
            currency='DZD',
            payment_method='wallet',
            description=f"Commission plateforme pour {self.shipment.tracking_number}",
            status='completed'
        )
        platform_transaction.complete()
        
        # Gains pour le voyageur
        traveler_transaction = Transaction.objects.create(
            user=traveler,
            shipment=self.shipment,
            related_transaction=platform_transaction,
            type='earning',
            amount=self.traveler_earning,
            currency='DZD',
            payment_method='wallet',
            description=f"Gains pour transport de {self.shipment.tracking_number}",
            status='completed'
        )
        traveler_transaction.complete()
        
        return platform_transaction, traveler_transaction


class PaymentMethod(models.Model):
    """Modèle pour gérer les méthodes de paiement disponibles."""
    
    METHOD_TYPES = [
        ('card', 'Carte bancaire'),
        ('cib', 'CIB'),
        ('eddahabia', 'Eddahabia'),
        ('cash', 'Espèces'),
        ('bank_transfer', 'Virement bancaire'),
        ('chargily', 'Chargily Pay'),
    ]
    
    name = models.CharField(max_length=50, unique=True)
    method_type = models.CharField(max_length=20, choices=METHOD_TYPES)
    is_active = models.BooleanField(default=True)
    is_online = models.BooleanField(default=True, help_text="Paiement en ligne ou au bureau")
    
    # Configuration spécifique
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.01)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, default=100000.00)
    processing_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Frais de traitement en %")
    fixed_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Frais fixes")
    
    # Informations pour paiement au bureau
    office_locations = models.JSONField(default=list, blank=True, help_text="Liste des bureaux disponibles")
    office_hours = models.CharField(max_length=200, blank=True, help_text="Heures d'ouverture")
    office_instructions = models.TextField(blank=True, help_text="Instructions pour paiement au bureau")
    
    # Métadonnées
    description = models.TextField(blank=True)
    icon_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['method_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_method_type_display()})"
    
    def calculate_fees(self, amount):
        """Calcule les frais pour un montant donné."""
        percentage_fee = (amount * self.processing_fee) / 100
        total_fees = percentage_fee + self.fixed_fee
        return total_fees
    
    def is_available_for_amount(self, amount):
        """Vérifie si la méthode est disponible pour un montant donné."""
        return self.is_active and self.min_amount <= amount <= self.max_amount
