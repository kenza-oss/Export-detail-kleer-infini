"""
Serializers for users app - JSON serialization for API responses
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from phonenumber_field.serializerfields import PhoneNumberField

from .models import User, UserProfile, UserDocument


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les utilisateurs avec profil."""
    
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_active', 'date_joined', 'last_login', 'profile'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_profile(self, obj):
        """Récupérer les données du profil utilisateur."""
        try:
            profile = obj.userprofile
            return {
                'user_type': profile.user_type,
                'phone_number': profile.phone_number,
                'phone_verified': profile.phone_verified,
                'first_name': profile.first_name,
                'last_name': profile.last_name,
                'date_of_birth': profile.date_of_birth,
                'country': profile.country,
                'city': profile.city,
                'address': profile.address,
                'rating': profile.rating,
                'total_trips': profile.total_trips,
                'total_shipments': profile.total_shipments,
                'is_verified': profile.is_verified,
                'verification_status': profile.verification_status,
            }
        except UserProfile.DoesNotExist:
            return None


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription d'un nouvel utilisateur."""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField()
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name',
            'password', 'password_confirm'
        ]
    
    def validate(self, attrs):
        """Valider les données d'inscription."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        
        # Valider le mot de passe
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({'password': e.messages})
        
        # Vérifier que l'email n'existe pas déjà
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({'email': 'Cet email est déjà utilisé.'})
        
        # Vérifier que le nom d'utilisateur n'existe pas déjà
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({'username': 'Ce nom d\'utilisateur est déjà utilisé.'})
        
        return attrs
    
    def create(self, validated_data):
        """Créer un nouvel utilisateur."""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil utilisateur."""
    
    class Meta:
        model = UserProfile
        fields = [
            'user_type', 'phone_number', 'phone_verified',
            'first_name', 'last_name', 'date_of_birth',
            'country', 'city', 'address', 'rating',
            'total_trips', 'total_shipments', 'is_verified',
            'verification_status', 'bio', 'profile_picture'
        ]
        read_only_fields = ['rating', 'total_trips', 'total_shipments', 'is_verified']
    
    def validate_phone_number(self, value):
        """Valider le numéro de téléphone."""
        if value and UserProfile.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return value


class PhoneVerificationSerializer(serializers.Serializer):
    """Serializer pour la vérification du téléphone."""
    
    phone = PhoneNumberField()
    otp = serializers.CharField(max_length=6, min_length=6)
    
    def validate_otp(self, value):
        """Valider le format de l'OTP."""
        if not value.isdigit():
            raise serializers.ValidationError("L'OTP doit contenir uniquement des chiffres.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour le changement de mot de passe."""
    
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Valider le changement de mot de passe."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Les nouveaux mots de passe ne correspondent pas.")
        
        # Valider le nouveau mot de passe
        try:
            validate_password(attrs['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': e.messages})
        
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer pour la réinitialisation de mot de passe."""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Valider que l'email existe."""
        if not User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError("Aucun utilisateur actif trouvé avec cet email.")
        return value


class UserDocumentSerializer(serializers.ModelSerializer):
    """Serializer pour les documents utilisateur."""
    
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = UserDocument
        fields = [
            'id', 'document_type', 'file', 'file_url', 'file_size',
            'upload_date', 'is_verified', 'verification_date',
            'verification_notes'
        ]
        read_only_fields = ['id', 'upload_date', 'is_verified', 'verification_date']
    
    def get_file_url(self, obj):
        """Obtenir l'URL du fichier."""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_file_size(self, obj):
        """Obtenir la taille du fichier en bytes."""
        if obj.file:
            try:
                return obj.file.size
            except:
                return 0
        return 0
    
    def validate_file(self, value):
        """Valider le fichier uploadé."""
        # Vérifier la taille du fichier (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Le fichier ne doit pas dépasser 10MB.")
        
        # Vérifier le type de fichier
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Type de fichier non autorisé. Utilisez JPEG, PNG, GIF ou PDF.")
        
        return value


class UserSearchSerializer(serializers.ModelSerializer):
    """Serializer pour la recherche d'utilisateurs."""
    
    profile_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'profile_summary']
    
    def get_profile_summary(self, obj):
        """Obtenir un résumé du profil pour la recherche."""
        try:
            profile = obj.userprofile
            return {
                                 'user_type': profile.user_type,
                 'rating': profile.rating,
                 'total_trips': profile.total_trips,
                'total_shipments': profile.total_shipments,
                'is_verified': profile.is_verified,
                'country': profile.country,
                'city': profile.city,
            }
        except UserProfile.DoesNotExist:
            return None


class LoginSerializer(serializers.Serializer):
    """Serializer pour la connexion."""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Valider les identifiants de connexion."""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError("Identifiants invalides.")
            if not user.is_active:
                raise serializers.ValidationError("Compte désactivé.")
            attrs['user'] = user
        else:
            raise serializers.ValidationError("Email et mot de passe requis.")
        
        return attrs


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
        """Formater les statistiques pour l'API."""
        return {
            'success': True,
            'stats': {
                'total_trips': instance.total_trips,
                'total_shipments': instance.total_shipments,
                'rating': float(instance.rating),
                'is_phone_verified': instance.is_phone_verified,
                'is_document_verified': instance.is_document_verified,
                'verification_status': instance.verification_status,
                'member_since': instance.date_joined,
            }
        } 