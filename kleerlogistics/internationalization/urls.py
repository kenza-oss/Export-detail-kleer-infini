"""
URLs for internationalization app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.TranslationCategoryViewSet)
router.register(r'keys', views.TranslationKeyViewSet)
router.register(r'translations', views.TranslationViewSet)
router.register(r'templates', views.TranslationTemplateViewSet)
router.register(r'template-contents', views.TranslationTemplateContentViewSet)
router.register(r'cache', views.TranslationCacheViewSet)

urlpatterns = [
    # Routes principales de l'API
    path('', include(router.urls)),
    
    # Routes spécialisées
    path('export-import/', include([
        path('export/', views.TranslationExportImportViewSet.as_view({'post': 'export'}), name='translation-export'),
        path('import/', views.TranslationExportImportViewSet.as_view({'post': 'import_translations'}), name='translation-import'),
    ])),
    
    path('services/', include([
        path('get-translation/', views.TranslationServiceViewSet.as_view({'get': 'get_translation'}), name='get-translation'),
        path('get-multiple-translations/', views.TranslationServiceViewSet.as_view({'get': 'get_multiple_translations'}), name='get-multiple-translations'),
        path('language-statistics/', views.TranslationServiceViewSet.as_view({'get': 'language_statistics'}), name='language-statistics'),
    ])),
    
    # Routes pour les préférences utilisateur
    path('user-preferences/', include([
        path('my-preferences/', views.UserLanguagePreferenceViewSet.as_view({'get': 'my_preferences'}), name='my-preferences'),
        path('update-preferences/', views.UserLanguagePreferenceViewSet.as_view({'post': 'update_preferences'}), name='update-preferences'),
    ])),
    
    # Routes pour les opérations en lot
    path('bulk/', include([
        path('keys/', views.TranslationKeyViewSet.as_view({'post': 'bulk_create'}), name='bulk-create-keys'),
        path('translations/', views.TranslationViewSet.as_view({'post': 'bulk_operations'}), name='bulk-operations'),
        path('approve/', views.TranslationViewSet.as_view({'post': 'approve_multiple'}), name='approve-multiple'),
    ])),
    
    # Routes pour la recherche
    path('search/', include([
        path('keys/', views.TranslationKeyViewSet.as_view({'get': 'search'}), name='search-keys'),
    ])),
    
    # Routes pour les statistiques
    path('statistics/', include([
        path('translations/', views.TranslationViewSet.as_view({'get': 'statistics'}), name='translation-statistics'),
        path('categories/<int:pk>/', views.TranslationCategoryViewSet.as_view({'get': 'statistics'}), name='category-statistics'),
    ])),
    
    # Routes pour les modèles de traduction
    path('templates/', include([
        path('<int:pk>/render/', views.TranslationTemplateViewSet.as_view({'get': 'render_template'}), name='render-template'),
    ])),
    
    # Routes pour le cache
    path('cache/', include([
        path('clear-expired/', views.TranslationCacheViewSet.as_view({'post': 'clear_expired'}), name='clear-expired-cache'),
        path('clear-all/', views.TranslationCacheViewSet.as_view({'post': 'clear_all'}), name='clear-all-cache'),
    ])),
] 