from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django_countries.fields import CountryField

User = get_user_model()


class Trip(models.Model):
    """Modèle pour les trajets proposés par les voyageurs"""
    
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
        ('expired', 'Expiré'),
    ]
    
    PACKAGE_TYPE_CHOICES = [
        ('document', 'Document'),
        ('electronics', 'Électronique'),
        ('clothing', 'Vêtements'),
        ('food', 'Nourriture'),
        ('medicine', 'Médicament'),
        ('fragile', 'Fragile'),
        ('other', 'Autre'),
    ]
    
    # Informations de base
    traveler = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='trips',
        verbose_name="Voyageur"
    )
    
    # Origine
    origin_city = models.CharField(
        max_length=100, 
        verbose_name="Ville d'origine",
        help_text="Ville de départ du voyageur"
    )
    origin_country = models.CharField(
        max_length=100,
        default='Algeria',
        verbose_name="Pays d'origine",
        help_text="Pays de départ (par défaut Algérie)"
    )
    origin_address = models.TextField(
        blank=True,
        verbose_name="Adresse d'origine",
        help_text="Adresse complète de départ"
    )
    
    # Destination
    destination_city = models.CharField(
        max_length=100, 
        verbose_name="Ville de destination",
        help_text="Ville d'arrivée du voyageur"
    )
    destination_country = models.CharField(
        max_length=100,
        verbose_name="Pays de destination",
        help_text="Pays d'arrivée"
    )
    destination_address = models.TextField(
        blank=True,
        verbose_name="Adresse de destination",
        help_text="Adresse complète d'arrivée"
    )
    
    # Dates
    departure_date = models.DateTimeField(
        verbose_name="Date de départ",
        help_text="Date et heure de départ"
    )
    arrival_date = models.DateTimeField(
        verbose_name="Date d'arrivée",
        help_text="Date et heure d'arrivée"
    )
    flexible_dates = models.BooleanField(
        default=False,
        verbose_name="Dates flexibles",
        help_text="Le voyageur accepte des dates flexibles"
    )
    flexibility_days = models.PositiveIntegerField(
        default=0, 
        validators=[MaxValueValidator(30)],
        verbose_name="Jours de flexibilité",
        help_text="Nombre de jours de flexibilité (0-30)"
    )
    
    # Capacité
    max_weight = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)],
        verbose_name="Poids maximum",
        help_text="Poids maximum en kg que le voyageur peut transporter"
    )
    remaining_weight = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Poids restant",
        help_text="Poids restant disponible en kg"
    )
    max_packages = models.PositiveIntegerField(
        default=1,
        verbose_name="Nombre maximum de colis",
        help_text="Nombre maximum de colis que le voyageur peut transporter"
    )
    remaining_packages = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Colis restants",
        help_text="Nombre de colis restants que le voyageur peut transporter"
    )
    
    # Types de colis acceptés
    accepted_package_types = models.JSONField(
        default=list,
        verbose_name="Types de colis acceptés",
        help_text="Liste des types de colis acceptés par le voyageur"
    )
    
    # Prix et conditions
    min_price_per_kg = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)],
        verbose_name="Prix minimum par kg",
        help_text="Prix minimum demandé par kg de transport"
    )
    accepts_fragile = models.BooleanField(
        default=False,
        verbose_name="Accepte les colis fragiles",
        help_text="Le voyageur accepte de transporter des colis fragiles"
    )
    
    # Statut et vérification
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        verbose_name="Statut du trajet"
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Trajet vérifié",
        help_text="Le trajet a été vérifié par l'administration"
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
        help_text="Notes additionnelles du voyageur"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Trajet"
        verbose_name_plural = "Trajets"
        indexes = [
            models.Index(fields=['traveler', 'status']),
            models.Index(fields=['origin_city', 'destination_city']),
            models.Index(fields=['departure_date', 'arrival_date']),
            models.Index(fields=['remaining_weight', 'remaining_packages']),
            models.Index(fields=['status', 'is_verified']),
            models.Index(fields=['destination_country', 'departure_date']),
        ]
    
    def __str__(self):
        return f"Trajet {self.id} - {self.origin_city} → {self.destination_city}"
    
    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        
        # Vérifier que l'origine et la destination sont différentes
        if self.origin_city == self.destination_city and self.origin_country == self.destination_country:
            raise ValidationError("L'origine et la destination ne peuvent pas être identiques.")
        
        # Vérifier que la date d'arrivée est après la date de départ
        if self.departure_date and self.arrival_date:
            if self.arrival_date <= self.departure_date:
                raise ValidationError("La date d'arrivée doit être après la date de départ.")
        
        # Vérifier que la date de départ est dans le futur
        if self.departure_date and self.departure_date <= timezone.now():
            raise ValidationError("La date de départ doit être dans le futur.")
        
        # Vérifier que l'origine est en Algérie
        if self.origin_country != 'Algeria':
            raise ValidationError("L'origine doit être en Algérie.")
        
        # Vérifier que la destination n'est pas en Algérie
        if self.destination_country == 'Algeria':
            raise ValidationError("La destination ne peut pas être en Algérie.")
        
        # Vérifier que les types de colis acceptés sont valides
        valid_types = [choice[0] for choice in self.PACKAGE_TYPE_CHOICES]
        for package_type in self.accepted_package_types:
            if package_type not in valid_types:
                raise ValidationError(f"Type de colis invalide: {package_type}")
        
        # Vérifier la cohérence des dates flexibles
        if self.flexible_dates and self.flexibility_days == 0:
            raise ValidationError("Si les dates sont flexibles, les jours de flexibilité doivent être supérieurs à 0.")
        
        if not self.flexible_dates and self.flexibility_days > 0:
            raise ValidationError("Si les dates ne sont pas flexibles, les jours de flexibilité doivent être 0.")
    
    def save(self, *args, **kwargs):
        # Initialiser remaining_weight et remaining_packages si c'est une nouvelle instance
        if not self.pk:
            if self.remaining_weight is None:
                self.remaining_weight = self.max_weight
            if self.remaining_packages is None:
                self.remaining_packages = self.max_packages
        
        # Validation avant sauvegarde
        self.full_clean()
        
        # Mettre à jour le statut si le trajet est expiré
        if self.departure_date and self.departure_date < timezone.now() and self.status == 'active':
            self.status = 'expired'
        
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Vérifie si le trajet est actif et peut accepter des colis."""
        return (
            self.status == 'active' and 
            self.remaining_weight > 0 and 
            self.remaining_packages > 0 and
            self.departure_date > timezone.now() and
            self.is_verified
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
    
    @property
    def days_until_departure(self):
        """Calcule le nombre de jours jusqu'au départ."""
        if self.departure_date:
            delta = self.departure_date.date() - timezone.now().date()
            return delta.days
        return None
    
    @property
    def estimated_earnings(self):
        """Calcule les gains estimés du trajet."""
        return self.total_weight_carried * self.min_price_per_kg
    
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
    
    def remove_shipment(self, shipment):
        """Retire un colis du trajet."""
        self.remaining_weight += shipment.weight
        self.remaining_packages += 1
        
        # S'assurer que les valeurs ne dépassent pas le maximum
        if self.remaining_weight > self.max_weight:
            self.remaining_weight = self.max_weight
        if self.remaining_packages > self.max_packages:
            self.remaining_packages = self.max_packages
        
        # Remettre le statut à actif si le trajet n'est plus plein
        if self.status == 'in_progress' and self.remaining_packages > 0 and self.remaining_weight > 0:
            self.status = 'active'
        
        self.save()
    
    def update_status(self, new_status):
        """Met à jour le statut du trajet avec validation."""
        valid_transitions = {
            'draft': ['active', 'cancelled'],
            'active': ['in_progress', 'cancelled', 'expired'],
            'in_progress': ['completed', 'cancelled'],
            'completed': [],
            'cancelled': [],
            'expired': []
        }
        
        if new_status not in valid_transitions.get(self.status, []):
            raise ValueError(f"Transition de statut invalide: {self.status} → {new_status}")
        
        self.status = new_status
        self.save()
    
    def get_route_display(self):
        """Retourne l'affichage de la route."""
        return f"{self.origin_city} → {self.destination_city}"


