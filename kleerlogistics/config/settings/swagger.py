"""
Configuration avancée pour Swagger/OpenAPI
"""

# Configuration Swagger avancée
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Token JWT au format: Bearer <token>'
        },
        'Session': {
            'type': 'apiKey',
            'name': 'sessionid',
            'in': 'cookie',
            'description': 'Session Django'
        }
    },
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
    'SUPPORTED_SUBMIT_METHODS': [
        'get',
        'post',
        'put',
        'delete',
        'patch'
    ],
    'OPERATIONS_SORTER': 'alpha',
    'TAGS_SORTER': 'alpha',
    'DOC_EXPANSION': 'list',
    'DEEP_LINKING': True,
    'DISPLAY_OPERATION_ID': False,
    'DEFAULT_MODEL_RENDERING': 'example',
    'DEFAULT_INFO': {
        'title': 'KleerLogistics API',
        'description': """
        # API KleerLogistics - Plateforme d'envoi collaboratif

        Cette API permet de gérer les expéditions, voyages, utilisateurs et paiements sur la plateforme KleerLogistics.

        ## Fonctionnalités principales

        ### 👤 Utilisateurs
        - Inscription et authentification
        - Gestion des profils utilisateurs
        - Vérification téléphonique par OTP
        - Upload de documents d'identité

        ### 📦 Expéditions
        - Création et gestion d'expéditions
        - Suivi en temps réel
        - Matching avec les voyages disponibles
        - Gestion des statuts et paiements

        ### 🚗 Voyages
        - Création de voyages
        - Recherche de voyages disponibles
        - Gestion de la capacité et des prix
        - Acceptation d'expéditions

        ### 💳 Paiements
        - Intégration Chargily Pay
        - Gestion de portefeuille
        - Historique des transactions
        - Remboursements

        ### 📱 Notifications
        - Notifications en temps réel
        - Emails et SMS
        - Templates personnalisables

        ### ⭐ Évaluations
        - Système d'évaluation mutuelle
        - Statistiques et analytics
        - Historique des évaluations

        ## Authentification

        L'API utilise l'authentification JWT. Incluez le token dans l'en-tête Authorization :
        ```
        Authorization: Bearer <votre_token_jwt>
        ```

        ## Codes de statut

        - `200` : Succès
        - `201` : Créé avec succès
        - `400` : Erreur de validation
        - `401` : Non authentifié
        - `403` : Non autorisé
        - `404` : Ressource non trouvée
        - `500` : Erreur serveur

        ## Pagination

        Les listes sont paginées avec les paramètres :
        - `page` : Numéro de page (défaut: 1)
        - `per_page` : Éléments par page (défaut: 10)

        ## Filtrage et recherche

        La plupart des endpoints de liste supportent :
        - `query` : Recherche textuelle
        - `status` : Filtrage par statut
        - `date_from` / `date_to` : Filtrage par date
        - `sort_by` / `sort_order` : Tri

        ## Exemples de réponses

        Tous les endpoints incluent des exemples JSON détaillés pour les requêtes et réponses.
        """,
        'version': '1.0.0',
        'contact': {
            'name': 'Support KleerLogistics',
            'email': 'support@kleerinfini.com',
            'url': 'https://www.kleerinfini.com/support'
        },
        'license': {
            'name': 'Proprietary',
            'url': 'https://www.kleerinfini.com/terms'
        }
    },
    'TAGS': [
        {
            'name': 'Authentication',
            'description': 'Endpoints pour l\'authentification et la gestion des utilisateurs'
        },
        {
            'name': 'Users',
            'description': 'Gestion des profils utilisateurs, documents et vérifications'
        },
        {
            'name': 'Shipments',
            'description': 'Création, gestion et suivi des expéditions'
        },
        {
            'name': 'Trips',
            'description': 'Création et recherche de voyages'
        },
        {
            'name': 'Payments',
            'description': 'Gestion des paiements et portefeuilles'
        },
        {
            'name': 'Notifications',
            'description': 'Envoi et gestion des notifications'
        },
        {
            'name': 'Ratings',
            'description': 'Système d\'évaluation et de feedback'
        },
        {
            'name': 'Admin',
            'description': 'Endpoints administratifs (accès restreint)'
        }
    ],
    'CUSTOM_FIELD_DEFAULTS': {
        'headers': {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    },
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': False,
        'defaultModelsExpandDepth': 1,
        'defaultModelExpandDepth': 1,
        'displayRequestDuration': True,
        'docExpansion': 'list',
        'filter': True,
        'showExtensions': True,
        'showCommonExtensions': True,
        'syntaxHighlight.theme': 'monokai'
    },
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': False,
        'hideHostname': False,
        'hideLoading': False,
        'nativeScrollbars': False,
        'noAutoAuth': False,
        'pathInMiddlePanel': False,
        'requiredPropsFirst': True,
        'scrollYOffset': 0,
        'showExtensions': True,
        'sortPropsAlphabetically': True,
        'suppressWarnings': False,
        'theme': {
            'colors': {
                'primary': {
                    'main': '#32329f'
                }
            },
            'typography': {
                'fontSize': '14px',
                'lineHeight': '1.5em'
            }
        }
    }
}

