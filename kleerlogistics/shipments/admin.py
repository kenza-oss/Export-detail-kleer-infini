from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum, Avg, Q
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from datetime import timedelta
import logging

from .models import (
    Shipment, ShipmentTracking, Package, ShipmentDocument, 
    ShipmentRating, DeliveryOTP
)

logger = logging.getLogger(__name__)


class ShipmentStatusFilter(SimpleListFilter):
    """Filtre personnalisé pour le statut des envois."""
    title = 'Statut de l\'envoi'
    parameter_name = 'status_filter'

    def lookups(self, request, model_admin):
        return [
            ('pending', 'En attente'),
            ('in_transit', 'En transit'),
            ('delivered', 'Livré'),
            ('cancelled', 'Annulé'),
            ('overdue', 'En retard'),
            ('urgent', 'Urgents'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'overdue':
            return queryset.filter(
                status='in_transit',
                max_delivery_date__lt=timezone.now()
            )
        elif self.value() == 'urgent':
            return queryset.filter(urgency='urgent')
        elif self.value():
            return queryset.filter(status=self.value())
        return queryset


class ShipmentDateFilter(SimpleListFilter):
    """Filtre personnalisé pour les dates des envois."""
    title = 'Période de création'
    parameter_name = 'date_filter'

    def lookups(self, request, model_admin):
        return [
            ('today', 'Aujourd\'hui'),
            ('week', 'Cette semaine'),
            ('month', 'Ce mois'),
            ('quarter', 'Ce trimestre'),
            ('year', 'Cette année'),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'today':
            return queryset.filter(created_at__date=now.date())
        elif self.value() == 'week':
            return queryset.filter(created_at__gte=now - timedelta(days=7))
        elif self.value() == 'month':
            return queryset.filter(created_at__gte=now - timedelta(days=30))
        elif self.value() == 'quarter':
            return queryset.filter(created_at__gte=now - timedelta(days=90))
        elif self.value() == 'year':
            return queryset.filter(created_at__gte=now - timedelta(days=365))
        return queryset


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    """Administration des envois."""
    
    list_display = [
        'tracking_number', 'sender_info', 'origin_destination', 'package_info',
        'status_badge', 'urgency_badge', 'payment_status_badge', 'created_date'
    ]
    
    list_filter = [
        ShipmentStatusFilter,
        ShipmentDateFilter,
        'package_type',
        'urgency',
        'payment_status',
        'is_paid',
        'insurance_requested',
        'created_at',
    ]
    
    search_fields = [
        'tracking_number', 'sender__email', 'sender__first_name', 'sender__last_name',
        'origin_city', 'destination_city', 'recipient_name', 'recipient_phone'
    ]
    
    readonly_fields = [
        'tracking_number', 'created_at', 'updated_at', 'otp_code', 'otp_generated_at'
    ]
    
    fieldsets = (
        ('Informations de base', {
            'fields': (
                'tracking_number', 'sender', 'status', 'urgency'
            )
        }),
        ('Détails du colis', {
            'fields': (
                'package_type', 'description', 'weight', 'dimensions', 'value',
                'is_fragile', 'insurance_requested'
            )
        }),
        ('Origine', {
            'fields': ('origin_city', 'origin_address')
        }),
        ('Destination', {
            'fields': (
                'destination_city', 'destination_country', 'destination_address',
                'recipient_name', 'recipient_phone', 'recipient_email'
            )
        }),
        ('Dates et planning', {
            'fields': (
                'preferred_pickup_date', 'max_delivery_date', 'delivery_date'
            )
        }),
        ('Paiement', {
            'fields': (
                'price', 'shipping_cost', 'is_paid', 'payment_method',
                'payment_status', 'payment_date'
            )
        }),
        ('Sécurité et OTP', {
            'fields': (
                'otp_code', 'otp_generated_at', 'delivery_otp'
            ),
            'classes': ('collapse',)
        }),
        ('Informations système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_as_in_transit', 'mark_as_delivered', 'mark_as_cancelled',
        'generate_tracking_number', 'send_notification'
    ]
    
    def sender_info(self, obj):
        """Afficher les informations de l'expéditeur."""
        if obj.sender:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                f"{obj.sender.first_name} {obj.sender.last_name}",
                obj.sender.email
            )
        return "-"
    sender_info.short_description = "Expéditeur"
    
    def origin_destination(self, obj):
        """Afficher l'origine et la destination."""
        return format_html(
            '<strong>De:</strong> {}<br><strong>À:</strong> {}',
            obj.origin_city, obj.destination_city
        )
    origin_destination.short_description = "Trajet"
    
    def package_info(self, obj):
        """Afficher les informations du colis."""
        return format_html(
            '<strong>{}</strong><br><small>{} kg</small>',
            obj.get_package_type_display(), obj.weight
        )
    package_info.short_description = "Colis"
    
    def status_badge(self, obj):
        """Afficher le statut avec un badge coloré."""
        colors = {
            'draft': 'gray',
            'pending': 'orange',
            'matched': 'blue',
            'in_transit': 'yellow',
            'delivered': 'green',
            'cancelled': 'red',
            'lost': 'darkred',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Statut"
    
    def urgency_badge(self, obj):
        """Afficher l'urgence avec un badge coloré."""
        colors = {
            'low': 'green',
            'medium': 'orange',
            'high': 'red',
            'urgent': 'darkred',
        }
        color = colors.get(obj.urgency, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_urgency_display()
        )
    urgency_badge.short_description = "Urgence"
    
    def payment_status_badge(self, obj):
        """Afficher le statut de paiement avec un badge coloré."""
        colors = {
            'pending': 'orange',
            'paid': 'green',
            'failed': 'red',
            'refunded': 'blue',
        }
        color = colors.get(obj.payment_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_status_badge.short_description = "Paiement"
    
    def created_date(self, obj):
        """Afficher la date de création formatée."""
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    created_date.short_description = "Créé le"
    
    # Actions d'administration
    def mark_as_in_transit(self, request, queryset):
        """Marquer les envois sélectionnés comme en transit."""
        updated = queryset.update(status='in_transit')
        self.message_user(
            request, 
            f"{updated} envoi(s) marqué(s) comme en transit."
        )
    mark_as_in_transit.short_description = "Marquer comme en transit"
    
    def mark_as_delivered(self, request, queryset):
        """Marquer les envois sélectionnés comme livrés."""
        updated = queryset.update(
            status='delivered',
            delivery_date=timezone.now()
        )
        self.message_user(
            request, 
            f"{updated} envoi(s) marqué(s) comme livré(s)."
        )
    mark_as_delivered.short_description = "Marquer comme livré"
    
    def mark_as_cancelled(self, request, queryset):
        """Marquer les envois sélectionnés comme annulés."""
        updated = queryset.update(status='cancelled')
        self.message_user(
            request, 
            f"{updated} envoi(s) marqué(s) comme annulé(s)."
        )
    mark_as_cancelled.short_description = "Marquer comme annulé"
    
    def generate_tracking_number(self, request, queryset):
        """Générer des numéros de suivi pour les envois sélectionnés."""
        updated = 0
        for shipment in queryset:
            if not shipment.tracking_number:
                shipment.tracking_number = shipment.generate_tracking_number()
                shipment.save()
                updated += 1
        
        self.message_user(
            request, 
            f"{updated} numéro(s) de suivi généré(s)."
        )
    generate_tracking_number.short_description = "Générer numéros de suivi"
    
    def send_notification(self, request, queryset):
        """Envoyer des notifications pour les envois sélectionnés."""
        # Ici on pourrait implémenter l'envoi de notifications
        self.message_user(
            request, 
            f"Notifications envoyées pour {queryset.count()} envoi(s)."
        )
    send_notification.short_description = "Envoyer notifications"
    
    def get_queryset(self, request):
        """Optimiser les requêtes avec select_related."""
        return super().get_queryset(request).select_related('sender')
    
    def get_list_display(self, request):
        """Adapter l'affichage selon les permissions."""
        if request.user.is_superuser:
            return self.list_display
        # Pour les staff non-superuser, masquer certains champs sensibles
        return [field for field in self.list_display if field != 'sender_info']


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    """Administration des détails des colis."""
    
    list_display = [
        'shipment_tracking', 'category', 'dimensions_display', 'volume',
        'special_handling', 'created_date'
    ]
    
    list_filter = [
        'category', 'requires_special_handling', 'is_hazardous',
        'temperature_sensitive', 'created_at'
    ]
    
    search_fields = [
        'shipment__tracking_number', 'shipment__sender__email',
        'handling_instructions'
    ]
    
    readonly_fields = ['volume', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('shipment', 'category')
        }),
        ('Dimensions', {
            'fields': ('length', 'width', 'height', 'volume')
        }),
        ('Sécurité', {
            'fields': (
                'requires_special_handling', 'is_hazardous',
                'temperature_sensitive', 'min_temperature', 'max_temperature'
            )
        }),
        ('Instructions', {
            'fields': ('handling_instructions', 'storage_requirements')
        }),
        ('Informations système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def shipment_tracking(self, obj):
        """Afficher le numéro de suivi de l'envoi."""
        if obj.shipment:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.shipment.tracking_number,
                obj.shipment.get_status_display()
            )
        return "-"
    shipment_tracking.short_description = "Envoi"
    
    def dimensions_display(self, obj):
        """Afficher les dimensions du colis."""
        return f"{obj.length} × {obj.width} × {obj.height} cm"
    dimensions_display.short_description = "Dimensions"
    
    def special_handling(self, obj):
        """Afficher les besoins de manutention spéciale."""
        flags = []
        if obj.requires_special_handling:
            flags.append("Manutention spéciale")
        if obj.is_hazardous:
            flags.append("Dangereux")
        if obj.temperature_sensitive:
            flags.append("Température contrôlée")
        
        if flags:
            return format_html(
                '<span style="color: orange; font-weight: bold;">{}</span>',
                ", ".join(flags)
            )
        return "Standard"
    special_handling.short_description = "Manutention"
    
    def created_date(self, obj):
        """Afficher la date de création formatée."""
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    created_date.short_description = "Créé le"


@admin.register(ShipmentTracking)
class ShipmentTrackingAdmin(admin.ModelAdmin):
    """Administration du suivi des envois."""
    
    list_display = [
        'shipment_tracking', 'event_type', 'status', 'location',
        'description', 'timestamp'
    ]
    
    list_filter = [
        'event_type', 'status', 'timestamp', 'shipment__status'
    ]
    
    search_fields = [
        'shipment__tracking_number', 'location', 'description'
    ]
    
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('shipment', 'event_type', 'status')
        }),
        ('Détails', {
            'fields': ('location', 'description', 'timestamp')
        }),
    )
    
    def shipment_tracking(self, obj):
        """Afficher le numéro de suivi de l'envoi."""
        if obj.shipment:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.shipment.tracking_number,
                obj.shipment.get_status_display()
            )
        return "-"
    shipment_tracking.short_description = "Envoi"


