from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Trip(models.Model):
    """Modèle pour les trajets proposés par les voyageurs."""
    
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
        ('expired', 'Expiré'),
    ]
    
    # Informations de base
    traveler = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    
    # Origine
    origin_city = models.CharField(max_length=100)
    origin_country = models.CharField(max_length=100)
    
    # Destination
    destination_city = models.CharField(max_length=100)
    destination_country = models.CharField(max_length=100)
    
    # Dates
    departure_date = models.DateTimeField()
    arrival_date = models.DateTimeField()
    flexible_dates = models.BooleanField(default=False)
    flexibility_days = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(30)])
    
    # Capacité
    max_weight = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    remaining_weight = models.DecimalField(max_digits=8, decimal_places=2)
    max_packages = models.PositiveIntegerField(default=1)
    remaining_packages = models.PositiveIntegerField()
    
    # Types de colis acceptés
    accepted_package_types = models.JSONField(default=list)  # Liste des types acceptés
    
    # Prix et conditions
    min_price_per_kg = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    accepts_fragile = models.BooleanField(default=False)
    
    # Statut et vérification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_verified = models.BooleanField(default=False)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['traveler', 'status']),
            models.Index(fields=['origin_city', 'destination_city']),
            models.Index(fields=['departure_date', 'arrival_date']),
            models.Index(fields=['remaining_weight', 'remaining_packages']),
        ]
    
    def __str__(self):
        return f"Trip {self.id} - {self.origin_city} to {self.destination_city}"
    
    def save(self, *args, **kwargs):
        # Initialiser remaining_weight et remaining_packages si c'est une nouvelle instance
        if not self.pk:
            self.remaining_weight = self.max_weight
            self.remaining_packages = self.max_packages
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Vérifie si le trajet est actif et peut accepter des colis."""
        from django.utils import timezone
        return (
            self.status == 'active' and 
            self.remaining_weight > 0 and 
            self.remaining_packages > 0 and
            self.departure_date > timezone.now()
        )
    
    @property
    def total_weight_carried(self):
        """Calcule le poids total transporté."""
        return self.max_weight - self.remaining_weight
    
    @property
    def total_packages_carried(self):
        """Calcule le nombre total de colis transportés."""
        return self.max_packages - self.remaining_packages
    
    @property
    def utilization_rate(self):
        """Calcule le taux d'utilisation du trajet."""
        if self.max_weight > 0:
            return (self.total_weight_carried / self.max_weight) * 100
        return 0
    
    def can_accept_shipment(self, shipment):
        """Vérifie si le trajet peut accepter un colis spécifique."""
        if not self.is_active:
            return False
        
        # Vérifier le poids
        if shipment.weight > self.remaining_weight:
            return False
        
        # Vérifier le nombre de colis
        if self.remaining_packages <= 0:
            return False
        
        # Vérifier le type de colis
        if shipment.package_type not in self.accepted_package_types:
            return False
        
        # Vérifier si le colis est fragile
        if shipment.is_fragile and not self.accepts_fragile:
            return False
        
        # Vérifier les dates
        if shipment.preferred_pickup_date > self.departure_date:
            return False
        
        if shipment.max_delivery_date < self.arrival_date:
            return False
        
        return True
    
    def add_shipment(self, shipment):
        """Ajoute un colis au trajet."""
        if not self.can_accept_shipment(shipment):
            raise ValueError("Ce trajet ne peut pas accepter ce colis")
        
        self.remaining_weight -= shipment.weight
        self.remaining_packages -= 1
        self.save()
        
        # Mettre à jour le statut si le trajet est plein
        if self.remaining_packages == 0 or self.remaining_weight <= 0:
            self.status = 'in_progress'
            self.save()


class TripDocument(models.Model):
    """Modèle pour les documents associés aux trajets."""
    
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='documents')
    flight_ticket = models.FileField(upload_to='trip_documents/flight_tickets/', blank=True)
    passport_copy = models.FileField(upload_to='trip_documents/passports/', blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Documents for Trip {self.trip.id}"
    
    @property
    def is_complete(self):
        """Vérifie si tous les documents requis sont fournis."""
        return bool(self.flight_ticket and self.passport_copy)
