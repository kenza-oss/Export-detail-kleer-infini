"""
Admin interface for verification app - Document verification and validation
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    DocumentVerification, DocumentValidationRule, 
    VerificationWorkflow, VerificationLog, DocumentTemplate
)
from django.utils import timezone


@admin.register(DocumentVerification)
class DocumentVerificationAdmin(admin.ModelAdmin):
    """Interface d'administration pour les vérifications de documents."""
    
    list_display = [
        'id', 'user', 'document_type', 'verification_method', 'status', 
        'validation_score', 'fraud_detection_score', 'created_at', 'verified_at'
    ]
    
    list_filter = [
        'status', 'verification_method', 'document__document_type', 
        'created_at', 'verified_at'
    ]
    
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'document__document_type', 'verification_notes'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'verification_duration',
        'validation_score', 'fraud_detection_score'
    ]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('id', 'user', 'document', 'verification_method', 'status')
        }),
        ('Résultats de vérification', {
            'fields': ('validation_score', 'fraud_detection_score', 'ocr_data')
        }),
        ('Vérification manuelle', {
            'fields': ('verified_by', 'verified_at', 'rejection_reason', 'verification_notes')
        }),
        ('Métadonnées', {
            'fields': ('verification_duration', 'created_at', 'updated_at')
        })
    )
    
    actions = ['approve_verifications', 'reject_verifications', 'mark_for_manual_review']
    
    def document_type(self, obj):
        """Afficher le type de document."""
        return obj.document.document_type if obj.document else '-'
    document_type.short_description = 'Type de document'
    
    def approve_verifications(self, request, queryset):
        """Approuver les vérifications sélectionnées."""
        count = 0
        for verification in queryset:
            if verification.status == 'pending':
                verification.status = 'approved'
                verification.verified_by = request.user
                verification.verified_at = timezone.now()
                verification.save()
                
                # Mettre à jour le document
                verification.document.status = 'approved'
                verification.document.verified_at = verification.verified_at
                verification.document.verified_by = verification.verified_by
                verification.document.save()
                
                count += 1
        
        self.message_user(request, f'{count} vérifications ont été approuvées.')
    approve_verifications.short_description = 'Approuver les vérifications sélectionnées'
    
    def reject_verifications(self, request, queryset):
        """Rejeter les vérifications sélectionnées."""
        count = 0
        for verification in queryset:
            if verification.status == 'pending':
                verification.status = 'rejected'
                verification.verified_by = request.user
                verification.verified_at = timezone.now()
                verification.rejection_reason = 'Rejeté par l\'administrateur'
                verification.save()
                
                # Mettre à jour le document
                verification.document.status = 'rejected'
                verification.document.verified_at = verification.verified_at
                verification.document.verified_by = verification.verified_by
                verification.document.save()
                
                count += 1
        
        self.message_user(request, f'{count} vérifications ont été rejetées.')
    reject_verifications.short_description = 'Rejeter les vérifications sélectionnées'
    
    def mark_for_manual_review(self, request, queryset):
        """Marquer les vérifications pour vérification manuelle."""
        count = 0
        for verification in queryset:
            if verification.status == 'pending':
                verification.status = 'requires_manual_review'
                verification.save()
                count += 1
        
        self.message_user(request, f'{count} vérifications ont été marquées pour vérification manuelle.')
    mark_for_manual_review.short_description = 'Marquer pour vérification manuelle'


@admin.register(DocumentValidationRule)
class DocumentValidationRuleAdmin(admin.ModelAdmin):
    """Interface d'administration pour les règles de validation."""
    
    list_display = [
        'name', 'document_type', 'validation_type', 'is_active', 
        'priority', 'threshold_score'
    ]
    
    list_filter = [
        'document_type', 'validation_type', 'is_active', 'priority'
    ]
    
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'document_type', 'validation_type', 'is_active', 'priority')
        }),
        ('Configuration', {
            'fields': ('validation_config', 'threshold_score')
        }),
        ('Description', {
            'fields': ('description', 'notes')
        })
    )
    
    actions = ['activate_rules', 'deactivate_rules']
    
    def activate_rules(self, request, queryset):
        """Activer les règles sélectionnées."""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} règles ont été activées.')
    activate_rules.short_description = 'Activer les règles sélectionnées'
    
    def deactivate_rules(self, request, queryset):
        """Désactiver les règles sélectionnées."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} règles ont été désactivées.')
    deactivate_rules.short_description = 'Désactiver les règles sélectionnées'


@admin.register(VerificationWorkflow)
class VerificationWorkflowAdmin(admin.ModelAdmin):
    """Interface d'administration pour les workflows de vérification."""
    
    list_display = [
        'name', 'workflow_type', 'is_active', 'auto_approval_threshold',
        'requires_manual_review', 'max_processing_time'
    ]
    
    list_filter = ['workflow_type', 'is_active', 'requires_manual_review']
    
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'workflow_type', 'is_active', 'description')
        }),
        ('Configuration du workflow', {
            'fields': ('steps', 'auto_approval_threshold', 'requires_manual_review')
        }),
        ('Limites', {
            'fields': ('max_processing_time',)
        })
    )
    
    actions = ['activate_workflows', 'deactivate_workflows']
    
    def activate_workflows(self, request, queryset):
        """Activer les workflows sélectionnés."""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} workflows ont été activés.')
    activate_workflows.short_description = 'Activer les workflows sélectionnés'
    
    def deactivate_workflows(self, request, queryset):
        """Désactiver les workflows sélectionnés."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} workflows ont été désactivés.')
    deactivate_workflows.short_description = 'Désactiver les workflows sélectionnés'


@admin.register(VerificationLog)
class VerificationLogAdmin(admin.ModelAdmin):
    """Interface d'administration pour les logs de vérification."""
    
    list_display = [
        'timestamp', 'verification', 'log_level', 'message', 'user'
    ]
    
    list_filter = ['log_level', 'timestamp']
    
    search_fields = ['message', 'verification__id', 'user__username']
    
    readonly_fields = ['timestamp', 'verification', 'log_level', 'message', 'user', 'details']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('verification', 'log_level', 'timestamp', 'user')
        }),
        ('Contenu', {
            'fields': ('message', 'details')
        })
    )
    
    def has_add_permission(self, request):
        """Les logs ne peuvent pas être créés manuellement."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Les logs ne peuvent pas être modifiés."""
        return False


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    """Interface d'administration pour les templates de documents."""
    
    list_display = [
        'name', 'document_type', 'country', 'is_active', 'sample_image_preview'
    ]
    
    list_filter = ['document_type', 'country', 'is_active']
    
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'document_type', 'country', 'is_active', 'description')
        }),
        ('Configuration', {
            'fields': ('sample_image', 'validation_zones', 'required_fields')
        })
    )
    
    def sample_image_preview(self, obj):
        """Aperçu de l'image d'exemple."""
        if obj.sample_image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.sample_image.url
            )
        return '-'
    sample_image_preview.short_description = 'Aperçu'
    
    actions = ['activate_templates', 'deactivate_templates']
    
    def activate_templates(self, request, queryset):
        """Activer les templates sélectionnés."""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} templates ont été activés.')
    activate_templates.short_description = 'Activer les templates sélectionnés'
    
    def deactivate_templates(self, request, queryset):
        """Désactiver les templates sélectionnés."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} templates ont été désactivés.')
    deactivate_templates.short_description = 'Désactiver les templates sélectionnés'
