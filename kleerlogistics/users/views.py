"""
Views for users app - Authentication and user management
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
import random
import string
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import User, UserProfile, UserDocument
from .serializers import (
    UserSerializer, UserProfileSerializer, UserDocumentSerializer,
    UserRegistrationSerializer, PhoneVerificationSerializer,
    ChangePasswordSerializer, ResetPasswordSerializer
)
from config.swagger_examples import (
    USER_REGISTRATION_EXAMPLE, USER_PROFILE_EXAMPLE, PHONE_VERIFICATION_EXAMPLE,
    PASSWORD_CHANGE_EXAMPLE, PASSWORD_RESET_EXAMPLE, USER_DOCUMENT_EXAMPLE,
    USER_SEARCH_EXAMPLE, ERROR_EXAMPLES
)
from config.swagger_config import (
    user_registration_schema, user_profile_get_schema, user_profile_update_schema,
    send_otp_schema, verify_otp_schema, change_password_schema, reset_password_schema,
    user_document_upload_schema, user_document_list_schema, user_search_schema
)


class UserRegistrationView(APIView):
    """Vue pour l'inscription des utilisateurs."""
    
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Inscription d'un nouvel utilisateur",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                'date_of_birth': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                'gender': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['male', 'female', 'other']
                ),
                'address': openapi.Schema(type=openapi.TYPE_STRING),
                'city': openapi.Schema(type=openapi.TYPE_STRING),
                'postal_code': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['email', 'password', 'confirm_password', 'first_name', 'last_name']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Utilisateur créé",
                examples={"application/json": {
                    "success": True,
                    "message": "Utilisateur créé avec succès",
                    "user_id": 1,
                    "email": "user@example.com"
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "errors": {
                        "email": ["Cette adresse email est déjà utilisée."],
                        "password": ["Ce mot de passe est trop court."],
                        "confirm_password": ["Les mots de passe ne correspondent pas."]
                    }
                }}
            )
        }
    )
    def post(self, request):
        """Inscription d'un nouvel utilisateur."""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                user = serializer.save()
                # Créer automatiquement un profil utilisateur
                UserProfile.objects.create(user=user)
                
            return Response({
                'success': True,
                'message': 'Utilisateur créé avec succès',
                'user_id': user.id,
                'email': user.email
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """Vue pour la gestion du profil utilisateur."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer le profil de l'utilisateur",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Profil utilisateur",
                examples={"application/json": {
                    "success": True,
                    "profile": {
                        "id": 1,
                        "user": 1,
                        "phone_number": "+213123456789",
                        "date_of_birth": "1990-01-01",
                        "gender": "male",
                        "address": "123 Rue de la Paix",
                        "city": "Alger",
                        "postal_code": "16000",
                        "rating": 4.5,
                        "total_trips": 25,
                        "total_shipments": 15,
                        "is_verified": True,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Profil non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Profil non trouvé"
                }}
            )
        }
    )
    def get(self, request):
        """Récupérer le profil de l'utilisateur connecté."""
        try:
            profile = request.user.userprofile
            serializer = UserProfileSerializer(profile)
            return Response({
                'success': True,
                'profile': serializer.data
            })
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Profil non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_description="Mettre à jour le profil utilisateur",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                'date_of_birth': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                'gender': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['male', 'female', 'other']
                ),
                'address': openapi.Schema(type=openapi.TYPE_STRING),
                'city': openapi.Schema(type=openapi.TYPE_STRING),
                'postal_code': openapi.Schema(type=openapi.TYPE_STRING),
                'bio': openapi.Schema(type=openapi.TYPE_STRING),
                'preferences': openapi.Schema(type=openapi.TYPE_OBJECT)
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Profil mis à jour",
                examples={"application/json": {
                    "success": True,
                    "message": "Profil mis à jour avec succès",
                    "profile": {
                        "id": 1,
                        "user": 1,
                        "phone_number": "+213123456789",
                        "date_of_birth": "1990-01-01",
                        "gender": "male",
                        "address": "123 Rue de la Paix",
                        "city": "Alger",
                        "postal_code": "16000",
                        "rating": 4.5,
                        "total_trips": 25,
                        "total_shipments": 15,
                        "is_verified": True,
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "errors": {
                        "phone_number": ["Numéro de téléphone invalide."],
                        "date_of_birth": ["Date de naissance invalide."]
                    }
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Profil non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Profil non trouvé"
                }}
            )
        }
    )
    def put(self, request):
        """Mettre à jour le profil utilisateur."""
        try:
            profile = request.user.userprofile
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Profil mis à jour avec succès',
                    'profile': serializer.data
                })
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Profil non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class UserProfileUpdateView(APIView):
    """Vue pour la mise à jour du profil."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request):
        """Mettre à jour partiellement le profil."""
        try:
            profile = request.user.userprofile
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Profil mis à jour avec succès',
                    'profile': serializer.data
                })
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Profil non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class PhoneVerificationView(APIView):
    """Vue pour la vérification du téléphone."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupérer le statut de vérification du téléphone."""
        try:
            profile = request.user.userprofile
            return Response({
                'success': True,
                'phone_verified': profile.phone_verified,
                'phone_number': profile.phone_number
            })
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Profil non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class SendOTPView(APIView):
    """Vue pour envoyer un OTP."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @send_otp_schema()
    def post(self, request):
        """Envoyer un OTP par SMS."""
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
            return Response({
                'success': False,
                'message': 'Numéro de téléphone requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Générer un OTP à 6 chiffres
        otp = ''.join(random.choices(string.digits, k=6))
        
        # En production, envoyer par SMS
        # Pour la démonstration, on simule
        
        try:
            profile = request.user.userprofile
            profile.phone_number = phone_number
            profile.otp_code = otp
            profile.otp_created_at = timezone.now()
            profile.save()
            
            return Response({
                'success': True,
                'message': f'OTP envoyé au {phone_number}',
                'otp': otp  # En production, ne pas renvoyer l'OTP
            })
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Profil non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class VerifyOTPView(APIView):
    """Vue pour vérifier l'OTP."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @verify_otp_schema()
    def post(self, request):
        """Vérifier l'OTP reçu."""
        otp = request.data.get('otp')
        
        if not otp:
            return Response({
                'success': False,
                'message': 'OTP requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            profile = request.user.userprofile
            
            # Vérifier l'OTP
            if profile.otp_code == otp:
                profile.phone_verified = True
                profile.save()
                
                return Response({
                    'success': True,
                    'message': 'Téléphone vérifié avec succès'
                })
            else:
                return Response({
                    'success': False,
                    'message': 'OTP incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Profil non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class ChangePasswordView(APIView):
    """Vue pour changer le mot de passe."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @change_password_schema()
    def post(self, request):
        """Changer le mot de passe."""
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']
            
            if not user.check_password(old_password):
                return Response({
                    'success': False,
                    'message': 'Ancien mot de passe incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(new_password)
            user.save()
            
            return Response({
                'success': True,
                'message': 'Mot de passe changé avec succès'
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    """Vue pour réinitialiser le mot de passe."""
    
    permission_classes = [permissions.AllowAny]
    
    @reset_password_schema()
    def post(self, request):
        """Demander une réinitialisation de mot de passe."""
        email = request.data.get('email')
        
        if not email:
            return Response({
                'success': False,
                'message': 'Email requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            # En production, envoyer un email avec un lien de réinitialisation
            return Response({
                'success': True,
                'message': 'Email de réinitialisation envoyé'
            })
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Utilisateur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class ResetPasswordConfirmView(APIView):
    """Vue pour confirmer la réinitialisation du mot de passe."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Confirmer la réinitialisation du mot de passe."""
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            # En production, vérifier le token de réinitialisation
            email = serializer.validated_data['email']
            new_password = serializer.validated_data['new_password']
            
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                
                return Response({
                    'success': True,
                    'message': 'Mot de passe réinitialisé avec succès'
                })
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Utilisateur non trouvé'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserDocumentListView(APIView):
    """Vue pour la liste des documents utilisateur."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @user_document_list_schema()
    def get(self, request):
        """Récupérer la liste des documents."""
        documents = UserDocument.objects.filter(user=request.user)
        serializer = UserDocumentSerializer(documents, many=True)
        
        return Response({
            'success': True,
            'documents': serializer.data,
            'count': documents.count()
        })


class UserDocumentUploadView(APIView):
    """Vue pour uploader un document."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @user_document_upload_schema()
    def post(self, request):
        """Uploader un nouveau document."""
        serializer = UserDocumentSerializer(data=request.data)
        if serializer.is_valid():
            document = serializer.save(user=request.user)
            return Response({
                'success': True,
                'message': 'Document uploadé avec succès',
                'document': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserDocumentDetailView(APIView):
    """Vue pour les détails d'un document."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        """Récupérer les détails d'un document."""
        try:
            document = UserDocument.objects.get(pk=pk, user=request.user)
            serializer = UserDocumentSerializer(document)
            return Response({
                'success': True,
                'document': serializer.data
            })
        except UserDocument.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Document non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, pk):
        """Supprimer un document."""
        try:
            document = UserDocument.objects.get(pk=pk, user=request.user)
            document.delete()
            return Response({
                'success': True,
                'message': 'Document supprimé avec succès'
            })
        except UserDocument.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Document non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class UserSearchView(APIView):
    """Vue pour la recherche d'utilisateurs."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @user_search_schema()
    def get(self, request):
        """Rechercher des utilisateurs."""
        query = request.query_params.get('q', '')
        
        if not query:
            return Response({
                'success': False,
                'message': 'Terme de recherche requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        users = User.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )[:20]
        
        serializer = UserSerializer(users, many=True)
        return Response({
            'success': True,
            'users': serializer.data,
            'count': users.count()
        })


class AdminUserListView(APIView):
    """Vue admin pour la liste des utilisateurs."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Récupérer la liste de tous les utilisateurs."""
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        
        return Response({
            'success': True,
            'users': serializer.data,
            'count': users.count()
        })


class AdminUserDetailView(APIView):
    """Vue admin pour les détails d'un utilisateur."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request, pk):
        """Récupérer les détails d'un utilisateur."""
        try:
            user = User.objects.get(pk=pk)
            serializer = UserSerializer(user)
            return Response({
                'success': True,
                'user': serializer.data
            })
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Utilisateur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
