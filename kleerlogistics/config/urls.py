"""
Main URL configuration for KleerLogistics project
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Health Check View
def health_check(request):
    """Health check endpoint for monitoring."""
    return JsonResponse({
        'status': 'healthy',
        'service': 'kleerlogistics',
        'version': '1.0.0'
    })

# Root URL View - Redirect to API documentation
def root_redirect(request):
    """Redirect root URL to API documentation."""
    return redirect('schema-swagger-ui')

# Favicon View
def favicon(request):
    """Handle favicon requests."""
    return HttpResponse(status=204)  # No content response

# Swagger Schema View
schema_view = get_schema_view(
    openapi.Info(
        title="KleerLogistics API",
        default_version='v1',
        description="API pour la plateforme d'envoi collaboratif KleerLogistics",
        terms_of_service="https://www.kleerinfini.com/terms/",
        contact=openapi.Contact(email="contact@kleerinfini.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Root URL - Redirect to API documentation
    path('', root_redirect, name='root'),
    
    # Favicon
    path('favicon.ico', favicon, name='favicon'),
    
    # Health Check
    path('health/', health_check, name='health_check'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API URLs
    path('api/v1/', include([
        path('users/', include('users.urls')),
        path('shipments/', include('shipments.urls')),
        path('trips/', include('trips.urls')),
        path('matching/', include('matching.urls')),
        path('payments/', include('payments.urls')),
        #path('documents/', include('documents.urls')),
        path('verification/', include('verification.urls')),
        path('admin/', include('admin_panel.urls')),
        path('notifications/', include('notifications.urls')),
        path('analytics/', include('analytics.urls')),
        path('ratings/', include('ratings.urls')),
        path('internationalization/', include('internationalization.urls')),
    ])),
]

# Debug Toolbar URLs (only in development)
if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
