"""
Permissions personnalisées pour la gestion des rôles
"""

from rest_framework import permissions
from .models import User

class IsAdminUser(permissions.BasePermission):
    """
    Permission pour les administrateurs uniquement.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_admin or request.user.is_superuser)
        )

class IsSender(permissions.BasePermission):
    """
    Permission pour les expéditeurs.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_sender
        )

class IsTraveler(permissions.BasePermission):
    """
    Permission pour les voyageurs.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_traveler
        )

class IsSenderOrTraveler(permissions.BasePermission):
    """
    Permission pour les expéditeurs ou voyageurs.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_sender or request.user.is_traveler)
        )

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission pour le propriétaire de la ressource ou un admin.
    """
    def has_object_permission(self, request, view, obj):
        # Les admins peuvent accéder à tout
        if request.user.is_admin:
            return True
        
        # Le propriétaire peut accéder à sa propre ressource
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'id'):
            return obj.id == request.user.id
        
        return False

class IsPhoneVerified(permissions.BasePermission):
    """
    Permission pour les utilisateurs avec téléphone vérifié.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_phone_verified
        )

class IsDocumentVerified(permissions.BasePermission):
    """
    Permission pour les utilisateurs avec documents vérifiés.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_document_verified
        ) 