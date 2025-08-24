from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    TranslationCategory, TranslationKey, Translation, 
    UserLanguagePreference, TranslationTemplate, 
    TranslationTemplateContent, TranslationCache
)

@admin.register(TranslationCategory)
class TranslationCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'keys_count', 'translations_count', 'completion_percentage']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    def keys_count(self, obj):
        return obj.translation_keys.count()
    keys_count.short_description = _('Clés')
    
    def translations_count(self, obj):
        return Translation.objects.filter(key__category=obj).count()
    translations_count.short_description = _('Traductions')
    
    def completion_percentage(self, obj):
        total_keys = obj.translation_keys.count()
        if total_keys == 0:
            return "0%"
        
        approved_translations = Translation.objects.filter(
            key__category=obj, 
            is_approved=True
        ).count()
        
        percentage = (approved_translations / (total_keys * 3)) * 100  # 3 langues
        return f"{percentage:.1f}%"
    completion_percentage.short_description = _('Complétude')
    
    def changelist_view(self, request, extra_context=None):
        """Vue personnalisée avec dashboard pour les catégories"""
        # Statistiques générales
        total_keys = TranslationKey.objects.count()
        total_translations = Translation.objects.count()
        approved_translations = Translation.objects.filter(is_approved=True).count()
        
        # Statistiques par langue
        language_stats = {}
        for lang_code, lang_name in Translation.LANGUAGE_CHOICES:
            lang_count = Translation.objects.filter(language_code=lang_code).count()
            lang_approved = Translation.objects.filter(language_code=lang_code, is_approved=True).count()
            language_stats[lang_code] = {
                'name': lang_name,
                'total': lang_count,
                'approved': lang_approved,
                'percentage': (lang_approved / total_keys * 100) if total_keys > 0 else 0
            }
        
        # Statistiques par catégorie
        category_stats = Translation.objects.values('key__category__name').annotate(
            total=Count('id'),
            approved=Count('id', filter=Q(is_approved=True))
        )
        
        # Activité récente
        recent_translations = Translation.objects.filter(
            updated_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-updated_at')[:10]
        
        # Traductions en attente d'approbation
        pending_translations = Translation.objects.filter(is_approved=False).count()
        
        extra_context = extra_context or {}
        extra_context.update({
            'total_keys': total_keys,
            'total_translations': total_translations,
            'approved_translations': approved_translations,
            'pending_translations': pending_translations,
            'language_stats': language_stats,
            'category_stats': category_stats,
            'recent_translations': recent_translations,
            'completion_percentage': (approved_translations / (total_keys * 3) * 100) if total_keys > 0 else 0
        })
        
        return super().changelist_view(request, extra_context)

@admin.register(TranslationKey)
class TranslationKeyAdmin(admin.ModelAdmin):
    list_display = ['key', 'category', 'is_active', 'translations_count', 'approved_count', 'missing_languages']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['key', 'description', 'context']
    ordering = ['key']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['activate_keys', 'deactivate_keys', 'create_missing_translations']
    
    def translations_count(self, obj):
        return obj.translations.count()
    translations_count.short_description = _('Traductions')
    
    def approved_count(self, obj):
        return obj.translations.filter(is_approved=True).count()
    approved_count.short_description = _('Approuvées')
    
    def missing_languages(self, obj):
        existing_langs = set(obj.translations.values_list('language_code', flat=True))
        all_langs = {'fr', 'en', 'ar'}
        missing = all_langs - existing_langs
        if missing:
            return ', '.join(missing)
        return _('Aucune')
    missing_languages.short_description = _('Langues manquantes')
    
    def activate_keys(self, request, queryset):
        updated = queryset.update(is_active=True)
        messages.success(request, f'{updated} clés activées.')
    activate_keys.short_description = _('Activer les clés sélectionnées')
    
    def deactivate_keys(self, request, queryset):
        updated = queryset.update(is_active=False)
        messages.success(request, f'{updated} clés désactivées.')
    deactivate_keys.short_description = _('Désactiver les clés sélectionnées')
    
    def create_missing_translations(self, request, queryset):
        created_count = 0
        for key in queryset:
            existing_langs = set(key.translations.values_list('language_code', flat=True))
            for lang_code, lang_name in Translation.LANGUAGE_CHOICES:
                if lang_code not in existing_langs:
                    Translation.objects.create(
                        key=key,
                        language_code=lang_code,
                        text=f"[{lang_code.upper()}] {key.key}",
                        is_approved=False
                    )
                    created_count += 1
        
        messages.success(request, f'{created_count} traductions créées.')
    create_missing_translations.short_description = _('Créer les traductions manquantes')

@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ['key', 'language_code', 'text_preview', 'is_approved', 'approved_by', 'updated_at']
    list_filter = ['language_code', 'is_approved', 'key__category', 'created_at']
    search_fields = ['text', 'key__key']
    ordering = ['-updated_at']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_translations', 'unapprove_translations', 'delete_translations']
    
    def text_preview(self, obj):
        preview = obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
        return format_html('<span title="{}">{}</span>', obj.text, preview)
    text_preview.short_description = _('Texte')
    
    def approve_translations(self, request, queryset):
        updated = queryset.update(
            is_approved=True,
            approved_by=request.user,
            approved_at=timezone.now()
        )
        messages.success(request, f'{updated} traductions approuvées.')
    approve_translations.short_description = _('Approuver les traductions sélectionnées')
    
    def unapprove_translations(self, request, queryset):
        updated = queryset.update(
            is_approved=False,
            approved_by=None,
            approved_at=None
        )
        messages.success(request, f'{updated} traductions désapprouvées.')
    unapprove_translations.short_description = _('Désapprouver les traductions sélectionnées')
    
    def delete_translations(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        messages.success(request, f'{count} traductions supprimées.')
    delete_translations.short_description = _('Supprimer les traductions sélectionnées')

@admin.register(UserLanguagePreference)
class UserLanguagePreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_language', 'fallback_language', 'created_at']
    list_filter = ['preferred_language', 'fallback_language', 'created_at']
    search_fields = ['user__username', 'user__email']
    ordering = ['user__username']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(TranslationTemplate)
class TranslationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'category', 'is_active', 'contents_count', 'variables_count']
    list_filter = ['template_type', 'category', 'is_active', 'created_at']
    search_fields = ['name', 'key']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    def contents_count(self, obj):
        return obj.contents.count()
    contents_count.short_description = _('Contenus')
    
    def variables_count(self, obj):
        return len(obj.variables) if obj.variables else 0
    variables_count.short_description = _('Variables')

@admin.register(TranslationTemplateContent)
class TranslationTemplateContentAdmin(admin.ModelAdmin):
    list_display = ['template', 'language_code', 'subject_preview', 'is_approved', 'approved_by', 'updated_at']
    list_filter = ['language_code', 'is_approved', 'template__template_type', 'created_at']
    search_fields = ['subject', 'content', 'template__name']
    ordering = ['-updated_at']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_contents', 'unapprove_contents']
    
    def subject_preview(self, obj):
        preview = obj.subject[:30] + '...' if len(obj.subject) > 30 else obj.subject
        return format_html('<span title="{}">{}</span>', obj.subject, preview)
    subject_preview.short_description = _('Sujet')
    
    def approve_contents(self, request, queryset):
        updated = queryset.update(
            is_approved=True,
            approved_by=request.user,
            approved_at=timezone.now()
        )
        messages.success(request, f'{updated} contenus approuvés.')
    approve_contents.short_description = _('Approuver les contenus sélectionnés')
    
    def unapprove_contents(self, request, queryset):
        updated = queryset.update(
            is_approved=False,
            approved_by=None,
            approved_at=None
        )
        messages.success(request, f'{updated} contenus désapprouvés.')
    unapprove_contents.short_description = _('Désapprouver les contenus sélectionnés')

@admin.register(TranslationCache)
class TranslationCacheAdmin(admin.ModelAdmin):
    list_display = ['cache_key', 'language_code', 'content_preview', 'expires_at', 'is_expired']
    list_filter = ['language_code', 'expires_at', 'created_at']
    search_fields = ['cache_key', 'content']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    actions = ['clear_expired_cache', 'clear_all_cache']
    
    def content_preview(self, obj):
        preview = obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
        return format_html('<span title="{}">{}</span>', obj.content, preview)
    content_preview.short_description = _('Contenu')
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = _('Expiré')
    
    def clear_expired_cache(self, request, queryset):
        expired_count = TranslationCache.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()[0]
        messages.success(request, f'{expired_count} entrées de cache expirées supprimées.')
    clear_expired_cache.short_description = _('Nettoyer le cache expiré')
    
    def clear_all_cache(self, request, queryset):
        total_count = TranslationCache.objects.count()
        TranslationCache.objects.all().delete()
        messages.success(request, f'Tout le cache supprimé ({total_count} entrées).')
    clear_all_cache.short_description = _('Nettoyer tout le cache')



# Actions personnalisées pour l'admin
@admin.action(description=_('Exporter les traductions en JSON'))
def export_translations_json(modeladmin, request, queryset):
    from .utils import TranslationService
    import json
    
    data = []
    for translation in queryset:
        data.append({
            'key': translation.key.key,
            'category': translation.key.category.code,
            'language_code': translation.language_code,
            'text': translation.text,
            'is_approved': translation.is_approved,
            'context': translation.key.context
        })
    
    response = HttpResponseRedirect(request.get_full_path())
    response['Content-Type'] = 'application/json'
    response['Content-Disposition'] = f'attachment; filename="translations_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
    response.write(json.dumps(data, ensure_ascii=False, indent=2))
    return response

# Ajouter l'action aux modèles appropriés
TranslationAdmin.actions = list(TranslationAdmin.actions) + [export_translations_json]
