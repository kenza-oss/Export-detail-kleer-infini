"""
Configuration avancée pour Swagger/OpenAPI avec exemples détaillés
"""

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from .swagger_examples import *

# Paramètres de requête communs
PAGINATION_PARAMS = [
    openapi.Parameter(
        'page',
        openapi.IN_QUERY,
        description="Numéro de page",
        type=openapi.TYPE_INTEGER,
        default=1
    ),
    openapi.Parameter(
        'per_page',
        openapi.IN_QUERY,
        description="Nombre d'éléments par page",
        type=openapi.TYPE_INTEGER,
        default=10
    )
]

SEARCH_PARAMS = [
    openapi.Parameter(
        'query',
        openapi.IN_QUERY,
        description="Terme de recherche",
        type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        'status',
        openapi.IN_QUERY,
        description="Filtrer par statut",
        type=openapi.TYPE_STRING,
        enum=['pending', 'active', 'completed', 'cancelled']
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
]

# Schémas de réponses communs
SUCCESS_RESPONSE = openapi.Response(
    description="Opération réussie",
    examples={
        "application/json": {
            "success": True,
            "message": "Opération effectuée avec succès"
        }
    }
)

ERROR_RESPONSE = openapi.Response(
    description="Erreur de validation",
    examples={
        "application/json": ERROR_EXAMPLES["validation_error"]
    }
)

NOT_FOUND_RESPONSE = openapi.Response(
    description="Ressource non trouvée",
    examples={
        "application/json": ERROR_EXAMPLES["not_found_error"]
    }
)

AUTH_ERROR_RESPONSE = openapi.Response(
    description="Erreur d'authentification",
    examples={
        "application/json": ERROR_EXAMPLES["authentication_error"]
    }
)

# Décorateurs Swagger pour les vues utilisateurs
def user_registration_schema():
    return swagger_auto_schema(
        operation_description="Inscription d'un nouvel utilisateur",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD),
                'password_confirm': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD)
            },
            required=['email', 'username', 'password', 'password_confirm']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Utilisateur créé avec succès",
                examples={"application/json": USER_REGISTRATION_EXAMPLE["response_success"]}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Données invalides",
                examples={"application/json": USER_REGISTRATION_EXAMPLE["response_error"]}
            )
        },

    )

def user_profile_get_schema():
    return swagger_auto_schema(
        operation_description="Récupérer le profil de l'utilisateur connecté",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Profil récupéré avec succès",
                examples={"application/json": USER_PROFILE_EXAMPLE["response_get"]}
            ),
            status.HTTP_404_NOT_FOUND: NOT_FOUND_RESPONSE
        }
    )

def user_profile_update_schema():
    return swagger_auto_schema(
        operation_description="Mettre à jour le profil utilisateur",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                'date_of_birth': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                'country': openapi.Schema(type=openapi.TYPE_STRING),
                'city': openapi.Schema(type=openapi.TYPE_STRING),
                'address': openapi.Schema(type=openapi.TYPE_STRING),
                'bio': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Profil mis à jour avec succès",
                examples={"application/json": {
                    "success": True,
                    "message": "Profil mis à jour avec succès",
                    "profile": USER_PROFILE_EXAMPLE["response_get"]["profile"]
                }}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE,
            status.HTTP_404_NOT_FOUND: NOT_FOUND_RESPONSE
        },

    )

def send_otp_schema():
    return swagger_auto_schema(
        operation_description="Envoyer un code OTP par SMS",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Numéro de téléphone")
            },
            required=['phone_number']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Code OTP envoyé avec succès",
                examples={"application/json": PHONE_VERIFICATION_EXAMPLE["response_send_otp"]}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Numéro de téléphone manquant",
                examples={"application/json": {
                    "success": False,
                    "message": "Numéro de téléphone requis"
                }}
            )
        },

    )

def verify_otp_schema():
    return swagger_auto_schema(
        operation_description="Vérifier le code OTP reçu",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone': openapi.Schema(type=openapi.TYPE_STRING, description="Numéro de téléphone"),
                'otp': openapi.Schema(type=openapi.TYPE_STRING, description="Code OTP à 6 chiffres")
            },
            required=['phone', 'otp']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Numéro de téléphone vérifié avec succès",
                examples={"application/json": PHONE_VERIFICATION_EXAMPLE["response_verify_otp"]}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="OTP incorrect",
                examples={"application/json": {
                    "success": False,
                    "message": "OTP incorrect"
                }}
            )
        },

    )

