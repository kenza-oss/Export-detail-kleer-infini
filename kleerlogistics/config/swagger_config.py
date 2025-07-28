"""
Configuration Swagger pour KleerLogistics
"""

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status

def user_registration_schema():
    """Schéma pour l'inscription utilisateur."""
    return swagger_auto_schema(
        operation_description="Inscription d'un nouvel utilisateur avec gestion des rôles",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description="Nom d'utilisateur unique"),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="Adresse email"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description="Mot de passe (min 8 caractères)"),
                'password_confirm': openapi.Schema(type=openapi.TYPE_STRING, description="Confirmation du mot de passe"),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description="Prénom"),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de famille"),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Numéro de téléphone (+213...)"),
                'role': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['sender', 'traveler', 'admin', 'both'],
                    description="Rôle utilisateur"
                )
            },
            required=['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Utilisateur créé avec succès",
                examples={"application/json": {
                    "success": True,
                    "message": "Utilisateur créé avec succès",
                    "user_id": 1,
                    "email": "john.doe@example.com",
                    "role": "sender"
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "errors": {
                        "email": ["Cette adresse email est déjà utilisée."],
                        "password": ["Ce mot de passe est trop court."],
                        "phone_number": ["Ce numéro de téléphone est déjà utilisé."]
                    }
                }}
            )
        }
    )

def user_login_schema():
    """Schéma pour la connexion utilisateur."""
    return swagger_auto_schema(
        operation_description="Connexion utilisateur avec authentification JWT",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description="Nom d'utilisateur"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description="Mot de passe")
            },
            required=['username', 'password']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Connexion réussie",
                examples={"application/json": {
                    "success": True,
                    "message": "Connexion réussie",
                    "tokens": {
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                    },
                    "user": {
                        "id": 1,
                        "username": "john_doe",
                        "email": "john.doe@example.com",
                        "role": "sender",
                        "permissions": {
                            "is_admin": False,
                            "is_sender": True,
                            "is_traveler": False,
                            "can_access_admin_panel": False
                        }
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Identifiants invalides",
                examples={"application/json": {
                    "success": False,
                    "message": "Identifiants invalides"
                }}
            )
        }
    )

def user_profile_get_schema():
    """Schéma pour récupérer le profil utilisateur."""
    return swagger_auto_schema(
        operation_description="Récupérer le profil de l'utilisateur connecté",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Profil utilisateur",
                examples={"application/json": {
                    "success": True,
                    "profile": {
                        "id": 1,
                        "user": 1,
                        "phone_number": "+213123456789",
                        "birth_date": "1990-01-01",
                        "address": "123 Rue de la Paix",
                        "city": "Alger",
                        "country": "Algeria",
                        "rating": 4.5,
                        "total_trips": 25,
                        "total_shipments": 15,
                        "is_verified": True
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

def user_profile_update_schema():
    """Schéma pour mettre à jour le profil utilisateur."""
    return swagger_auto_schema(
        operation_description="Mettre à jour le profil de l'utilisateur connecté",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'address': openapi.Schema(type=openapi.TYPE_STRING, description="Adresse"),
                'city': openapi.Schema(type=openapi.TYPE_STRING, description="Ville"),
                'country': openapi.Schema(type=openapi.TYPE_STRING, description="Pays"),
                'birth_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Date de naissance (YYYY-MM-DD)"),
                'avatar': openapi.Schema(type=openapi.TYPE_FILE, description="Photo de profil"),
                'bio': openapi.Schema(type=openapi.TYPE_STRING, description="Biographie")
            }
        ),
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Profil mis à jour",
                examples={"application/json": {
                    "success": True,
                    "message": "Profil mis à jour avec succès",
                    "profile": {
                        "id": 1,
                        "address": "123 Rue de la Paix",
                        "city": "Alger",
                        "country": "Algeria",
                        "birth_date": "1990-01-01"
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "errors": {
                        "birth_date": ["Format de date invalide. Utilisez YYYY-MM-DD."]
                    }
                }}
            )
        }
    )

def phone_verification_schema():
    """Schéma pour vérifier le statut du téléphone."""
    return swagger_auto_schema(
        operation_description="Récupérer le statut de vérification du téléphone",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Statut de vérification",
                examples={"application/json": {
                    "success": True,
                    "phone_verified": True,
                    "phone_number": "+213123456789"
                }}
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description="Authentification requise",
                examples={"application/json": {
                    "success": False,
                    "message": "Authentification requise pour vérifier le statut du téléphone"
                }}
            )
        }
    )