class TripDocument(models.Model):
    """Modèle pour les documents associés aux trajets"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('flight_ticket', 'Billet d\'avion'),
        ('passport_copy', 'Copie du passeport'),
        ('visa', 'Visa'),
        ('boarding_pass', 'Carte d\'embarquement'),
        ('travel_insurance', 'Assurance voyage'),
        ('other', 'Autre'),
    ]
    
    trip = models.ForeignKey(
        Trip, 
        on_delete=models.CASCADE, 
        related_name='documents',
        verbose_name="Trajet"
    )
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        default='other',
        verbose_name="Type de document"
    )
    file = models.FileField(
        upload_to='trip_documents/',
        verbose_name="Fichier",
        blank=True,
        null=True
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Document vérifié"
    )
    verification_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de vérification"
    )
    verification_notes = models.TextField(
        blank=True,
        verbose_name="Notes de vérification"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'upload"
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Document de trajet"
        verbose_name_plural = "Documents de trajet"
        unique_together = ['trip', 'document_type']
    
    def __str__(self):
        return f"Document {self.get_document_type_display()} pour Trajet {self.trip.id}"
    
    @property
    def is_complete(self):
        """Vérifie si le document est complet et vérifié."""
        return bool(self.file and self.is_verified)
    
    def clean(self):
        """Validation personnalisée du document."""
        super().clean()
        
        # Vérifier la taille du fichier (max 10MB)
        if self.file and self.file.size > 10 * 1024 * 1024:
            raise ValidationError("Le fichier ne doit pas dépasser 10MB.")
        
        # Vérifier le type de fichier
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
        if self.file and hasattr(self.file, 'content_type'):
            if self.file.content_type not in allowed_types:
                raise ValidationError("Type de fichier non autorisé. Utilisez JPEG, PNG, GIF ou PDF.")
    
    def save(self, *args, **kwargs):
        # Validation avant sauvegarde
        self.full_clean()
        super().save(*args, **kwargs)