def change_password_schema():
    return swagger_auto_schema(
        operation_description="Changer le mot de passe de l'utilisateur",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD),
                'new_password_confirm': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD)
            },
            required=['old_password', 'new_password', 'new_password_confirm']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Mot de passe modifié avec succès",
                examples={"application/json": PASSWORD_CHANGE_EXAMPLE["response_success"]}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": PASSWORD_CHANGE_EXAMPLE["response_error"]}
            )
        },

    )

def reset_password_schema():
    return swagger_auto_schema(
        operation_description="Demander la réinitialisation du mot de passe",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL)
            },
            required=['email']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Email de réinitialisation envoyé",
                examples={"application/json": PASSWORD_RESET_EXAMPLE["response_reset"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        },

    )

def user_document_upload_schema():
    return swagger_auto_schema(
        operation_description="Uploader un document utilisateur",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'document_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['identity_card', 'proof_of_address', 'passport', 'driving_license']
                ),
                'file': openapi.Schema(type=openapi.TYPE_FILE)
            },
            required=['document_type', 'file']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Document uploadé avec succès",
                examples={"application/json": USER_DOCUMENT_EXAMPLE["response_upload"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        },

    )

def user_document_list_schema():
    return swagger_auto_schema(
        operation_description="Lister les documents de l'utilisateur",
        manual_parameters=PAGINATION_PARAMS,
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des documents",
                examples={"application/json": USER_DOCUMENT_EXAMPLE["response_list"]}
            )
        }
    )

def user_search_schema():
    return swagger_auto_schema(
        operation_description="Rechercher des utilisateurs",
        manual_parameters=[
            openapi.Parameter(
                'query',
                openapi.IN_QUERY,
                description="Terme de recherche",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'user_type',
                openapi.IN_QUERY,
                description="Type d'utilisateur",
                type=openapi.TYPE_STRING,
                enum=['sender', 'driver', 'both']
            ),
            openapi.Parameter(
                'country',
                openapi.IN_QUERY,
                description="Pays",
                type=openapi.TYPE_STRING
            )
        ] + PAGINATION_PARAMS,
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Résultats de la recherche",
                examples={"application/json": USER_SEARCH_EXAMPLE["response"]}
            )
        }
    )

# Décorateurs Swagger pour les expéditions
def shipment_create_schema():
    return swagger_auto_schema(
        operation_description="Créer une nouvelle expédition",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING),
                'origin_address': openapi.Schema(type=openapi.TYPE_STRING),
                'destination_address': openapi.Schema(type=openapi.TYPE_STRING),
                'weight': openapi.Schema(type=openapi.TYPE_NUMBER),
                'dimensions': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'length': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'width': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'height': openapi.Schema(type=openapi.TYPE_NUMBER)
                    }
                ),
                'fragile': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'urgent': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'estimated_value': openapi.Schema(type=openapi.TYPE_NUMBER),
                'category': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['documents', 'electronics', 'clothing', 'furniture', 'other']
                ),
                'pickup_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                'delivery_deadline': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE)
            },
            required=['title', 'origin_address', 'destination_address', 'weight']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Expédition créée avec succès",
                examples={"application/json": SHIPMENT_CREATE_EXAMPLE["response_success"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        },

    )

def shipment_list_schema():
    return swagger_auto_schema(
        operation_description="Lister les expéditions",
        manual_parameters=SEARCH_PARAMS + PAGINATION_PARAMS,
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des expéditions",
                examples={"application/json": SHIPMENT_LIST_EXAMPLE["response"]}
            )
        }
    )

# Décorateurs Swagger pour les voyages
def trip_create_schema():
    return swagger_auto_schema(
        operation_description="Créer un nouveau voyage",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING),
                'origin_address': openapi.Schema(type=openapi.TYPE_STRING),
                'destination_address': openapi.Schema(type=openapi.TYPE_STRING),
                'departure_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'arrival_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'available_space': openapi.Schema(type=openapi.TYPE_NUMBER),
                'max_weight': openapi.Schema(type=openapi.TYPE_NUMBER),
                'price_per_kg': openapi.Schema(type=openapi.TYPE_NUMBER),
                'vehicle_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['car', 'van', 'truck', 'motorcycle']
                ),
                'route_details': openapi.Schema(type=openapi.TYPE_STRING),
                'flexible_dates': openapi.Schema(type=openapi.TYPE_BOOLEAN)
            },
            required=['title', 'origin_address', 'destination_address', 'departure_date', 'arrival_date']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Voyage créé avec succès",
                examples={"application/json": TRIP_CREATE_EXAMPLE["response_success"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        },

    )