def reset_password_confirm_schema():
    """Schéma pour confirmer la réinitialisation de mot de passe."""
    return swagger_auto_schema(
        operation_description="Confirmer la réinitialisation de mot de passe avec token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="Adresse email"),
                'token': openapi.Schema(type=openapi.TYPE_STRING, description="Token de réinitialisation"),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description="Nouveau mot de passe (min 8 caractères)"),
                'new_password_confirm': openapi.Schema(type=openapi.TYPE_STRING, description="Confirmation du nouveau mot de passe")
            },
            required=['email', 'token', 'new_password', 'new_password_confirm']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Mot de passe réinitialisé",
                examples={"application/json": {
                    "success": True,
                    "message": "Mot de passe réinitialisé avec succès"
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "errors": {
                        "token": ["Token de réinitialisation invalide"],
                        "new_password_confirm": ["Les mots de passe ne correspondent pas."]
                    }
                }}
            )
        }
    )

def user_document_upload_schema():
    """Schéma pour l'upload de documents."""
    return swagger_auto_schema(
        operation_description="Uploader un document utilisateur",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'document_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['passport', 'national_id', 'flight_ticket', 'address_proof'],
                    description="Type de document"
                ),
                'document_file': openapi.Schema(type=openapi.TYPE_FILE, description="Fichier document")
            },
            required=['document_type', 'document_file']
        ),
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Document uploadé",
                examples={"application/json": {
                    "success": True,
                    "message": "Document uploadé avec succès",
                    "document": {
                        "id": 1,
                        "document_type": "passport",
                        "status": "pending",
                        "uploaded_at": "2024-01-15T10:30:00Z"
                    }
                }}
            )
        }
    )

def user_document_list_schema():
    """Schéma pour la liste des documents."""
    return swagger_auto_schema(
        operation_description="Récupérer la liste des documents de l'utilisateur",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des documents",
                examples={"application/json": {
                    "success": True,
                    "documents": [
                        {
                            "id": 1,
                            "document_type": "passport",
                            "status": "approved",
                            "uploaded_at": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "count": 1
                }}
            )
        }
    )

def user_search_schema():
    """Schéma pour la recherche d'utilisateurs."""
    return swagger_auto_schema(
        operation_description="Rechercher des utilisateurs",
        manual_parameters=[
            openapi.Parameter(
                'q',
                openapi.IN_QUERY,
                description="Terme de recherche",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Résultats de recherche",
                examples={"application/json": {
                    "success": True,
                    "users": [
                        {
                            "id": 1,
                            "username": "john_doe",
                            "first_name": "John",
                            "last_name": "Doe",
                            "role": "sender",
                            "rating": 4.5,
                            "is_document_verified": True
                        }
                    ],
                    "count": 1
                }}
            )
        }
    )

def admin_user_list_schema():
    """Schéma pour la liste des utilisateurs (admin)."""
    return swagger_auto_schema(
        operation_description="Récupérer la liste de tous les utilisateurs (Admin uniquement)",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer) - Admin requis",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des utilisateurs",
                examples={"application/json": {
                    "success": True,
                    "users": [
                        {
                            "id": 1,
                            "username": "john_doe",
                            "email": "john.doe@example.com",
                            "role": "sender",
                            "is_phone_verified": True,
                            "is_document_verified": True,
                            "is_active": True
                        }
                    ],
                    "count": 1
                }}
            ),
            status.HTTP_403_FORBIDDEN: openapi.Response(
                description="Accès refusé",
                examples={"application/json": {
                    "success": False,
                    "message": "Accès refusé. Permissions insuffisantes."
                }}
            )
        }
    )

