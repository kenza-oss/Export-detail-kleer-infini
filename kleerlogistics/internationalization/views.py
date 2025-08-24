from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.db.models import Q, Count, F
from django.utils import timezone
from datetime import timedelta
import json
import csv
import io
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd

from .models import (
    TranslationCategory, TranslationKey, Translation, 
    UserLanguagePreference, TranslationTemplate, 
    TranslationTemplateContent, TranslationCache
)
from .serializers import (
    TranslationCategorySerializer, TranslationKeySerializer, TranslationSerializer,
    TranslationDetailSerializer, UserLanguagePreferenceSerializer,
    TranslationTemplateSerializer, TranslationTemplateContentSerializer,
    TranslationCacheSerializer, BulkTranslationSerializer, TranslationSearchSerializer,
    TranslationExportSerializer, TranslationImportSerializer, LanguageStatisticsSerializer,
    TranslationApprovalSerializer
)
from .utils import TranslationService

class TranslationCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet pour les catégories de traduction"""
    queryset = TranslationCategory.objects.all()
    serializer_class = TranslationCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'code']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Statistiques d'une catégorie"""
        category = self.get_object()
        stats = {
            'total_keys': category.translation_keys.count(),
            'total_translations': Translation.objects.filter(key__category=category).count(),
            'approved_translations': Translation.objects.filter(key__category=category, is_approved=True).count(),
            'languages_coverage': {}
        }
        
        for lang_code, lang_name in Translation.LANGUAGE_CHOICES:
            count = Translation.objects.filter(key__category=category, language_code=lang_code).count()
            approved_count = Translation.objects.filter(key__category=category, language_code=lang_code, is_approved=True).count()
            stats['languages_coverage'][lang_code] = {
                'name': lang_name,
                'total': count,
                'approved': approved_count,
                'percentage': (approved_count / stats['total_keys'] * 100) if stats['total_keys'] > 0 else 0
            }
        
        return Response(stats)

