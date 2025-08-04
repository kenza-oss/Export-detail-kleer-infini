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
    payment_status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'En attente'),
        ('paid', 'Payé'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
    ])
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # OTP pour livraison
    otp_code = models.CharField(max_length=6, blank=True)
    otp_generated_at = models.DateTimeField(null=True, blank=True)
    delivery_otp = models.CharField(max_length=6, blank=True)
    
    # Dates de livraison
    delivery_date = models.DateTimeField(null=True, blank=True)
    
    # Coût d'expédition
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Propriétés calculées pour compatibilité
    @property
    def destination(self):
        """Retourne la destination pour compatibilité avec l'ancien code."""
        return f"{self.destination_city}, {self.destination_country}"
    
    @property
    def origin(self):
        """Retourne l'origine pour compatibilité avec l'ancien code."""
        return self.origin_city
    
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
    
    def generate_tracking_number(self):
        """Générer un numéro de suivi unique."""
        return f"KL{uuid.uuid4().hex[:8].upper()}"
    
    def save(self, *args, **kwargs):
        """Sauvegarder l'envoi avec génération automatique du numéro de suivi."""
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()
        
        # Validation du poids
        if self.weight <= 0:
            raise ValueError("Le poids doit être supérieur à 0.")
        if self.weight > 50:  # 50kg max
            raise ValueError("Le poids ne peut pas dépasser 50kg.")
        
        # Validation des dates
        if self.max_delivery_date <= self.preferred_pickup_date:
            raise ValueError("La date de livraison maximale doit être postérieure à la date de ramassage préférée.")
        
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


class Package(models.Model):
    """Modèle pour les détails spécifiques des colis."""
    
    PACKAGE_CATEGORIES = [
        ('small', 'Petit colis (< 1kg)'),
        ('medium', 'Colis moyen (1-5kg)'),
        ('large', 'Gros colis (5-20kg)'),
        ('oversized', 'Très gros colis (> 20kg)'),
    ]
    
    shipment = models.OneToOneField(Shipment, on_delete=models.CASCADE, related_name='package_details')
    category = models.CharField(max_length=20, choices=PACKAGE_CATEGORIES)
    length = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    width = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    height = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Informations de sécurité
    requires_special_handling = models.BooleanField(default=False)
    is_hazardous = models.BooleanField(default=False)
    temperature_sensitive = models.BooleanField(default=False)
    min_temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Instructions de manutention
    handling_instructions = models.TextField(blank=True)
    storage_requirements = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Détails du colis'
        verbose_name_plural = 'Détails des colis'
    
    def save(self, *args, **kwargs):
        # Calculer le volume automatiquement
        if self.length and self.width and self.height:
            self.volume = self.length * self.width * self.height
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Package for {self.shipment.tracking_number} - {self.category}"


class ShipmentDocument(models.Model):
    """Modèle pour les documents associés aux envois."""
    
    DOCUMENT_TYPES = [
        ('invoice', 'Facture'),
        ('receipt', 'Reçu'),
        ('contract', 'Contrat'),
        ('insurance', 'Assurance'),
        ('customs', 'Document douanier'),
        ('photo', 'Photo du colis'),
        ('other', 'Autre'),
    ]
    
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='shipment_documents/')
    description = models.TextField(blank=True)
    
    # Métadonnées
    file_size = models.PositiveIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    
    # Statut
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_shipment_documents')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Document d\'envoi'
        verbose_name_plural = 'Documents d\'envoi'
    
    def __str__(self):
        return f"{self.document_type} - {self.shipment.tracking_number}"


class ShipmentRating(models.Model):
    """Modèle pour les évaluations des envois."""
    
    shipment = models.OneToOneField(Shipment, on_delete=models.CASCADE, related_name='rating')
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipment_ratings_given')
    
    # Évaluations
    overall_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    delivery_speed = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    package_condition = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    communication = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Commentaires
    comment = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Évaluation d\'envoi'
        verbose_name_plural = 'Évaluations d\'envoi'
        unique_together = ['shipment', 'rater']
    
    def __str__(self):
        return f"Rating {self.overall_rating}/5 for {self.shipment.tracking_number}"
    
    @property
    def average_rating(self):
        """Calcule la note moyenne."""
        ratings = [self.delivery_speed, self.package_condition, self.communication]
        return sum(ratings) / len(ratings)


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
    
    EVENT_TYPE_CHOICES = [
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
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='created')
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
