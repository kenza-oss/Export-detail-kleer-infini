"""
Interface d'administration pour le module de paiements KleerLogistics
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Wallet, Transaction, PaymentMethod, Commission


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """Administration des portefeuilles."""
    
    list_display = [
        'user', 'balance', 'pending_balance', 'available_balance',
        'total_earned', 'total_spent', 'created_at'
    ]
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations utilisateur', {
            'fields': ('user',)
        }),
        ('Soldes', {
            'fields': ('balance', 'pending_balance', 'available_balance')
        }),
        ('Statistiques', {
            'fields': ('total_earned', 'total_spent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def available_balance(self, obj):
        """Affiche le solde disponible."""
        return f"{obj.available_balance} DA"
    available_balance.short_description = "Solde disponible"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Administration des transactions."""
    
    list_display = [
        'transaction_id', 'user', 'type', 'amount', 'currency',
        'payment_method', 'status', 'created_at', 'completed_at'
    ]
    list_filter = [
        'type', 'status', 'payment_method', 'currency',
        'created_at', 'completed_at'
    ]
    search_fields = [
        'transaction_id', 'user__username', 'user__email',
        'description', 'external_payment_id'
    ]
    readonly_fields = [
        'transaction_id', 'created_at', 'completed_at',
        'external_payment_id', 'cash_payment_confirmed_by'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('transaction_id', 'user', 'shipment', 'related_transaction')
        }),
        ('Détails de la transaction', {
            'fields': ('type', 'amount', 'currency', 'status', 'description')
        }),
        ('Méthode de paiement', {
            'fields': (
                'payment_method', 'payment_gateway', 'external_payment_id'
            )
        }),
        ('Informations carte bancaire', {
            'fields': (
                'card_type', 'card_last_four', 'card_holder_name'
            ),
            'classes': ('collapse',)
        }),
        ('Paiement en espèces', {
            'fields': (
                'cash_payment_reference', 'cash_payment_location',
                'cash_payment_date', 'cash_payment_confirmed_by'
            ),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimise les requêtes avec select_related."""
        return super().get_queryset(request).select_related('user', 'shipment')
    
    def transaction_link(self, obj):
        """Lien vers la transaction."""
        if obj.transaction_id:
            url = reverse('admin:payments_transaction_change', args=[obj.id])
            return format_html('<a href="{}">{}</a>', url, obj.transaction_id)
        return obj.transaction_id
    transaction_link.short_description = "ID Transaction"
    
    def user_link(self, obj):
        """Lien vers l'utilisateur."""
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return obj.user.username if obj.user else '-'
    user_link.short_description = "Utilisateur"
    
    def amount_display(self, obj):
        """Affiche le montant avec la devise."""
        return f"{obj.amount} {obj.currency}"
    amount_display.short_description = "Montant"


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Administration des méthodes de paiement."""
    
    list_display = [
        'name', 'method_type', 'is_active', 'is_online',
        'min_amount', 'max_amount', 'processing_fee', 'fixed_fee'
    ]
    list_filter = ['method_type', 'is_active', 'is_online']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'method_type', 'description')
        }),
        ('Configuration', {
            'fields': ('is_active', 'is_online')
        }),
        ('Limites', {
            'fields': ('min_amount', 'max_amount')
        }),
        ('Frais', {
            'fields': ('processing_fee', 'fixed_fee')
        }),
        ('Bureaux (espèces)', {
            'fields': ('office_locations', 'office_hours', 'office_instructions'),
            'classes': ('collapse',)
        }),
        ('Interface', {
            'fields': ('icon_url',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def method_type_display(self, obj):
        """Affiche le type de méthode avec couleur."""
        colors = {
            'cib': '#28a745',
            'eddahabia': '#007bff',
            'visa': '#1a1f71',
            'mastercard': '#eb001b',
            'cash': '#ffc107',
            'bank_transfer': '#6c757d',
            'chargily': '#17a2b8',
            'wallet': '#fd7e14'
        }
        color = colors.get(obj.method_type, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_method_type_display()
        )
    method_type_display.short_description = "Type"


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    """Administration des commissions."""
    
    list_display = [
        'shipment', 'platform_commission', 'traveler_earning',
        'total_amount', 'commission_rate', 'created_at'
    ]
    list_filter = ['commission_rate', 'created_at']
    search_fields = [
        'shipment__tracking_number', 'shipment__sender__username',
        'shipment__matched_trip__traveler__username'
    ]
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Envoi', {
            'fields': ('shipment',)
        }),
        ('Commissions', {
            'fields': (
                'platform_commission', 'traveler_earning', 'total_amount',
                'commission_rate'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimise les requêtes avec select_related."""
        return super().get_queryset(request).select_related(
            'shipment', 'shipment__sender', 'shipment__matched_trip__traveler'
        )


# Actions personnalisées pour l'administration
@admin.action(description="Marquer comme complétées")
def mark_completed(modeladmin, request, queryset):
    """Marque les transactions comme complétées."""
    from django.utils import timezone
    updated = queryset.update(
        status='completed',
        completed_at=timezone.now()
    )
    modeladmin.message_user(
        request,
        f"{updated} transaction(s) marquée(s) comme complétée(s)."
    )


@admin.action(description="Marquer comme échouées")
def mark_failed(modeladmin, request, queryset):
    """Marque les transactions comme échouées."""
    updated = queryset.update(status='failed')
    modeladmin.message_user(
        request,
        f"{updated} transaction(s) marquée(s) comme échouée(s)."
    )


@admin.action(description="Annuler les transactions")
def cancel_transactions(modeladmin, request, queryset):
    """Annule les transactions."""
    updated = queryset.update(status='cancelled')
    modeladmin.message_user(
        request,
        f"{updated} transaction(s) annulée(s)."
    )


# Ajouter les actions aux modèles
TransactionAdmin.actions = [mark_completed, mark_failed, cancel_transactions]


# Configuration de l'interface d'administration
admin.site.site_header = "Administration KleerLogistics"
admin.site.site_title = "KleerLogistics Admin"
admin.site.index_title = "Gestion de la plateforme KleerLogistics"
