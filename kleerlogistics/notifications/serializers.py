"""
Serializers for notifications app - JSON serialization for notification data
"""

from rest_framework import serializers
from django.utils import timezone

from .models import Notification, EmailTemplate, SMSTemplate


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer pour les notifications."""
    
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'notification_type', 'notification_type_display',
            'title', 'message', 'status', 'status_display', 'is_read',
            'read_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'read_at'
        ]


class EmailTemplateSerializer(serializers.ModelSerializer):
    """Serializer pour les modèles d'email."""
    
    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'name', 'description', 'subject', 'body',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_subject(self, value):
        """Valider le sujet de l'email."""
        if not value:
            raise serializers.ValidationError("Le sujet ne peut pas être vide.")
        return value
    
    def validate_body(self, value):
        """Valider le corps de l'email."""
        if not value:
            raise serializers.ValidationError("Le corps de l'email ne peut pas être vide.")
        return value


class SMSTemplateSerializer(serializers.ModelSerializer):
    """Serializer pour les modèles de SMS."""
    
    class Meta:
        model = SMSTemplate
        fields = [
            'id', 'name', 'description', 'message',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_message(self, value):
        """Valider le message SMS."""
        if not value:
            raise serializers.ValidationError("Le message ne peut pas être vide.")
        if len(value) > 160:
            raise serializers.ValidationError("Le message SMS ne peut pas dépasser 160 caractères.")
        return value


class EmailNotificationSerializer(serializers.Serializer):
    """Serializer pour l'envoi d'emails."""
    
    template_name = serializers.CharField(max_length=100)
    recipient_email = serializers.EmailField()
    context = serializers.DictField(required=False, default=dict)
    
    def validate_template_name(self, value):
        """Valider le nom du modèle."""
        if not value:
            raise serializers.ValidationError("Le nom du modèle ne peut pas être vide.")
        return value


class SMSNotificationSerializer(serializers.Serializer):
    """Serializer pour l'envoi de SMS."""
    
    template_name = serializers.CharField(max_length=100)
    phone_number = serializers.CharField(max_length=20)
    context = serializers.DictField(required=False, default=dict)
    
    def validate_template_name(self, value):
        """Valider le nom du modèle."""
        if not value:
            raise serializers.ValidationError("Le nom du modèle ne peut pas être vide.")
        return value
    
    def validate_phone_number(self, value):
        """Valider le numéro de téléphone."""
        if not value:
            raise serializers.ValidationError("Le numéro de téléphone ne peut pas être vide.")
        # En production, ajouter une validation plus stricte
        return value


class ShipmentNotificationSerializer(serializers.Serializer):
    """Serializer pour les notifications d'envoi."""
    
    shipment_id = serializers.IntegerField()
    notification_type = serializers.ChoiceField(choices=['email', 'sms'], default='email')
    
    def validate_shipment_id(self, value):
        """Valider l'ID de l'envoi."""
        if value <= 0:
            raise serializers.ValidationError("ID d'envoi invalide.")
        return value


class NotificationSearchSerializer(serializers.ModelSerializer):
    """Serializer pour la recherche de notifications."""
    
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'notification_type_display',
            'title', 'status', 'status_display', 'is_read',
            'created_at', 'user_summary'
        ]
    
    def get_user_summary(self, obj):
        """Obtenir un résumé de l'utilisateur."""
        return {
            'id': obj.user.id,
            'name': f"{obj.user.first_name} {obj.user.last_name}",
            'email': obj.user.email
        }


class NotificationAnalyticsSerializer(serializers.Serializer):
    """Serializer pour les analytics des notifications."""
    
    total_notifications = serializers.IntegerField()
    email_notifications = serializers.IntegerField()
    sms_notifications = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    sent_today = serializers.IntegerField()
    sent_this_month = serializers.IntegerField()
    
    def to_representation(self, instance):
        """Formater les analytics."""
        return {
            'success': True,
            'analytics': {
                'total_notifications': instance.get('total_notifications', 0),
                'email_notifications': instance.get('email_notifications', 0),
                'sms_notifications': instance.get('sms_notifications', 0),
                'unread_notifications': instance.get('unread_notifications', 0),
                'sent_today': instance.get('sent_today', 0),
                'sent_this_month': instance.get('sent_this_month', 0)
            }
        }


class NotificationExportSerializer(serializers.ModelSerializer):
    """Serializer pour l'export des notifications."""
    
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'notification_type', 'notification_type_display',
            'title', 'status', 'status_display', 'user_email',
            'created_at'
        ] 