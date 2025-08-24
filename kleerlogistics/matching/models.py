"""
Models for matching app
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class Match(models.Model):
    """Modèle pour les associations entre envois et trajets."""
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('accepted', 'Accepté'),
        ('rejected', 'Rejeté'),
        ('expired', 'Expiré'),
        ('cancelled', 'Annulé'),
    ]
    
    # Relations
    shipment = models.ForeignKey('shipments.Shipment', on_delete=models.CASCADE, related_name='matches')
    trip = models.ForeignKey('trips.Trip', on_delete=models.CASCADE, related_name='matches')
    
    # Score de compatibilité (0-100)
    compatibility_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Prix proposé
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Calculs économiques
    traveler_earnings = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Gains du voyageur (70-80% du prix total)"
    )
    commission_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Commission de la plateforme (20-30% du prix total)"
    )
    packaging_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Frais d'emballage (500-1000 DA)"
    )
    service_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Frais de service"
    )
    
    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    
    # Version de l'algorithme de matching
    algorithm_version = models.CharField(max_length=20, default='1.0')
    
    # Facteurs de matching (JSON)
    matching_factors = models.JSONField(default=dict)
    
    # Intégration OTP de livraison
    delivery_otp = models.CharField(
        max_length=6, 
        null=True, 
        blank=True,
        help_text="Code OTP de livraison généré automatiquement"
    )
    otp_generated_at = models.DateTimeField(null=True, blank=True)
    otp_expires_at = models.DateTimeField(null=True, blank=True)
    delivery_confirmed = models.BooleanField(default=False)
    delivery_confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # Intégration chat
    chat_activated = models.BooleanField(default=False)
    chat_room_id = models.UUIDField(null=True, blank=True)
    chat_activated_at = models.DateTimeField(null=True, blank=True)
    
    # Auto-acceptance
    auto_accepted = models.BooleanField(default=False)
    auto_accept_threshold = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=90.00,
        help_text="Seuil de score pour auto-acceptance"
    )
    
    # Notifications
    notification_sent = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-compatibility_score', '-created_at']
        indexes = [
            models.Index(fields=['shipment', 'status']),
            models.Index(fields=['trip', 'status']),
            models.Index(fields=['compatibility_score']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['delivery_otp']),
            models.Index(fields=['chat_room_id']),
        ]
        unique_together = ['shipment', 'trip']
    
    def __str__(self):
        return f"Match {self.id}: Shipment {self.shipment.tracking_number} - Trip {self.trip.id} ({self.compatibility_score}%)"
    
    @property
    def is_expired(self):
        """Vérifie si le match a expiré."""
        return timezone.now() > self.expires_at
    
    @property
    def can_be_accepted(self):
        """Vérifie si le match peut être accepté."""
        return (
            self.status == 'pending' and 
            not self.is_expired
        )
    
    @property
    def can_auto_accept(self):
        """Vérifie si le match peut être auto-accepté."""
        return (
            self.can_be_accepted and
            self.compatibility_score >= self.auto_accept_threshold
        )
    
    @property
    def otp_is_valid(self):
        """Vérifie si l'OTP est encore valide."""
        if not self.delivery_otp or not self.otp_expires_at:
            return False
        return timezone.now() < self.otp_expires_at
    
    def calculate_economic_breakdown(self):
        """Calcule la répartition économique."""
        total_price = self.proposed_price
        
        # Commission plateforme (20-30%)
        commission_rate = Decimal('0.25')  # 25% par défaut
        self.commission_amount = total_price * commission_rate
        
        # Frais d'emballage (500-1000 DA selon le type)
        if self.shipment.package_type in ['fragile', 'electronics']:
            self.packaging_fee = Decimal('1000.00')
        else:
            self.packaging_fee = Decimal('500.00')
        
        # Frais de service (optionnels)
        if self.shipment.urgency in ['high', 'urgent']:
            self.service_fee = Decimal('200.00')
        else:
            self.service_fee = Decimal('0.00')
        
        # Gains du voyageur (reste après commission et frais)
        self.traveler_earnings = (
            total_price - 
            self.commission_amount - 
            self.packaging_fee - 
            self.service_fee
        )
        
        return {
            'total_price': total_price,
            'commission_amount': self.commission_amount,
            'packaging_fee': self.packaging_fee,
            'service_fee': self.service_fee,
            'traveler_earnings': self.traveler_earnings
        }
    
    def generate_delivery_otp(self):
        """Génère un code OTP de livraison à 6 chiffres."""
        import random
        self.delivery_otp = str(random.randint(100000, 999999))
        self.otp_generated_at = timezone.now()
        self.otp_expires_at = self.otp_generated_at + timezone.timedelta(hours=24)
        self.save()
        return self.delivery_otp
    
    def verify_delivery_otp(self, otp_code):
        """Vérifie le code OTP de livraison."""
        if not self.otp_is_valid:
            return False
        
        if self.delivery_otp == otp_code:
            self.delivery_confirmed = True
            self.delivery_confirmed_at = timezone.now()
            self.save()
            return True
        return False
    
    def activate_chat(self):
        """Active le chat pour ce match."""
        if not self.chat_activated and self.status == 'accepted':
            self.chat_activated = True
            self.chat_room_id = uuid.uuid4()
            self.chat_activated_at = timezone.now()
            self.save()
            return True
        return False
    
    def accept(self):
        """Accepte le match."""
        if not self.can_be_accepted:
            raise ValueError("Ce match ne peut pas être accepté")
        
        # Calculer la répartition économique
        self.calculate_economic_breakdown()
        
        # Mettre à jour le statut
        self.status = 'accepted'
        self.responded_at = timezone.now()
        self.accepted_at = timezone.now()
        self.save()
        
        # Associer le shipment au trip
        self.shipment.matched_trip = self.trip
        self.shipment.status = 'matched'
        self.shipment.price = self.proposed_price
        self.shipment.save()
        
        # Générer automatiquement l'OTP de livraison
        self.generate_delivery_otp()
        
        # Activer automatiquement le chat
        self.activate_chat()
        
        # Rejeter les autres matches pour ce shipment
        other_matches = Match.objects.filter(
            shipment=self.shipment,
            status='pending'
        ).exclude(id=self.id)
        other_matches.update(status='cancelled')
    
    def auto_accept(self):
        """Accepte automatiquement le match si le score est suffisant."""
        if self.can_auto_accept:
            self.auto_accepted = True
            self.accept()
            return True
        return False
    
    def reject(self, reason=None):
        """Rejette le match."""
        if not self.can_be_accepted:
            raise ValueError("Ce match ne peut pas être rejeté")
        
        self.status = 'rejected'
        self.responded_at = timezone.now()
        self.rejected_at = timezone.now()
        self.save()
    
    def expire(self):
        """Expire le match."""
        if self.status == 'pending':
            self.status = 'expired'
            self.save()
    
    def cancel(self):
        """Annule le match."""
        if self.status in ['pending', 'accepted']:
            self.status = 'cancelled'
            self.save()