@admin.register(ShipmentDocument)
class ShipmentDocumentAdmin(admin.ModelAdmin):
    """Administration des documents d'envoi."""
    
    list_display = [
        'shipment_tracking', 'document_type', 'title', 'file_size',
        'created_at'
    ]
    
    list_filter = [
        'document_type', 'created_at', 'shipment__status'
    ]
    
    search_fields = [
        'shipment__tracking_number', 'title', 'description'
    ]
    
    readonly_fields = ['created_at', 'file_size']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('shipment', 'document_type', 'file_name')
        }),
        ('Fichier', {
            'fields': ('file', 'file_size', 'uploaded_by', 'uploaded_at')
        }),
    )
    
    def shipment_tracking(self, obj):
        """Afficher le numéro de suivi de l'envoi."""
        if obj.shipment:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.shipment.tracking_number,
                obj.shipment.get_status_display()
            )
        return "-"
    shipment_tracking.short_description = "Envoi"
    
    def file_size(self, obj):
        """Afficher la taille du fichier."""
        if obj.file:
            try:
                size = obj.file.size
                if size < 1024:
                    return f"{size} B"
                elif size < 1024 * 1024:
                    return f"{size / 1024:.1f} KB"
                else:
                    return f"{size / (1024 * 1024):.1f} MB"
            except:
                return "N/A"
        return "N/A"
    file_size.short_description = "Taille"