def trip_search_schema():
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
                'date_from',
                openapi.IN_QUERY,
                description="Date de départ minimale",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            ),
            openapi.Parameter(
                'date_to',
                openapi.IN_QUERY,
                description="Date de départ maximale",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            ),
            openapi.Parameter(
                'max_price',
                openapi.IN_QUERY,
                description="Prix maximum par kg",
                type=openapi.TYPE_NUMBER
            ),
            openapi.Parameter(
                'vehicle_type',
                openapi.IN_QUERY,
                description="Type de véhicule",
                type=openapi.TYPE_STRING,
                enum=['car', 'van', 'truck', 'motorcycle']
            )
        ] + PAGINATION_PARAMS,
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Résultats de la recherche",
                examples={"application/json": TRIP_SEARCH_EXAMPLE["response"]}
            )
        }
    )

# Décorateurs Swagger pour les paiements
def payment_create_schema():
    return swagger_auto_schema(
        operation_description="Créer un nouveau paiement",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                'currency': openapi.Schema(type=openapi.TYPE_STRING, default="EUR"),
                'payment_method': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['card', 'bank_transfer', 'paypal']
                ),
                'description': openapi.Schema(type=openapi.TYPE_STRING),
                'shipment_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            },
            required=['amount', 'payment_method', 'description']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Paiement initié avec succès",
                examples={"application/json": PAYMENT_CREATE_EXAMPLE["response_success"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        },

    )

# Décorateurs Swagger pour les notifications
def notification_send_schema():
    return swagger_auto_schema(
        operation_description="Envoyer une notification",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'recipient_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'title': openapi.Schema(type=openapi.TYPE_STRING),
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'notification_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['shipment_match', 'trip_update', 'payment_received', 'system_alert']
                ),
                'data': openapi.Schema(type=openapi.TYPE_OBJECT)
            },
            required=['recipient_id', 'title', 'message']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Notification envoyée avec succès",
                examples={"application/json": NOTIFICATION_EXAMPLE["response_send"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        },

    )

def notification_list_schema():
    return swagger_auto_schema(
        operation_description="Lister les notifications de l'utilisateur",
        manual_parameters=PAGINATION_PARAMS + [
            openapi.Parameter(
                'unread_only',
                openapi.IN_QUERY,
                description="Afficher seulement les notifications non lues",
                type=openapi.TYPE_BOOLEAN
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des notifications",
                examples={"application/json": NOTIFICATION_EXAMPLE["response_list"]}
            )
        }
    )

# Décorateurs Swagger pour les évaluations
def rating_create_schema():
    return swagger_auto_schema(
        operation_description="Créer une évaluation",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'rating': openapi.Schema(type=openapi.TYPE_INTEGER, minimum=1, maximum=5),
                'comment': openapi.Schema(type=openapi.TYPE_STRING),
                'shipment_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'rated_user_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            },
            required=['rating', 'rated_user_id']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Évaluation créée avec succès",
                examples={"application/json": RATING_CREATE_EXAMPLE["response_success"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        },

    )

