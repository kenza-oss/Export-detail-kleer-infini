from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'shipment', 'sender', 'traveler', 'is_active', 'created_at', 'last_message_at']
    list_filter = ['is_active', 'created_at', 'last_message_at']
    search_fields = ['shipment__tracking_number', 'sender__username', 'traveler__username']
    readonly_fields = ['created_at', 'last_message_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('shipment', 'sender', 'traveler', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'last_message_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'message_type', 'is_read', 'created_at']
    list_filter = ['message_type', 'is_read', 'created_at']
    search_fields = ['content', 'sender__username', 'conversation__shipment__tracking_number']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('conversation', 'sender', 'content', 'message_type')
        }),
        ('Métadonnées', {
            'fields': ('metadata', 'is_read', 'created_at'),
            'classes': ('collapse',)
        }),
    )
