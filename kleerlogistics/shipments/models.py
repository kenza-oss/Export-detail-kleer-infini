from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()


class Shipment(models.Model):
    """Modèle pour les envois de colis."""
    
    PACKAGE_TYPES = [
        ('document', 'Document'),
        ('electronics', 'Électronique'),
        ('clothing', 'Vêtements'),
        ('food', 'Nourriture'),
        ('medicine', 'Médicaments'),
        ('fragile', 'Fragile'),
        ('other', 'Autre'),
    ]
    
    URGENCY_CHOICES = [
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Élevée'),
        ('urgent', 'Urgente'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('pending', 'En attente'),
        ('matched', 'Associé'),
        ('in_transit', 'En transit'),
        ('delivered', 'Livré'),
        ('cancelled', 'Annulé'),
        ('lost', 'Perdu'),
    ]
    
    PAYMENT_METHODS = [
        ('wallet', 'Portefeuille'),
        ('card', 'Carte bancaire'),
        ('cash', 'Espèces'),
        ('bank_transfer', 'Virement bancaire'),
    ]
    
    # Informations de base
    tracking_number = models.CharField(max_length=50, unique=True, blank=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_shipments')
    
    # Détails du colis
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES)
    description = models.TextField()
    weight = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    dimensions = models.JSONField(default=dict)  # {length, width, height}
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_fragile = models.BooleanField(default=False)
    
    # Origine
    origin_city = models.CharField(max_length=100)
    origin_address = models.TextField()
    
    # Destination
    destination_city = models.CharField(max_length=100)
    destination_country = models.CharField(max_length=100)
    destination_address = models.TextField()
    recipient_name = models.CharField(max_length=200)
    recipient_phone = models.CharField(max_length=20)
    recipient_email = models.EmailField(blank=True)
    
    # Dates
    preferred_pickup_date = models.DateTimeField()
    max_delivery_date = models.DateTimeField()
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='medium')
    
    # Statut et matching
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    matched_trip = models.ForeignKey('trips.Trip', on_delete=models.SET_NULL, null=True, blank=True, related_name='matched_shipments')
    
    # Paiement
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, blank=True)
    
    # OTP pour livraison
    otp_code = models.CharField(max_length=6, blank=True)
    otp_generated_at = models.DateTimeField(null=True, blank=True)
    
    # Instructions spéciales
    special_instructions = models.TextField(blank=True)
    insurance_requested = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'status']),
            models.Index(fields=['origin_city', 'destination_city']),
            models.Index(fields=['preferred_pickup_date', 'max_delivery_date']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = f"KL{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Shipment {self.tracking_number} - {self.origin_city} to {self.destination_city}"
    
    @property
    def is_overdue(self):
        """Vérifie si le colis est en retard."""
        from django.utils import timezone
        return self.status == 'in_transit' and timezone.now() > self.max_delivery_date
    
    @property
    def can_be_matched(self):
        """Vérifie si le colis peut être associé à un trajet."""
        return self.status in ['draft', 'pending']


class ShipmentTracking(models.Model):
    """Modèle pour le suivi des envois."""
    
    STATUS_CHOICES = [
        ('created', 'Créé'),
        ('pending_pickup', 'En attente de ramassage'),
        ('picked_up', 'Ramassé'),
        ('in_transit', 'En transit'),
        ('out_for_delivery', 'En livraison'),
        ('delivered', 'Livré'),
        ('failed_delivery', 'Livraison échouée'),
        ('returned', 'Retourné'),
    ]
    
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='tracking_events')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    description = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tracking_events_created')
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['shipment', 'timestamp']),
            models.Index(fields=['status', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.shipment.tracking_number} - {self.status} at {self.timestamp}"
    
    def save(self, *args, **kwargs):
        # Mettre à jour le statut du shipment si nécessaire
        if self.status in ['delivered', 'failed_delivery', 'returned']:
            self.shipment.status = self.status
            self.shipment.save(update_fields=['status'])
        super().save(*args, **kwargs)