# Décorateurs Swagger pour les correspondances (matching)
def matching_create_schema():
    return swagger_auto_schema(
        operation_description="Créer une correspondance entre expédition et voyage",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'shipment_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'trip_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'proposed_price': openapi.Schema(type=openapi.TYPE_NUMBER),
                'message': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['shipment_id', 'trip_id']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Correspondance créée avec succès",
                examples={"application/json": MATCHING_EXAMPLE["response_create"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

def matching_list_schema():
    return swagger_auto_schema(
        operation_description="Lister les correspondances",
        manual_parameters=PAGINATION_PARAMS + [
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Statut de la correspondance",
                type=openapi.TYPE_STRING,
                enum=['pending', 'accepted', 'rejected', 'cancelled']
            ),
            openapi.Parameter(
                'shipment_id',
                openapi.IN_QUERY,
                description="ID de l'expédition",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'trip_id',
                openapi.IN_QUERY,
                description="ID du voyage",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des correspondances",
                examples={"application/json": MATCHING_EXAMPLE["response_list"]}
            )
        }
    )

# Décorateurs Swagger pour les conversations (chat)
def conversation_create_schema():
    return swagger_auto_schema(
        operation_description="Créer une nouvelle conversation",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'shipment_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'participant_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER)
                )
            },
            required=['shipment_id', 'participant_ids']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Conversation créée avec succès",
                examples={"application/json": CHAT_EXAMPLE["response_create_conversation"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

def message_send_schema():
    return swagger_auto_schema(
        operation_description="Envoyer un message dans une conversation",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'content': openapi.Schema(type=openapi.TYPE_STRING),
                'message_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['text', 'image', 'file'],
                    default='text'
                )
            },
            required=['content']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Message envoyé avec succès",
                examples={"application/json": CHAT_EXAMPLE["response_send_message"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

def message_list_schema():
    return swagger_auto_schema(
        operation_description="Lister les messages d'une conversation",
        manual_parameters=PAGINATION_PARAMS,
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des messages",
                examples={"application/json": CHAT_EXAMPLE["response_list_messages"]}
            )
        }
    )

# Décorateurs Swagger pour l'internationalisation
def translation_schema():
    return swagger_auto_schema(
        operation_description="Traduire un texte",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'text': openapi.Schema(type=openapi.TYPE_STRING),
                'source_language': openapi.Schema(type=openapi.TYPE_STRING),
                'target_language': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['text', 'source_language', 'target_language']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Texte traduit",
                examples={"application/json": INTERNATIONALIZATION_EXAMPLE["response_translate"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

def languages_list_schema():
    return swagger_auto_schema(
        operation_description="Lister les langues disponibles",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des langues",
                examples={"application/json": INTERNATIONALIZATION_EXAMPLE["response_languages"]}
            )
        }
    )

# Décorateurs Swagger pour la vérification
def verification_request_schema():
    return swagger_auto_schema(
        operation_description="Demander la vérification d'un utilisateur",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'verification_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['identity', 'address', 'vehicle', 'insurance']
                ),
                'documents': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_FILE)
                ),
                'additional_info': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['verification_type']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Demande de vérification créée",
                examples={"application/json": {
                    "success": True,
                    "message": "Demande de vérification soumise avec succès",
                    "verification_id": 1,
                    "status": "pending"
                }}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

def verification_status_schema():
    return swagger_auto_schema(
        operation_description="Récupérer le statut de vérification",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Statut de vérification",
                examples={"application/json": {
                    "success": True,
                    "verification_status": "verified",
                    "verifications": [
                        {
                            "id": 1,
                            "type": "identity",
                            "status": "verified",
                            "verified_at": "2024-01-15T10:30:00Z"
                        }
                    ]
                }}
            )
        }
    )

# Décorateurs Swagger pour l'admin panel
def admin_user_management_schema():
    return swagger_auto_schema(
        operation_description="Gérer les utilisateurs (Admin)",
        manual_parameters=[
            openapi.Parameter(
                'action',
                openapi.IN_QUERY,
                description="Action à effectuer",
                type=openapi.TYPE_STRING,
                enum=['suspend', 'activate', 'delete', 'verify']
            ),
            openapi.Parameter(
                'user_id',
                openapi.IN_QUERY,
                description="ID de l'utilisateur",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Action effectuée avec succès",
                examples={"application/json": {
                    "success": True,
                    "message": "Utilisateur suspendu avec succès"
                }}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

def admin_system_stats_schema():
    return swagger_auto_schema(
        operation_description="Récupérer les statistiques système (Admin)",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Statistiques système",
                examples={"application/json": {
                    "success": True,
                    "stats": {
                        "total_users": 1250,
                        "active_shipments": 45,
                        "active_trips": 15,
                        "total_revenue": 25000.00,
                        "system_health": "good"
                    }
                }}
            )
        }
    )

# Décorateurs Swagger pour Analytics
def analytics_dashboard_schema():
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
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Analytics du tableau de bord",
                examples={"application/json": ANALYTICS_DASHBOARD_EXAMPLE["response"]}
            )
        }
    )

