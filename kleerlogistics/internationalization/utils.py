from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import re
import json
from typing import Dict, List, Optional, Any

from .models import TranslationKey, Translation, UserLanguagePreference

class TranslationService:
    """
    Service centralisé pour la gestion des traductions
    """
    
    @staticmethod
    def get_translation(key: str, language_code: str = 'fr', user=None, allow_fallback: bool = True) -> str:
        """
        Récupère une traduction par clé et langue
        
        Args:
            key: Clé de traduction
            language_code: Code de langue (fr, en, ar)
            user: Utilisateur pour les préférences de langue
            allow_fallback: Si le fallback est autorisé
            
        Returns:
            Texte traduit ou clé si non trouvé
        """
        # Vérifier le cache d'abord
        cache_key = f"translation_{key}_{language_code}"
        cached_translation = cache.get(cache_key)
        
        if cached_translation is not None:
            return cached_translation
        
        try:
            translation_key = TranslationKey.objects.get(key=key, is_active=True)
            
            # Initialiser result avec la clé par défaut
            result = key
            
            # 1. Essayer d'abord la langue demandée
            translation = translation_key.translations.filter(
                language_code=language_code,
                is_approved=True
            ).first()
            
            if translation:
                result = translation.text
            elif allow_fallback:
                # 2. Si pas de traduction dans la langue demandée et fallback autorisé, essayer le fallback utilisateur
                if user and hasattr(user, 'language_preference'):
                    fallback_lang = user.language_preference.fallback_language
                    if fallback_lang != language_code:
                        fallback_translation = translation_key.translations.filter(
                            language_code=fallback_lang,
                            is_approved=True
                        ).first()
                        if fallback_translation:
                            result = fallback_translation.text
                        else:
                            # 3. Si pas de fallback utilisateur, essayer la langue préférée de l'utilisateur
                            preferred_lang = user.language_preference.preferred_language
                            if preferred_lang != language_code and preferred_lang != fallback_lang:
                                preferred_translation = translation_key.translations.filter(
                                    language_code=preferred_lang,
                                    is_approved=True
                                ).first()
                                if preferred_translation:
                                    result = preferred_translation.text
                                else:
                                    # 4. Si pas de langue préférée, essayer le français par défaut
                                    # Mais seulement si ce n'est pas la langue demandée
                                    if 'fr' != language_code:
                                        default_translation = translation_key.translations.filter(
                                            language_code='fr',
                                            is_approved=True
                                        ).first()
                                        if default_translation:
                                            result = default_translation.text
                                        else:
                                            result = key
                                    else:
                                        result = key
                            else:
                                # 5. Si la langue préférée est la même, essayer le français
                                # Mais seulement si ce n'est pas la langue demandée
                                if 'fr' != language_code:
                                    default_translation = translation_key.translations.filter(
                                        language_code='fr',
                                        is_approved=True
                                    ).first()
                                    if default_translation:
                                        result = default_translation.text
                                    else:
                                        result = key
                                else:
                                    result = key
                    else:
                        # 6. Si le fallback est la même langue, essayer la langue préférée puis le français
                        preferred_lang = user.language_preference.preferred_language
                        if preferred_lang != language_code:
                            preferred_translation = translation_key.translations.filter(
                                language_code=preferred_lang,
                                is_approved=True
                            ).first()
                            if preferred_translation:
                                result = preferred_translation.text
                            else:
                                # Essayer le français seulement si ce n'est pas la langue demandée
                                if 'fr' != language_code:
                                    default_translation = translation_key.translations.filter(
                                        language_code='fr',
                                        is_approved=True
                                    ).first()
                                    if default_translation:
                                        result = default_translation.text
                                    else:
                                        result = key
                                else:
                                    result = key
                        else:
                            # 7. Si tout est la même langue, essayer le français
                            # Mais seulement si ce n'est pas la langue demandée
                            if 'fr' != language_code:
                                default_translation = translation_key.translations.filter(
                                    language_code='fr',
                                    is_approved=True
                                ).first()
                                if default_translation:
                                    result = default_translation.text
                                else:
                                    result = key
                            else:
                                result = key
                else:
                    # 8. Si pas d'utilisateur, essayer le français
                    # Mais seulement si ce n'est pas la langue demandée
                    if 'fr' != language_code:
                        default_translation = translation_key.translations.filter(
                            language_code='fr',
                            is_approved=True
                        ).first()
                        if default_translation:
                            result = default_translation.text
                        else:
                            result = key
                    else:
                        result = key
            else:
                # Si pas de fallback autorisé, retourner la clé
                result = key
            
            # Mettre en cache pour 1 heure
            cache.set(cache_key, result, 3600)
            return result
            
        except TranslationKey.DoesNotExist:
            return key
    
    @staticmethod
    def get_multiple_translations(keys: List[str], language_code: str = 'fr', user=None) -> Dict[str, str]:
        """
        Récupère plusieurs traductions en une seule requête
        
        Args:
            keys: Liste des clés de traduction
            language_code: Code de langue
            user: Utilisateur pour les préférences de langue
            
        Returns:
            Dictionnaire {clé: traduction}
        """
        if not keys:
            return {}
        
        # Vérifier le cache pour toutes les clés
        cache_keys = [f"translation_{key}_{language_code}" for key in keys]
        cached_results = cache.get_many(cache_keys)
        
        # Séparer les clés trouvées et non trouvées
        found_keys = []
        missing_keys = []
        result = {}
        
        for key in keys:
            cache_key = f"translation_{key}_{language_code}"
            if cache_key in cached_results:
                result[key] = cached_results[cache_key]
            else:
                missing_keys.append(key)
        
        if missing_keys:
            # Récupérer les traductions manquantes depuis la base de données
            translation_keys = TranslationKey.objects.filter(
                key__in=missing_keys,
                is_active=True
            ).prefetch_related('translations')
            
            for translation_key in translation_keys:
                translation = translation_key.translations.filter(
                    language_code=language_code,
                    is_approved=True
                ).first()
                
                if translation:
                    result[translation_key.key] = translation.text
                else:
                    # Essayer la langue de secours
                    if user and hasattr(user, 'language_preference'):
                        fallback_lang = user.language_preference.fallback_language
                        if fallback_lang != language_code:
                            fallback_translation = translation_key.translations.filter(
                                language_code=fallback_lang,
                                is_approved=True
                            ).first()
                            if fallback_translation:
                                result[translation_key.key] = fallback_translation.text
                            else:
                                result[translation_key.key] = translation_key.key
                        else:
                            result[translation_key.key] = translation_key.key
                    else:
                        result[translation_key.key] = translation_key.key
                
                # Mettre en cache
                cache_key = f"translation_{translation_key.key}_{language_code}"
                cache.set(cache_key, result[translation_key.key], 3600)
        
        return result
    
    @staticmethod
    def render_template(template_content: str, variables: Dict[str, Any]) -> str:
        """
        Rend un modèle de traduction avec des variables
        
        Args:
            template_content: Contenu du modèle avec variables {{variable}}
            variables: Dictionnaire des variables
            
        Returns:
            Contenu rendu
        """
        if not variables:
            return template_content
        
        # Remplacer les variables {{variable}}
        pattern = r'\{\{(\w+)\}\}'
        
        def replace_variable(match):
            var_name = match.group(1)
            return str(variables.get(var_name, f'{{{{{var_name}}}}}'))
        
        return re.sub(pattern, replace_variable, template_content)
    
    @staticmethod
    def get_user_language(user) -> str:
        """
        Récupère la langue préférée d'un utilisateur
        
        Args:
            user: Utilisateur
            
        Returns:
            Code de langue
        """
        if not user or not user.is_authenticated:
            return 'fr'
        
        try:
            preference = user.language_preference
            return preference.preferred_language
        except UserLanguagePreference.DoesNotExist:
            return 'fr'
    
    @staticmethod
    def detect_language_from_request(request) -> str:
        """
        Détecte la langue à partir de la requête HTTP
        
        Args:
            request: Requête Django
            
        Returns:
            Code de langue
        """
        # 1. Vérifier l'utilisateur connecté
        if hasattr(request, 'user') and request.user.is_authenticated:
            return TranslationService.get_user_language(request.user)
        
        # 2. Vérifier le paramètre de langue dans l'URL
        lang_param = request.GET.get('lang') or request.POST.get('lang')
        if lang_param in ['fr', 'en', 'ar']:
            return lang_param
        
        # 3. Vérifier l'en-tête Accept-Language
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        if accept_language:
            # Parser l'en-tête Accept-Language
            languages = accept_language.split(',')
            for lang in languages:
                lang_code = lang.split(';')[0].strip()[:2].lower()
                if lang_code in ['fr', 'en', 'ar']:
                    return lang_code
        
        # 4. Langue par défaut
        return 'fr'
    
    @staticmethod
    def create_translation_key(key: str, category_code: str, description: str = '', context: str = '') -> TranslationKey:
        """
        Crée une nouvelle clé de traduction
        
        Args:
            key: Clé de traduction
            category_code: Code de la catégorie
            description: Description de la clé
            context: Contexte d'utilisation
            
        Returns:
            Objet TranslationKey créé
        """
        from .models import TranslationCategory
        
        category, created = TranslationCategory.objects.get_or_create(
            code=category_code,
            defaults={'name': category_code.title(), 'description': f'Catégorie {category_code}'}
        )
        
        translation_key, created = TranslationKey.objects.get_or_create(
            key=key,
            defaults={
                'category': category,
                'description': description,
                'context': context
            }
        )
        
        return translation_key
    
    @staticmethod
    def add_translation(key: str, language_code: str, text: str, is_approved: bool = False, approved_by=None) -> Translation:
        """
        Ajoute une traduction pour une clé
        
        Args:
            key: Clé de traduction
            language_code: Code de langue
            text: Texte traduit
            is_approved: Si la traduction est approuvée
            approved_by: Utilisateur qui approuve
            
        Returns:
            Objet Translation créé
        """
        translation_key = TranslationKey.objects.get(key=key)
        
        translation, created = Translation.objects.get_or_create(
            key=translation_key,
            language_code=language_code,
            defaults={
                'text': text,
                'is_approved': is_approved,
                'approved_by': approved_by,
                'approved_at': timezone.now() if is_approved and approved_by else None
            }
        )
        
        if not created:
            translation.text = text
            translation.is_approved = is_approved
            translation.approved_by = approved_by
            translation.approved_at = timezone.now() if is_approved and approved_by else None
            translation.save()
        
        # Invalider le cache
        cache_key = f"translation_{key}_{language_code}"
        cache.delete(cache_key)
        
        return translation
    
    @staticmethod
    def get_translation_statistics(language_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Récupère les statistiques des traductions
        
        Args:
            language_code: Code de langue optionnel pour filtrer
            
        Returns:
            Dictionnaire de statistiques
        """
        queryset = Translation.objects.all()
        if language_code:
            queryset = queryset.filter(language_code=language_code)
        
        stats = {
            'total_translations': queryset.count(),
            'approved_translations': queryset.filter(is_approved=True).count(),
            'pending_translations': queryset.filter(is_approved=False).count(),
            'by_language': {},
            'by_category': {},
            'recent_activity': []
        }
        
        # Statistiques par langue
        for lang_code, lang_name in Translation.LANGUAGE_CHOICES:
            lang_queryset = Translation.objects.filter(language_code=lang_code)
            stats['by_language'][lang_code] = {
                'name': lang_name,
                'total': lang_queryset.count(),
                'approved': lang_queryset.filter(is_approved=True).count(),
                'pending': lang_queryset.filter(is_approved=False).count()
            }
        
        # Statistiques par catégorie
        from django.db.models import Count, Q
        category_stats = Translation.objects.values('key__category__name').annotate(
            total=Count('id'),
            approved=Count('id', filter=Q(is_approved=True))
        )
        
        for stat in category_stats:
            category_name = stat['key__category__name'] or 'Sans catégorie'
            stats['by_category'][category_name] = {
                'total': stat['total'],
                'approved': stat['approved'],
                'pending': stat['total'] - stat['approved']
            }
        
        # Activité récente
        recent_translations = Translation.objects.filter(
            updated_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-updated_at')[:10]
        
        stats['recent_activity'] = [
            {
                'key': t.key.key,
                'language_code': t.language_code,
                'text': t.text[:50] + '...' if len(t.text) > 50 else t.text,
                'is_approved': t.is_approved,
                'updated_at': t.updated_at
            }
            for t in recent_translations
        ]
        
        return stats
    
    @staticmethod
    def export_translations(format_type: str = 'json', language_codes: List[str] = None, 
                           categories: List[str] = None, include_unapproved: bool = False) -> str:
        """
        Exporte les traductions dans différents formats
        
        Args:
            format_type: Format d'export (json, csv, xlsx)
            language_codes: Codes de langue à exporter
            categories: Catégories à exporter
            include_unapproved: Inclure les traductions non approuvées
            
        Returns:
            Contenu exporté
        """
        if language_codes is None:
            language_codes = ['fr', 'en', 'ar']
        
        queryset = Translation.objects.filter(language_code__in=language_codes)
        
        if categories:
            queryset = queryset.filter(key__category__code__in=categories)
        
        if not include_unapproved:
            queryset = queryset.filter(is_approved=True)
        
        if format_type == 'json':
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
            return json.dumps(data, ensure_ascii=False, indent=2)
        
        elif format_type == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Key', 'Category', 'Language', 'Text', 'Approved', 'Context'])
            
            for translation in queryset:
                writer.writerow([
                    translation.key.key,
                    translation.key.category.code,
                    translation.language_code,
                    translation.text,
                    translation.is_approved,
                    translation.key.context
                ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Format non supporté: {format_type}")
    
    @staticmethod
    def clear_cache(language_code: Optional[str] = None):
        """
        Nettoie le cache des traductions
        
        Args:
            language_code: Code de langue optionnel pour nettoyer spécifiquement
        """
        if language_code:
            # Nettoyer le cache pour une langue spécifique
            pattern = f"translation_*_{language_code}"
            # Note: Django cache ne supporte pas les patterns, donc on nettoie tout
            cache.clear()
        else:
            # Nettoyer tout le cache
            cache.clear()

class TranslationMiddleware:
    """
    Middleware pour détecter automatiquement la langue
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Détecter la langue
        language_code = TranslationService.detect_language_from_request(request)
        
        # Ajouter la langue à la requête
        request.detected_language = language_code
        
        response = self.get_response(request)
        return response

class TranslationContext:
    """
    Contexte pour les traductions dans les templates
    """
    
    def __init__(self, language_code: str = 'fr', user=None):
        self.language_code = language_code
        self.user = user
    
    def get(self, key: str) -> str:
        """Récupère une traduction"""
        return TranslationService.get_translation(key, self.language_code, self.user)
    
    def get_multiple(self, keys: List[str]) -> Dict[str, str]:
        """Récupère plusieurs traductions"""
        return TranslationService.get_multiple_translations(keys, self.language_code, self.user)
    
    def render_template(self, template_key: str, variables: Dict[str, Any]) -> str:
        """Rend un modèle de traduction"""
        from .models import TranslationTemplate, TranslationTemplateContent
        
        try:
            template = TranslationTemplate.objects.get(key=template_key, is_active=True)
            content = template.contents.get(language_code=self.language_code)
            return TranslationService.render_template(content.content, variables)
        except (TranslationTemplate.DoesNotExist, TranslationTemplateContent.DoesNotExist):
            return template_key