def role_update_schema():
    """Schéma pour la mise à jour de rôle (admin)."""
    return swagger_auto_schema(
        operation_description="Mettre à jour le rôle d'un utilisateur (Admin uniquement)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'role': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['sender', 'traveler', 'admin', 'both'],
                    description="Nouveau rôle"
                )
            },
            required=['role']
        ),
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer) - Admin requis",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Rôle mis à jour",
                examples={"application/json": {
                    "success": True,
                    "message": "Rôle mis à jour vers traveler",
                    "user": {
                        "id": 1,
                        "username": "john_doe",
                        "role": "traveler"
                    }
                }}
            ),
            status.HTTP_403_FORBIDDEN: openapi.Response(
                description="Accès refusé",
                examples={"application/json": {
                    "success": False,
                    "message": "Accès refusé. Permissions insuffisantes."
                }}
            )
        }
    )

# Schémas pour les shipments
def shipment_create_schema():
    """Schéma pour la création d'expédition."""
    return swagger_auto_schema(
        operation_description="Créer une nouvelle expédition",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Titre de l'expédition"),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description"),
                'origin_address': openapi.Schema(type=openapi.TYPE_STRING, description="Adresse d'origine"),
                'destination_address': openapi.Schema(type=openapi.TYPE_STRING, description="Adresse de destination"),
                'weight': openapi.Schema(type=openapi.TYPE_NUMBER, description="Poids en kg"),
                'fragile': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Colis fragile"),
                'urgent': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Livraison urgente"),
                'estimated_value': openapi.Schema(type=openapi.TYPE_NUMBER, description="Valeur estimée"),
                'category': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['documents', 'electronics', 'clothing', 'furniture', 'other'],
                    description="Catégorie"
                )
            },
            required=['title', 'origin_address', 'destination_address', 'weight']
        ),
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Expédition créée",
                examples={"application/json": {
                    "success": True,
                    "message": "Expédition créée avec succès",
                    "shipment": {
                        "id": 1,
                        "title": "Livraison de documents urgents",
                        "status": "pending",
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                }}
            )
        }
    )

def shipment_list_schema():
    """Schéma pour la liste des expéditions."""
    return swagger_auto_schema(
        operation_description="Récupérer la liste des expéditions",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des expéditions",
                examples={"application/json": {
                    "success": True,
                    "shipments": [
                        {
                            "id": 1,
                            "title": "Livraison de documents urgents",
                            "status": "pending",
                            "created_at": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "count": 1
                }}
            )
        }
    )

def shipment_update_schema():
    """Schéma pour la mise à jour d'expédition."""
    return swagger_auto_schema(
        operation_description="Mettre à jour une expédition",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Titre"),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description"),
                'urgent': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Urgent")
            }
        ),
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Expédition mise à jour",
                examples={"application/json": {
                    "success": True,
                    "message": "Expédition mise à jour avec succès"
                }}
            )
        }
    )

# Schémas pour les trips
def trip_create_schema():
    """Schéma pour la création de voyage."""
    return swagger_auto_schema(
        operation_description="Créer un nouveau voyage",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Titre du voyage"),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description"),
                'origin_address': openapi.Schema(type=openapi.TYPE_STRING, description="Adresse d'origine"),
                'destination_address': openapi.Schema(type=openapi.TYPE_STRING, description="Adresse de destination"),
                'departure_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Date de départ"),
                'arrival_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Date d'arrivée"),
                'available_space': openapi.Schema(type=openapi.TYPE_NUMBER, description="Espace disponible"),
                'max_weight': openapi.Schema(type=openapi.TYPE_NUMBER, description="Poids maximum"),
                'price_per_kg': openapi.Schema(type=openapi.TYPE_NUMBER, description="Prix par kg"),
                'vehicle_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['car', 'van', 'truck', 'motorcycle'],
                    description="Type de véhicule"
                )
            },
            required=['title', 'origin_address', 'destination_address', 'departure_date', 'arrival_date']
        ),
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Voyage créé",
                examples={"application/json": {
                    "success": True,
                    "message": "Voyage créé avec succès",
                    "trip": {
                        "id": 1,
                        "title": "Voyage Paris-Lyon",
                        "status": "active",
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                }}
            )
        }
    )