class MatchingPreferences(models.Model):
    """Préférences de matching pour les utilisateurs."""
    
    user = models.OneToOneField('users.User', on_delete=models.CASCADE)
    
    # Auto-acceptance
    auto_accept_threshold = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=80.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Notifications
    notification_enabled = models.BooleanField(default=True)
    
    # Critères de réputation
    min_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=3.0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    
    # Critères géographiques
    preferred_cities = models.JSONField(default=list)
    blacklisted_users = models.JSONField(default=list)
    response_time_hours = models.PositiveIntegerField(
        default=24,
        validators=[MaxValueValidator(168)]
    )
    
    # Critères de prix (ajoutés dans migration 0003)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Critères de transport (ajoutés pour correspondre à la base de données)
    accepts_fragile = models.BooleanField(default=False)
    accepts_urgent = models.BooleanField(default=False)
    max_distance_km = models.PositiveIntegerField(default=100)
    max_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_package_types = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Préférence de matching"
        verbose_name_plural = "Préférences de matching"
    
    def __str__(self):
        return f"Préférences de {self.user.username}"


class MatchingRule(models.Model):
    """Règles configurables pour l'algorithme de matching."""
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Seuils de compatibilité
    min_compatibility_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=30.00
    )
    
    # Critères géographiques
    max_distance_km = models.PositiveIntegerField(default=100)
    max_date_flexibility_days = models.PositiveIntegerField(default=7)
    
    # Poids des facteurs de matching
    geographic_weight = models.DecimalField(max_digits=5, decimal_places=2, default=35.00)
    weight_weight = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)
    package_type_weight = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    fragility_weight = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    date_weight = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    reputation_weight = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    
    # Auto-acceptance
    enable_auto_acceptance = models.BooleanField(default=False)
    auto_accept_threshold = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=90.00
    )
    
    # Statut
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Règle de matching"
        verbose_name_plural = "Règles de matching"
    
    def __str__(self):
        return self.name
