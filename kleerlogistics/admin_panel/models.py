"""
Models for admin_panel app - Dashboard and Analytics for Administrators
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Sum, Count, Avg
import uuid

User = get_user_model()


class DashboardMetric(models.Model):
    """Modèle pour stocker les métriques du tableau de bord."""
    
    METRIC_TYPES = [
        ('shipments', 'Envois'),
        ('payments', 'Paiements'),
        ('commissions', 'Commissions'),
        ('users', 'Utilisateurs'),
        ('revenue', 'Revenus'),
        ('performance', 'Performance'),
    ]
    
    PERIOD_TYPES = [
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
        ('yearly', 'Annuel'),
    ]
    
    # Informations de base
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES, verbose_name="Type de métrique")
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPES, verbose_name="Type de période")
    period_start = models.DateTimeField(verbose_name="Début de période")
    period_end = models.DateTimeField(verbose_name="Fin de période")
    
    # Valeurs de la métrique
    value = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valeur")
    previous_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Valeur précédente")
    change_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Pourcentage de changement")
    
    # Métadonnées
    metadata = models.JSONField(default=dict, help_text="Données additionnelles de la métrique")
    is_active = models.BooleanField(default=True, verbose_name="Métrique active")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        ordering = ['-period_start', 'metric_type']
        verbose_name = "Métrique du tableau de bord"
        verbose_name_plural = "Métriques du tableau de bord"
        indexes = [
            models.Index(fields=['metric_type', 'period_type', 'period_start']),
            models.Index(fields=['is_active', 'created_at']),
        ]
        unique_together = ['metric_type', 'period_type', 'period_start']
    
    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.get_period_type_display()} ({self.period_start.strftime('%Y-%m-%d')})"
    
    @property
    def trend_direction(self):
        """Détermine la direction de la tendance."""
        if not self.change_percentage:
            return 'neutral'
        return 'up' if self.change_percentage > 0 else 'down'


class AdminReport(models.Model):
    """Modèle pour les rapports administratifs."""
    
    REPORT_TYPES = [
        ('shipments_summary', 'Résumé des envois'),
        ('payments_summary', 'Résumé des paiements'),
        ('commissions_summary', 'Résumé des commissions'),
        ('users_summary', 'Résumé des utilisateurs'),
        ('financial_summary', 'Résumé financier'),
        ('performance_summary', 'Résumé des performances'),
        ('custom', 'Rapport personnalisé'),
    ]
    
    REPORT_FORMATS = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ]
    
    # Informations de base
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="Nom du rapport")
    report_type = models.CharField(max_length=25, choices=REPORT_TYPES, verbose_name="Type de rapport")
    format = models.CharField(max_length=10, choices=REPORT_FORMATS, default='json', verbose_name="Format")
    
    # Configuration du rapport
    parameters = models.JSONField(default=dict, help_text="Paramètres du rapport")
    filters = models.JSONField(default=dict, help_text="Filtres appliqués")
    
    # Résultats du rapport
    result_data = models.JSONField(default=dict, help_text="Données du rapport")
    file_path = models.CharField(max_length=500, blank=True, verbose_name="Chemin du fichier généré")
    
    # Métadonnées
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Généré par")
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name="Généré le")
    is_scheduled = models.BooleanField(default=False, verbose_name="Rapport programmé")
    schedule_cron = models.CharField(max_length=100, blank=True, verbose_name="Expression CRON")
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = "Rapport administratif"
        verbose_name_plural = "Rapports administratifs"
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()}) - {self.generated_at.strftime('%Y-%m-%d')}"


class AdminNotification(models.Model):
    """Modèle pour les notifications administratives."""
    
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('error', 'Erreur'),
        ('success', 'Succès'),
        ('alert', 'Alerte'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Faible'),
        ('normal', 'Normal'),
        ('high', 'Élevée'),
        ('urgent', 'Urgente'),
    ]
    
    # Informations de base
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    notification_type = models.CharField(max_length=15, choices=NOTIFICATION_TYPES, default='info', verbose_name="Type")
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='normal', verbose_name="Priorité")
    
    # Destinataires
    recipients = models.ManyToManyField(User, related_name='admin_notifications', verbose_name="Destinataires")
    is_broadcast = models.BooleanField(default=False, verbose_name="Notification générale")
    
    # État de la notification
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    read_by = models.ManyToManyField(User, related_name='read_admin_notifications', blank=True, verbose_name="Lu par")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Lu le")
    
    # Actions
    action_url = models.URLField(blank=True, verbose_name="URL d'action")
    action_text = models.CharField(max_length=100, blank=True, verbose_name="Texte de l'action")
    
    # Métadonnées
    metadata = models.JSONField(default=dict, help_text="Données additionnelles")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Expire le")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        ordering = ['-created_at', '-priority']
        verbose_name = "Notification administrative"
        verbose_name_plural = "Notifications administratives"
    
    def __str__(self):
        return f"{self.title} ({self.get_priority_display()}) - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def is_expired(self):
        """Vérifie si la notification est expirée."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at


class SystemHealth(models.Model):
    """Modèle pour surveiller la santé du système."""
    
    HEALTH_STATUS = [
        ('healthy', 'En bonne santé'),
        ('warning', 'Avertissement'),
        ('critical', 'Critique'),
        ('offline', 'Hors ligne'),
    ]
    
    # Informations de base
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_name = models.CharField(max_length=100, verbose_name="Nom du service")
    status = models.CharField(max_length=15, choices=HEALTH_STATUS, default='healthy', verbose_name="Statut")
    
    # Métriques de performance
    response_time = models.DurationField(null=True, blank=True, verbose_name="Temps de réponse")
    uptime_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Pourcentage de disponibilité")
    error_count = models.PositiveIntegerField(default=0, verbose_name="Nombre d'erreurs")
    
    # Détails
    last_check = models.DateTimeField(auto_now=True, verbose_name="Dernière vérification")
    details = models.JSONField(default=dict, help_text="Détails du statut")
    
    class Meta:
        ordering = ['service_name']
        verbose_name = "Santé du système"
        verbose_name_plural = "Santé du système"
        unique_together = ['service_name']
    
    def __str__(self):
        return f"{self.service_name} - {self.get_status_display()}"


class AdminAuditLog(models.Model):
    """Modèle pour les logs d'audit administratifs."""
    
    ACTION_TYPES = [
        ('create', 'Création'),
        ('update', 'Modification'),
        ('delete', 'Suppression'),
        ('view', 'Consultation'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('permission_change', 'Changement de permission'),
    ]
    
    # Informations de base
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Utilisateur")
    action = models.CharField(max_length=20, choices=ACTION_TYPES, verbose_name="Action")
    
    # Détails de l'action
    model_name = models.CharField(max_length=100, blank=True, verbose_name="Nom du modèle")
    object_id = models.CharField(max_length=100, blank=True, verbose_name="ID de l'objet")
    changes = models.JSONField(default=dict, help_text="Changements effectués")
    
    # Contexte
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Adresse IP")
    user_agent = models.TextField(blank=True, null=True, verbose_name="User Agent")
    session_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID de session")
    
    # Métadonnées
    metadata = models.JSONField(default=dict, help_text="Métadonnées additionnelles")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Horodatage")
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Log d'audit administratif"
        verbose_name_plural = "Logs d'audit administratifs"
        indexes = [
            models.Index(fields=['user', 'action', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.get_action_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