def trip_search_schema():
    """Schéma pour la recherche de voyages."""
    return swagger_auto_schema(
        operation_description="Rechercher des voyages",
        manual_parameters=[
            openapi.Parameter(
                'origin',
                openapi.IN_QUERY,
                description="Ville d'origine",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'destination',
                openapi.IN_QUERY,
                description="Ville de destination",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Résultats de recherche",
                examples={"application/json": {
                    "success": True,
                    "trips": [
                        {
                            "id": 1,
                            "title": "Voyage Paris-Lyon",
                            "status": "active",
                            "created_at": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "count": 1
                }}
            )
        }
    )

# Schémas pour le matching
def matching_accept_schema():
    """Schéma pour accepter un match."""
    return swagger_auto_schema(
        operation_description="Accepter un match",
        manual_parameters=[
            openapi.Parameter(
                'match_id',
                openapi.IN_PATH,
                description="ID du match",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'accepted_price': openapi.Schema(type=openapi.TYPE_NUMBER, description="Prix accepté"),
                'message': openapi.Schema(type=openapi.TYPE_STRING, description="Message optionnel")
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Match accepté",
                examples={"application/json": {
                    "success": True,
                    "message": "Match accepté avec succès",
                    "match": {
                        "id": 1,
                        "status": "accepted",
                        "accepted_price": 150.00,
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                }}
            ),
            status.HTTP_403_FORBIDDEN: openapi.Response(
                description="Non autorisé",
                examples={"application/json": {
                    "success": False,
                    "message": "Non autorisé"
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Match non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Match non trouvé"
                }}
            )
        }
    )

def matching_reject_schema():
    """Schéma pour rejeter un match."""
    return swagger_auto_schema(
        operation_description="Rejeter un match",
        manual_parameters=[
            openapi.Parameter(
                'match_id',
                openapi.IN_PATH,
                description="ID du match",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'reason': openapi.Schema(type=openapi.TYPE_STRING, description="Raison du rejet"),
                'message': openapi.Schema(type=openapi.TYPE_STRING, description="Message optionnel")
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Match rejeté",
                examples={"application/json": {
                    "success": True,
                    "message": "Match rejeté avec succès",
                    "match": {
                        "id": 1,
                        "status": "rejected",
                        "rejection_reason": "Prix trop élevé",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                }}
            ),
            status.HTTP_403_FORBIDDEN: openapi.Response(
                description="Non autorisé",
                examples={"application/json": {
                    "success": False,
                    "message": "Non autorisé"
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Match non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Match non trouvé"
                }}
            )
        }
    ) 

def payment_create_schema():
    """Schéma pour la création de paiement."""
    return swagger_auto_schema(
        operation_description="Créer un nouveau paiement",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER, description="Montant du paiement"),
                'currency': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['EUR', 'USD', 'DZD'],
                    description="Devise du paiement"
                ),
                'payment_method': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['card', 'bank_transfer', 'chargily', 'wallet'],
                    description="Méthode de paiement"
                ),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description du paiement"),
                'shipment_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de l'expédition (optionnel)")
            },
            required=['amount', 'currency', 'payment_method']
        ),
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Paiement créé",
                examples={"application/json": {
                    "success": True,
                    "message": "Paiement créé avec succès",
                    "payment": {
                        "id": 1,
                        "amount": 125.50,
                        "currency": "EUR",
                        "payment_method": "card",
                        "status": "pending",
                        "reference": "PAY123456",
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "message": "Montant invalide"
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

def document_upload_schema():
    """Schéma pour l'upload de documents."""
    return swagger_auto_schema(
        operation_description="Uploader un document",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'document_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['invoice', 'receipt', 'contract', 'custom'],
                    description="Type de document"
                ),
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Titre du document"),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description du document"),
                'file': openapi.Schema(type=openapi.TYPE_FILE, description="Fichier document")
            },
            required=['document_type', 'title']
        ),
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Document uploadé",
                examples={"application/json": {
                    "success": True,
                    "message": "Document uploadé avec succès",
                    "document": {
                        "id": 1,
                        "document_type": "invoice",
                        "title": "Facture INV12345678",
                        "status": "uploaded",
                        "uploaded_at": "2024-01-15T10:30:00Z"
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "message": "Type de document invalide"
                }}
            )
        }
    )

