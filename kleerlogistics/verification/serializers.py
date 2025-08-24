"""
Serializers for verification app - Document verification and validation
"""

from rest_framework import serializers
from .models import (
    DocumentVerification, DocumentValidationRule, 
    VerificationWorkflow, VerificationLog, DocumentTemplate
)


class DocumentVerificationSerializer(serializers.ModelSerializer):
    """Serializer pour la vérification des documents."""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    document_type = serializers.CharField(source='document.document_type', read_only=True)
    document_file = serializers.CharField(source='document.document_file', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    verification_method_display = serializers.CharField(source='get_verification_method_display', read_only=True)
    
    class Meta:
        model = DocumentVerification
        fields = [
            'id', 'user', 'user_username', 'document', 'document_type', 'document_file',
            'status', 'status_display', 'verification_method', 'verification_method_display',
            'verified_at', 'verified_by', 'rejection_reason', 'ocr_data', 'validation_score',
            'fraud_detection_score', 'verification_notes', 'verification_duration',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_username', 'document_type', 'document_file', 'status_display',
            'verification_method_display', 'verified_at', 'verified_by', 'created_at', 'updated_at'
        ]


class DocumentVerificationCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une vérification de document."""
    
    class Meta:
        model = DocumentVerification
        fields = ['document', 'verification_method', 'verification_notes']


class DocumentVerificationUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour une vérification de document."""
    
    class Meta:
        model = DocumentVerification
        fields = ['status', 'rejection_reason', 'verification_notes']


class DocumentValidationRuleSerializer(serializers.ModelSerializer):
    """Serializer pour les règles de validation des documents."""
    
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    validation_type_display = serializers.CharField(source='get_validation_type_display', read_only=True)
    
    class Meta:
        model = DocumentValidationRule
        fields = [
            'id', 'name', 'document_type', 'document_type_display', 'validation_type',
            'validation_type_display', 'is_active', 'priority', 'validation_config',
            'threshold_score', 'description', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VerificationWorkflowSerializer(serializers.ModelSerializer):
    """Serializer pour les workflows de vérification."""
    
    workflow_type_display = serializers.CharField(source='get_workflow_type_display', read_only=True)
    
    class Meta:
        model = VerificationWorkflow
        fields = [
            'id', 'name', 'workflow_type', 'workflow_type_display', 'is_active',
            'steps', 'auto_approval_threshold', 'requires_manual_review',
            'max_processing_time', 'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VerificationLogSerializer(serializers.ModelSerializer):
    """Serializer pour les logs de vérification."""
    
    log_level_display = serializers.CharField(source='get_log_level_display', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = VerificationLog
        fields = [
            'id', 'verification', 'log_level', 'log_level_display', 'message',
            'details', 'timestamp', 'user', 'user_username'
        ]
        read_only_fields = ['id', 'timestamp']


class DocumentTemplateSerializer(serializers.ModelSerializer):
    """Serializer pour les templates de documents."""
    
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    country_display = serializers.CharField(source='get_country_display', read_only=True)
    
    class Meta:
        model = DocumentTemplate
        fields = [
            'id', 'name', 'document_type', 'document_type_display', 'country',
            'country_display', 'is_active', 'sample_image', 'validation_zones',
            'required_fields', 'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer pour l'upload de documents."""
    
    document_type = serializers.ChoiceField(choices=[
        ('passport', 'Passeport'),
        ('national_id', 'Carte d\'identité nationale'),
        ('flight_ticket', 'Billet d\'avion'),
        ('address_proof', 'Justificatif de domicile'),
        ('driver_license', 'Permis de conduire'),
        ('birth_certificate', 'Acte de naissance'),
        ('marriage_certificate', 'Acte de mariage'),
    ])
    
    document_file = serializers.FileField(
        max_length=255,
        allow_empty_file=False,
        use_url=False
    )
    
    country = serializers.ChoiceField(choices=[
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
    ], default='DZ')
    
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_document_file(self, value):
        """Valider le fichier uploadé."""
        # Vérifier la taille du fichier (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Le fichier ne peut pas dépasser 10MB")
        
        # Vérifier le type de fichier
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
        file_extension = value.name.lower()
        
        if not any(file_extension.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError(
                f"Seuls les formats suivants sont acceptés : {', '.join(allowed_extensions)}"
            )
        
        return value


class DocumentVerificationRequestSerializer(serializers.Serializer):
    """Serializer pour demander une vérification de document."""
    
    verification_method = serializers.ChoiceField(choices=[
        ('automatic', 'Vérification automatique'),
        ('manual', 'Vérification manuelle'),
        ('hybrid', 'Vérification hybride'),
    ], default='automatic')
    
    priority = serializers.ChoiceField(choices=[
        ('low', 'Faible'),
        ('normal', 'Normal'),
        ('high', 'Élevée'),
        ('urgent', 'Urgente'),
    ], default='normal')
    
    notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)


class DocumentVerificationResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse de vérification de document."""
    
    verification_id = serializers.UUIDField()
    status = serializers.CharField()
    validation_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    fraud_detection_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    estimated_completion_time = serializers.DateTimeField(required=False)
    requires_manual_review = serializers.BooleanField()
    verification_notes = serializers.CharField(required=False)


class BulkVerificationSerializer(serializers.Serializer):
    """Serializer pour la vérification en lot de documents."""
    
    document_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=50
    )
    
    verification_method = serializers.ChoiceField(choices=[
        ('automatic', 'Vérification automatique'),
        ('manual', 'Vérification manuelle'),
        ('hybrid', 'Vérification hybride'),
    ], default='automatic')
    
    priority = serializers.ChoiceField(choices=[
        ('low', 'Faible'),
        ('normal', 'Normal'),
        ('high', 'Élevée'),
        ('urgent', 'Urgente'),
    ], default='normal')


class VerificationStatisticsSerializer(serializers.Serializer):
    """Serializer pour les statistiques de vérification."""
    
    total_verifications = serializers.IntegerField()
    pending_verifications = serializers.IntegerField()
    approved_verifications = serializers.IntegerField()
    rejected_verifications = serializers.IntegerField()
    requires_manual_review = serializers.IntegerField()
    
    average_processing_time = serializers.DurationField(required=False)
    average_validation_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    fraud_detection_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    
    verifications_by_type = serializers.DictField()
    verifications_by_status = serializers.DictField()
    verifications_by_method = serializers.DictField()