def analytics_shipment_schema():
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
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Analytics des expéditions",
                examples={"application/json": ANALYTICS_SHIPMENT_EXAMPLE["response"]}
            )
        }
    )

def analytics_trip_schema():
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
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Analytics des voyages",
                examples={"application/json": ANALYTICS_TRIP_EXAMPLE["response"]}
            )
        }
    )

def analytics_financial_schema():
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
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Analytics financiers",
                examples={"application/json": ANALYTICS_FINANCIAL_EXAMPLE["response"]}
            )
        }
    )

def analytics_event_schema():
    return swagger_auto_schema(
        operation_description="Enregistrer un événement analytics",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'event_type': openapi.Schema(type=openapi.TYPE_STRING),
                'event_data': openapi.Schema(type=openapi.TYPE_OBJECT),
                'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)
            },
            required=['event_type', 'event_data']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Événement enregistré",
                examples={"application/json": ANALYTICS_EVENT_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

# Décorateurs Swagger pour Documents
def document_upload_schema():
    return swagger_auto_schema(
        operation_description="Uploader un document",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'document_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['identity_card', 'proof_of_address', 'passport', 'driving_license', 'vehicle_registration']
                ),
                'file': openapi.Schema(type=openapi.TYPE_FILE),
                'description': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['document_type', 'file']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Document uploadé",
                examples={"application/json": DOCUMENT_UPLOAD_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

def document_list_schema():
    return swagger_auto_schema(
        operation_description="Lister les documents",
        manual_parameters=PAGINATION_PARAMS + [
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
                enum=['pending_verification', 'verified', 'rejected']
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des documents",
                examples={"application/json": DOCUMENT_LIST_EXAMPLE["response"]}
            )
        }
    )

def document_verify_schema():
    return swagger_auto_schema(
        operation_description="Vérifier un document",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['verified', 'rejected']
                ),
                'verification_notes': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['status']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Document vérifié",
                examples={"application/json": DOCUMENT_VERIFY_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

# Décorateurs Swagger pour Matching
def matching_accept_schema():
    return swagger_auto_schema(
        operation_description="Accepter une correspondance",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'accepted_price': openapi.Schema(type=openapi.TYPE_NUMBER),
                'message': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Correspondance acceptée",
                examples={"application/json": MATCHING_ACCEPT_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

def matching_reject_schema():
    return swagger_auto_schema(
        operation_description="Rejeter une correspondance",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'reason': openapi.Schema(type=openapi.TYPE_STRING),
                'message': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['reason']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Correspondance rejetée",
                examples={"application/json": MATCHING_REJECT_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

# Décorateurs Swagger pour Notifications
def notification_mark_read_schema():
    return swagger_auto_schema(
        operation_description="Marquer des notifications comme lues",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'notification_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER)
                )
            },
            required=['notification_ids']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Notifications marquées comme lues",
                examples={"application/json": NOTIFICATION_MARK_READ_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

def notification_template_schema():
    return swagger_auto_schema(
        operation_description="Créer un modèle de notification",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'subject': openapi.Schema(type=openapi.TYPE_STRING),
                'body': openapi.Schema(type=openapi.TYPE_STRING),
                'notification_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['email', 'sms', 'push']
                )
            },
            required=['name', 'subject', 'body', 'notification_type']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Modèle créé",
                examples={"application/json": NOTIFICATION_TEMPLATE_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

# Décorateurs Swagger pour Payments
def payment_deposit_schema():
    return swagger_auto_schema(
        operation_description="Effectuer un dépôt",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                'payment_method': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['card', 'bank_transfer', 'paypal']
                ),
                'description': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['amount']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Dépôt effectué",
                examples={"application/json": PAYMENT_DEPOSIT_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

def payment_withdraw_schema():
    return swagger_auto_schema(
        operation_description="Effectuer un retrait",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                'bank_account': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['amount', 'bank_account']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Retrait initié",
                examples={"application/json": PAYMENT_WITHDRAW_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

def payment_transfer_schema():
    return swagger_auto_schema(
        operation_description="Effectuer un transfert",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'recipient_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                'description': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['recipient_id', 'amount']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Transfert effectué",
                examples={"application/json": PAYMENT_TRANSFER_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

def payment_refund_schema():
    return swagger_auto_schema(
        operation_description="Demander un remboursement",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'transaction_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'reason': openapi.Schema(type=openapi.TYPE_STRING),
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER)
            },
            required=['transaction_id', 'reason']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Remboursement initié",
                examples={"application/json": PAYMENT_REFUND_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

# Décorateurs Swagger pour Shipments
def shipment_tracking_schema():
    return swagger_auto_schema(
        operation_description="Suivre une expédition",
        manual_parameters=[
            openapi.Parameter(
                'tracking_number',
                openapi.IN_PATH,
                description="Numéro de suivi",
                type=openapi.TYPE_STRING
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Informations de suivi",
                examples={"application/json": SHIPMENT_TRACKING_EXAMPLE["response"]}
            ),
            status.HTTP_404_NOT_FOUND: NOT_FOUND_RESPONSE
        }
    )

def shipment_update_status_schema():
    return swagger_auto_schema(
        operation_description="Mettre à jour le statut d'une expédition",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['pending', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'cancelled']
                ),
                'location': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['status']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Statut mis à jour",
                examples={"application/json": SHIPMENT_UPDATE_STATUS_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

def shipment_delivery_otp_schema():
    return swagger_auto_schema(
        operation_description="Générer un OTP de livraison",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="OTP généré",
                examples={"application/json": SHIPMENT_DELIVERY_OTP_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

def shipment_verify_delivery_schema():
    return swagger_auto_schema(
        operation_description="Vérifier l'OTP de livraison",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'otp': openapi.Schema(type=openapi.TYPE_STRING),
                'signature': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['otp']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Livraison confirmée",
                examples={"application/json": SHIPMENT_VERIFY_DELIVERY_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

# Décorateurs Swagger pour Trips
def trip_update_status_schema():
    return swagger_auto_schema(
        operation_description="Mettre à jour le statut d'un voyage",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['active', 'in_progress', 'completed', 'cancelled']
                ),
                'notes': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['status']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Statut mis à jour",
                examples={"application/json": TRIP_UPDATE_STATUS_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

def trip_update_capacity_schema():
    return swagger_auto_schema(
        operation_description="Mettre à jour la capacité d'un voyage",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'available_space': openapi.Schema(type=openapi.TYPE_NUMBER),
                'max_weight': openapi.Schema(type=openapi.TYPE_NUMBER)
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Capacité mise à jour",
                examples={"application/json": TRIP_UPDATE_CAPACITY_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

def trip_document_schema():
    return swagger_auto_schema(
        operation_description="Uploader un document de voyage",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'document_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['vehicle_registration', 'insurance', 'license']
                ),
                'file': openapi.Schema(type=openapi.TYPE_FILE),
                'description': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['document_type', 'file']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Document uploadé",
                examples={"application/json": TRIP_DOCUMENT_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

# Décorateurs Swagger pour Users
def user_login_schema():
    return swagger_auto_schema(
        operation_description="Se connecter",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD)
            },
            required=['username', 'password']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Connexion réussie",
                examples={"application/json": USER_LOGIN_EXAMPLE["response"]}
            ),
            status.HTTP_401_UNAUTHORIZED: AUTH_ERROR_RESPONSE
        }
    )

def user_refresh_token_schema():
    return swagger_auto_schema(
        operation_description="Rafraîchir le token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['refresh']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Token rafraîchi",
                examples={"application/json": USER_REFRESH_TOKEN_EXAMPLE["response"]}
            ),
            status.HTTP_401_UNAUTHORIZED: AUTH_ERROR_RESPONSE
        }
    )

def user_logout_schema():
    return swagger_auto_schema(
        operation_description="Se déconnecter",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['refresh']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Déconnexion réussie",
                examples={"application/json": USER_LOGOUT_EXAMPLE["response"]}
            )
        }
    )

def user_verification_schema():
    return swagger_auto_schema(
        operation_description="Demander la vérification",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'verification_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['identity', 'address', 'vehicle', 'insurance']
                ),
                'documents': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_FILE)
                ),
                'additional_info': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['verification_type']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Demande soumise",
                examples={"application/json": USER_VERIFICATION_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: ERROR_RESPONSE
        }
    )

def user_verification_status_schema():
    return swagger_auto_schema(
        operation_description="Récupérer le statut de vérification",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Statut de vérification",
                examples={"application/json": USER_VERIFICATION_STATUS_EXAMPLE["response"]}
            )
        }
    ) 