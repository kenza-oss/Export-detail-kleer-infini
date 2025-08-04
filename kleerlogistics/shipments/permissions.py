"""
Permissions pour le module shipments
"""

from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class IsShipmentOwner(permissions.BasePermission):
    """
    Permission pour vérifier que l'utilisateur est le propriétaire de l'envoi.
    """
    
    def has_object_permission(self, request, view, obj):
        # L'utilisateur doit être le propriétaire de l'envoi
        return obj.sender == request.user


class IsShipmentOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission pour permettre la lecture à tous mais la modification seulement au propriétaire.
    """
    
    def has_object_permission(self, request, view, obj):
        # Permettre la lecture à tous les utilisateurs authentifiés
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Permettre la modification seulement au propriétaire
        return obj.sender == request.user


class CanCreateShipment(permissions.BasePermission):
    """
    Permission pour créer un envoi.
    """
    
    def has_permission(self, request, view):
        # Vérifier que l'utilisateur est authentifié et a le rôle d'expéditeur
        return (
            request.user.is_authenticated and
            request.user.role in ['sender', 'both']
        )


class CanRateShipment(permissions.BasePermission):
    """
    Permission pour évaluer un envoi.
    """
    
    def has_object_permission(self, request, view, obj):
        # Vérifier que l'envoi est livré
        if obj.status != 'delivered':
            return False
        
        # Vérifier que l'utilisateur n'a pas déjà évalué cet envoi
        from .models import ShipmentRating
        return not ShipmentRating.objects.filter(
            shipment=obj,
            rater=request.user
        ).exists()


class CanUploadDocument(permissions.BasePermission):
    """
    Permission pour uploader des documents.
    """
    
    def has_object_permission(self, request, view, obj):
        # Seul le propriétaire de l'envoi peut uploader des documents
        return obj.sender == request.user


class CanManagePackageDetails(permissions.BasePermission):
    """
    Permission pour gérer les détails du colis.
    """
    
    def has_object_permission(self, request, view, obj):
        # Seul le propriétaire de l'envoi peut gérer les détails du colis
        return obj.shipment.sender == request.user


class IsAdminOrShipmentOwner(permissions.BasePermission):
    """
    Permission pour les administrateurs ou le propriétaire de l'envoi.
    """
    
    def has_object_permission(self, request, view, obj):
        # Les administrateurs ont tous les droits
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Le propriétaire de l'envoi peut accéder
        return obj.sender == request.user


class CanViewShipmentTracking(permissions.BasePermission):
    """
    Permission pour voir le suivi d'un envoi.
    """
    
    def has_object_permission(self, request, view, obj):
        # Le propriétaire de l'envoi peut voir le suivi
        if obj.sender == request.user:
            return True
        
        # Les administrateurs peuvent voir le suivi
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Les voyageurs associés peuvent voir le suivi
        if hasattr(obj, 'matched_trip') and obj.matched_trip:
            return obj.matched_trip.traveler == request.user
        
        return False


class CanAddTrackingEvent(permissions.BasePermission):
    """
    Permission pour ajouter un événement de suivi.
    """
    
    def has_object_permission(self, request, view, obj):
        # Les administrateurs peuvent ajouter des événements
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Le propriétaire de l'envoi peut ajouter des événements
        if obj.sender == request.user:
            return True
        
        # Le voyageur associé peut ajouter des événements
        if hasattr(obj, 'matched_trip') and obj.matched_trip:
            return obj.matched_trip.traveler == request.user
        
        return False


class CanMatchShipment(permissions.BasePermission):
    """
    Permission pour associer un envoi à un trajet.
    """
    
    def has_object_permission(self, request, view, obj):
        # Seul le propriétaire de l'envoi peut l'associer à un trajet
        return obj.sender == request.user


class CanCancelShipment(permissions.BasePermission):
    """
    Permission pour annuler un envoi.
    """
    
    def has_object_permission(self, request, view, obj):
        # Seul le propriétaire peut annuler un envoi
        if obj.sender != request.user:
            return False
        
        # L'envoi doit être dans un statut annulable
        return obj.status in ['draft', 'pending', 'matched']


class CanDeleteShipment(permissions.BasePermission):
    """
    Permission pour supprimer un envoi.
    """
    
    def has_object_permission(self, request, view, obj):
        # Seul le propriétaire peut supprimer un envoi
        if obj.sender != request.user:
            return False
        
        # L'envoi doit être dans un statut supprimable
        return obj.status in ['draft', 'pending']


class IsVerifiedUser(permissions.BasePermission):
    """
    Permission pour les utilisateurs vérifiés.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.is_phone_verified and
            request.user.is_document_verified
        )


class HasActiveWallet(permissions.BasePermission):
    """
    Permission pour les utilisateurs avec un portefeuille actif.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'wallet_balance') and
            request.user.wallet_balance >= 0
        )


class CanAccessShipmentAnalytics(permissions.BasePermission):
    """
    Permission pour accéder aux analytics des envois.
    """
    
    def has_permission(self, request, view):
        # Les administrateurs ont accès aux analytics
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Les utilisateurs vérifiés peuvent voir leurs propres analytics
        return (
            request.user.is_authenticated and
            request.user.is_phone_verified
        )