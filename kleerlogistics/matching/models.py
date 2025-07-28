from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


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
    
    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)
    
    # Version de l'algorithme de matching
    algorithm_version = models.CharField(max_length=20, default='1.0')
    
    # Facteurs de matching (JSON)
    matching_factors = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-compatibility_score', '-created_at']
        indexes = [
            models.Index(fields=['shipment', 'status']),
            models.Index(fields=['trip', 'status']),
            models.Index(fields=['compatibility_score']),
            models.Index(fields=['expires_at']),
        ]
        unique_together = ['shipment', 'trip']
    
    def __str__(self):
        return f"Match {self.id}: Shipment {self.shipment.tracking_number} - Trip {self.trip.id} ({self.compatibility_score}%)"
    
    @property
    def is_expired(self):
        """Vérifie si le match a expiré."""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    @property
    def can_be_accepted(self):
        """Vérifie si le match peut être accepté."""
        return (
            self.status == 'pending' and 
            not self.is_expired and
            self.shipment.can_be_matched and
            self.trip.is_active
        )
    
    def accept(self):
        """Accepte le match."""
        if not self.can_be_accepted:
            raise ValueError("Ce match ne peut pas être accepté")
        
        from django.utils import timezone
        
        # Mettre à jour le statut
        self.status = 'accepted'
        self.responded_at = timezone.now()
        self.save()
        
        # Associer le shipment au trip
        self.shipment.matched_trip = self.trip
        self.shipment.status = 'matched'
        self.shipment.price = self.proposed_price
        self.shipment.save()
        
        # Ajouter le shipment au trip
        self.trip.add_shipment(self.shipment)
        
        # Rejeter les autres matches pour ce shipment
        other_matches = Match.objects.filter(
            shipment=self.shipment,
            status='pending'
        ).exclude(id=self.id)
        other_matches.update(status='cancelled')
    
    def reject(self):
        """Rejette le match."""
        if self.status != 'pending':
            raise ValueError("Seuls les matches en attente peuvent être rejetés")
        
        from django.utils import timezone
        
        self.status = 'rejected'
        self.responded_at = timezone.now()
        self.save()
    
    def calculate_compatibility_score(self):
        """Calcule le score de compatibilité entre le shipment et le trip."""
        score = 0
        factors = {}
        
        # Facteur géographique (40 points)
        origin_match = (
            self.shipment.origin_city.lower() == self.trip.origin_city.lower() and
            self.shipment.destination_city.lower() == self.trip.destination_city.lower()
        )
        if origin_match:
            score += 40
            factors['geographic'] = 40
        else:
            factors['geographic'] = 0
        
        # Facteur de poids (20 points)
        weight_ratio = self.shipment.weight / self.trip.remaining_weight
        if weight_ratio <= 1:
            weight_score = 20 * (1 - weight_ratio)
            score += weight_score
            factors['weight'] = weight_score
        else:
            factors['weight'] = 0
        
        # Facteur de type de colis (15 points)
        if self.shipment.package_type in self.trip.accepted_package_types:
            score += 15
            factors['package_type'] = 15
        else:
            factors['package_type'] = 0
        
        # Facteur de fragilité (10 points)
        if not self.shipment.is_fragile or self.trip.accepts_fragile:
            score += 10
            factors['fragility'] = 10
        else:
            factors['fragility'] = 0
        
        # Facteur de dates (15 points)
        date_score = 0
        if (self.shipment.preferred_pickup_date <= self.trip.departure_date and
            self.shipment.max_delivery_date >= self.trip.arrival_date):
            date_score = 15
        elif self.trip.flexible_dates:
            # Calculer la flexibilité
            from datetime import timedelta
            departure_diff = abs((self.shipment.preferred_pickup_date - self.trip.departure_date).days)
            arrival_diff = abs((self.shipment.max_delivery_date - self.trip.arrival_date).days)
            
            if departure_diff <= self.trip.flexibility_days and arrival_diff <= self.trip.flexibility_days:
                date_score = 10
            elif departure_diff <= self.trip.flexibility_days * 2 and arrival_diff <= self.trip.flexibility_days * 2:
                date_score = 5
        
        score += date_score
        factors['dates'] = date_score
        
        self.compatibility_score = score
        self.matching_factors = factors
        return score


class MatchingPreferences(models.Model):
    """Modèle pour les préférences de matching des utilisateurs."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='matching_preferences')
    
    # Seuil d'acceptation automatique (0-100)
    auto_accept_threshold = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=80.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Notifications
    notification_enabled = models.BooleanField(default=True)
    
    # Note minimale requise
    min_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=3.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    
    # Villes préférées
    preferred_cities = models.JSONField(default=list)
    
    # Utilisateurs blacklistés
    blacklisted_users = models.JSONField(default=list)
    
    # Temps de réponse en heures
    response_time_hours = models.PositiveIntegerField(default=24, validators=[MaxValueValidator(168)])
    
    class Meta:
        verbose_name_plural = "Matching preferences"
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
    
    def is_user_blacklisted(self, user_id):
        """Vérifie si un utilisateur est blacklisté."""
        return user_id in self.blacklisted_users
    
    def add_blacklisted_user(self, user_id):
        """Ajoute un utilisateur à la blacklist."""
        if user_id not in self.blacklisted_users:
            self.blacklisted_users.append(user_id)
            self.save()
    
    def remove_blacklisted_user(self, user_id):
        """Retire un utilisateur de la blacklist."""
        if user_id in self.blacklisted_users:
            self.blacklisted_users.remove(user_id)
            self.save()
    
    def add_preferred_city(self, city):
        """Ajoute une ville préférée."""
        if city not in self.preferred_cities:
            self.preferred_cities.append(city)
            self.save()
    
    def remove_preferred_city(self, city):
        """Retire une ville préférée."""
        if city in self.preferred_cities:
            self.preferred_cities.remove(city)
            self.save()