def document_list_schema():
    """Schéma pour la liste des documents."""
    return swagger_auto_schema(
        operation_description="Récupérer la liste des documents",
        manual_parameters=[
            openapi.Parameter(
                'document_type',
                openapi.IN_QUERY,
                description="Type de document",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Statut du document",
                type=openapi.TYPE_STRING,
                enum=['generated', 'uploaded', 'pending', 'completed']
            ),
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des documents",
                examples={"application/json": {
                    "success": True,
                    "documents": [
                        {
                            "id": 1,
                            "document_type": "invoice",
                            "title": "Facture INV12345678",
                            "status": "generated",
                            "created_at": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "count": 1
                }}
            )
        }
    )

def document_verify_schema():
    """Schéma pour la vérification de documents."""
    return swagger_auto_schema(
        operation_description="Vérifier un document",
        manual_parameters=[
            openapi.Parameter(
                'document_id',
                openapi.IN_PATH,
                description="ID du document",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'verification_status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['approved', 'rejected'],
                    description="Statut de vérification"
                ),
                'verification_notes': openapi.Schema(type=openapi.TYPE_STRING, description="Notes de vérification")
            },
            required=['verification_status']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Document vérifié",
                examples={"application/json": {
                    "success": True,
                    "message": "Document vérifié avec succès",
                    "document": {
                        "id": 1,
                        "status": "verified",
                        "verified_at": "2024-01-16T14:20:00Z",
                        "verification_notes": "Document vérifié et approuvé"
                    }
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Document non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Document non trouvé"
                }}
            )
        }
    ) 

def notification_send_schema():
    """Schéma pour l'envoi de notifications."""
    return swagger_auto_schema(
        operation_description="Envoyer une notification",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'notification_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['email', 'sms', 'push'],
                    description="Type de notification"
                ),
                'recipient_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID du destinataire"),
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Titre de la notification"),
                'message': openapi.Schema(type=openapi.TYPE_STRING, description="Message de la notification"),
                'template_name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom du modèle (optionnel)"),
                'context': openapi.Schema(type=openapi.TYPE_OBJECT, description="Contexte pour le modèle")
            },
            required=['notification_type', 'recipient_id', 'title', 'message']
        ),
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Notification envoyée",
                examples={"application/json": {
                    "success": True,
                    "message": "Notification envoyée avec succès",
                    "notification": {
                        "id": 1,
                        "notification_type": "email",
                        "title": "Nouvelle correspondance trouvée",
                        "message": "Une correspondance a été trouvée pour votre expédition",
                        "status": "sent",
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "message": "Type de notification invalide"
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Destinataire non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Destinataire non trouvé"
                }}
            )
        }
    )

