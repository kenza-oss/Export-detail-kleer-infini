"""
Backends d'authentification personnalisés
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class PhoneNumberBackend(ModelBackend):
    """
    Backend d'authentification permettant la connexion par numéro de téléphone
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('username')
        if password is None:
            password = kwargs.get('password')
        if username is None or password is None:
            return None
        
        try:
            # Chercher l'utilisateur par email ou numéro de téléphone
            user = User.objects.get(
                Q(email=username) | Q(phone_number=username)
            )
        except User.DoesNotExist:
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None 