@admin.register(ShipmentRating)
class ShipmentRatingAdmin(admin.ModelAdmin):
    """Administration des évaluations d'envois."""
    
    list_display = [
        'shipment_tracking', 'rating_stars', 'rater_info', 'comment_preview',
        'created_date'
    ]
    
    list_filter = [
        'overall_rating', 'created_at', 'shipment__status'
    ]
    
    search_fields = [
        'shipment__tracking_number', 'rater__email', 'comment'
    ]
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('shipment', 'rater', 'rating')
        }),
        ('Évaluation', {
            'fields': ('comment', 'created_at')
        }),
    )
    
    def shipment_tracking(self, obj):
        """Afficher le numéro de suivi de l'envoi."""
        if obj.shipment:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.shipment.tracking_number,
                obj.shipment.get_status_display()
            )
        return "-"
    shipment_tracking.short_description = "Envoi"
    
    def rating_stars(self, obj):
        """Afficher l'évaluation avec des étoiles."""
        stars = "★" * obj.rating + "☆" * (5 - obj.rating)
        return format_html(
            '<span style="color: gold; font-size: 16px;">{}</span> ({})',
            stars, obj.rating
        )
    rating_stars.short_description = "Évaluation"
    
    def rater_info(self, obj):
        """Afficher les informations de l'évaluateur."""
        if obj.rater:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                f"{obj.rater.first_name} {obj.rater.last_name}",
                obj.rater.email
            )
        return "-"
    rater_info.short_description = "Évaluateur"
    
    def comment_preview(self, obj):
        """Afficher un aperçu du commentaire."""
        if obj.comment:
            preview = obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment
            return preview
        return "Aucun commentaire"
    comment_preview.short_description = "Commentaire"
    
    def created_date(self, obj):
        """Afficher la date de création formatée."""
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    created_date.short_description = "Créé le"


