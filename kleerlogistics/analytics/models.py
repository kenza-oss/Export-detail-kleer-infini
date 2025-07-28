"""
Models for analytics app - Dashboard analytics and statistics
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class AnalyticsEvent(models.Model):
    """Modèle pour les événements d'analytics."""
    
    EVENT_TYPES = [
        ('page_view', 'Vue de page'),
        ('api_call', 'Appel API'),
        ('user_action', 'Action utilisateur'),
        ('error', 'Erreur'),
        ('performance', 'Performance'),
    ]
    
    # Informations de base
    event_id = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name="ID d'événement")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, verbose_name="Type d'événement")
    event_name = models.CharField(max_length=100, verbose_name="Nom de l'événement")
    
    # Relations
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Utilisateur")
    
    # Données
    event_data = models.JSONField(default=dict, verbose_name="Données de l'événement")
    session_id = models.CharField(max_length=100, blank=True, verbose_name="ID de session")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Adresse IP")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    
    # Métadonnées
    duration = models.FloatField(null=True, blank=True, verbose_name="Durée (secondes)")
    success = models.BooleanField(default=True, verbose_name="Succès")
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    
    class Meta:
        verbose_name = "Événement d'analytics"
        verbose_name_plural = "Événements d'analytics"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.event_name} - {self.user.email if self.user else 'Anonyme'}"

class DashboardMetric(models.Model):
    """Modèle pour les métriques du tableau de bord."""
    
    METRIC_TYPES = [
        ('count', 'Compteur'),
        ('sum', 'Somme'),
        ('average', 'Moyenne'),
        ('percentage', 'Pourcentage'),
        ('trend', 'Tendance'),
    ]
    
    # Informations de base
    metric_id = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name="ID de métrique")
    name = models.CharField(max_length=100, verbose_name="Nom de la métrique")
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES, verbose_name="Type de métrique")
    
    # Valeurs
    current_value = models.FloatField(verbose_name="Valeur actuelle")
    previous_value = models.FloatField(null=True, blank=True, verbose_name="Valeur précédente")
    target_value = models.FloatField(null=True, blank=True, verbose_name="Valeur cible")
    
    # Métadonnées
    unit = models.CharField(max_length=20, blank=True, verbose_name="Unité")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    last_calculated = models.DateTimeField(null=True, blank=True, verbose_name="Dernier calcul")
    
    class Meta:
        verbose_name = "Métrique du tableau de bord"
        verbose_name_plural = "Métriques du tableau de bord"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_metric_type_display()})"
    
    def calculate_change_percentage(self):
        """Calculer le pourcentage de changement."""
        if self.previous_value and self.previous_value != 0:
            return ((self.current_value - self.previous_value) / self.previous_value) * 100
        return 0

class ChartData(models.Model):
    """Modèle pour les données de graphiques."""
    
    CHART_TYPES = [
        ('line', 'Ligne'),
        ('bar', 'Barre'),
        ('pie', 'Camembert'),
        ('area', 'Zone'),
    ]
    
    # Informations de base
    chart_id = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name="ID du graphique")
    name = models.CharField(max_length=100, verbose_name="Nom du graphique")
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES, verbose_name="Type de graphique")
    
    # Données
    data = models.JSONField(default=dict, verbose_name="Données du graphique")
    config = models.JSONField(default=dict, verbose_name="Configuration")
    
    # Métadonnées
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Données de graphique"
        verbose_name_plural = "Données de graphiques"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_chart_type_display()})"
