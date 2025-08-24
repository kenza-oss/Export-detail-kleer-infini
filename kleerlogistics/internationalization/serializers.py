from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import (
    TranslationCategory, TranslationKey, Translation, 
    UserLanguagePreference, TranslationTemplate, 
    TranslationTemplateContent, TranslationCache
)

class TranslationCategorySerializer(serializers.ModelSerializer):
    """Sérialiseur pour les catégories de traduction"""
    
    class Meta:
        model = TranslationCategory
        fields = [
            'id', 'name', 'code', 'description', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class TranslationKeySerializer(serializers.ModelSerializer):
    """Sérialiseur pour les clés de traduction"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    translations_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TranslationKey
        fields = [
            'id', 'key', 'category', 'category_name', 'description', 
            'context', 'is_active', 'translations_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_translations_count(self, obj):
        return obj.translations.count()

class TranslationSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les traductions"""
    key_name = serializers.CharField(source='key.key', read_only=True)
    category_name = serializers.CharField(source='key.category.name', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    
    class Meta:
        model = Translation
        fields = [
            'id', 'key', 'key_name', 'category_name', 'language_code',
            'text', 'is_approved', 'approved_by', 'approved_by_username',
            'approved_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'key_name', 'category_name', 'approved_by_username',
            'approved_at', 'created_at', 'updated_at'
        ]

class TranslationDetailSerializer(serializers.ModelSerializer):
    """Sérialiseur détaillé pour les traductions avec toutes les langues"""
    translations = serializers.SerializerMethodField()
    
    class Meta:
        model = TranslationKey
        fields = [
            'id', 'key', 'category', 'description', 'context',
            'is_active', 'translations', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_translations(self, obj):
        translations = {}
        for translation in obj.translations.all():
            translations[translation.language_code] = {
                'id': translation.id,
                'text': translation.text,
                'is_approved': translation.is_approved,
                'approved_by': translation.approved_by.username if translation.approved_by else None,
                'approved_at': translation.approved_at,
                'created_at': translation.created_at,
                'updated_at': translation.updated_at,
            }
        return translations

class UserLanguagePreferenceSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les préférences de langue des utilisateurs"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserLanguagePreference
        fields = [
            'id', 'user', 'username', 'preferred_language',
            'fallback_language', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'username', 'created_at', 'updated_at']

class TranslationTemplateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les modèles de traduction"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    contents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TranslationTemplate
        fields = [
            'id', 'name', 'template_type', 'key', 'variables',
            'category', 'category_name', 'is_active', 'contents_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'category_name', 'contents_count', 'created_at', 'updated_at']
    
    def get_contents_count(self, obj):
        return obj.contents.count()

class TranslationTemplateContentSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le contenu des modèles de traduction"""
    template_name = serializers.CharField(source='template.name', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    
    class Meta:
        model = TranslationTemplateContent
        fields = [
            'id', 'template', 'template_name', 'language_code',
            'subject', 'content', 'is_approved', 'approved_by',
            'approved_by_username', 'approved_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'template_name', 'approved_by_username',
            'approved_at', 'created_at', 'updated_at'
        ]

class TranslationCacheSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le cache des traductions"""
    
    class Meta:
        model = TranslationCache
        fields = [
            'id', 'cache_key', 'language_code', 'content',
            'expires_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class BulkTranslationSerializer(serializers.Serializer):
    """Sérialiseur pour les opérations en lot sur les traductions"""
    translations = serializers.ListField(
        child=serializers.DictField(),
        help_text=_("Liste des traductions à traiter")
    )
    action = serializers.ChoiceField(
        choices=['create', 'update', 'delete', 'approve'],
        help_text=_("Action à effectuer sur les traductions")
    )
    language_code = serializers.CharField(
        max_length=2,
        help_text=_("Code de langue pour les traductions")
    )

class TranslationSearchSerializer(serializers.Serializer):
    """Sérialiseur pour la recherche de traductions"""
    query = serializers.CharField(
        max_length=200,
        help_text=_("Terme de recherche")
    )
    language_code = serializers.CharField(
        max_length=2,
        required=False,
        help_text=_("Code de langue pour filtrer les résultats")
    )
    category = serializers.CharField(
        max_length=50,
        required=False,
        help_text=_("Catégorie pour filtrer les résultats")
    )
    is_approved = serializers.BooleanField(
        required=False,
        help_text=_("Filtrer par statut d'approbation")
    )

class TranslationExportSerializer(serializers.Serializer):
    """Sérialiseur pour l'export des traductions"""
    format = serializers.ChoiceField(
        choices=['json', 'csv', 'xlsx', 'po'],
        default='json',
        help_text=_("Format d'export")
    )
    language_codes = serializers.ListField(
        child=serializers.CharField(max_length=2),
        required=False,
        help_text=_("Codes de langue à exporter")
    )
    categories = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        help_text=_("Catégories à exporter")
    )
    include_unapproved = serializers.BooleanField(
        default=False,
        help_text=_("Inclure les traductions non approuvées")
    )

class TranslationImportSerializer(serializers.Serializer):
    """Sérialiseur pour l'import des traductions"""
    file = serializers.FileField(
        help_text=_("Fichier à importer")
    )
    format = serializers.ChoiceField(
        choices=['json', 'csv', 'xlsx', 'po'],
        help_text=_("Format du fichier")
    )
    overwrite_existing = serializers.BooleanField(
        default=False,
        help_text=_("Écraser les traductions existantes")
    )
    auto_approve = serializers.BooleanField(
        default=False,
        help_text=_("Approuver automatiquement les traductions importées")
    )

class LanguageStatisticsSerializer(serializers.Serializer):
    """Sérialiseur pour les statistiques de langue"""
    language_code = serializers.CharField(max_length=2)
    total_translations = serializers.IntegerField()
    approved_translations = serializers.IntegerField()
    pending_translations = serializers.IntegerField()
    completion_percentage = serializers.FloatField()
    last_updated = serializers.DateTimeField()

class TranslationApprovalSerializer(serializers.Serializer):
    """Sérialiseur pour l'approbation des traductions"""
    translation_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text=_("IDs des traductions à approuver")
    )
    approve = serializers.BooleanField(
        default=True,
        help_text=_("Approuver ou désapprouver les traductions")
    )
    notes = serializers.CharField(
        max_length=500,
        required=False,
        help_text=_("Notes sur l'approbation")
    )
