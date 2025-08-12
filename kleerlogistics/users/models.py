from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    ROLE_CHOICES = [
        ('sender', 'Expéditeur'),
        ('traveler', 'Voyageur'),
        ('admin', 'Administrateur'),
        ('both', 'Expéditeur et Voyageur')
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='sender')
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$')],
        unique=True,
        null=True,
        blank=True
    )
    is_phone_verified = models.BooleanField(default=False)
    is_document_verified = models.BooleanField(default=False)
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.00,
        validators=[
            MinValueValidator(0.00, message="La note ne peut pas être négative"),
            MaxValueValidator(9.99, message="La note ne peut pas dépasser 9.99")
        ]
    )
    total_trips = models.PositiveIntegerField(default=0)
    total_shipments = models.PositiveIntegerField(default=0)
    preferred_language = models.CharField(max_length=5, default='fr')
    is_active_traveler = models.BooleanField(default=False, help_text="Voyageur actif avec trajets en cours")
    is_active_sender = models.BooleanField(default=False, help_text="Expéditeur actif avec envois en cours")
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Solde du portefeuille")
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, help_text="Taux de commission en %")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser
    
    @property
    def is_sender(self):
        return self.role in ['sender', 'both']
    
    @property
    def is_traveler(self):
        return self.role in ['traveler', 'both']
    
    def can_access_admin_panel(self):
        return self.is_admin
    
    def get_verification_status(self):
        """Retourne le statut de vérification complet de l'utilisateur"""
        return {
            'phone_verified': self.is_phone_verified,
            'document_verified': self.is_document_verified,
            'fully_verified': self.is_phone_verified and self.is_document_verified
        }

# Signal pour créer automatiquement le profil utilisateur
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Créer automatiquement le profil utilisateur lors de la création d'un utilisateur."""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Sauvegarder le profil utilisateur."""
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)

class OTPCode(models.Model):
    """Modèle pour gérer les codes OTP de manière sécurisée"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes', null=True, blank=True)
    phone_number = models.CharField(max_length=15)
    # Stocke le hash du code (hex sha256 => 64 chars)
    code = models.CharField(max_length=64)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        verbose_name = 'Code OTP'
        verbose_name_plural = 'Codes OTP'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number', 'is_used', 'expires_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"OTP for {self.phone_number} - ****"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.is_used and not self.is_expired()
    
    def mark_as_used(self):
        self.is_used = True
        self.save()
    
    @classmethod
    def cleanup_expired_otps(cls):
        """Nettoie tous les OTP expirés pour libérer l'espace"""
        expired_count = cls.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()[0]
        return expired_count
    
    @classmethod
    def get_active_otp_count(cls, phone_number):
        """Retourne le nombre d'OTP actifs pour un numéro de téléphone"""
        return cls.objects.filter(
            phone_number=phone_number,
            is_used=False,
            expires_at__gt=timezone.now()
        ).count()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    birth_date = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Algeria')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)

class UserDocument(models.Model):
    DOCUMENT_TYPES = [
        ('passport', 'Passeport'),
        ('national_id', 'Carte d\'identité nationale'),
        ('flight_ticket', 'Billet d\'avion'),
        ('address_proof', 'Justificatif de domicile')
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_file = models.FileField(upload_to='documents/')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='verified_documents')
    rejection_reason = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Document utilisateur'
        verbose_name_plural = 'Documents utilisateur'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_document_type_display()}"
    
    def approve(self, verified_by_user):
        """Approuve le document"""
        self.status = 'approved'
        self.verified_at = timezone.now()
        self.verified_by = verified_by_user
        self.save()
        
        # Mettre à jour le statut de vérification de l'utilisateur
        user_documents = self.user.documents.filter(status='approved')
        if user_documents.count() >= 2:  # Au moins 2 documents approuvés
            self.user.is_document_verified = True
            self.user.save()
    
    def reject(self, verified_by_user, reason):
        """Rejette le document"""
        self.status = 'rejected'
        self.verified_at = timezone.now()
        self.verified_by = verified_by_user
        self.rejection_reason = reason
        self.save()
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_rejected(self):
        return self.status == 'rejected'