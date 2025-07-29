"""
Serializers for users app - JSON serialization for API responses
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from phonenumber_field.serializerfields import PhoneNumberField

from .models import User, UserProfile, UserDocument, OTPCode


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les utilisateurs avec profil."""
    
    profile = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'role', 
            'phone_number', 'is_phone_verified', 'is_document_verified', 
            'rating', 'total_trips', 'total_shipments', 'preferred_language',
            'is_active_traveler', 'is_active_sender', 'wallet_balance', 'commission_rate',
            'created_at', 'updated_at', 'profile', 'permissions'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'rating', 'total_trips', 
            'total_shipments', 'is_phone_verified', 'is_document_verified',
            'is_active_traveler', 'is_active_sender', 'wallet_balance'
        ]
    
    def get_profile(self, obj):
        """Récupérer les données du profil utilisateur."""
        try:
            profile = obj.profile
            return {
                'birth_date': profile.birth_date,
                'address': profile.address,
                'city': profile.city,
                'country': profile.country,
                'avatar': profile.avatar.url if profile.avatar else None,
                'bio': profile.bio,
            }
        except UserProfile.DoesNotExist:
            return None
    
    def get_permissions(self, obj):
        return {
            'is_admin': obj.is_admin,
            'is_sender': obj.is_sender,
            'is_traveler': obj.is_traveler,
            'can_access_admin_panel': obj.can_access_admin_panel(),
        }


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription d'un nouvel utilisateur."""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default='sender')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone_number', 'role']
        extra_kwargs = {
            'password': {'write_only': True},
            'password_confirm': {'write_only': True}
        }
    
    def validate(self, attrs):
        """Valider les données d'inscription."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'non_field_errors': 'Les mots de passe ne correspondent pas.'})
        
        # Vérifier l'unicité du numéro de téléphone
        if attrs.get('phone_number') and User.objects.filter(phone_number=attrs['phone_number']).exists():
            raise serializers.ValidationError({'phone_number': 'Ce numéro de téléphone est déjà utilisé.'})
        
        return attrs
    
    def create(self, validated_data):
        """Créer un nouvel utilisateur."""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer pour la connexion des utilisateurs."""
    
    username = serializers.CharField()
    password = serializers.CharField()
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    
    def validate(self, attrs):
        """Valider les identifiants de connexion."""
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            # Pass the request object to authenticate for Axes compatibility
            user = authenticate(request=self.request, username=username, password=password)
            if not user:
                raise serializers.ValidationError('Identifiants invalides.')
            if not user.is_active:
                raise serializers.ValidationError('Compte désactivé.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Nom d\'utilisateur et mot de passe requis.')
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil utilisateur."""
    
    class Meta:
        model = UserProfile
        fields = ['birth_date', 'address', 'city', 'country', 'avatar', 'bio']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour du profil utilisateur."""
    
    class Meta:
        model = UserProfile
        fields = ['birth_date', 'address', 'city', 'country', 'avatar', 'bio']


class PhoneVerificationSerializer(serializers.Serializer):
    """Serializer pour la vérification du téléphone."""
    
    phone_number = serializers.CharField(max_length=15)
    
    def validate_phone_number(self, value):
        """Valider le format du numéro de téléphone."""
        # Validation basique du format du numéro de téléphone
        if not value.startswith('+'):
            raise serializers.ValidationError('Le numéro de téléphone doit commencer par +')
        return value


class OTPSendSerializer(serializers.Serializer):
    """Serializer pour l'envoi d'un OTP."""
    
    phone_number = serializers.CharField(max_length=15)
    
    def validate_phone_number(self, value):
        """Valider le format du numéro de téléphone pour l'envoi d'OTP."""
        if not value.startswith('+'):
            raise serializers.ValidationError('Le numéro de téléphone doit commencer par +')
        return value


