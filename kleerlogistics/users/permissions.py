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


class IsActiveTraveler(permissions.BasePermission):
    """
    Permission pour les voyageurs actifs.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_traveler and
            request.user.is_active_traveler
        )


class IsActiveSender(permissions.BasePermission):
    """
    Permission pour les expéditeurs actifs.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_sender and
            request.user.is_active_sender
        )


class IsFullyVerified(permissions.BasePermission):
    """
    Permission pour les utilisateurs entièrement vérifiés (téléphone + documents).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_phone_verified and
            request.user.is_document_verified
        )


class CanAccessWallet(permissions.BasePermission):
    """
    Permission pour accéder aux fonctionnalités de portefeuille.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_phone_verified
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission pour permettre la lecture à tous les utilisateurs authentifiés,
    mais la modification uniquement au propriétaire.
    """
    def has_object_permission(self, request, view, obj):
        # Lecture autorisée pour tous les utilisateurs authentifiés
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Écriture uniquement pour le propriétaire ou admin
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_admin
        elif hasattr(obj, 'id'):
            return obj.id == request.user.id or request.user.is_admin
        
        return False


class IsVerifiedForTransactions(permissions.BasePermission):
    """
    Permission pour les transactions (nécessite une vérification complète).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_phone_verified and
            request.user.is_document_verified
        ) 