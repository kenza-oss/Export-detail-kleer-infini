"""
Admin interface pour le module trips
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Trip, TripDocument


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    """Interface d'administration pour les trajets."""
    
    list_display = [
        'id', 'traveler_info', 'route_display', 'departure_date', 
        'status_badge', 'capacity_info', 'price_info', 'verification_status'
    ]
    
    list_filter = [
        'status', 'is_verified', 'origin_country', 'destination_country',
        'accepts_fragile', 'flexible_dates', 'created_at', 'departure_date'
    ]
    
    search_fields = [
        'traveler__username', 'traveler__email', 'traveler__first_name', 
        'traveler__last_name', 'origin_city', 'destination_city', 'notes'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'remaining_weight', 'remaining_packages',
        'total_weight_carried', 'total_packages_carried', 'utilization_rate',
        'days_until_departure', 'estimated_earnings'
    ]
    
    fieldsets = [
        ('Informations de base', {
            'fields': [
                'id', 'traveler', 'status', 'is_verified'
            ]
        }),
        ('Origine et destination', {
            'fields': [
                'origin_city', 'origin_country', 'destination_city', 'destination_country'
            ]
        }),
        ('Dates', {
            'fields': [
                'departure_date', 'arrival_date', 'flexible_dates', 'flexibility_days'
            ]
        }),
        ('Capacité', {
            'fields': [
                'max_weight', 'remaining_weight', 'max_packages', 'remaining_packages',
                'total_weight_carried', 'total_packages_carried', 'utilization_rate'
            ]
        }),
        ('Conditions', {
            'fields': [
                'accepted_package_types', 'min_price_per_kg', 'accepts_fragile'
            ]
        }),
        ('Calculs', {
            'fields': [
                'days_until_departure', 'estimated_earnings'
            ],
            'classes': ['collapse']
        }),
        ('Notes', {
            'fields': ['notes']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    actions = [
        'verify_trips', 'activate_trips', 'expire_trips', 'export_trips'
    ]
    
    def traveler_info(self, obj):
        """Afficher les informations du voyageur."""
        if obj.traveler:
            url = reverse('admin:users_user_change', args=[obj.traveler.id])
            return format_html(
                '<a href="{}">{} {}</a><br><small>{}</small>',
                url, obj.traveler.first_name, obj.traveler.last_name, obj.traveler.email
            )
        return '-'
    traveler_info.short_description = 'Voyageur'
    
    def route_display(self, obj):
        """Afficher la route du trajet."""
        return format_html(
            '<strong>{} → {}</strong><br><small>{} → {}</small>',
            obj.origin_city, obj.destination_city,
            obj.get_origin_country_display(), obj.get_destination_country_display()
        )
    route_display.short_description = 'Route'
    
    def status_badge(self, obj):
        """Afficher le statut avec un badge coloré."""
        status_colors = {
            'draft': 'gray',
            'active': 'green',
            'in_progress': 'blue',
            'completed': 'darkgreen',
            'cancelled': 'red',
            'expired': 'orange'
        }
        
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def capacity_info(self, obj):
        """Afficher les informations de capacité."""
        return format_html(
            '<strong>{:.1f}kg / {:.1f}kg</strong><br><small>{} / {} colis</small>',
            obj.remaining_weight, obj.max_weight,
            obj.remaining_packages, obj.max_packages
        )
    capacity_info.short_description = 'Capacité'
    
    def price_info(self, obj):
        """Afficher les informations de prix."""
        return format_html(
            '<strong>{:.2f} DA/kg</strong><br><small>Gains estimés: {:.2f} DA</small>',
            obj.min_price_per_kg, obj.estimated_earnings
        )
    price_info.short_description = 'Prix'
    
    def verification_status(self, obj):
        """Afficher le statut de vérification."""
        if obj.is_verified:
            return format_html(
                '<span style="color: green;">✓ Vérifié</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Non vérifié</span>'
            )
    verification_status.short_description = 'Vérification'
    
    def total_weight_carried(self, obj):
        """Calculer le poids total transporté."""
        return obj.total_weight_carried
    
    def total_packages_carried(self, obj):
        """Calculer le nombre total de colis transportés."""
        return obj.total_packages_carried
    
    def utilization_rate(self, obj):
        """Calculer le taux d'utilisation."""
        return f"{obj.utilization_rate:.1f}%"
    
    def days_until_departure(self, obj):
        """Calculer les jours jusqu'au départ."""
        days = obj.days_until_departure
        if days is not None:
            if days < 0:
                return f"En retard ({abs(days)} jours)"
            elif days == 0:
                return "Aujourd'hui"
            else:
                return f"Dans {days} jours"
        return "N/A"
    
    def estimated_earnings(self, obj):
        """Calculer les gains estimés."""
        return f"{obj.estimated_earnings:.2f} DA"
    
    def verify_trips(self, request, queryset):
        """Vérifier les trajets sélectionnés."""
        count = queryset.update(is_verified=True)
        self.message_user(
            request, 
            f"{count} trajet(s) ont été vérifiés avec succès."
        )
    verify_trips.short_description = "Vérifier les trajets sélectionnés"
    
    def activate_trips(self, request, queryset):
        """Activer les trajets sélectionnés."""
        count = 0
        for trip in queryset:
            try:
                trip.update_status('active')
                count += 1
            except ValueError:
                pass
        
        self.message_user(
            request, 
            f"{count} trajet(s) ont été activés avec succès."
        )
    activate_trips.short_description = "Activer les trajets sélectionnés"
    
    def expire_trips(self, request, queryset):
        """Expirer les trajets sélectionnés."""
        count = queryset.filter(
            departure_date__lt=timezone.now(),
            status='active'
        ).update(status='expired')
        
        self.message_user(
            request, 
            f"{count} trajet(s) ont été expirés avec succès."
        )
    expire_trips.short_description = "Expirer les trajets en retard"
    
    def export_trips(self, request, queryset):
        """Exporter les trajets sélectionnés."""
        # Cette action pourrait générer un fichier CSV ou Excel
        count = queryset.count()
        self.message_user(
            request, 
            f"Export de {count} trajet(s) - Fonctionnalité à implémenter."
        )
    export_trips.short_description = "Exporter les trajets sélectionnés"
    
    def get_queryset(self, request):
        """Optimiser les requêtes avec select_related."""
        return super().get_queryset(request).select_related('traveler')
    
    def has_delete_permission(self, request, obj=None):
        """Contrôler les permissions de suppression."""
        if obj and obj.status in ['in_progress', 'completed']:
            return False
        return super().has_delete_permission(request, obj)
    
    def save_model(self, request, obj, form, change):
        """Validation avant sauvegarde."""
        try:
            obj.full_clean()
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            self.message_user(request, f"Erreur de validation: {e}", level='ERROR')


@admin.register(TripDocument)
class TripDocumentAdmin(admin.ModelAdmin):
    """Interface d'administration pour les documents de trajet."""
    
    list_display = [
        'id', 'trip_link', 'document_type_display', 'file_info', 
        'verification_status', 'uploaded_at'
    ]
    
    list_filter = [
        'document_type', 'is_verified', 'uploaded_at', 'verification_date'
    ]
    
    search_fields = [
        'trip__id', 'trip__traveler__username', 'trip__traveler__email',
        'verification_notes'
    ]
    
    readonly_fields = [
        'id', 'uploaded_at', 'file_size', 'file_type'
    ]
    
    fieldsets = [
        ('Informations de base', {
            'fields': [
                'id', 'trip', 'document_type', 'file'
            ]
        }),
        ('Vérification', {
            'fields': [
                'is_verified', 'verification_date', 'verification_notes'
            ]
        }),
        ('Informations techniques', {
            'fields': [
                'uploaded_at', 'file_size', 'file_type'
            ],
            'classes': ['collapse']
        })
    ]
    
    actions = [
        'verify_documents', 'reject_documents'
    ]
    
    def trip_link(self, obj):
        """Lien vers le trajet."""
        if obj.trip:
            url = reverse('admin:trips_trip_change', args=[obj.trip.id])
            return format_html(
                '<a href="{}">Trajet #{}</a><br><small>{} → {}</small>',
                url, obj.trip.id, obj.trip.origin_city, obj.trip.destination_city
            )
        return '-'
    trip_link.short_description = 'Trajet'
    
    def document_type_display(self, obj):
        """Afficher le type de document."""
        return obj.get_document_type_display()
    document_type_display.short_description = 'Type de document'
    
    def file_info(self, obj):
        """Afficher les informations du fichier."""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">Voir le fichier</a><br>'
                '<small>Taille: {}</small>',
                obj.file.url, self.file_size(obj)
            )
        return 'Aucun fichier'
    file_info.short_description = 'Fichier'
    
    def verification_status(self, obj):
        """Afficher le statut de vérification."""
        if obj.is_verified:
            return format_html(
                '<span style="color: green;">✓ Vérifié</span><br>'
                '<small>{}</small>',
                obj.verification_date.strftime('%d/%m/%Y %H:%M') if obj.verification_date else ''
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Non vérifié</span>'
            )
    verification_status.short_description = 'Statut de vérification'
    
    def file_size(self, obj):
        """Calculer la taille du fichier."""
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
    
    def file_type(self, obj):
        """Obtenir le type de fichier."""
        if obj.file and hasattr(obj.file, 'content_type'):
            return obj.file.content_type
        return "N/A"
    
    def verify_documents(self, request, queryset):
        """Vérifier les documents sélectionnés."""
        count = queryset.update(
            is_verified=True,
            verification_date=timezone.now()
        )
        self.message_user(
            request, 
            f"{count} document(s) ont été vérifiés avec succès."
        )
    verify_documents.short_description = "Vérifier les documents sélectionnés"
    
    def reject_documents(self, request, queryset):
        """Rejeter les documents sélectionnés."""
        count = queryset.update(
            is_verified=False,
            verification_date=timezone.now()
        )
        self.message_user(
            request, 
            f"{count} document(s) ont été rejetés."
        )
    reject_documents.short_description = "Rejeter les documents sélectionnés"
    
    def get_queryset(self, request):
        """Optimiser les requêtes avec select_related."""
        return super().get_queryset(request).select_related('trip', 'trip__traveler')
    
    def has_delete_permission(self, request, obj=None):
        """Contrôler les permissions de suppression."""
        if obj and obj.is_verified:
            return False
        return super().has_delete_permission(request, obj)


# Configuration de l'admin
admin.site.site_header = "Kleer Logistics - Administration"
admin.site.site_title = "Kleer Logistics Admin"
admin.site.index_title = "Gestion de la plateforme"

# Personnalisation de l'ordre des apps
admin.site.site_header = "Kleer Logistics - Administration"
admin.site.site_title = "Kleer Logistics Admin"
admin.site.index_title = "Gestion de la plateforme"
