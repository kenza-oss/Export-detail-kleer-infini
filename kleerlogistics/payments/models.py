from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
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
        return self.balance - self.pending_balance
    
    def can_withdraw(self, amount):
        """Vérifie si le retrait est possible."""
        return self.available_balance >= amount
    
    def add_funds(self, amount, transaction_type='credit'):
        """Ajoute des fonds au portefeuille."""
        if amount <= 0:
            raise ValueError("Le montant doit être positif")
        
        self.balance += amount
        
        if transaction_type == 'earning':
            self.total_earned += amount
        elif transaction_type == 'refund':
            self.total_spent -= amount
        
        self.save()
    
    def deduct_funds(self, amount, transaction_type='debit'):
        """Déduit des fonds du portefeuille."""
        if amount <= 0:
            raise ValueError("Le montant doit être positif")
        
        if not self.can_withdraw(amount):
            raise ValueError("Solde insuffisant")
        
        self.balance -= amount
        
        if transaction_type == 'payment':
            self.total_spent += amount
        
        self.save()
    
    def hold_funds(self, amount):
        """Met en attente des fonds pour une transaction."""
        if amount <= 0:
            raise ValueError("Le montant doit être positif")
        
        if not self.can_withdraw(amount):
            raise ValueError("Solde insuffisant")
        
        self.pending_balance += amount
        self.save()
    
    def release_hold(self, amount):
        """Libère les fonds en attente."""
        if amount <= 0:
            raise ValueError("Le montant doit être positif")
        
        if self.pending_balance < amount:
            raise ValueError("Montant en attente insuffisant")
        
        self.pending_balance -= amount
        self.save()
    
    def confirm_hold(self, amount):
        """Confirme une mise en attente (déduit du solde principal)."""
        if amount <= 0:
            raise ValueError("Le montant doit être positif")
        
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
    
    PAYMENT_METHODS = [
        ('wallet', 'Portefeuille'),
        ('card', 'Carte bancaire'),
        ('bank_transfer', 'Virement bancaire'),
        ('cash', 'Espèces'),
        ('chargily', 'Chargily Pay'),
    ]
    
    PAYMENT_GATEWAYS = [
        ('chargily', 'Chargily Pay'),
        ('stripe', 'Stripe'),
        ('manual', 'Manuel'),
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
        ]
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.type} {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"TXN{uuid.uuid4().hex[:12].upper()}"
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
        if self.type in ['deposit', 'earning', 'refund']:
            self.user.wallet.add_funds(self.amount, self.type)
        elif self.type in ['withdrawal', 'payment']:
            self.user.wallet.deduct_funds(self.amount, self.type)
    
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
