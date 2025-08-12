"""
Permissions pour la gestion des paiements algériens
"""

from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission personnalisée pour permettre l'accès au propriétaire ou à l'admin.
    """
    
    def has_object_permission(self, request, view, obj):
        # Les admins ont toujours accès
        if request.user.is_staff:
            return True
        
        # Le propriétaire a accès
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Pour les transactions, vérifier l'utilisateur
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsPaymentMethodActive(permissions.BasePermission):
    """
    Permission pour vérifier si une méthode de paiement est active.
    """
    
    def has_permission(self, request, view):
        # Cette permission est utilisée dans les vues qui nécessitent
        # une méthode de paiement active
        return True
    
    def has_object_permission(self, request, view, obj):
        # Vérifier si la méthode de paiement est active
        if hasattr(obj, 'is_active'):
            return obj.is_active
        return True


class CanProcessPayment(permissions.BasePermission):
    """
    Permission pour vérifier si l'utilisateur peut effectuer un paiement.
    """
    
    def has_permission(self, request, view):
        # L'utilisateur doit être authentifié
        if not request.user.is_authenticated:
            return False
        
        # L'utilisateur doit avoir un portefeuille
        if hasattr(request.user, 'wallet'):
            return True
        
        return False


class CanConfirmCashPayment(permissions.BasePermission):
    """
    Permission pour confirmer un paiement en espèces (admin/bureau).
    """
    
    def has_permission(self, request, view):
        # Seuls les admins ou les utilisateurs avec des permissions spéciales
        # peuvent confirmer les paiements en espèces
        return request.user.is_staff or request.user.has_perm('payments.confirm_cash_payment')
    
    def has_object_permission(self, request, view, obj):
        # Vérifier si l'utilisateur peut confirmer cette transaction spécifique
        if request.user.is_staff:
            return True
        
        # Vérifier les permissions spécifiques
        return request.user.has_perm('payments.confirm_cash_payment')


class CanViewPaymentStatistics(permissions.BasePermission):
    """
    Permission pour voir les statistiques de paiement.
    """
    
    def has_permission(self, request, view):
        # Seuls les admins peuvent voir les statistiques
        return request.user.is_staff or request.user.has_perm('payments.view_statistics')


class CanManagePaymentMethods(permissions.BasePermission):
    """
    Permission pour gérer les méthodes de paiement (admin).
    """
    
    def has_permission(self, request, view):
        # Seuls les admins peuvent gérer les méthodes de paiement
        return request.user.is_staff or request.user.has_perm('payments.manage_payment_methods')


class IsValidPaymentAmount(permissions.BasePermission):
    """
    Permission pour vérifier si le montant de paiement est valide.
    """
    
    def has_permission(self, request, view):
        # Cette permission est utilisée pour valider les montants
        # La validation réelle se fait dans les sérialiseurs
        return True


class CanAccessTransaction(permissions.BasePermission):
    """
    Permission pour accéder aux détails d'une transaction.
    """
    
    def has_object_permission(self, request, view, obj):
        # Les admins ont toujours accès
        if request.user.is_staff:
            return True
        
        # Le propriétaire de la transaction a accès
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Pour les transactions liées (remboursements, etc.)
        if hasattr(obj, 'related_transaction'):
            if obj.related_transaction and obj.related_transaction.user == request.user:
                return True
        
        return False


class IsPaymentCompleted(permissions.BasePermission):
    """
    Permission pour vérifier si un paiement est terminé.
    """
    
    def has_object_permission(self, request, view, obj):
        # Vérifier si la transaction est terminée
        if hasattr(obj, 'status'):
            return obj.status == 'completed'
        return False


class CanRefundPayment(permissions.BasePermission):
    """
    Permission pour rembourser un paiement.
    """
    
    def has_permission(self, request, view):
        # Seuls les admins peuvent rembourser
        return request.user.is_staff or request.user.has_perm('payments.refund_payment')
    
    def has_object_permission(self, request, view, obj):
        # Vérifier si la transaction peut être remboursée
        if not request.user.is_staff and not request.user.has_perm('payments.refund_payment'):
            return False
        
        # La transaction doit être terminée
        if hasattr(obj, 'status') and obj.status != 'completed':
            return False
        
        # La transaction ne doit pas déjà être remboursée
        if hasattr(obj, 'status') and obj.status == 'refunded':
            return False
        
        return True
