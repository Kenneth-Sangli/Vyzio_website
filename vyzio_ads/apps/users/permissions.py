"""
Permissions personnalisées pour la gestion des utilisateurs
"""
from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Permission pour modifier uniquement son propre profil
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.id == request.user.id


class IsSellerOrReadOnly(BasePermission):
    """
    Permission pour que seul un vendeur puisse créer des annonces
    """
    
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return request.user and (
            request.user.role in ['seller', 'professional'] or 
            request.user.is_superuser
        )


class IsOwnListingOrReadOnly(BasePermission):
    """
    Permission pour modifier uniquement ses propres annonces
    """
    
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return obj.seller == request.user or request.user.is_superuser


class IsAdminUser(BasePermission):
    """
    Permission pour accès admin uniquement
    """
    
    def has_permission(self, request, view):
        return request.user and (request.user.is_superuser or request.user.is_staff)


class IsVerifiedSeller(BasePermission):
    """
    Permission pour les vendeurs vérifiés
    """
    
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return (
            request.user and 
            request.user.is_verified and 
            request.user.role in ['seller', 'professional']
        )


class CanAccessConversation(BasePermission):
    """
    Permission pour accéder à une conversation
    (acheteur ou vendeur uniquement)
    """
    
    def has_object_permission(self, request, view, obj):
        return (
            request.user == obj.buyer or 
            request.user == obj.seller or 
            request.user.is_superuser
        )


class CanSendMessage(BasePermission):
    """
    Permission pour envoyer des messages
    (pas d'utilisateurs bloqués)
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Récupérer l'utilisateur destinataire du request
        recipient_id = request.data.get('recipient_id')
        if not recipient_id:
            return False
        
        # Vérifier s'il n'est pas bloqué
        from apps.messaging.models import BlockedUser
        is_blocked = BlockedUser.objects.filter(
            blocker_id=recipient_id,
            blocked_id=request.user.id
        ).exists()
        
        return not is_blocked


class IsBuyer(BasePermission):
    """
    Permission pour les acheteurs
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsSeller(BasePermission):
    """
    Permission pour les vendeurs uniquement (toutes les méthodes)
    Utilisé pour le dashboard seller et les analytics
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['seller', 'professional']
        )


class IsReviewOwnerOrReadOnly(BasePermission):
    """
    Permission pour modifier uniquement ses propres avis
    """
    
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return obj.reviewer == request.user or request.user.is_superuser
