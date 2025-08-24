"""
Models for verification app - Document verification and validation
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class DocumentVerification(models.Model):
    """Modèle pour la vérification des documents utilisateur."""
    
    VERIFICATION_STATUS = [
        ('pending', 'En attente'),
        ('processing', 'En cours de traitement'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('requires_manual_review', 'Nécessite vérification manuelle'),
        ('expired', 'Expiré'),
    ]
    
    VERIFICATION_METHODS = [
        ('automatic', 'Vérification automatique'),
        ('manual', 'Vérification manuelle'),
        ('hybrid', 'Vérification hybride'),
    ]
    
    # Informations de base
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verifications')
    document = models.ForeignKey('users.UserDocument', on_delete=models.CASCADE, related_name='verifications')
    
    # Statut et méthode de vérification
    status = models.CharField(max_length=25, choices=VERIFICATION_STATUS, default='pending')
    verification_method = models.CharField(max_length=20, choices=VERIFICATION_METHODS, default='automatic')
    
    # Informations de vérification
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verifications_performed')
    rejection_reason = models.TextField(blank=True)
    
    # Résultats de vérification automatique
    ocr_data = models.JSONField(default=dict, help_text="Données extraites par OCR")
    validation_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Score de validation (0-100)")
    fraud_detection_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Score de détection de fraude (0-100)")
    
    # Métadonnées de vérification
    verification_notes = models.TextField(blank=True)
    verification_duration = models.DurationField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Vérification de document"
        verbose_name_plural = "Vérifications de documents"
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['document', 'status']),
            models.Index(fields=['verification_method']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Vérification {self.id} - {self.document.document_type} - {self.status}"
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_rejected(self):
        return self.status == 'rejected'
    
    @property
    def is_pending(self):
        return self.status in ['pending', 'processing']
    
    @property
    def requires_manual_review(self):
        return self.status == 'requires_manual_review'


class DocumentValidationRule(models.Model):
    """Modèle pour les règles de validation des documents."""
    
    DOCUMENT_TYPES = [
        ('passport', 'Passeport'),
        ('national_id', 'Carte d\'identité nationale'),
        ('flight_ticket', 'Billet d\'avion'),
        ('address_proof', 'Justificatif de domicile'),
        ('driver_license', 'Permis de conduire'),
        ('birth_certificate', 'Acte de naissance'),
        ('marriage_certificate', 'Acte de mariage'),
    ]
    
    VALIDATION_TYPES = [
        ('ocr_extraction', 'Extraction OCR'),
        ('format_validation', 'Validation de format'),
        ('expiry_check', 'Vérification d\'expiration'),
        ('fraud_detection', 'Détection de fraude'),
        ('data_consistency', 'Cohérence des données'),
        ('image_quality', 'Qualité d\'image'),
    ]
    
    # Informations de base
    name = models.CharField(max_length=100, verbose_name="Nom de la règle")
    document_type = models.CharField(max_length=25, choices=DOCUMENT_TYPES, verbose_name="Type de document")
    validation_type = models.CharField(max_length=25, choices=VALIDATION_TYPES, verbose_name="Type de validation")
    
    # Configuration de la règle
    is_active = models.BooleanField(default=True, verbose_name="Règle active")
    priority = models.PositiveIntegerField(default=1, verbose_name="Priorité d'exécution")
    
    # Paramètres de validation
    validation_config = models.JSONField(default=dict, help_text="Configuration de la règle de validation")
    threshold_score = models.DecimalField(max_digits=5, decimal_places=2, default=80.00, help_text="Score seuil pour validation")
    
    # Description et notes
    description = models.TextField(blank=True, verbose_name="Description de la règle")
    notes = models.TextField(blank=True, verbose_name="Notes additionnelles")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['priority', 'name']
        verbose_name = "Règle de validation"
        verbose_name_plural = "Règles de validation"
        unique_together = ['document_type', 'validation_type', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.get_document_type_display()} - {self.get_validation_type_display()}"


class VerificationWorkflow(models.Model):
    """Modèle pour les workflows de vérification."""
    
    WORKFLOW_TYPES = [
        ('standard', 'Workflow standard'),
        ('premium', 'Workflow premium'),
        ('express', 'Workflow express'),
        ('manual', 'Workflow manuel uniquement'),
    ]
    
    # Informations de base
    name = models.CharField(max_length=100, verbose_name="Nom du workflow")
    workflow_type = models.CharField(max_length=20, choices=WORKFLOW_TYPES, default='standard')
    is_active = models.BooleanField(default=True, verbose_name="Workflow actif")
    
    # Étapes du workflow
    steps = models.JSONField(default=list, help_text="Liste des étapes du workflow")
    auto_approval_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=90.00, help_text="Seuil d'approbation automatique")
    
    # Configuration
    requires_manual_review = models.BooleanField(default=False, verbose_name="Nécessite vérification manuelle")
    max_processing_time = models.DurationField(null=True, blank=True, help_text="Temps maximum de traitement")
    
    # Description
    description = models.TextField(blank=True, verbose_name="Description du workflow")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Workflow de vérification"
        verbose_name_plural = "Workflows de vérification"
    
    def __str__(self):
        return f"{self.name} ({self.get_workflow_type_display()})"


class VerificationLog(models.Model):
    """Modèle pour l'historique des vérifications."""
    
    LOG_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('error', 'Erreur'),
        ('success', 'Succès'),
    ]
    
    # Informations de base
    verification = models.ForeignKey(DocumentVerification, on_delete=models.CASCADE, related_name='logs')
    log_level = models.CharField(max_length=10, choices=LOG_LEVELS, default='info')
    
    # Contenu du log
    message = models.TextField(verbose_name="Message du log")
    details = models.JSONField(default=dict, help_text="Détails additionnels")
    
    # Métadonnées
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verification_logs')
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Log de vérification"
        verbose_name_plural = "Logs de vérification"
    
    def __str__(self):
        return f"{self.timestamp} - {self.get_log_level_display()} - {self.message[:50]}"


