"""
Views for users app - Authentication and user management
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger(__name__)

class LoginRateThrottle(AnonRateThrottle):
    """Throttle spécifique pour le login."""
    rate = '5/minute'
    scope = 'login'

from .models import User, UserProfile, UserDocument, OTPCode
from .serializers import (
    UserSerializer, UserProfileSerializer, UserDocumentSerializer,
    UserRegistrationSerializer, PhoneVerificationSerializer,
    ChangePasswordSerializer, ResetPasswordSerializer, UserLoginSerializer,
    OTPSendSerializer, OTPVerifySerializer, RoleUpdateSerializer,
    AdminUserSerializer
)
from .permissions import IsAdminUser, IsSender, IsTraveler, IsOwnerOrAdmin, IsPhoneVerified, IsVerifiedForTransactions
from .services import OTPService, AuthService, OTPAuditService
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
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
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
    throttle_classes = [LoginRateThrottle]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
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


class UserLogoutView(APIView):
    """Vue pour la déconnexion des utilisateurs."""
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Déconnexion de l'utilisateur",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token à invalider")
            },
            required=['refresh']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Déconnexion réussie",
                examples={"application/json": {
                    "success": True,
                    "message": "Déconnexion réussie"
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Token invalide",
                examples={"application/json": {
                    "success": False,
                    "message": "Token de rafraîchissement invalide"
                }}
            )
        }
    )
    def post(self, request):
        """Déconnexion de l'utilisateur."""
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response({
                    'success': False,
                    'message': 'Token de rafraîchissement requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Invalider le refresh token
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                
                return Response({
                    'success': True,
                    'message': 'Déconnexion réussie'
                })
            except Exception as e:
                return Response({
                    'success': False,
                    'message': 'Token de rafraîchissement invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur lors de la déconnexion: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """Vue pour la gestion du profil utilisateur."""
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
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
            user = request.user
            profile = user.profile
            
            # Mettre à jour les champs de l'utilisateur
            if 'first_name' in request.data:
                user.first_name = request.data['first_name']
            if 'last_name' in request.data:
                user.last_name = request.data['last_name']
            if 'phone_number' in request.data:
                user.phone_number = request.data['phone_number']
            
            # Sauvegarder l'utilisateur
            user.save()
            
            # Mettre à jour le profil
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
            serializer = OTPSendSerializer(data=request.data, context={'default_region': getattr(settings, 'PHONENUMBER_DEFAULT_REGION', 'DZ')})
            if serializer.is_valid():
                phone_number = serializer.validated_data['phone_number']
                
                # Get user (authenticated or None for unauthenticated)
                user = request.user if request.user.is_authenticated else None
                
                # Créer l'OTP avec le paramètre request pour la sécurité
                otp, plain_code, error_message = OTPService.create_otp(user, phone_number, request)
                
                if error_message:
                    # Audit de l'échec
                    OTPAuditService.log_otp_creation(phone_number, user, request, False, error_message)
                    return Response({
                        'success': False,
                        'message': error_message
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if not otp:
                    # Audit de l'échec
                    OTPAuditService.log_otp_creation(phone_number, user, request, False, "Erreur lors de la création de l'OTP")
                    return Response({
                        'success': False,
                        'message': 'Erreur lors de la création de l\'OTP'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # Envoyer par SMS via le provider configuré
                sms_success, sms_message = OTPService.send_otp_sms(phone_number, plain_code)
                
                if not sms_success:
                    # En cas d'échec d'envoi SMS, supprimer l'OTP créé
                    otp.delete()
                    # Audit de l'échec
                    OTPAuditService.log_otp_creation(phone_number, user, request, False, f"Erreur SMS: {sms_message}")
                    return Response({
                        'success': False,
                        'message': f'Erreur lors de l\'envoi SMS: {sms_message}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # Audit du succès
                OTPAuditService.log_otp_creation(phone_number, user, request, True)
                
                resp = {
                    'success': True,
                    'message': f'OTP envoyé au {phone_number}',
                    'sms_status': sms_message,
                    'expires_in': '10 minutes',
                    'provider': getattr(settings, 'SMS_PROVIDER', 'console')
                }
                
                # Ne pas inclure le code OTP dans la réponse en production
                if getattr(settings, 'DEBUG', False) and plain_code:
                    resp['debug_code'] = plain_code
                
                return Response(resp)
            else:
                return Response({
                    'success': False,
                    'message': 'Données invalides',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in SendOTPView: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors du traitement de la requête'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            serializer = OTPVerifySerializer(data=request.data, context={'default_region': getattr(settings, 'PHONENUMBER_DEFAULT_REGION', 'DZ')})
            if serializer.is_valid():
                phone_number = serializer.validated_data['phone_number']
                code = serializer.validated_data['code']
                
                # Vérifier l'OTP avec le paramètre request pour la sécurité
                is_valid, user = OTPService.verify_otp(phone_number, code, request.user if request.user.is_authenticated else None, request)
                
                if is_valid:
                    # Audit du succès
                    OTPAuditService.log_otp_verification(phone_number, user, request, True)
                    return Response({
                        'success': True,
                        'message': 'Téléphone vérifié avec succès',
                        'phone_verified': True,
                        'user_id': user.id if user else None
                    })
                else:
                    # Audit de l'échec
                    OTPAuditService.log_otp_verification(phone_number, user, request, False, "Code OTP invalide ou expiré")
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
            logger.error(f"Error in VerifyOTPView: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors du traitement de la requête'
            }, status=status.HTTP_400_BAD_REQUEST)


class PhoneVerificationView(APIView):
    """Vue pour la vérification du téléphone."""
    
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
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

    @swagger_auto_schema(
        operation_description="Vérifier le statut de vérification d'un numéro de téléphone",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Numéro de téléphone à vérifier")
            },
            required=['phone_number']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Statut de vérification du téléphone",
                examples={"application/json": {
                    "success": True,
                    "phone_verified": True,
                    "phone_number": "+261234567890"
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Numéro de téléphone invalide",
                examples={"application/json": {
                    "success": False,
                    "message": "Numéro de téléphone invalide"
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Utilisateur non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Aucun utilisateur trouvé avec ce numéro de téléphone"
                }}
            )
        }
    )
    def post(self, request):
        """Vérifier le statut de vérification d'un numéro de téléphone."""
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
            return Response({
                'success': False,
                'message': 'Numéro de téléphone requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(phone_number=phone_number)
            return Response({
                'success': True,
                'phone_verified': user.is_phone_verified,
                'phone_number': user.phone_number
            })
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Aucun utilisateur trouvé avec ce numéro de téléphone'
            }, status=status.HTTP_404_NOT_FOUND)


class ChangePasswordView(APIView):
    """Vue pour changer le mot de passe."""
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
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
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
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
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
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
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
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
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
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
            # Générer un token sécurisé de reset
            from django.contrib.auth.tokens import PasswordResetTokenGenerator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes
            token_gen = PasswordResetTokenGenerator()
            token = token_gen.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            # TODO: envoyer par email en production (ici, renvoi du token en dev / sandbox)
            payload = {
                'success': True,
                'message': 'Email de réinitialisation envoyé',
            }
            if getattr(settings, 'DEBUG', False):
                payload.update({'uid': uid, 'token': token})
            return Response(payload)
        except User.DoesNotExist:
            # Pour des raisons de sécurité, toujours retourner 200 même si l'utilisateur n'existe pas
            return Response({
                'success': True,
                'message': 'Si un compte existe avec cet email, un lien de réinitialisation a été envoyé'
            })


class ResetPasswordConfirmView(APIView):
    """Vue pour confirmer la réinitialisation du mot de passe."""
    
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    @reset_password_confirm_schema()
    def post(self, request):
        """Confirmer la réinitialisation du mot de passe."""
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            new_password = serializer.validated_data['new_password']
            token = serializer.validated_data.get('token')
            uidb64 = serializer.validated_data.get('uid')
            
            try:
                user = User.objects.get(email=email)
                from django.contrib.auth.tokens import PasswordResetTokenGenerator
                from django.utils.http import urlsafe_base64_decode
                token_gen = PasswordResetTokenGenerator()
                # Si uid est fourni, l'utiliser pour plus de sécurité
                if uidb64:
                    try:
                        uid = int(urlsafe_base64_decode(uidb64).decode())
                        if uid != user.pk:
                            return Response({'success': False, 'message': 'Jeton invalide'}, status=status.HTTP_400_BAD_REQUEST)
                    except Exception:
                        return Response({'success': False, 'message': 'Jeton invalide'}, status=status.HTTP_400_BAD_REQUEST)
                if not token or not token_gen.check_token(user, token):
                    return Response({'success': False, 'message': 'Token de réinitialisation invalide'}, status=status.HTTP_400_BAD_REQUEST)
                user.set_password(new_password)
                user.save()
                return Response({'success': True, 'message': 'Mot de passe réinitialisé avec succès'})
                    
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
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
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
        query = request.GET.get('q', '')
        if not query:
            return Response({
                'success': False,
                'message': 'Paramètre de recherche requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone_number__icontains=query)
        ).exclude(id=request.user.id)[:10]
        
        serializer = UserSerializer(users, many=True)
        return Response({
            'success': True,
            'users': serializer.data,
            'count': len(serializer.data)
        })


class UserStatusView(APIView):
    """Vue pour récupérer le statut complet de l'utilisateur."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer le statut complet de l'utilisateur connecté",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Statut de l'utilisateur",
                examples={"application/json": {
                    "success": True,
                    "user": {
                        "id": 1,
                        "username": "testuser",
                        "email": "user@example.com",
                        "role": "sender",
                        "is_phone_verified": True,
                        "is_document_verified": False,
                        "rating": "4.50",
                        "total_trips": 5,
                        "total_shipments": 12,
                        "is_active_traveler": True,
                        "is_active_sender": False,
                        "wallet_balance": "150.00",
                        "commission_rate": "10.00",
                        "preferred_language": "fr",
                        "created_at": "2024-01-15T10:30:00Z"
                    },
                    "verification_status": {
                        "phone_verified": True,
                        "document_verified": False,
                        "fully_verified": False
                    },
                    "activity_status": {
                        "has_active_trips": True,
                        "has_active_shipments": False,
                        "last_activity": "2024-01-20T15:45:00Z"
                    }
                }}
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description="Non authentifié",
                examples={"application/json": {
                    "success": False,
                    "message": "Authentification requise"
                }}
            )
        }
    )
    def get(self, request):
        """Récupérer le statut complet de l'utilisateur connecté."""
        user = request.user
        
        # Récupérer les informations de base de l'utilisateur
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'is_phone_verified': user.is_phone_verified,
            'is_document_verified': user.is_document_verified,
            'rating': str(user.rating),
            'total_trips': user.total_trips,
            'total_shipments': user.total_shipments,
            'is_active_traveler': user.is_active_traveler,
            'is_active_sender': user.is_active_sender,
            'wallet_balance': str(user.wallet_balance),
            'commission_rate': str(user.commission_rate),
            'preferred_language': user.preferred_language,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
        
        # Statut de vérification
        verification_status = user.get_verification_status()
        
        # Statut d'activité (à implémenter selon les besoins)
        activity_status = {
            'has_active_trips': user.is_active_traveler,
            'has_active_shipments': user.is_active_sender,
            'last_activity': user.updated_at.isoformat() if user.updated_at else None
        }
        
        return Response({
            'success': True,
            'user': user_data,
            'verification_status': verification_status,
            'activity_status': activity_status
        })


class UserVerificationStatusView(APIView):
    """Vue pour récupérer le statut de vérification de l'utilisateur."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer le statut de vérification de l'utilisateur connecté",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Statut de vérification",
                examples={"application/json": {
                    "success": True,
                    "verification_status": {
                        "phone_verified": True,
                        "document_verified": False,
                        "fully_verified": False,
                        "verification_completion": 50
                    },
                    "verification_details": {
                        "phone_number": "+261234567890",
                        "phone_verified": True,
                        "document_uploaded": False,
                        "document_verified": False,
                        "pending_verifications": ["document"]
                    }
                }}
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description="Non authentifié",
                examples={"application/json": {
                    "success": False,
                    "message": "Authentification requise"
                }}
            )
        }
    )
    def get(self, request):
        """Récupérer le statut de vérification de l'utilisateur connecté."""
        user = request.user
        
        # Récupérer le statut de vérification
        verification_status = user.get_verification_status()
        
        # Calculer le pourcentage de completion
        completion_percentage = self._calculate_verification_completion(user)
        
        # Détails de vérification
        verification_details = {
            'phone_number': user.phone_number,
            'phone_verified': user.is_phone_verified,
            'document_uploaded': user.documents.exists(),
            'document_verified': user.is_document_verified,
            'pending_verifications': []
        }
        
        # Déterminer les vérifications en attente
        if not user.is_phone_verified:
            verification_details['pending_verifications'].append('phone')
        if not user.is_document_verified:
            verification_details['pending_verifications'].append('document')
        
        return Response({
            'success': True,
            'verification_status': {
                **verification_status,
                'verification_completion': completion_percentage
            },
            'verification_details': verification_details
        })
    
    def _calculate_verification_completion(self, user):
        """Calculer le pourcentage de completion de la vérification."""
        total_verifications = 2  # phone + document
        completed_verifications = 0
        
        if user.is_phone_verified:
            completed_verifications += 1
        if user.is_document_verified:
            completed_verifications += 1
        
        return int((completed_verifications / total_verifications) * 100)


class UserRequestVerificationView(APIView):
    """Vue pour demander la vérification d'un document."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Demander la vérification d'un document",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['document_id'],
            properties={
                'document_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID du document à vérifier"
                )
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Demande de vérification soumise avec succès",
                examples={"application/json": {
                    "success": True,
                    "message": "Demande de vérification soumise avec succès",
                    "document_id": 1,
                    "status": "pending"
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Données invalides",
                examples={"application/json": {
                    "success": False,
                    "message": "Document introuvable ou déjà vérifié"
                }}
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description="Non authentifié",
                examples={"application/json": {
                    "success": False,
                    "message": "Authentification requise"
                }}
            )
        }
    )
    def post(self, request):
        """Demander la vérification d'un document."""
        document_id = request.data.get('document_id')
        
        if not document_id:
            return Response({
                'success': False,
                'message': 'document_id est requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Vérifier que le document appartient à l'utilisateur connecté
            document = request.user.documents.get(id=document_id)
            
            # Vérifier que le document n'est pas déjà vérifié
            if document.status == 'approved':
                return Response({
                    'success': False,
                    'message': 'Ce document est déjà vérifié'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if document.status == 'rejected':
                return Response({
                    'success': False,
                    'message': 'Ce document a été rejeté. Veuillez télécharger un nouveau document.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier s'il existe déjà une vérification en cours pour ce document
            from verification.models import DocumentVerification
            existing_verification = DocumentVerification.objects.filter(
                document=document,
                status__in=['pending', 'processing']
            ).first()
            
            if existing_verification:
                return Response({
                    'success': True,
                    'message': 'Demande de vérification déjà en cours',
                    'document_id': document_id,
                    'verification_id': str(existing_verification.id),
                    'status': existing_verification.status
                })
            
            # Créer une nouvelle vérification automatique
            verification = DocumentVerification.objects.create(
                user=request.user,
                document=document,
                verification_method='automatic',
                status='pending'
            )
            
            # Lancer la vérification automatique en arrière-plan
            self.start_automatic_verification(verification)
            
            return Response({
                'success': True,
                'message': 'Demande de vérification soumise avec succès',
                'document_id': document_id,
                'verification_id': str(verification.id),
                'status': 'pending',
                'estimated_completion_time': '5 minutes'
            })
            
        except UserDocument.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Document introuvable'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur lors de la demande de vérification: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def start_automatic_verification(self, verification):
        """Démarrer la vérification automatique."""
        try:
            # Simuler la vérification automatique (à remplacer par l'implémentation réelle)
            import threading
            import time
            
            def verify_document():
                time.sleep(2)  # Simulation du traitement
                
                # Mettre à jour le statut
                verification.status = 'approved'
                verification.validation_score = 95.50
                verification.fraud_detection_score = 98.00
                verification.verified_at = timezone.now()
                verification.verification_duration = timezone.timedelta(seconds=2)
                verification.save()
                
                # Mettre à jour le document
                verification.document.status = 'approved'
                verification.document.verified_at = timezone.now()
                verification.document.save()
                
                # Créer un log
                from verification.models import VerificationLog
                VerificationLog.objects.create(
                    verification=verification,
                    log_level='success',
                    message='Vérification automatique terminée avec succès',
                    details={'score': 95.50, 'fraud_score': 98.00}
                )
            
            # Lancer la vérification en arrière-plan
            thread = threading.Thread(target=verify_document)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification automatique: {str(e)}")
            verification.status = 'requires_manual_review'
            verification.save()


class UserLanguagePreferenceView(APIView):
    """Vue pour mettre à jour la préférence de langue de l'utilisateur."""
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Mettre à jour la préférence de langue de l'utilisateur",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['preferred_language'],
            properties={
                'preferred_language': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Code de langue préférée (ex: 'en', 'fr', 'ar')",
                    enum=['en', 'fr', 'ar']
                )
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Préférence de langue mise à jour",
                examples={"application/json": {
                    "success": True,
                    "message": "Préférence de langue mise à jour avec succès",
                    "preferred_language": "en"
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Données invalides",
                examples={"application/json": {
                    "success": False,
                    "message": "Code de langue invalide"
                }}
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description="Non authentifié",
                examples={"application/json": {
                    "success": False,
                    "message": "Authentification requise"
                }}
            )
        }
    )
    def put(self, request):
        """Mettre à jour la préférence de langue de l'utilisateur."""
        preferred_language = request.data.get('preferred_language')
        
        if not preferred_language:
            return Response({
                'success': False,
                'message': 'preferred_language est requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Valider le code de langue
        valid_languages = ['en', 'fr', 'ar']
        if preferred_language not in valid_languages:
            return Response({
                'success': False,
                'message': f'Code de langue invalide. Valeurs acceptées: {", ".join(valid_languages)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Mettre à jour la préférence de langue
            request.user.preferred_language = preferred_language
            request.user.save()
            
            return Response({
                'success': True,
                'message': 'Préférence de langue mise à jour avec succès',
                'preferred_language': preferred_language
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur lors de la mise à jour: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserCommissionPreferenceView(APIView):
    """Vue pour mettre à jour le taux de commission de l'utilisateur."""
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Mettre à jour le taux de commission de l'utilisateur",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['commission_rate'],
            properties={
                'commission_rate': openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description="Taux de commission en pourcentage (ex: 15.0 pour 15%)",
                    minimum=0,
                    maximum=100
                )
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Taux de commission mis à jour",
                examples={"application/json": {
                    "success": True,
                    "message": "Taux de commission mis à jour avec succès",
                    "commission_rate": 15.0
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Données invalides",
                examples={"application/json": {
                    "success": False,
                    "message": "Taux de commission invalide"
                }}
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description="Non authentifié",
                examples={"application/json": {
                    "success": False,
                    "message": "Authentification requise"
                }}
            )
        }
    )
    def put(self, request):
        """Mettre à jour le taux de commission de l'utilisateur."""
        commission_rate = request.data.get('commission_rate')
        
        if commission_rate is None:
            return Response({
                'success': False,
                'message': 'commission_rate est requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            commission_rate = float(commission_rate)
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'message': 'commission_rate doit être un nombre valide'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Valider le taux de commission
        if commission_rate < 0 or commission_rate > 100:
            return Response({
                'success': False,
                'message': 'Le taux de commission doit être entre 0 et 100'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Mettre à jour le taux de commission
            request.user.commission_rate = commission_rate
            request.user.save()
            
            return Response({
                'success': True,
                'message': 'Taux de commission mis à jour avec succès',
                'commission_rate': commission_rate
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur lors de la mise à jour: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserActivateSenderView(APIView):
    """Vue pour activer le mode expéditeur."""
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Activer le mode expéditeur pour l'utilisateur",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Mode expéditeur activé",
                examples={"application/json": {
                    "success": True,
                    "message": "Mode expéditeur activé avec succès",
                    "is_active_sender": True
                }}
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description="Non authentifié",
                examples={"application/json": {
                    "success": False,
                    "message": "Authentification requise"
                }}
            )
        }
    )
    def post(self, request):
        """Activer le mode expéditeur."""
        try:
            request.user.is_active_sender = True
            request.user.save()
            
            return Response({
                'success': True,
                'message': 'Mode expéditeur activé avec succès',
                'is_active_sender': True
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur lors de l\'activation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserActivateTravelerView(APIView):
    """Vue pour activer le mode voyageur."""
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Activer le mode voyageur pour l'utilisateur",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Mode voyageur activé",
                examples={"application/json": {
                    "success": True,
                    "message": "Mode voyageur activé avec succès",
                    "is_active_traveler": True
                }}
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description="Non authentifié",
                examples={"application/json": {
                    "success": False,
                    "message": "Authentification requise"
                }}
            )
        }
    )
    def post(self, request):
        """Activer le mode voyageur."""
        try:
            request.user.is_active_traveler = True
            request.user.save()
            
            return Response({
                'success': True,
                'message': 'Mode voyageur activé avec succès',
                'is_active_traveler': True
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur lors de l\'activation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDeactivateSenderView(APIView):
    """Vue pour désactiver le mode expéditeur."""
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Désactiver le mode expéditeur pour l'utilisateur",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Mode expéditeur désactivé",
                examples={"application/json": {
                    "success": True,
                    "message": "Mode expéditeur désactivé avec succès",
                    "is_active_sender": False
                }}
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description="Non authentifié",
                examples={"application/json": {
                    "success": False,
                    "message": "Authentification requise"
                }}
            )
        }
    )
    def post(self, request):
        """Désactiver le mode expéditeur."""
        try:
            request.user.is_active_sender = False
            request.user.save()
            
            return Response({
                'success': True,
                'message': 'Mode expéditeur désactivé avec succès',
                'is_active_sender': False
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur lors de la désactivation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDeactivateTravelerView(APIView):
    """Vue pour désactiver le mode voyageur."""
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Désactiver le mode voyageur pour l'utilisateur",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Mode voyageur désactivé",
                examples={"application/json": {
                    "success": True,
                    "message": "Mode voyageur désactivé avec succès",
                    "is_active_traveler": False
                }}
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description="Non authentifié",
                examples={"application/json": {
                    "success": False,
                    "message": "Authentification requise"
                }}
            )
        }
    )
    def post(self, request):
        """Désactiver le mode voyageur."""
        try:
            request.user.is_active_traveler = False
            request.user.save()
            
            return Response({
                'success': True,
                'message': 'Mode voyageur désactivé avec succès',
                'is_active_traveler': False
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur lors de la désactivation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserAnalyticsView(APIView):
    """Vue pour récupérer les analytics de l'utilisateur."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer les analytics de l'utilisateur connecté",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Analytics de l'utilisateur",
                examples={"application/json": {
                    "success": True,
                    "analytics": {
                        "total_trips": 15,
                        "total_shipments": 28,
                        "completed_trips": 12,
                        "completed_shipments": 25,
                        "pending_trips": 3,
                        "pending_shipments": 3,
                        "total_earnings": "2500.00",
                        "total_spent": "800.00",
                        "average_rating": "4.75",
                        "total_ratings": 20,
                        "monthly_stats": {
                            "current_month": {
                                "trips": 5,
                                "shipments": 8,
                                "earnings": "450.00"
                            },
                            "previous_month": {
                                "trips": 4,
                                "shipments": 6,
                                "earnings": "380.00"
                            }
                        }
                    }
                }}
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description="Non authentifié",
                examples={"application/json": {
                    "success": False,
                    "message": "Authentification requise"
                }}
            )
        }
    )
    def get(self, request):
        """Récupérer les analytics de l'utilisateur."""
        user = request.user
        
        # Calculer les statistiques de base
        analytics = {
            'total_trips': user.total_trips,
            'total_shipments': user.total_shipments,
            'completed_trips': 0,  # À calculer depuis les modèles
            'completed_shipments': 0,  # À calculer depuis les modèles
            'pending_trips': 0,  # À calculer depuis les modèles
            'pending_shipments': 0,  # À calculer depuis les modèles
            'total_earnings': "0.00",  # À calculer depuis les transactions
            'total_spent': "0.00",  # À calculer depuis les transactions
            'average_rating': str(user.rating),
            'total_ratings': 0,  # À calculer depuis les ratings
            'monthly_stats': {
                'current_month': {
                    'trips': 0,
                    'shipments': 0,
                    'earnings': "0.00"
                },
                'previous_month': {
                    'trips': 0,
                    'shipments': 0,
                    'earnings': "0.00"
                }
            }
        }
        
        return Response({
            'success': True,
            'analytics': analytics
        })


class UserPerformanceView(APIView):
    """Vue pour récupérer les performances de l'utilisateur."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer les performances de l'utilisateur connecté",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Performances de l'utilisateur",
                examples={"application/json": {
                    "success": True,
                    "performance": {
                        "completion_rate": 85.5,
                        "average_delivery_time": "2.5 days",
                        "customer_satisfaction": 4.8,
                        "on_time_delivery_rate": 92.0,
                        "total_distance_traveled": "1500 km",
                        "total_packages_delivered": 45,
                        "performance_score": 88.5,
                        "monthly_trends": {
                            "delivery_speed": "improving",
                            "customer_rating": "stable",
                            "completion_rate": "improving"
                        }
                    }
                }}
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description="Non authentifié",
                examples={"application/json": {
                    "success": False,
                    "message": "Authentification requise"
                }}
            )
        }
    )
    def get(self, request):
        """Récupérer les performances de l'utilisateur."""
        user = request.user
        
        # Calculer les performances de base
        performance = {
            'completion_rate': 85.5,  # À calculer depuis les données
            'average_delivery_time': "2.5 days",  # À calculer depuis les données
            'customer_satisfaction': float(user.rating),
            'on_time_delivery_rate': 92.0,  # À calculer depuis les données
            'total_distance_traveled': "0 km",  # À calculer depuis les données
            'total_packages_delivered': 0,  # À calculer depuis les données
            'performance_score': 88.5,  # À calculer depuis les données
            'monthly_trends': {
                'delivery_speed': 'stable',
                'customer_rating': 'stable',
                'completion_rate': 'stable'
            }
        }
        
        return Response({
            'success': True,
            'performance': performance
        })


class UserStatsView(APIView):
    """Vue pour récupérer les statistiques de l'utilisateur."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer les statistiques de l'utilisateur connecté",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Statistiques de l'utilisateur",
                examples={"application/json": {
                    "success": True,
                    "stats": {
                        "total_trips": 5,
                        "total_shipments": 12,
                        "completed_trips": 4,
                        "completed_shipments": 10,
                        "pending_trips": 1,
                        "pending_shipments": 2,
                        "total_earnings": "500.00",
                        "total_spent": "150.00",
                        "average_rating": "4.50",
                        "total_ratings": 8,
                        "verification_completion": 75,
                        "account_age_days": 45,
                        "last_activity": "2024-01-20T15:45:00Z"
                    },
                    "recent_activity": [
                        {
                            "type": "shipment_created",
                            "description": "Nouvel envoi créé",
                            "date": "2024-01-20T10:30:00Z"
                        },
                        {
                            "type": "trip_completed",
                            "description": "Trajet terminé avec succès",
                            "date": "2024-01-19T14:20:00Z"
                        }
                    ]
                }}
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description="Non authentifié",
                examples={"application/json": {
                    "success": False,
                    "message": "Authentification requise"
                }}
            )
        }
    )
    def get(self, request):
        """Récupérer les statistiques de l'utilisateur connecté."""
        user = request.user
        
        # Calculer les statistiques de base
        stats = {
            'total_trips': user.total_trips,
            'total_shipments': user.total_shipments,
            'completed_trips': user.total_trips,  # À remplacer par la logique métier
            'completed_shipments': user.total_shipments,  # À remplacer par la logique métier
            'pending_trips': 0,  # À calculer depuis les modèles Trip
            'pending_shipments': 0,  # À calculer depuis les modèles Shipment
            'total_earnings': str(user.wallet_balance),  # À calculer depuis les transactions
            'total_spent': "0.00",  # À calculer depuis les transactions
            'average_rating': str(user.rating),
            'total_ratings': 0,  # À calculer depuis les modèles Rating
            'verification_completion': self._calculate_verification_completion(user),
            'account_age_days': self._calculate_account_age_days(user),
            'last_activity': user.updated_at.isoformat() if user.updated_at else None
        }
        
        # Activité récente (placeholder - à implémenter selon les besoins)
        recent_activity = [
            {
                'type': 'account_created',
                'description': 'Compte créé',
                'date': user.created_at.isoformat() if user.created_at else None
            }
        ]
        
        return Response({
            'success': True,
            'stats': stats,
            'recent_activity': recent_activity
        })
    
    def _calculate_verification_completion(self, user):
        """Calculer le pourcentage de vérification du compte."""
        completion = 0
        if user.is_phone_verified:
            completion += 50
        if user.is_document_verified:
            completion += 50
        return completion
    
    def _calculate_account_age_days(self, user):
        """Calculer l'âge du compte en jours."""
        if user.created_at:
            from django.utils import timezone
            now = timezone.now()
            age = now - user.created_at
            return age.days
        return 0

class UserWalletView(APIView):
    """Vue pour la gestion du portefeuille - Redirection vers payments app."""
    
    permission_classes = [IsVerifiedForTransactions]
    
    @swagger_auto_schema(
        operation_description="Récupérer le portefeuille de l'utilisateur",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Portefeuille récupéré",
                examples={"application/json": {
                    "success": True,
                    "wallet": {
                        "id": 1,
                        "user": 1,
                        "balance": 1500.00,
                        "currency": "DZD",
                        "is_active": True,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                }}
            )
        }
    )
    def get(self, request):
        """Récupérer le portefeuille de l'utilisateur."""
        # Import the WalletView from payments app
        from payments.views import WalletView
        
        # Create an instance of WalletView and call its get method
        wallet_view = WalletView()
        wallet_view.request = request
        wallet_view.format_kwarg = None
        
        return wallet_view.get(request)


class UserDepositView(APIView):
    """Vue pour les dépôts - Redirection vers payments app."""
    
    permission_classes = [IsVerifiedForTransactions]
    
    @swagger_auto_schema(
        operation_description="Effectuer un dépôt",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                'payment_method': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['card', 'bank_transfer', 'chargily']
                )
            },
            required=['amount']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Dépôt effectué",
                examples={"application/json": {
                    "success": True,
                    "message": "Dépôt effectué avec succès",
                    "transaction": {
                        "id": 1,
                        "transaction_type": "deposit",
                        "amount": 500.00,
                        "currency": "DZD",
                        "payment_method": "card",
                        "status": "completed",
                        "reference": "DEP123456"
                    },
                    "new_balance": 2000.00
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "message": "Montant invalide"
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Portefeuille non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Portefeuille non trouvé"
                }}
            )
        }
    )
    def post(self, request):
        """Effectuer un dépôt."""
        # Import the WalletDepositView from payments app
        from payments.views import WalletDepositView
        
        # Create an instance of WalletDepositView and call its post method
        deposit_view = WalletDepositView()
        deposit_view.request = request
        deposit_view.format_kwarg = None
        
        return deposit_view.post(request)


class UserWithdrawView(APIView):
    """Vue pour les retraits - Redirection vers payments app."""
    
    permission_classes = [IsVerifiedForTransactions]
    
    @swagger_auto_schema(
        operation_description="Effectuer un retrait",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                'payment_method': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['bank_transfer', 'mobile_money']
                ),
                'bank_account': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['amount']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Retrait effectué",
                examples={"application/json": {
                    "success": True,
                    "message": "Retrait effectué avec succès",
                    "transaction": {
                        "id": 1,
                        "transaction_type": "withdrawal",
                        "amount": 500.00,
                        "currency": "DZD",
                        "payment_method": "bank_transfer",
                        "status": "completed",
                        "reference": "WIT123456"
                    },
                    "new_balance": 1000.00
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "message": "Montant invalide ou solde insuffisant"
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Portefeuille non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Portefeuille non trouvé"
                }}
            )
        }
    )
    def post(self, request):
        """Effectuer un retrait."""
        # Import the WalletWithdrawView from payments app
        from payments.views import WalletWithdrawView
        
        # Create an instance of WalletWithdrawView and call its post method
        withdraw_view = WalletWithdrawView()
        withdraw_view.request = request
        withdraw_view.format_kwarg = None
        
        return withdraw_view.post(request)


class UserTransferView(APIView):
    """Vue pour les transferts - Redirection vers payments app."""
    
    permission_classes = [IsVerifiedForTransactions]
    
    @swagger_auto_schema(
        operation_description="Effectuer un transfert",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'recipient_email': openapi.Schema(type=openapi.TYPE_STRING),
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                'description': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['recipient_email', 'amount']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Transfert effectué",
                examples={"application/json": {
                    "success": True,
                    "message": "Transfert effectué avec succès",
                    "transaction": {
                        "id": 1,
                        "transaction_type": "transfer",
                        "amount": 500.00,
                        "currency": "DZD",
                        "payment_method": "wallet_transfer",
                        "status": "completed",
                        "reference": "TRF123456"
                    },
                    "new_balance": 1000.00
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "message": "Montant invalide ou destinataire non trouvé"
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Portefeuille non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Portefeuille non trouvé"
                }}
            )
        }
    )
    def post(self, request):
        """Effectuer un transfert."""
        # Import the WalletTransferView from payments app
        from payments.views import WalletTransferView
        
        # Create an instance of WalletTransferView and call its post method
        transfer_view = WalletTransferView()
        transfer_view.request = request
        transfer_view.format_kwarg = None
        
        return transfer_view.post(request)


class UserTransactionListView(APIView):
    """Vue pour la liste des transactions - Redirection vers payments app."""
    
    permission_classes = [IsVerifiedForTransactions]
    
    @swagger_auto_schema(
        operation_description="Récupérer l'historique des transactions",
        manual_parameters=[
            openapi.Parameter(
                'transaction_type',
                openapi.IN_QUERY,
                description="Type de transaction",
                type=openapi.TYPE_STRING,
                enum=['deposit', 'withdrawal', 'transfer', 'payment', 'refund']
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Statut de la transaction",
                type=openapi.TYPE_STRING,
                enum=['pending', 'completed', 'failed', 'cancelled']
            ),
            openapi.Parameter(
                'date_from',
                openapi.IN_QUERY,
                description="Date de début (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            ),
            openapi.Parameter(
                'date_to',
                openapi.IN_QUERY,
                description="Date de fin (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des transactions",
                examples={"application/json": {
                    "success": True,
                    "transactions": [
                        {
                            "id": 1,
                            "transaction_type": "deposit",
                            "amount": 500.00,
                            "currency": "DZD",
                            "payment_method": "card",
                            "status": "completed",
                            "transaction_id": "TXN123456",
                            "created_at": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "count": 1
                }}
            )
        }
    )
    def get(self, request):
        """Récupérer l'historique des transactions."""
        # Import the WalletTransactionsView from payments app
        from payments.views import WalletTransactionsView
        
        # Create an instance of WalletTransactionsView and call its get method
        transaction_view = WalletTransactionsView()
        transaction_view.request = request
        transaction_view.format_kwarg = None
        
        return transaction_view.get(request)