# Configuration pour les exemples de réponses
SWAGGER_EXAMPLES = {
    'success_response': {
        'success': True,
        'message': 'Opération effectuée avec succès',
        'data': {}
    },
    'error_response': {
        'success': False,
        'message': 'Une erreur s\'est produite',
        'errors': {}
    },
    'validation_error': {
        'success': False,
        'message': 'Données invalides',
        'errors': {
            'field_name': ['Ce champ est requis.']
        }
    },
    'not_found': {
        'success': False,
        'message': 'Ressource non trouvée'
    },
    'unauthorized': {
        'success': False,
        'message': 'Authentification requise'
    },
    'forbidden': {
        'success': False,
        'message': 'Permission refusée'
    }
}

# Configuration pour les paramètres de requête communs
COMMON_QUERY_PARAMS = {
    'pagination': [
        {
            'name': 'page',
            'in': 'query',
            'description': 'Numéro de page',
            'required': False,
            'type': 'integer',
            'default': 1
        },
        {
            'name': 'per_page',
            'in': 'query',
            'description': 'Nombre d\'éléments par page',
            'required': False,
            'type': 'integer',
            'default': 10
        }
    ],
    'search': [
        {
            'name': 'query',
            'in': 'query',
            'description': 'Terme de recherche',
            'required': False,
            'type': 'string'
        },
        {
            'name': 'status',
            'in': 'query',
            'description': 'Filtrer par statut',
            'required': False,
            'type': 'string',
            'enum': ['pending', 'active', 'completed', 'cancelled']
        }
    ],
    'date_filter': [
        {
            'name': 'date_from',
            'in': 'query',
            'description': 'Date de début (YYYY-MM-DD)',
            'required': False,
            'type': 'string',
            'format': 'date'
        },
        {
            'name': 'date_to',
            'in': 'query',
            'description': 'Date de fin (YYYY-MM-DD)',
            'required': False,
            'type': 'string',
            'format': 'date'
        }
    ],
    'sorting': [
        {
            'name': 'sort_by',
            'in': 'query',
            'description': 'Champ de tri',
            'required': False,
            'type': 'string',
            'enum': ['created_at', 'updated_at', 'title', 'status']
        },
        {
            'name': 'sort_order',
            'in': 'query',
            'description': 'Ordre de tri',
            'required': False,
            'type': 'string',
            'enum': ['asc', 'desc'],
            'default': 'desc'
        }
    ]
}

# Configuration pour les en-têtes de réponse
COMMON_RESPONSE_HEADERS = {
    'X-Total-Count': {
        'description': 'Nombre total d\'éléments',
        'type': 'integer'
    },
    'X-Page-Count': {
        'description': 'Nombre total de pages',
        'type': 'integer'
    },
    'X-Current-Page': {
        'description': 'Page actuelle',
        'type': 'integer'
    },
    'X-Per-Page': {
        'description': 'Éléments par page',
        'type': 'integer'
    }
}

# Configuration pour les codes de statut HTTP
HTTP_STATUS_CODES = {
    '200': 'OK - Requête traitée avec succès',
    '201': 'Created - Ressource créée avec succès',
    '204': 'No Content - Requête traitée mais pas de contenu',
    '400': 'Bad Request - Données invalides',
    '401': 'Unauthorized - Authentification requise',
    '403': 'Forbidden - Permission refusée',
    '404': 'Not Found - Ressource non trouvée',
    '405': 'Method Not Allowed - Méthode HTTP non autorisée',
    '409': 'Conflict - Conflit avec l\'état actuel',
    '422': 'Unprocessable Entity - Données valides mais non traitables',
    '429': 'Too Many Requests - Trop de requêtes',
    '500': 'Internal Server Error - Erreur serveur',
    '502': 'Bad Gateway - Erreur de passerelle',
    '503': 'Service Unavailable - Service indisponible'
}

# Configuration pour les types de contenu
CONTENT_TYPES = {
    'application/json': 'Données JSON',
    'multipart/form-data': 'Données de formulaire avec fichiers',
    'application/x-www-form-urlencoded': 'Données de formulaire'
}

# Configuration pour les formats de date
DATE_FORMATS = {
    'date': 'YYYY-MM-DD',
    'datetime': 'YYYY-MM-DDTHH:MM:SSZ',
    'time': 'HH:MM:SS'
}

# Configuration pour les limites et contraintes
API_LIMITS = {
    'max_file_size': '10MB',
    'max_request_size': '10MB',
    'rate_limit_auth': '5 requests/minute',
    'rate_limit_general': '100 requests/hour',
    'rate_limit_upload': '10 requests/hour',
    'pagination_max_per_page': 100,
    'search_max_length': 100,
    'comment_max_length': 1000
}

# Configuration pour les environnements
ENVIRONMENT_CONFIGS = {
    'development': {
        'base_url': 'http://localhost:8000',
        'api_version': 'v1',
        'debug': True
    },
    'staging': {
        'base_url': 'https://staging.kleerinfini.com',
        'api_version': 'v1',
        'debug': False
    },
    'production': {
        'base_url': 'https://api.kleerinfini.com',
        'api_version': 'v1',
        'debug': False
    }
} 