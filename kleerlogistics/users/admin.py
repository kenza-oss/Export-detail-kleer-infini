"""
Interface d'administration Django pour le module users
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import User, UserProfile, UserDocument, OTPCode


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Interface d'administration pour les utilisateurs."""
    
    list_display = [
        'username', 'email', 'full_name', 'role', 'phone_number', 
        'verification_status', 'wallet_balance', 'rating', 'is_active', 
        'created_at', 'last_login'
    ]
    
    list_filter = [
        'role', 'is_active', 'is_phone_verified', 'is_document_verified',
        'is_active_traveler', 'is_active_sender', 'preferred_language',
        'created_at', 'last_login'
    ]
    
    search_fields = [
        'username', 'email', 'first_name', 'last_name', 'phone_number'
    ]
    
    ordering = ['-created_at']
    
    readonly_fields = [
        'created_at', 'updated_at', 'last_login', 'date_joined',
        'verification_status', 'wallet_balance', 'rating', 'total_trips', 
        'total_shipments'
    ]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('username', 'email', 'password')
        }),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'phone_number', 'role')
        }),
        ('Statut et vérification', {
            'fields': ('is_active', 'is_phone_verified', 'is_document_verified')
        }),
        ('Activité', {
            'fields': ('is_active_traveler', 'is_active_sender')
        }),
        ('Préférences', {
            'fields': ('preferred_language', 'commission_rate')
        }),
        ('Statistiques', {
            'fields': ('rating', 'total_trips', 'total_shipments', 'wallet_balance'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
    
    def full_name(self, obj):
        """Afficher le nom complet de l'utilisateur."""
        return f"{obj.first_name} {obj.last_name}".strip() or "Non renseigné"
    full_name.short_description = "Nom complet"
    
    def verification_status(self, obj):
        """Afficher le statut de vérification avec des icônes."""
        phone_status = "✅" if obj.is_phone_verified else "❌"
        doc_status = "✅" if obj.is_document_verified else "❌"
        return format_html(
            '<span style="font-size: 14px;">📱 {} | 📄 {}</span>',
            phone_status, doc_status
        )
    verification_status.short_description = "Vérification"
    
    def wallet_balance(self, obj):
        """Afficher le solde du portefeuille avec couleur."""
        if obj.wallet_balance > 0:
            color = "green"
        elif obj.wallet_balance < 0:
            color = "red"
        else:
            color = "gray"
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f} DZD</span>',
            color, obj.wallet_balance
        )
    wallet_balance.short_description = "Portefeuille"
    
    def rating(self, obj):
        """Afficher la note avec des étoiles."""
        if obj.rating > 0:
            stars = "⭐" * int(obj.rating) + "☆" * (5 - int(obj.rating))
            return format_html(
                '<span style="font-size: 12px;">{} ({:.1f})</span>',
                stars, obj.rating
            )
        return "Aucune note"
    rating.short_description = "Note"
    
    actions = ['activate_users', 'deactivate_users', 'verify_phone', 'verify_documents']
    
    def activate_users(self, request, queryset):
        """Activer les utilisateurs sélectionnés."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} utilisateur(s) activé(s) avec succès.")
    activate_users.short_description = "Activer les utilisateurs sélectionnés"
    
    def deactivate_users(self, request, queryset):
        """Désactiver les utilisateurs sélectionnés."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} utilisateur(s) désactivé(s) avec succès.")
    deactivate_users.short_description = "Désactiver les utilisateurs sélectionnés"
    
    def verify_phone(self, request, queryset):
        """Marquer les téléphones comme vérifiés."""
        updated = queryset.update(is_phone_verified=True)
        self.message_user(request, f"{updated} téléphone(s) marqué(s) comme vérifié(s).")
    verify_phone.short_description = "Marquer téléphones comme vérifiés"
    
    def verify_documents(self, request, queryset):
        """Marquer les documents comme vérifiés."""
        updated = queryset.update(is_document_verified=True)
        self.message_user(request, f"{updated} utilisateur(s) marqué(s) comme documents vérifiés.")
    verify_documents.short_description = "Marquer documents comme vérifiés"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Interface d'administration pour les profils utilisateur."""
    
    list_display = [
        'user', 'full_name', 'city', 'country', 'birth_date', 
        'has_avatar'
    ]
    
    list_filter = ['country', 'city']
    
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 
        'user__last_name', 'city', 'country'
    ]
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Informations personnelles', {
            'fields': ('birth_date', 'address', 'city', 'country')
        }),
        ('Avatar et bio', {
            'fields': ('avatar', 'bio')
        }),
    )
    
    def full_name(self, obj):
        """Afficher le nom complet."""
        return f"{obj.user.first_name} {obj.user.last_name}".strip()
    full_name.short_description = "Nom complet"
    
    def has_avatar(self, obj):
        """Indiquer si l'utilisateur a un avatar."""
        return "✅" if obj.avatar else "❌"
    has_avatar.short_description = "Avatar"


