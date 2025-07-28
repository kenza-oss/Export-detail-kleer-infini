"""
URLs for admin_panel app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'dashboard', views.DashboardViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 