class DocumentTemplate(models.Model):
    """Modèle pour les templates de documents acceptés."""
    
    DOCUMENT_TYPES = [
        ('passport', 'Passeport'),
        ('national_id', 'Carte d\'identité nationale'),
        ('flight_ticket', 'Billet d\'avion'),
        ('address_proof', 'Justificatif de domicile'),
    ]
    
    COUNTRIES = [
        ('DZ', 'Algérie'),
        ('FR', 'France'),
        ('US', 'États-Unis'),
        ('GB', 'Royaume-Uni'),
        ('DE', 'Allemagne'),
        ('IT', 'Italie'),
        ('ES', 'Espagne'),
        ('CA', 'Canada'),
        ('AU', 'Australie'),
        ('OTHER', 'Autre'),
    ]
    
    # Informations de base
    name = models.CharField(max_length=100, verbose_name="Nom du template")
    document_type = models.CharField(max_length=25, choices=DOCUMENT_TYPES, verbose_name="Type de document")
    country = models.CharField(max_length=5, choices=COUNTRIES, verbose_name="Pays d'origine")
    
    # Configuration du template
    is_active = models.BooleanField(default=True, verbose_name="Template actif")
    sample_image = models.ImageField(upload_to='document_templates/', null=True, blank=True, verbose_name="Image d'exemple")
    
    # Zones de validation
    validation_zones = models.JSONField(default=dict, help_text="Zones de validation sur le document")
    required_fields = models.JSONField(default=list, help_text="Champs requis pour ce type de document")
    
    # Description
    description = models.TextField(blank=True, verbose_name="Description du template")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['document_type', 'country', 'name']
        verbose_name = "Template de document"
        verbose_name_plural = "Templates de documents"
        unique_together = ['document_type', 'country', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.get_document_type_display()} ({self.get_country_display()})"