class OTPVerifySerializer(serializers.Serializer):
    """Serializer pour la vérification d'un OTP."""
    
    phone_number = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=6, min_length=6)
    
    def validate_phone_number(self, value):
        """Valider le format du numéro de téléphone pour la vérification d'OTP."""
        if not value.startswith('+'):
            raise serializers.ValidationError('Le numéro de téléphone doit commencer par +')
        return value
    
    def validate(self, attrs):
        """Valider le format de l'OTP."""
        phone_number = attrs.get('phone_number')
        code = attrs.get('code')
        
        if not code.isdigit():
            raise serializers.ValidationError({'code': 'Le code OTP doit contenir uniquement des chiffres.'})
        
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour le changement de mot de passe."""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    
    def validate(self, attrs):
        """Valider le changement de mot de passe."""
        # Valider le nouveau mot de passe
        try:
            validate_password(attrs['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': e.messages})
        
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer pour la réinitialisation de mot de passe."""
    
    email = serializers.EmailField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField()
    token = serializers.CharField()  # Token de réinitialisation
    
    def validate(self, attrs):
        """Valider la réinitialisation de mot de passe."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Les mots de passe ne correspondent pas.'})
        
        return attrs


class UserDocumentSerializer(serializers.ModelSerializer):
    """Serializer pour les documents utilisateur."""
    
    class Meta:
        model = UserDocument
        fields = ['id', 'document_type', 'document_file', 'status', 'uploaded_at', 'verified_at', 'rejection_reason']
        read_only_fields = ['id', 'status', 'uploaded_at', 'verified_at', 'rejection_reason']


class UserSearchSerializer(serializers.ModelSerializer):
    """Serializer pour la recherche d'utilisateurs."""
    
    profile_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'role', 'rating', 'total_trips', 'total_shipments', 'is_document_verified', 'profile_summary']
    
    def get_profile_summary(self, obj):
        """Récupérer un résumé du profil utilisateur."""
        try:
            profile = obj.profile
            return {
                'rating': obj.rating,
                'total_trips': obj.total_trips,
                'total_shipments': obj.total_shipments,
                'is_verified': obj.is_document_verified,
                'country': profile.country,
                'city': profile.city,
            }
        except UserProfile.DoesNotExist:
            return None


class RoleUpdateSerializer(serializers.Serializer):
    """Serializer pour la mise à jour du rôle d'un utilisateur."""
    
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)
    
    def validate_role(self, value):
        """Valider le rôle."""
        if value not in dict(User.ROLE_CHOICES):
            raise serializers.ValidationError('Rôle invalide.')
        return value


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer pour les utilisateurs administrateurs."""
    
    profile = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'role', 
            'phone_number', 'is_phone_verified', 'is_document_verified', 
            'rating', 'total_trips', 'total_shipments', 'preferred_language',
            'is_active_traveler', 'is_active_sender', 'wallet_balance', 'commission_rate',
            'created_at', 'updated_at', 'is_active', 'is_staff', 'is_superuser', 
            'profile', 'permissions'
        ]
    
    def get_profile(self, obj):
        """Récupérer les données du profil utilisateur."""
        try:
            profile = obj.profile
            return {
                'birth_date': profile.birth_date,
                'address': profile.address,
                'city': profile.city,
                'country': profile.country,
                'avatar': profile.avatar.url if profile.avatar else None,
                'bio': profile.bio,
            }
        except UserProfile.DoesNotExist:
            return None
    
    def get_permissions(self, obj):
        """Récupérer les permissions de l'utilisateur."""
        return {
            'is_admin': obj.is_admin,
            'is_sender': obj.is_sender,
            'is_traveler': obj.is_traveler,
            'can_access_admin_panel': obj.can_access_admin_panel(),
        }


class UserStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques utilisateur."""
    
    total_trips = serializers.IntegerField()
    total_shipments = serializers.IntegerField()
    rating = serializers.FloatField()
    is_phone_verified = serializers.BooleanField()
    is_document_verified = serializers.BooleanField()
    verification_status = serializers.CharField()
    member_since = serializers.DateTimeField()
    
    def to_representation(self, instance):
        """Convertir l'instance en représentation JSON."""
        return {
            'total_trips': instance.total_trips,
            'total_shipments': instance.total_shipments,
            'rating': float(instance.rating),
            'is_phone_verified': instance.is_phone_verified,
            'is_document_verified': instance.is_document_verified,
            'verification_status': 'verified' if instance.is_document_verified else 'pending',
            'member_since': instance.created_at
        }


class UserWalletSerializer(serializers.ModelSerializer):
    """Serializer pour la gestion du portefeuille utilisateur."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'wallet_balance', 'commission_rate']
        read_only_fields = ['id', 'username']


class WalletTransactionSerializer(serializers.Serializer):
    """Serializer pour les transactions du portefeuille."""
    
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = serializers.ChoiceField(choices=[
        ('deposit', 'Dépôt'),
        ('withdrawal', 'Retrait'),
        ('commission', 'Commission'),
        ('payment', 'Paiement'),
        ('refund', 'Remboursement')
    ])
    description = serializers.CharField(max_length=255, required=False)
    
    def validate_amount(self, value):
        """Valider le montant de la transaction."""
        if value <= 0:
            raise serializers.ValidationError('Le montant doit être positif.')
        return value


class UserVerificationStatusSerializer(serializers.ModelSerializer):
    """Serializer pour le statut de vérification de l'utilisateur."""
    
    verification_status = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'is_phone_verified', 'is_document_verified',
            'verification_status'
        ]
        read_only_fields = ['id', 'username', 'is_phone_verified', 'is_document_verified']
    
    def get_verification_status(self, obj):
        """Récupérer le statut de vérification complet."""
        return obj.get_verification_status() 