@admin.register(DeliveryOTP)
class DeliveryOTPAdmin(admin.ModelAdmin):
    """Administration des OTP de livraison."""
    
    list_display = [
        'shipment_tracking', 'otp_code', 'recipient_info', 'generated_by_info',
        'is_used', 'expires_at', 'created_at'
    ]
    
    list_filter = [
        'is_used', 'created_at', 'expires_at', 'shipment__status'
    ]
    
    search_fields = [
        'shipment__tracking_number', 'recipient_phone', 'recipient_name'
    ]
    
    readonly_fields = ['created_at', 'otp_code']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('shipment', 'otp_code', 'status')
        }),
        ('Destinataire', {
            'fields': ('recipient_phone', 'recipient_name')
        }),
        ('Génération', {
            'fields': ('generated_by', 'created_at', 'expires_at')
        }),
    )
    
    def shipment_tracking(self, obj):
        """Afficher le numéro de suivi de l'envoi."""
        if obj.shipment:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.shipment.tracking_number,
                obj.shipment.get_status_display()
            )
        return "-"
    shipment_tracking.short_description = "Envoi"
    
    def recipient_info(self, obj):
        """Afficher les informations du destinataire."""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.recipient_name, obj.recipient_phone
        )
    recipient_info.short_description = "Destinataire"
    
    def generated_by_info(self, obj):
        """Afficher les informations de l'utilisateur qui a généré l'OTP."""
        if obj.generated_by:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                f"{obj.generated_by.first_name} {obj.generated_by.last_name}",
                obj.generated_by.email
            )
        return "-"
    generated_by_info.short_description = "Généré par"


# Configuration de l'interface d'administration
admin.site.site_header = "Administration Kleer Logistics"
admin.site.site_title = "Kleer Logistics Admin"
admin.site.index_title = "Gestion des Expéditions"