@admin.register(UserDocument)
class UserDocumentAdmin(admin.ModelAdmin):
    """Interface d'administration pour les documents utilisateur."""
    
    list_display = [
        'user', 'document_type', 'status', 'uploaded_at', 
        'verified_at', 'verified_by', 'file_preview'
    ]
    
    list_filter = [
        'document_type', 'status', 'uploaded_at', 'verified_at'
    ]
    
    search_fields = [
        'user__username', 'user__email', 'document_type', 'rejection_reason'
    ]
    
    readonly_fields = [
        'uploaded_at', 'verified_at', 'file_preview'
    ]
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Document', {
            'fields': ('document_type', 'document_file', 'file_preview')
        }),
        ('Statut', {
            'fields': ('status', 'verified_by', 'rejection_reason')
        }),
        ('Dates', {
            'fields': ('uploaded_at', 'verified_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_documents', 'reject_documents', 'mark_pending']
    
    def file_preview(self, obj):
        """Aperçu du fichier document."""
        if obj.document_file:
            if obj.document_file.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                return format_html(
                    '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                    obj.document_file.url
                )
            else:
                return format_html(
                    '<a href="{}" target="_blank">📄 Voir le document</a>',
                    obj.document_file.url
                )
        return "Aucun fichier"
    file_preview.short_description = "Aperçu"
    
    def approve_documents(self, request, queryset):
        """Approuver les documents sélectionnés."""
        for document in queryset:
            document.status = 'approved'
            document.verified_by = request.user
            document.verified_at = timezone.now()
            document.save()
        
        self.message_user(request, f"{queryset.count()} document(s) approuvé(s) avec succès.")
    approve_documents.short_description = "Approuver les documents sélectionnés"
    
    def reject_documents(self, request, queryset):
        """Rejeter les documents sélectionnés."""
        for document in queryset:
            document.status = 'rejected'
            document.verified_by = request.user
            document.verified_at = timezone.now()
            document.save()
        
        self.message_user(request, f"{queryset.count()} document(s) rejeté(s).")
    reject_documents.short_description = "Rejeter les documents sélectionnés"
    
    def mark_pending(self, request, queryset):
        """Marquer les documents comme en attente."""
        updated = queryset.update(status='pending', verified_by=None, verified_at=None)
        self.message_user(request, f"{updated} document(s) marqué(s) comme en attente.")
    mark_pending.short_description = "Marquer comme en attente"


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    """Interface d'administration pour les codes OTP."""
    
    list_display = [
        'phone_number', 'user', 'code', 'is_used', 'is_expired', 
        'created_at', 'expires_at'
    ]
    
    list_filter = [
        'is_used', 'created_at', 'expires_at'
    ]
    
    search_fields = [
        'phone_number', 'user__username', 'user__email', 'code'
    ]
    
    readonly_fields = [
        'created_at', 'expires_at', 'is_expired', 'is_valid'
    ]
    
    fieldsets = (
        ('Informations OTP', {
            'fields': ('phone_number', 'user', 'code')
        }),
        ('Statut', {
            'fields': ('is_used', 'is_expired', 'is_valid')
        }),
        ('Dates', {
            'fields': ('created_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    
    def is_expired(self, obj):
        """Indiquer si l'OTP est expiré."""
        return "✅" if obj.is_expired() else "❌"
    is_expired.short_description = "Expiré"
    
    def is_valid(self, obj):
        """Indiquer si l'OTP est valide."""
        return "✅" if obj.is_valid() else "❌"
    is_valid.short_description = "Valide"
    
    actions = ['mark_as_used', 'mark_as_unused', 'delete_expired']
    
    def mark_as_used(self, request, queryset):
        """Marquer les OTP comme utilisés."""
        updated = queryset.update(is_used=True)
        self.message_user(request, f"{updated} OTP(s) marqué(s) comme utilisé(s).")
    mark_as_used.short_description = "Marquer comme utilisés"
    
    def mark_as_unused(self, request, queryset):
        """Marquer les OTP comme non utilisés."""
        updated = queryset.update(is_used=False)
        self.message_user(request, f"{updated} OTP(s) marqué(s) comme non utilisé(s).")
    mark_as_unused.short_description = "Marquer comme non utilisés"
    
    def delete_expired(self, request, queryset):
        """Supprimer les OTP expirés."""
        expired_count = queryset.filter(expires_at__lt=timezone.now()).count()
        queryset.filter(expires_at__lt=timezone.now()).delete()
        self.message_user(request, f"{expired_count} OTP(s) expiré(s) supprimé(s).")
    delete_expired.short_description = "Supprimer les OTP expirés"


# Configuration personnalisée de l'admin
admin.site.site_header = "Kleer Logistics - Administration"
admin.site.site_title = "Kleer Logistics Admin"
admin.site.index_title = "Bienvenue dans l'administration de Kleer Logistics"

# Personnalisation de l'affichage des modèles
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