class TranslationKeyViewSet(viewsets.ModelViewSet):
    """ViewSet pour les clés de traduction"""
    queryset = TranslationKey.objects.select_related('category').prefetch_related('translations')
    serializer_class = TranslationKeySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['key', 'description', 'context']
    ordering_fields = ['key', 'created_at']
    ordering = ['key']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TranslationDetailSerializer
        return TranslationKeySerializer

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Créer plusieurs clés de traduction en lot"""
        serializer = self.get_serializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Recherche avancée de clés de traduction"""
        serializer = TranslationSearchSerializer(data=request.query_params)
        if serializer.is_valid():
            query = serializer.validated_data['query']
            language_code = serializer.validated_data.get('language_code')
            category = serializer.validated_data.get('category')
            is_approved = serializer.validated_data.get('is_approved')
            
            queryset = self.queryset.filter(
                Q(key__icontains=query) |
                Q(description__icontains=query) |
                Q(context__icontains=query)
            )
            
            if category:
                queryset = queryset.filter(category__code=category)
            
            if language_code:
                queryset = queryset.filter(translations__language_code=language_code)
            
            if is_approved is not None:
                queryset = queryset.filter(translations__is_approved=is_approved)
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TranslationViewSet(viewsets.ModelViewSet):
    """ViewSet pour les traductions"""
    queryset = Translation.objects.select_related('key', 'key__category', 'approved_by')
    serializer_class = TranslationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['key', 'language_code', 'is_approved']
    search_fields = ['text', 'key__key']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']

    @action(detail=False, methods=['post'])
    def bulk_operations(self, request):
        """Opérations en lot sur les traductions"""
        serializer = BulkTranslationSerializer(data=request.data)
        if serializer.is_valid():
            translations_data = serializer.validated_data['translations']
            action = serializer.validated_data['action']
            language_code = serializer.validated_data['language_code']
            
            results = []
            for translation_data in translations_data:
                try:
                    if action == 'create':
                        key = TranslationKey.objects.get(key=translation_data['key'])
                        translation, created = Translation.objects.get_or_create(
                            key=key,
                            language_code=language_code,
                            defaults={'text': translation_data['text']}
                        )
                        results.append({
                            'key': translation_data['key'],
                            'status': 'created' if created else 'exists',
                            'id': translation.id
                        })
                    
                    elif action == 'update':
                        key = TranslationKey.objects.get(key=translation_data['key'])
                        translation = Translation.objects.get(key=key, language_code=language_code)
                        translation.text = translation_data['text']
                        translation.save()
                        results.append({
                            'key': translation_data['key'],
                            'status': 'updated',
                            'id': translation.id
                        })
                    
                    elif action == 'approve':
                        translation = Translation.objects.get(id=translation_data['id'])
                        translation.is_approved = True
                        translation.approved_by = request.user
                        translation.approved_at = timezone.now()
                        translation.save()
                        results.append({
                            'key': translation.key.key,
                            'status': 'approved',
                            'id': translation.id
                        })
                
                except (TranslationKey.DoesNotExist, Translation.DoesNotExist) as e:
                    results.append({
                        'key': translation_data.get('key', 'unknown'),
                        'status': 'error',
                        'error': str(e)
                    })
            
            return Response({'results': results})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def approve_multiple(self, request):
        """Approuver plusieurs traductions"""
        serializer = TranslationApprovalSerializer(data=request.data)
        if serializer.is_valid():
            translation_ids = serializer.validated_data['translation_ids']
            approve = serializer.validated_data['approve']
            notes = serializer.validated_data.get('notes', '')
            
            translations = Translation.objects.filter(id__in=translation_ids)
            updated_count = translations.update(
                is_approved=approve,
                approved_by=request.user if approve else None,
                approved_at=timezone.now() if approve else None
            )
            
            return Response({
                'message': f'{updated_count} traductions {"approuvées" if approve else "désapprouvées"}',
                'updated_count': updated_count,
                'notes': notes
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Statistiques des traductions"""
        language_code = request.query_params.get('language_code')
        
        queryset = self.queryset
        if language_code:
            queryset = queryset.filter(language_code=language_code)
        
        stats = {
            'total_translations': queryset.count(),
            'approved_translations': queryset.filter(is_approved=True).count(),
            'pending_translations': queryset.filter(is_approved=False).count(),
            'by_language': {},
            'by_category': {},
            'recent_activity': {}
        }
        
        # Statistiques par langue
        for lang_code, lang_name in Translation.LANGUAGE_CHOICES:
            lang_queryset = self.queryset.filter(language_code=lang_code)
            stats['by_language'][lang_code] = {
                'name': lang_name,
                'total': lang_queryset.count(),
                'approved': lang_queryset.filter(is_approved=True).count(),
                'pending': lang_queryset.filter(is_approved=False).count()
            }
        
        # Statistiques par catégorie
        category_stats = self.queryset.values('key__category__name').annotate(
            total=Count('id'),
            approved=Count('id', filter=Q(is_approved=True))
        )
        for stat in category_stats:
            stats['by_category'][stat['key__category__name']] = {
                'total': stat['total'],
                'approved': stat['approved'],
                'pending': stat['total'] - stat['approved']
            }
        
        # Activité récente
        recent_translations = self.queryset.filter(
            updated_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-updated_at')[:10]
        
        stats['recent_activity'] = TranslationSerializer(recent_translations, many=True).data
        
        return Response(stats)

class UserLanguagePreferenceViewSet(viewsets.ModelViewSet):
    """ViewSet pour les préférences de langue des utilisateurs"""
    queryset = UserLanguagePreference.objects.all()
    serializer_class = UserLanguagePreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return UserLanguagePreference.objects.select_related('user')
        return UserLanguagePreference.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """Obtenir les préférences de l'utilisateur connecté"""
        try:
            preference = UserLanguagePreference.objects.get(user=request.user)
            serializer = self.get_serializer(preference)
            return Response(serializer.data)
        except UserLanguagePreference.DoesNotExist:
            # Créer des préférences par défaut
            preference = UserLanguagePreference.objects.create(
                user=request.user,
                preferred_language='fr',
                fallback_language='en'
            )
            serializer = self.get_serializer(preference)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def update_preferences(self, request):
        """Mettre à jour les préférences de langue"""
        try:
            preference = UserLanguagePreference.objects.get(user=request.user)
            serializer = self.get_serializer(preference, data=request.data, partial=True)
        except UserLanguagePreference.DoesNotExist:
            serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TranslationTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet pour les modèles de traduction"""
    queryset = TranslationTemplate.objects.select_related('category').prefetch_related('contents')
    serializer_class = TranslationTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['template_type', 'category', 'is_active']
    search_fields = ['name', 'key']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def render_template(self, request, pk=None):
        """Rendre un modèle avec des variables"""
        template = self.get_object()
        language_code = request.query_params.get('language_code', 'fr')
        variables = request.query_params.get('variables', '{}')
        
        try:
            variables_dict = json.loads(variables)
        except json.JSONDecodeError:
            return Response({'error': 'Variables invalides'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            content = template.contents.get(language_code=language_code)
            rendered_content = TranslationService.render_template(content.content, variables_dict)
            return Response({
                'template_name': template.name,
                'language_code': language_code,
                'rendered_content': rendered_content,
                'variables_used': list(variables_dict.keys())
            })
        except TranslationTemplateContent.DoesNotExist:
            return Response({'error': 'Contenu non trouvé pour cette langue'}, status=status.HTTP_404_NOT_FOUND)

class TranslationTemplateContentViewSet(viewsets.ModelViewSet):
    """ViewSet pour le contenu des modèles de traduction"""
    queryset = TranslationTemplateContent.objects.select_related('template', 'approved_by')
    serializer_class = TranslationTemplateContentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['template', 'language_code', 'is_approved']
    search_fields = ['subject', 'content']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']

class TranslationCacheViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour le cache des traductions (lecture seule)"""
    queryset = TranslationCache.objects.all()
    serializer_class = TranslationCacheSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['language_code']
    ordering_fields = ['created_at', 'expires_at']
    ordering = ['-created_at']

    @action(detail=False, methods=['post'])
    def clear_expired(self, request):
        """Nettoyer le cache expiré"""
        expired_count = TranslationCache.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()[0]
        
        return Response({
            'message': f'{expired_count} entrées de cache supprimées',
            'deleted_count': expired_count
        })

    @action(detail=False, methods=['post'])
    def clear_all(self, request):
        """Nettoyer tout le cache"""
        total_count = TranslationCache.objects.count()
        TranslationCache.objects.all().delete()
        
        return Response({
            'message': f'Tout le cache supprimé ({total_count} entrées)',
            'deleted_count': total_count
        })

class TranslationExportImportViewSet(viewsets.ViewSet):
    """ViewSet pour l'export et l'import des traductions"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def export(self, request):
        """Exporter les traductions"""
        serializer = TranslationExportSerializer(data=request.data)
        if serializer.is_valid():
            format_type = serializer.validated_data['format']
            language_codes = serializer.validated_data.get('language_codes', ['fr', 'en', 'ar'])
            categories = serializer.validated_data.get('categories', [])
            include_unapproved = serializer.validated_data.get('include_unapproved', False)
            
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
                
                response = Response(data)
                response['Content-Disposition'] = f'attachment; filename="translations_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
                return response
            
            elif format_type == 'csv':
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
                
                response = Response(output.getvalue())
                response['Content-Type'] = 'text/csv'
                response['Content-Disposition'] = f'attachment; filename="translations_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
                return response
            
            elif format_type == 'xlsx':
                wb = Workbook()
                ws = wb.active
                ws.title = "Translations"
                
                headers = ['Key', 'Category', 'Language', 'Text', 'Approved', 'Context']
                ws.append(headers)
                
                for translation in queryset:
                    ws.append([
                        translation.key.key,
                        translation.key.category.code,
                        translation.language_code,
                        translation.text,
                        translation.is_approved,
                        translation.key.context
                    ])
                
                output = io.BytesIO()
                wb.save(output)
                output.seek(0)
                
                response = Response(output.getvalue())
                response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                response['Content-Disposition'] = f'attachment; filename="translations_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
                return response
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def import_translations(self, request):
        """Importer des traductions"""
        serializer = TranslationImportSerializer(data=request.data)
        if serializer.is_valid():
            file_obj = serializer.validated_data['file']
            format_type = serializer.validated_data['format']
            overwrite_existing = serializer.validated_data.get('overwrite_existing', False)
            auto_approve = serializer.validated_data.get('auto_approve', False)
            
            results = {'imported': 0, 'updated': 0, 'errors': []}
            
            try:
                if format_type == 'json':
                    data = json.load(file_obj)
                    for item in data:
                        try:
                            key, created = TranslationKey.objects.get_or_create(
                                key=item['key'],
                                defaults={
                                    'category': TranslationCategory.objects.get(code=item['category']),
                                    'context': item.get('context', '')
                                }
                            )
                            
                            translation, created = Translation.objects.get_or_create(
                                key=key,
                                language_code=item['language_code'],
                                defaults={'text': item['text']}
                            )
                            
                            if not created and overwrite_existing:
                                translation.text = item['text']
                                translation.save()
                                results['updated'] += 1
                            elif created:
                                results['imported'] += 1
                            
                            if auto_approve:
                                translation.is_approved = True
                                translation.approved_by = request.user
                                translation.approved_at = timezone.now()
                                translation.save()
                        
                        except Exception as e:
                            results['errors'].append(f"Erreur pour {item.get('key', 'unknown')}: {str(e)}")
                
                elif format_type == 'csv':
                    content = file_obj.read().decode('utf-8')
                    reader = csv.DictReader(io.StringIO(content))
                    
                    for row in reader:
                        try:
                            key, created = TranslationKey.objects.get_or_create(
                                key=row['Key'],
                                defaults={
                                    'category': TranslationCategory.objects.get(code=row['Category']),
                                    'context': row.get('Context', '')
                                }
                            )
                            
                            translation, created = Translation.objects.get_or_create(
                                key=key,
                                language_code=row['Language'],
                                defaults={'text': row['Text']}
                            )
                            
                            if not created and overwrite_existing:
                                translation.text = row['Text']
                                translation.save()
                                results['updated'] += 1
                            elif created:
                                results['imported'] += 1
                            
                            if auto_approve:
                                translation.is_approved = True
                                translation.approved_by = request.user
                                translation.approved_at = timezone.now()
                                translation.save()
                        
                        except Exception as e:
                            results['errors'].append(f"Erreur pour {row.get('Key', 'unknown')}: {str(e)}")
            
            except Exception as e:
                results['errors'].append(f"Erreur générale: {str(e)}")
            
            return Response(results)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TranslationServiceViewSet(viewsets.ViewSet):
    """ViewSet pour les services de traduction"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def get_translation(self, request):
        """Obtenir une traduction par clé et langue"""
        key = request.query_params.get('key')
        language_code = request.query_params.get('language_code', 'fr')
        
        if not key:
            return Response({'error': 'Clé requise'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            translation_key = TranslationKey.objects.get(key=key)
            translation = translation_key.get_translation(language_code)
            return Response({
                'key': key,
                'language_code': language_code,
                'text': translation,
                'is_approved': translation_key.translations.filter(
                    language_code=language_code, is_approved=True
                ).exists()
            })
        except TranslationKey.DoesNotExist:
            return Response({'error': 'Clé non trouvée'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def get_multiple_translations(self, request):
        """Obtenir plusieurs traductions"""
        keys = request.query_params.getlist('keys')
        language_code = request.query_params.get('language_code', 'fr')
        
        if not keys:
            return Response({'error': 'Clés requises'}, status=status.HTTP_400_BAD_REQUEST)
        
        translations = {}
        for key in keys:
            try:
                translation_key = TranslationKey.objects.get(key=key)
                translation = translation_key.get_translation(language_code)
                translations[key] = {
                    'text': translation,
                    'is_approved': translation_key.translations.filter(
                        language_code=language_code, is_approved=True
                    ).exists()
                }
            except TranslationKey.DoesNotExist:
                translations[key] = {'text': key, 'is_approved': False}
        
        return Response({
            'language_code': language_code,
            'translations': translations
        })

    @action(detail=False, methods=['get'])
    def language_statistics(self, request):
        """Statistiques par langue"""
        stats = []
        
        for lang_code, lang_name in Translation.LANGUAGE_CHOICES:
            total = Translation.objects.filter(language_code=lang_code).count()
            approved = Translation.objects.filter(language_code=lang_code, is_approved=True).count()
            pending = total - approved
            completion = (approved / total * 100) if total > 0 else 0
            
            last_updated = Translation.objects.filter(
                language_code=lang_code
            ).order_by('-updated_at').first()
            
            stats.append({
                'language_code': lang_code,
                'language_name': lang_name,
                'total_translations': total,
                'approved_translations': approved,
                'pending_translations': pending,
                'completion_percentage': round(completion, 2),
                'last_updated': last_updated.updated_at if last_updated else None
            })
        
        return Response(stats)