def notification_list_schema():
    """Schéma pour la liste des notifications."""
    return swagger_auto_schema(
        operation_description="Récupérer la liste des notifications",
        manual_parameters=[
            openapi.Parameter(
                'notification_type',
                openapi.IN_QUERY,
                description="Type de notification",
                type=openapi.TYPE_STRING,
                enum=['email', 'sms', 'push', 'all']
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Statut de la notification",
                type=openapi.TYPE_STRING,
                enum=['sent', 'pending', 'failed', 'read', 'unread']
            ),
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des notifications",
                examples={"application/json": {
                    "success": True,
                    "notifications": [
                        {
                            "id": 1,
                            "notification_type": "email",
                            "title": "Nouvelle correspondance trouvée",
                            "message": "Une correspondance a été trouvée pour votre expédition",
                            "status": "sent",
                            "created_at": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "count": 1
                }}
            )
        }
    ) 

def analytics_dashboard_schema():
    """Schéma pour les analytics du tableau de bord."""
    return swagger_auto_schema(
        operation_description="Récupérer les analytics du tableau de bord",
        manual_parameters=[
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
            ),
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Analytics du tableau de bord",
                examples={"application/json": {
                    "success": True,
                    "analytics": {
                        "general": {
                            "total_users": 1250,
                            "total_shipments": 450,
                            "total_trips": 180,
                            "active_shipments": 45,
                            "completed_shipments": 380,
                            "active_trips": 25,
                            "completed_trips": 150
                        },
                        "shipments": {
                            "total_shipments": 45,
                            "pending_shipments": 8,
                            "in_transit_shipments": 12,
                            "delivered_shipments": 20,
                            "cancelled_shipments": 5,
                            "total_revenue": 2500.00,
                            "average_delivery_time": 3.2
                        },
                        "trips": {
                            "total_trips": 15,
                            "active_trips": 3,
                            "completed_trips": 10,
                            "cancelled_trips": 2,
                            "total_earnings": 1800.00,
                            "average_rating": 4.8
                        }
                    }
                }}
            )
        }
    )

def analytics_shipment_schema():
    """Schéma pour les analytics des expéditions."""
    return swagger_auto_schema(
        operation_description="Récupérer les analytics des expéditions",
        manual_parameters=[
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
            ),
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Analytics des expéditions",
                examples={"application/json": {
                    "success": True,
                    "shipment_analytics": {
                        "status_distribution": [
                            {"status": "pending", "count": 8, "percentage": 17.8},
                            {"status": "in_transit", "count": 12, "percentage": 26.7},
                            {"status": "delivered", "count": 20, "percentage": 44.4},
                            {"status": "cancelled", "count": 5, "percentage": 11.1}
                        ],
                        "monthly_trends": [
                            {"month": "2024-01", "count": 15, "revenue": 1200.00},
                            {"month": "2024-02", "count": 18, "revenue": 1400.00}
                        ],
                        "top_destinations": [
                            {"destination": "Lyon", "count": 8, "revenue": 640.00},
                            {"destination": "Marseille", "count": 6, "revenue": 480.00},
                            {"destination": "Toulouse", "count": 4, "revenue": 320.00}
                        ]
                    }
                }}
            )
        }
    )

def analytics_trip_schema():
    """Schéma pour les analytics des voyages."""
    return swagger_auto_schema(
        operation_description="Récupérer les analytics des voyages",
        manual_parameters=[
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
            ),
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Analytics des voyages",
                examples={"application/json": {
                    "success": True,
                    "trip_analytics": {
                        "status_distribution": [
                            {"status": "active", "count": 3, "percentage": 20.0},
                            {"status": "completed", "count": 10, "percentage": 66.7},
                            {"status": "cancelled", "count": 2, "percentage": 13.3}
                        ],
                        "monthly_trends": [
                            {"month": "2024-01", "count": 8, "earnings": 1200.00},
                            {"month": "2024-02", "count": 7, "earnings": 1000.00}
                        ],
                        "top_routes": [
                            {"route": "Paris-Lyon", "count": 5, "earnings": 750.00},
                            {"route": "Paris-Marseille", "count": 3, "earnings": 450.00},
                            {"route": "Lyon-Toulouse", "count": 2, "earnings": 300.00}
                        ]
                    }
                }}
            )
        }
    )

def analytics_financial_schema():
    """Schéma pour les analytics financiers."""
    return swagger_auto_schema(
        operation_description="Récupérer les analytics financiers",
        manual_parameters=[
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
            ),
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Analytics financiers",
                examples={"application/json": {
                    "success": True,
                    "financial_analytics": {
                        "balance_summary": {
                            "current_balance": 1250.50,
                            "total_deposits": 3000.00,
                            "total_withdrawals": 1500.00,
                            "net_income": 1500.00
                        },
                        "transaction_summary": {
                            "total_transactions": 25,
                            "deposits": 8,
                            "withdrawals": 5,
                            "transfers": 12
                        },
                        "monthly_transactions": [
                            {"month": "2024-01", "count": 15, "amount": 2000.00},
                            {"month": "2024-02", "count": 10, "amount": 1500.00}
                        ]
                    }
                }}
            )
        }
    )

