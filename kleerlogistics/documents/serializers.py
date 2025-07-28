"""
Serializers for documents app - JSON serialization for document data
"""

from rest_framework import serializers
from django.utils import timezone

from .models import Document, DocumentTemplate


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer pour les documents."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'user', 'document_type', 'document_type_display',
            'reference', 'title', 'content', 'status', 'status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'reference', 'created_at', 'updated_at'
        ]


class DocumentTemplateSerializer(serializers.ModelSerializer):
    """Serializer pour les modèles de documents."""
    
    class Meta:
        model = DocumentTemplate
        fields = [
            'id', 'name', 'description', 'document_type',
            'template_content', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_template_content(self, value):
        """Valider le contenu du modèle."""
        if not value:
            raise serializers.ValidationError("Le contenu du modèle ne peut pas être vide.")
        return value


class InvoiceSerializer(serializers.Serializer):
    """Serializer pour la génération de factures."""
    
    shipment_id = serializers.IntegerField()
    customer_name = serializers.CharField(max_length=255, required=False)
    customer_email = serializers.EmailField(required=False)
    notes = serializers.CharField(max_length=500, required=False)
    
    def validate_shipment_id(self, value):
        """Valider l'ID de l'envoi."""
        if value <= 0:
            raise serializers.ValidationError("ID d'envoi invalide.")
        return value


class ReceiptSerializer(serializers.Serializer):
    """Serializer pour la génération de reçus."""
    
    transaction_id = serializers.IntegerField()
    customer_name = serializers.CharField(max_length=255, required=False)
    customer_email = serializers.EmailField(required=False)
    notes = serializers.CharField(max_length=500, required=False)
    
    def validate_transaction_id(self, value):
        """Valider l'ID de la transaction."""
        if value <= 0:
            raise serializers.ValidationError("ID de transaction invalide.")
        return value


class CustomDocumentSerializer(serializers.Serializer):
    """Serializer pour la génération de documents personnalisés."""
    
    template_id = serializers.IntegerField()
    data = serializers.DictField()
    title = serializers.CharField(max_length=255, required=False)
    
    def validate_template_id(self, value):
        """Valider l'ID du modèle."""
        if value <= 0:
            raise serializers.ValidationError("ID de modèle invalide.")
        return value
    
    def validate_data(self, value):
        """Valider les données du document."""
        if not value:
            raise serializers.ValidationError("Les données ne peuvent pas être vides.")
        return value


class DocumentDownloadSerializer(serializers.Serializer):
    """Serializer pour le téléchargement de documents."""
    
    document_id = serializers.IntegerField()
    format = serializers.ChoiceField(choices=['pdf', 'docx', 'html'], default='pdf')
    
    def validate_document_id(self, value):
        """Valider l'ID du document."""
        if value <= 0:
            raise serializers.ValidationError("ID de document invalide.")
        return value


class DocumentPreviewSerializer(serializers.Serializer):
    """Serializer pour la prévisualisation de documents."""
    
    document_id = serializers.IntegerField()
    
    def validate_document_id(self, value):
        """Valider l'ID du document."""
        if value <= 0:
            raise serializers.ValidationError("ID de document invalide.")
        return value


class DocumentSearchSerializer(serializers.ModelSerializer):
    """Serializer pour la recherche de documents."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    user_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'reference', 'title', 'document_type',
            'document_type_display', 'status', 'status_display',
            'created_at', 'user_summary'
        ]
    
    def get_user_summary(self, obj):
        """Obtenir un résumé de l'utilisateur."""
        return {
            'id': obj.user.id,
            'name': f"{obj.user.first_name} {obj.user.last_name}",
            'email': obj.user.email
        }


class DocumentAnalyticsSerializer(serializers.Serializer):
    """Serializer pour les analytics des documents."""
    
    total_documents = serializers.IntegerField()
    invoices_count = serializers.IntegerField()
    receipts_count = serializers.IntegerField()
    custom_documents_count = serializers.IntegerField()
    generated_today = serializers.IntegerField()
    generated_this_month = serializers.IntegerField()
    
    def to_representation(self, instance):
        """Formater les analytics."""
        return {
            'success': True,
            'analytics': {
                'total_documents': instance.get('total_documents', 0),
                'invoices_count': instance.get('invoices_count', 0),
                'receipts_count': instance.get('receipts_count', 0),
                'custom_documents_count': instance.get('custom_documents_count', 0),
                'generated_today': instance.get('generated_today', 0),
                'generated_this_month': instance.get('generated_this_month', 0)
            }
        }


class DocumentExportSerializer(serializers.ModelSerializer):
    """Serializer pour l'export des documents."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'reference', 'title', 'document_type', 'document_type_display',
            'status', 'status_display', 'user_email', 'created_at'
        ] 