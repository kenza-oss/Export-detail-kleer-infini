"""
Views for users app - Authentication and user management
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import User, UserProfile, UserDocument, OTPCode
from .serializers import (
    UserSerializer, UserProfileSerializer, UserDocumentSerializer,
    UserRegistrationSerializer, PhoneVerificationSerializer,
    ChangePasswordSerializer, ResetPasswordSerializer, UserLoginSerializer,
    OTPSendSerializer, OTPVerifySerializer, RoleUpdateSerializer,
    AdminUserSerializer
)
from .permissions import IsAdminUser, IsSender, IsTraveler, IsOwnerOrAdmin, IsPhoneVerified
from .services import OTPService, AuthService
from config.swagger_examples import (
    USER_REGISTRATION_EXAMPLE, USER_PROFILE_EXAMPLE, PHONE_VERIFICATION_EXAMPLE,
    PASSWORD_CHANGE_EXAMPLE, PASSWORD_RESET_EXAMPLE, USER_DOCUMENT_EXAMPLE,
    USER_SEARCH_EXAMPLE, ERROR_EXAMPLES
)
from config.swagger_config import (
    user_registration_schema, user_login_schema, user_profile_get_schema, user_profile_update_schema,
    reset_password_confirm_schema, phone_verification_schema, 
    user_document_upload_schema, user_document_list_schema, user_document_detail_schema, 
    user_search_schema, admin_user_detail_schema, admin_user_update_schema
)


class UserRegistrationView(APIView):
    """Vue pour l'inscription des utilisateurs."""
    
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Inscription d'un nouvel utilisateur",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
                'password_confirm': openapi.Schema(type=openapi.TYPE_STRING),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                'role': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['sender', 'traveler', 'admin', 'both']
                )
            },
            required=['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
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
                        "password_confirm": ["Les mots de passe ne correspondent pas."]
                    }
                }}
            )
        }
    )
    def post(self, request):
        """Inscription d'un nouvel utilisateur."""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = AuthService.create_user_with_profile(serializer.validated_data)
            
            return Response({
                'success': True,
                'message': 'Utilisateur créé avec succès',
                'user_id': user.id,
                'email': user.email,
                'role': user.role
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """Vue pour la connexion des utilisateurs."""
    
    permission_classes = [permissions.AllowAny]
    
    @user_login_schema()
    def post(self, request):
        """Connexion d'un utilisateur."""
        serializer = UserLoginSerializer(data=request.data, request=request)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Générer les tokens JWT
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Ajouter des claims personnalisés
            access_token['user_id'] = user.id
            access_token['username'] = user.username
            access_token['role'] = user.role
            access_token['is_admin'] = user.is_admin
            
            return Response({
                'success': True,
                'message': 'Connexion réussie',
                'tokens': {
                    'access': str(access_token),
                    'refresh': str(refresh)
                },
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'permissions': AuthService.get_user_permissions(user)
                }
            })
        
        return Response({
            'success': False,
            'message': 'Identifiants invalides'
        }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """Vue pour la gestion du profil utilisateur."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @user_profile_get_schema()
    def get(self, request):
        """Récupérer le profil de l'utilisateur connecté."""
        try:
            profile = request.user.profile
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
    
    @user_profile_update_schema()
    def put(self, request):
        """Mettre à jour le profil utilisateur."""
        try:
            profile = request.user.profile
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


class SendOTPView(APIView):
    """Vue pour envoyer un OTP."""
    
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Envoyer un OTP par SMS",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Numéro de téléphone")
            },
            required=['phone_number']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="OTP envoyé",
                examples={"application/json": {
                    "success": True,
                    "message": "OTP envoyé au 1234567890",
                    "expires_in": "10 minutes"
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Données invalides ou erreur",
                examples={"application/json": {
                    "success": False,
                    "message": "Données invalides",
                    "errors": {
                        "phone_number": ["Ce numéro de téléphone n'est pas valide."]
                    }
                }}
            )
        }
    )
    def post(self, request):
        """Envoyer un OTP par SMS."""
        try:
            serializer = OTPSendSerializer(data=request.data)
            if serializer.is_valid():
                phone_number = serializer.validated_data['phone_number']
                
                # Get user (authenticated or None for unauthenticated)
                user = request.user if request.user.is_authenticated else None
                
                # Créer l'OTP
                otp, error_message = OTPService.create_otp(user, phone_number)
                
                if error_message:
                    return Response({
                        'success': False,
                        'message': error_message
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if not otp:
                    return Response({
                        'success': False,
                        'message': 'Erreur lors de la création de l\'OTP'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # Envoyer par SMS (simulation en développement)
                OTPService.send_otp_sms(phone_number, otp.code)
                
                return Response({
                    'success': True,
                    'message': f'OTP envoyé au {phone_number}',
                    'expires_in': '10 minutes'
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Données invalides',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error in OTP send: {e}")
            return Response({
                'success': False,
                'message': f'Erreur lors du traitement de la requête: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    """Vue pour vérifier l'OTP."""
    
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Vérifier l'OTP reçu",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Numéro de téléphone"),
                'code': openapi.Schema(type=openapi.TYPE_STRING, description="Code OTP")
            },
            required=['phone_number', 'code']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Téléphone vérifié",
                examples={"application/json": {
                    "success": True,
                    "message": "Téléphone vérifié avec succès",
                    "phone_verified": True,
                    "user_id": 1
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Code OTP invalide ou expiré",
                examples={"application/json": {
                    "success": False,
                    "message": "Code OTP invalide ou expiré. Veuillez vérifier le code et réessayer."
                }}
            )
        }
    )
    def post(self, request):
        """Vérifier l'OTP reçu."""
        try:
            # Debug: Log the request content type and data
            print(f"Content-Type: {request.content_type}")
            print(f"Request data: {request.data}")
            
            serializer = OTPVerifySerializer(data=request.data)
            if serializer.is_valid():
                phone_number = serializer.validated_data['phone_number']
                code = serializer.validated_data['code']
                
                # Vérifier l'OTP
                is_valid, user = OTPService.verify_otp(phone_number, code)
                
                if is_valid:
                    return Response({
                        'success': True,
                        'message': 'Téléphone vérifié avec succès',
                        'phone_verified': True,
                        'user_id': user.id if user else None
                    })
                else:
                    return Response({
                        'success': False,
                        'message': 'Code OTP invalide ou expiré. Veuillez vérifier le code et réessayer.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'success': False,
                    'message': 'Données invalides',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error in OTP verification: {e}")
            return Response({
                'success': False,
                'message': f'Erreur lors du traitement de la requête: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class PhoneVerificationView(APIView):
    """Vue pour la vérification du téléphone."""
    
    permission_classes = [permissions.AllowAny]
    
    @phone_verification_schema()
    def get(self, request):
        """Récupérer le statut de vérification du téléphone."""
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'message': 'Authentification requise pour vérifier le statut du téléphone'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user = request.user
        return Response({
            'success': True,
            'phone_verified': user.is_phone_verified,
            'phone_number': user.phone_number
        })


class ChangePasswordView(APIView):
    """Vue pour changer le mot de passe."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Changer le mot de passe",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, description="Ancien mot de passe"),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description="Nouveau mot de passe")
            },
            required=['old_password', 'new_password']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Mot de passe changé",
                examples={"application/json": {
                    "success": True,
                    "message": "Mot de passe changé avec succès"
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Ancien mot de passe incorrect",
                examples={"application/json": {
                    "success": False,
                    "message": "Ancien mot de passe incorrect"
                }}
            )
        }
    )
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


class RoleUpdateView(APIView):
    """Vue pour mettre à jour le rôle d'un utilisateur."""
    
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Mettre à jour le rôle d'un utilisateur",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'role': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['sender', 'traveler', 'admin', 'both']
                )
            },
            required=['role']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Rôle mis à jour",
                examples={"application/json": {
                    "success": True,
                    "message": "Rôle mis à jour vers sender",
                    "user": {
                        "id": 1,
                        "username": "testuser",
                        "role": "sender"
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Rôle invalide",
                examples={"application/json": {
                    "success": False,
                    "message": "Rôle invalide"
                }}
            )
        }
    )
    def patch(self, request, user_id):
        """Mettre à jour le rôle d'un utilisateur."""
        try:
            user = User.objects.get(id=user_id)
            serializer = RoleUpdateSerializer(data=request.data)
            
            if serializer.is_valid():
                new_role = serializer.validated_data['role']
                if AuthService.update_user_role(user, new_role):
                    return Response({
                        'success': True,
                        'message': f'Rôle mis à jour vers {new_role}',
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'role': user.role
                        }
                    })
                else:
                    return Response({
                        'success': False,
                        'message': 'Rôle invalide'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Utilisateur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class AdminUserListView(APIView):
    """Vue admin pour la liste des utilisateurs."""
    
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Récupérer la liste de tous les utilisateurs",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des utilisateurs",
                examples={"application/json": {
                    "success": True,
                    "users": [
                        {
                            "id": 1,
                            "username": "testuser1",
                            "email": "user1@example.com",
                            "role": "sender",
                            "is_phone_verified": True,
                            "is_document_verified": False
                        },
                        {
                            "id": 2,
                            "username": "testuser2",
                            "email": "user2@example.com",
                            "role": "traveler",
                            "is_phone_verified": False,
                            "is_document_verified": True
                        }
                    ],
                    "count": 2
                }}
            )
        }
    )
    def get(self, request):
        """Récupérer la liste de tous les utilisateurs."""
        users = User.objects.all()
        serializer = AdminUserSerializer(users, many=True)
        
        return Response({
            'success': True,
            'users': serializer.data,
            'count': users.count()
        })


class AdminUserDetailView(APIView):
    """Vue admin pour les détails d'un utilisateur."""
    
    permission_classes = [IsAdminUser]
    
    @admin_user_detail_schema()
    def get(self, request, pk):
        """Récupérer les détails d'un utilisateur."""
        try:
            user = User.objects.get(pk=pk)
            serializer = AdminUserSerializer(user)
            return Response({
                'success': True,
                'user': serializer.data
            })
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Utilisateur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @admin_user_update_schema()
    def patch(self, request, pk):
        """Mettre à jour un utilisateur (admin uniquement)."""
        try:
            user = User.objects.get(pk=pk)
            serializer = AdminUserSerializer(user, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Utilisateur mis à jour avec succès',
                    'user': serializer.data
                })
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Utilisateur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class UserPermissionsView(APIView):
    """Vue pour récupérer les permissions de l'utilisateur connecté."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer les permissions de l'utilisateur connecté",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Permissions de l'utilisateur",
                examples={"application/json": {
                    "success": True,
                    "permissions": ["can_view_profile", "can_update_profile", "can_change_password"],
                    "user": {
                        "id": 1,
                        "username": "testuser",
                        "role": "sender",
                        "is_phone_verified": True,
                        "is_document_verified": False
                    }
                }}
            )
        }
    )
    def get(self, request):
        """Récupérer les permissions de l'utilisateur."""
        permissions = AuthService.get_user_permissions(request.user)
        
        return Response({
            'success': True,
            'permissions': permissions,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'role': request.user.role,
                'is_phone_verified': request.user.is_phone_verified,
                'is_document_verified': request.user.is_document_verified
            }
        })


# Garder les autres vues existantes...
class UserProfileUpdateView(APIView):
    """Vue pour la mise à jour du profil."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Mettre à jour partiellement le profil",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description="Prénom"),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de famille"),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Numéro de téléphone")
            },
            partial=True
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Profil mis à jour",
                examples={"application/json": {
                    "success": True,
                    "message": "Profil mis à jour avec succès",
                    "profile": {
                        "id": 1,
                        "first_name": "John",
                        "last_name": "Doe",
                        "phone_number": "1234567890",
                        "user": {
                            "id": 1,
                            "username": "testuser",
                            "email": "user@example.com"
                        }
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Données invalides",
                examples={"application/json": {
                    "success": False,
                    "message": "Données invalides",
                    "errors": {
                        "first_name": ["Ce champ est requis."],
                        "phone_number": ["Ce numéro de téléphone n'est pas valide."]
                    }
                }}
            )
        }
    )
    def patch(self, request):
        """Mettre à jour partiellement le profil."""
        try:
            profile = request.user.profile
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
    
    @swagger_auto_schema(
        operation_description="Mettre à jour complètement le profil",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description="Prénom"),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de famille"),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Numéro de téléphone")
            },
            partial=False
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Profil mis à jour",
                examples={"application/json": {
                    "success": True,
                    "message": "Profil mis à jour avec succès",
                    "profile": {
                        "id": 1,
                        "first_name": "John",
                        "last_name": "Doe",
                        "phone_number": "1234567890",
                        "user": {
                            "id": 1,
                            "username": "testuser",
                            "email": "user@example.com"
                        }
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Données invalides",
                examples={"application/json": {
                    "success": False,
                    "message": "Données invalides",
                    "errors": {
                        "first_name": ["Ce champ est requis."],
                        "phone_number": ["Ce numéro de téléphone n'est pas valide."]
                    }
                }}
            )
        }
    )
    def put(self, request):
        """Mettre à jour complètement le profil."""
        try:
            profile = request.user.profile
            serializer = UserProfileSerializer(profile, data=request.data, partial=False)
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


class ResetPasswordView(APIView):
    """Vue pour réinitialiser le mot de passe."""
    
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Demander une réinitialisation de mot de passe",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description="Email de l'utilisateur")
            },
            required=['email']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Email de réinitialisation envoyé",
                examples={"application/json": {
                    "success": True,
                    "message": "Email de réinitialisation envoyé"
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Email requis",
                examples={"application/json": {
                    "success": False,
                    "message": "Email requis"
                }}
            )
        }
    )
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
            # Pour des raisons de sécurité, toujours retourner 200 même si l'utilisateur n'existe pas
            return Response({
                'success': True,
                'message': 'Si un compte existe avec cet email, un lien de réinitialisation a été envoyé'
            })


class ResetPasswordConfirmView(APIView):
    """Vue pour confirmer la réinitialisation du mot de passe."""
    
    permission_classes = [permissions.AllowAny]
    
    @reset_password_confirm_schema()
    def post(self, request):
        """Confirmer la réinitialisation du mot de passe."""
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            new_password = serializer.validated_data['new_password']
            token = serializer.validated_data['token']
            
            try:
                user = User.objects.get(email=email)
                
                # En production, vérifier le token de réinitialisation
                # Pour l'instant, on accepte n'importe quel token en développement
                if token and len(token) > 0:  # Validation basique du token
                    user.set_password(new_password)
                    user.save()
                    
                    return Response({
                        'success': True,
                        'message': 'Mot de passe réinitialisé avec succès'
                    })
                else:
                    return Response({
                        'success': False,
                        'message': 'Token de réinitialisation invalide'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except User.DoesNotExist:
                # Pour des raisons de sécurité, toujours retourner 200 même si l'utilisateur n'existe pas
                return Response({
                    'success': True,
                    'message': 'Si un compte existe avec cet email, le mot de passe a été réinitialisé'
                })
        
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
    
    @user_document_detail_schema()
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