def analytics_event_schema():
    """Schéma pour les événements analytics."""
    return swagger_auto_schema(
        operation_description="Enregistrer un événement analytics",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'event_type': openapi.Schema(type=openapi.TYPE_STRING, description="Type d'événement"),
                'event_data': openapi.Schema(type=openapi.TYPE_OBJECT, description="Données de l'événement"),
                'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Horodatage")
            },
            required=['event_type', 'event_data']
        ),
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Événement enregistré",
                examples={"application/json": {
                    "success": True,
                    "message": "Événement analytics enregistré avec succès",
                    "event": {
                        "id": 1,
                        "event_type": "shipment_created",
                        "event_data": {
                            "shipment_id": 1,
                            "user_id": 1,
                            "amount": 125.50
                        },
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "message": "Type d'événement requis"
                }}
            )
        }
    ) 

def user_document_detail_schema():
    """Schéma pour les détails d'un document."""
    return swagger_auto_schema(
        operation_description="Récupérer les détails d'un document utilisateur",
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description="ID du document",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Détails du document",
                examples={"application/json": {
                    "success": True,
                    "document": {
                        "id": 1,
                        "document_type": "passport",
                        "status": "approved",
                        "uploaded_at": "2024-01-15T10:30:00Z",
                        "verified_at": "2024-01-16T14:20:00Z",
                        "rejection_reason": None
                    }
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Document non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Document non trouvé"
                }}
            )
        }
    )

def admin_user_detail_schema():
    """Schéma pour les détails d'un utilisateur (admin)."""
    return swagger_auto_schema(
        operation_description="Récupérer les détails d'un utilisateur (admin uniquement)",
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description="ID de l'utilisateur",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer) - Admin requis",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Détails de l'utilisateur",
                examples={"application/json": {
                    "success": True,
                    "user": {
                        "id": 1,
                        "username": "john_doe",
                        "email": "john.doe@example.com",
                        "role": "sender",
                        "is_active": True,
                        "is_phone_verified": True,
                        "is_document_verified": False,
                        "created_at": "2024-01-15T10:30:00Z",
                        "profile": {
                            "address": "123 Rue de la Paix",
                            "city": "Alger",
                            "country": "Algeria"
                        }
                    }
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Utilisateur non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Utilisateur non trouvé"
                }}
            ),
            status.HTTP_403_FORBIDDEN: openapi.Response(
                description="Accès refusé",
                examples={"application/json": {
                    "success": False,
                    "message": "Vous n'avez pas les permissions pour accéder à cette ressource"
                }}
            )
        }
    )

def admin_user_update_schema():
    """Schéma pour mettre à jour un utilisateur (admin)."""
    return swagger_auto_schema(
        operation_description="Mettre à jour un utilisateur (admin uniquement)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description="Nom d'utilisateur"),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="Adresse email"),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description="Prénom"),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de famille"),
                'role': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['sender', 'traveler', 'admin', 'both'],
                    description="Rôle utilisateur"
                ),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Compte actif"),
                'is_phone_verified': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Téléphone vérifié"),
                'is_document_verified': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Documents vérifiés")
            }
        ),
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description="ID de l'utilisateur",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT (Bearer) - Admin requis",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Utilisateur mis à jour",
                examples={"application/json": {
                    "success": True,
                    "message": "Utilisateur mis à jour avec succès",
                    "user": {
                        "id": 1,
                        "username": "john_doe",
                        "email": "john.doe@example.com",
                        "role": "sender",
                        "is_active": True
                    }
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "errors": {
                        "email": ["Cette adresse email est déjà utilisée."]
                    }
                }}
            )
        }
    ) 