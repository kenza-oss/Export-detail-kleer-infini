"""
Interface d'administration Django pour le module users
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from .models import User, UserProfile, UserDocument, OTPCode
from .services import OTPMaintenanceService, OTPAuditService


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
    """Administration des codes OTP avec monitoring de sécurité."""
    
    list_display = [
        'phone_number', 'user_info', 'status', 'created_at', 'expires_at', 'security_info'
    ]
    list_filter = [
        'is_used', 'created_at', 'expires_at', 'user__role'
    ]
    search_fields = ['phone_number', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'expires_at', 'security_hash_info']
    ordering = ['-created_at']
    
    actions = ['cleanup_expired_otps', 'mark_as_used', 'reset_rate_limits']
    
    def user_info(self, obj):
        """Affiche les informations de l'utilisateur."""
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return "Anonyme"
    user_info.short_description = "Utilisateur"
    
    def status(self, obj):
        """Affiche le statut de l'OTP avec couleur."""
        if obj.is_used:
            return format_html('<span style="color: red;">Utilisé</span>')
        elif obj.is_expired():
            return format_html('<span style="color: orange;">Expiré</span>')
        else:
            return format_html('<span style="color: green;">Actif</span>')
    status.short_description = "Statut"
    
    def security_info(self, obj):
        """Affiche les informations de sécurité."""
        info = []
        if obj.is_used:
            info.append("✅ Utilisé")
        if obj.is_expired():
            info.append("⏰ Expiré")
        if not obj.is_used and not obj.is_expired():
            info.append("🔒 Actif")
        
        return format_html('<br>'.join(info))
    security_info.short_description = "Sécurité"
    
    def security_hash_info(self, obj):
        """Affiche les informations sur le hash (sans révéler le code)."""
        if ':' in obj.code:
            hash_part, salt_part = obj.code.split(':', 1)
            return format_html(
                'Hash: <code>{}</code><br>Salt: <code>{}</code>',
                hash_part[:16] + '...',
                salt_part[:8] + '...'
            )
        return "Format de hash invalide"
    security_hash_info.short_description = "Informations de Hash"
    
    def cleanup_expired_otps(self, request, queryset):
        """Nettoie les OTP expirés."""
        expired_count = OTPMaintenanceService.cleanup_expired_otps()
        self.message_user(
            request,
            f"{expired_count} OTP expirés ont été supprimés avec succès."
        )
    cleanup_expired_otps.short_description = "Nettoyer les OTP expirés"
    
    def mark_as_used(self, request, queryset):
        """Marque les OTP sélectionnés comme utilisés."""
        updated = queryset.update(is_used=True)
        self.message_user(
            request,
            f"{updated} OTP ont été marqués comme utilisés."
        )
    mark_as_used.short_description = "Marquer comme utilisés"
    
    def reset_rate_limits(self, request, queryset):
        """Réinitialise les limitations de taux pour les numéros sélectionnés."""
        from django.core.cache import cache
        
        reset_count = 0
        for otp in queryset:
            cache_key = f"otp_rate_limit_{otp.phone_number}"
            if cache.delete(cache_key):
                reset_count += 1
        
        self.message_user(
            request,
            f"Limitations de taux réinitialisées pour {reset_count} numéros."
        )
    reset_rate_limits.short_description = "Réinitialiser les limitations de taux"
    
    def get_queryset(self, request):
        """Optimise la requête avec les relations."""
        return super().get_queryset(request).select_related('user')
    
    def has_add_permission(self, request):
        """Interdit la création manuelle d'OTP."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Autorise uniquement la modification du statut utilisé."""
        return True
    
    def has_delete_permission(self, request, obj=None):
        """Autorise la suppression des OTP expirés uniquement."""
        if obj and obj.is_expired():
            return True
        return False

class OTPMonitoringAdmin(admin.ModelAdmin):
    """Interface de monitoring des OTP."""
    
    change_list_template = 'admin/otp_monitoring.html'
    
    def changelist_view(self, request, extra_context=None):
        """Vue personnalisée pour le monitoring des OTP."""
        extra_context = extra_context or {}
        
        # Statistiques des OTP
        otp_stats = OTPMaintenanceService.get_otp_statistics()
        extra_context['otp_stats'] = otp_stats
        
        # Activité suspecte
        suspicious_activity = OTPMaintenanceService.monitor_suspicious_activity()
        extra_context['suspicious_activity'] = suspicious_activity
        
        # Top des numéros avec le plus d'OTP
        top_phones = OTPCode.objects.values('phone_number').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        extra_context['top_phones'] = top_phones
        
        return super().changelist_view(request, extra_context)

# Configuration personnalisée de l'admin
admin.site.site_header = "Kleer Logistics - Administration"
admin.site.site_title = "Kleer Logistics Admin"
admin.site.index_title = "Bienvenue dans l'administration de Kleer Logistics"

# Note: Les modèles sont déjà enregistrés avec les décorateurs @admin.register
# Pas besoin d'enregistrements manuels supplémentaires
