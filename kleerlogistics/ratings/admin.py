from django.contrib import admin
from .models import Rating

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['rater', 'rated_user', 'shipment', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['rater__username', 'rated_user__username', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('rater', 'rated_user', 'shipment')
        }),
        ('Évaluation', {
            'fields': ('rating', 'comment')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ) 