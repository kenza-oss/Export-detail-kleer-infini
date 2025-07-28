"""
Models for notifications app - Email and SMS notifications
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class Notification(models.Model):
    """Modèle pour les notifications."""
    
    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push'),
        ('in_app', 'Dans l\'application'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('sent', 'Envoyé'),
        ('delivered', 'Livré'),
        ('failed', 'Échoué'),
        ('read', 'Lu'),
    ]
    
    # Informations de base
    notification_id = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name="ID de notification")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name="Type de notification")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    
    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    
    # Contenu
    subject = models.CharField(max_length=200, verbose_name="Sujet")
    message = models.TextField(verbose_name="Message")
    template_data = models.JSONField(default=dict, verbose_name="Données du template")
    
    # Métadonnées
    priority = models.IntegerField(default=1, verbose_name="Priorité")
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Envoyé le")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Lu le")
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject} - {self.user.email}"

class EmailTemplate(models.Model):
    """Modèle pour les templates d'email."""
    
    name = models.CharField(max_length=100, verbose_name="Nom du template")
    subject = models.CharField(max_length=200, verbose_name="Sujet")
    html_content = models.TextField(verbose_name="Contenu HTML")
    text_content = models.TextField(verbose_name="Contenu texte")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Template d'email"
        verbose_name_plural = "Templates d'email"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class SMSTemplate(models.Model):
    """Modèle pour les templates SMS."""
    
    name = models.CharField(max_length=100, verbose_name="Nom du template")
    message = models.TextField(max_length=160, verbose_name="Message")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Template SMS"
        verbose_name_plural = "Templates SMS"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class ShipmentNotification(models.Model):
    """Modèle pour les notifications liées aux envois."""
    
    NOTIFICATION_EVENTS = [
        ('created', 'Envoi créé'),
        ('status_changed', 'Statut modifié'),
        ('delivered', 'Livré'),
        ('problem', 'Problème détecté'),
    ]
    
    notification = models.OneToOneField(Notification, on_delete=models.CASCADE, verbose_name="Notification")
    shipment_id = models.IntegerField(verbose_name="ID de l'envoi")
    event_type = models.CharField(max_length=20, choices=NOTIFICATION_EVENTS, verbose_name="Type d'événement")
    tracking_number = models.CharField(max_length=50, blank=True, verbose_name="Numéro de suivi")
    
    class Meta:
        verbose_name = "Notification d'envoi"
        verbose_name_plural = "Notifications d'envoi"
    
    def __str__(self):
        return f"Notification {self.event_type} - Envoi {self.shipment_id}"
