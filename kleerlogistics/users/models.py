from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

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
        unique=True
    )
    is_phone_verified = models.BooleanField(default=False)
    is_document_verified = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_trips = models.PositiveIntegerField(default=0)
    total_shipments = models.PositiveIntegerField(default=0)
    preferred_language = models.CharField(max_length=5, default='fr')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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