"""
Exemples pour la documentation Swagger
"""

# Exemples d'inscription utilisateur
USER_REGISTRATION_EXAMPLE = {
    "application/json": {
        "username": "romualdo",
        "email": "romualdo@example.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+213123456789",
        "role": "sender"
    }
}

# Exemples de connexion
USER_LOGIN_EXAMPLE = {
    "application/json": {
        "username": "romualdo",
        "password": "SecurePass123!"
    }
}

# Réponse de connexion réussie
LOGIN_SUCCESS_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Connexion réussie",
        "tokens": {
            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        },
        "user": {
            "id": 1,
            "username": "romualdo",
            "email": "john.doe@example.com",
            "role": "sender",
            "permissions": {
                "is_admin": False,
                "is_sender": True,
                "is_traveler": False,
                "can_access_admin_panel": False
            }
        }
    }
}

# Exemples de profil utilisateur
USER_PROFILE_EXAMPLE = {
    "application/json": {
        "success": True,
        "profile": {
            "birth_date": "1990-01-15",
            "address": "123 Rue de la Paix",
            "city": "Alger",
            "country": "Algeria",
            "avatar": "https://example.com/avatars/user1.jpg",
            "bio": "Expéditeur professionnel avec 5 ans d'expérience"
        }
    }
}

# Exemples de mise à jour de profil
PROFILE_UPDATE_EXAMPLE = {
    "application/json": {
        "city": "Oran",
        "country": "Algeria",
        "bio": "Nouvelle bio mise à jour"
    }
}

# Exemples OTP
OTP_SEND_EXAMPLE = {
    "application/json": {
        "phone_number": "+213123456789"
    }
}

OTP_SEND_RESPONSE_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "OTP envoyé au +213123456789",
        "expires_in": "10 minutes"
    }
}

OTP_VERIFY_EXAMPLE = {
    "application/json": {
        "phone_number": "+213123456789",
        "code": "123456"
    }
}

OTP_VERIFY_RESPONSE_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Téléphone vérifié avec succès",
        "phone_verified": True
    }
}

# Exemples de changement de mot de passe
PASSWORD_CHANGE_EXAMPLE = {
    "application/json": {
        "old_password": "OldPassword123!",
        "new_password": "NewSecurePass456!",
        "new_password_confirm": "NewSecurePass456!"
    }
}

PASSWORD_CHANGE_RESPONSE_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Mot de passe changé avec succès"
    }
}

# Exemples de réinitialisation de mot de passe
PASSWORD_RESET_EXAMPLE = {
    "application/json": {
        "email": "john.doe@example.com"
    }
}

PASSWORD_RESET_RESPONSE_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Email de réinitialisation envoyé"
    }
}

# Exemples de documents utilisateur
USER_DOCUMENT_EXAMPLE = {
    "application/json": {
        "document_type": "passport",
        "document_file": "data:application/pdf;base64,JVBERi0xLjQK..."
    }
}

USER_DOCUMENT_RESPONSE_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Document uploadé avec succès",
        "document": {
            "id": 1,
            "document_type": "passport",
            "status": "pending",
            "uploaded_at": "2024-01-15T10:30:00Z"
        }
    }
}

# Exemples de recherche d'utilisateurs
USER_SEARCH_EXAMPLE = {
    "application/json": {
        "success": True,
        "users": [
            {
                "id": 1,
                "username": "romualdo",
                "first_name": "John",
                "last_name": "Doe",
                "role": "sender",
                "rating": 4.5,
                "total_trips": 25,
                "total_shipments": 15,
                "is_document_verified": True,
                "profile_summary": {
                    "rating": 4.5,
                    "total_trips": 25,
                    "total_shipments": 15,
                    "is_verified": True,
                    "country": "Algeria",
                    "city": "Alger"
                }
            }
        ],
        "count": 1
    }
}

# Exemples de gestion des rôles (Admin)
ROLE_UPDATE_EXAMPLE = {
    "application/json": {
        "role": "traveler"
    }
}

ROLE_UPDATE_RESPONSE_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Rôle mis à jour vers traveler",
        "user": {
            "id": 1,
            "username": "romualdo",
            "role": "traveler"
        }
    }
}

# Exemples de liste d'utilisateurs
ADMIN_USER_LIST_EXAMPLE = {
    "application/json": {
        "success": True,
        "users": [
            {
                "id": 1,
                "username": "romualdo",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "sender",
                "phone_number": "+213123456789",
                "is_phone_verified": True,
                "is_document_verified": True,
                "rating": 4.5,
                "total_trips": 25,
                "total_shipments": 15,
                "preferred_language": "fr",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
                "profile": {
                    "birth_date": "1990-01-15",
                    "address": "123 Rue de la Paix",
                    "city": "Alger",
                    "country": "Algeria",
                    "avatar": "https://example.com/avatars/user1.jpg",
                    "bio": "Expéditeur professionnel"
                },
                "permissions": {
                    "is_admin": False,
                    "is_sender": True,
                    "is_traveler": False,
                    "can_access_admin_panel": False
                }
            }
        ],
        "count": 1
    }
}

# Exemples de permissions utilisateur
USER_PERMISSIONS_EXAMPLE = {
    "application/json": {
        "success": True,
        "permissions": {
            "is_admin": False,
            "is_sender": True,
            "is_traveler": False,
            "is_phone_verified": True,
            "is_document_verified": True,
            "can_access_admin_panel": False
        },
        "user": {
            "id": 1,
            "username": "romualdo",
            "role": "sender",
            "is_phone_verified": True,
            "is_document_verified": True
        }
    }
}

# Exemples d'erreurs
ERROR_EXAMPLES = {
    "validation_error": {
        "application/json": {
            "success": False,
            "errors": {
                "email": ["Cette adresse email est déjà utilisée."],
                "password": ["Ce mot de passe est trop court."],
                "phone_number": ["Ce numéro de téléphone est déjà utilisé."]
            }
        }
    },
    "authentication_error": {
        "application/json": {
            "success": False,
            "message": "Identifiants invalides"
        }
    },
    "permission_error": {
        "application/json": {
            "success": False,
            "message": "Accès refusé. Permissions insuffisantes."
        }
    },
    "not_found_error": {
        "application/json": {
            "success": False,
            "message": "Utilisateur non trouvé"
        }
    },
    "otp_error": {
        "application/json": {
            "success": False,
            "message": "Code OTP invalide ou expiré"
        }
    }
}

# Exemples de statut de vérification téléphone
PHONE_VERIFICATION_EXAMPLE = {
    "application/json": {
        "success": True,
        "phone_verified": True,
        "phone_number": "+213123456789"
    }
}

# Exemples de tokens JWT
JWT_TOKEN_EXAMPLE = {
    "application/json": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImpvaG5fZG9lIiwicm9sZSI6InNlbmRlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzA1MzI0MDAwfQ.Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcwNTQxMDQwMH0.Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8"
    }
}

# Exemples pour les expéditions
SHIPMENT_CREATE_EXAMPLE = {
    "application/json": {
        "title": "Livraison de documents urgents",
        "description": "Documents importants à livrer rapidement",
        "origin_address": "123 Rue de la Paix, 75001 Paris, France",
        "destination_address": "456 Avenue des Champs, 69001 Lyon, France",
        "weight": 2.5,
        "dimensions": {
            "length": 30,
            "width": 20,
            "height": 5
        },
        "fragile": True,
        "urgent": True,
        "estimated_value": 500,
        "category": "documents",
        "pickup_date": "2024-01-20",
        "delivery_deadline": "2024-01-22"
    }
}

SHIPMENT_LIST_EXAMPLE = {
    "application/json": {
        "success": True,
        "shipments": [
            {
                "id": 1,
                "title": "Livraison de documents urgents",
                "status": "pending",
                "origin_address": "123 Rue de la Paix, 75001 Paris, France",
                "destination_address": "456 Avenue des Champs, 69001 Lyon, France",
                "weight": 2.5,
                "fragile": True,
                "urgent": True,
                "estimated_value": 500,
                "category": "documents",
                "created_at": "2024-01-15T10:30:00Z"
            }
        ],
        "count": 1
    }
}

SHIPMENT_UPDATE_EXAMPLE = {
    "application/json": {
        "title": "Livraison de documents urgents - Mise à jour",
        "description": "Documents importants à livrer rapidement - Urgent",
        "urgent": True,
        "delivery_deadline": "2024-01-22"
    }
}

# Exemples pour les voyages
TRIP_CREATE_EXAMPLE = {
    "application/json": {
        "title": "Voyage Paris-Lyon",
        "description": "Voyage régulier entre Paris et Lyon",
        "origin_address": "123 Rue de la Paix, 75001 Paris, France",
        "destination_address": "456 Avenue des Champs, 69001 Lyon, France",
        "departure_date": "2024-01-25T08:00:00Z",
        "arrival_date": "2024-01-25T12:00:00Z",
        "available_space": 100,
        "max_weight": 50,
        "price_per_kg": 2.5,
        "vehicle_type": "van",
        "route_details": "Autoroute A6",
        "flexible_dates": False
    }
}

TRIP_SEARCH_EXAMPLE = {
    "application/json": {
        "success": True,
        "trips": [
            {
                "id": 1,
                "title": "Voyage Paris-Lyon",
                "status": "active",
                "origin_address": "123 Rue de la Paix, 75001 Paris, France",
                "destination_address": "456 Avenue des Champs, 69001 Lyon, France",
                "departure_date": "2024-01-25T08:00:00Z",
                "arrival_date": "2024-01-25T12:00:00Z",
                "available_space": 100,
                "max_weight": 50,
                "price_per_kg": 2.5,
                "vehicle_type": "van",
                "driver": {
                    "id": 2,
                    "username": "driver1",
                    "first_name": "Jean",
                    "last_name": "Martin",
                    "rating": 4.9
                }
            }
        ],
        "count": 1
    }
}

# Exemples pour les paiements
PAYMENT_CREATE_EXAMPLE = {
    "application/json": {
        "amount": 125.50,
        "currency": "EUR",
        "payment_method": "card",
        "description": "Paiement pour expédition #1",
        "shipment_id": 1
    }
}

PAYMENT_WEBHOOK_EXAMPLE = {
    "application/json": {
        "payment_id": "pay_abc123",
        "status": "succeeded",
        "amount": 7550,
        "currency": "eur",
        "metadata": {
            "shipment_id": 1
        }
    }
}

# Exemples pour les notifications
NOTIFICATION_EXAMPLE = {
    "application/json": {
        "success": True,
        "notifications": [
            {
                "id": 1,
                "title": "Nouvelle correspondance trouvée",
                "message": "Une correspondance a été trouvée pour votre expédition",
                "notification_type": "shipment_match",
                "is_read": False,
                "created_at": "2024-01-15T10:30:00Z"
            }
        ],
        "count": 1
    }
}

# Exemples pour les évaluations
RATING_CREATE_EXAMPLE = {
    "application/json": {
        "rating": 5,
        "comment": "Service excellent, livraison rapide et soignée",
        "shipment_id": 1,
        "rated_user_id": 2
    }
}

# Exemples pour les correspondances (matching)
MATCHING_EXAMPLE = {
    "application/json": {
        "success": True,
        "matchings": [
            {
                "id": 1,
                "shipment": {
                    "id": 1,
                    "title": "Livraison de documents urgents",
                    "origin_address": "123 Rue de la Paix, 75001 Paris, France",
                    "destination_address": "456 Avenue des Champs, 69001 Lyon, France"
                },
                "trip": {
                    "id": 2,
                    "title": "Voyage Paris-Lyon",
                    "departure_date": "2024-01-25T08:00:00Z",
                    "arrival_date": "2024-01-25T12:00:00Z"
                },
                "status": "pending",
                "proposed_price": 150.00,
                "created_at": "2024-01-15T10:30:00Z"
            }
        ],
        "count": 1
    }
}

# Exemples pour les conversations (chat)
CHAT_EXAMPLE = {
    "application/json": {
        "success": True,
        "messages": [
            {
                "id": 1,
                "sender": {
                    "id": 1,
                    "username": "johndoe",
                    "first_name": "John",
                    "last_name": "Doe"
                },
                "content": "Bonjour, quand pouvez-vous récupérer le colis ?",
                "message_type": "text",
                "created_at": "2024-01-15T10:30:00Z"
            }
        ],
        "count": 1
    }
}

# Exemples pour l'internationalisation
INTERNATIONALIZATION_EXAMPLE = {
    "application/json": {
        "success": True,
        "translated_text": "Bonjour, comment allez-vous ?",
        "source_language": "en",
        "target_language": "fr"
    }
}

# Exemples pour Analytics
ANALYTICS_DASHBOARD_EXAMPLE = {
    "application/json": {
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
    }
}

ANALYTICS_SHIPMENT_EXAMPLE = {
    "application/json": {
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
    }
}

ANALYTICS_TRIP_EXAMPLE = {
    "application/json": {
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
    }
}

ANALYTICS_FINANCIAL_EXAMPLE = {
    "application/json": {
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
    }
}

ANALYTICS_EVENT_EXAMPLE = {
    "application/json": {
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
    }
}

# Exemples pour Documents
DOCUMENT_UPLOAD_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Document uploadé avec succès",
        "document": {
            "id": 1,
            "document_type": "identity_card",
            "file_url": "/media/documents/user_1/identity_card.pdf",
            "file_size": "2.5 MB",
            "uploaded_at": "2024-01-15T10:30:00Z",
            "status": "pending_verification",
            "description": "Carte d'identité française"
        }
    }
}

DOCUMENT_LIST_EXAMPLE = {
    "application/json": {
        "success": True,
        "documents": [
            {
                "id": 1,
                "document_type": "identity_card",
                "file_url": "/media/documents/user_1/identity_card.pdf",
                "file_size": "2.5 MB",
                "uploaded_at": "2024-01-15T10:30:00Z",
                "status": "verified",
                "verified_at": "2024-01-16T14:20:00Z",
                "description": "Carte d'identité française"
            }
        ],
        "count": 1
    }
}

DOCUMENT_VERIFY_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Document vérifié avec succès",
        "document": {
            "id": 1,
            "status": "verified",
            "verified_at": "2024-01-16T14:20:00Z",
            "verification_notes": "Document vérifié et approuvé"
        }
    }
}

# Exemples pour Matching
MATCHING_CREATE_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Correspondance créée avec succès",
        "matching": {
            "id": 1,
            "shipment": {
                "id": 1,
                "title": "Livraison de documents urgents",
                "origin": "Paris",
                "destination": "Lyon",
                "weight": 2.5
            },
            "trip": {
                "id": 2,
                "title": "Voyage Paris-Lyon",
                "departure_date": "2024-01-25T08:00:00Z",
                "available_space": 100
            },
            "compatibility_score": 85.5,
            "estimated_cost": 150.00,
            "status": "pending",
            "created_at": "2024-01-15T10:30:00Z"
        }
    }
}

MATCHING_LIST_EXAMPLE = {
    "application/json": {
        "success": True,
        "matchings": [
            {
                "id": 1,
                "shipment": {
                    "id": 1,
                    "title": "Livraison de documents urgents",
                    "origin": "Paris",
                    "destination": "Lyon",
                    "weight": 2.5
                },
                "trip": {
                    "id": 2,
                    "title": "Voyage Paris-Lyon",
                    "departure_date": "2024-01-25T08:00:00Z",
                    "available_space": 100
                },
                "compatibility_score": 85.5,
                "estimated_cost": 150.00,
                "status": "pending",
                "created_at": "2024-01-15T10:30:00Z"
            }
        ],
        "count": 1,
        "total_pages": 1,
        "current_page": 1
    }
}

MATCHING_ACCEPT_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Correspondance acceptée avec succès",
        "matching": {
            "id": 1,
            "status": "accepted",
            "accepted_price": 150.00,
            "accepted_at": "2024-01-15T11:30:00Z"
        }
    }
}

MATCHING_REJECT_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Correspondance rejetée",
        "matching": {
            "id": 1,
            "status": "rejected",
            "rejection_reason": "Prix trop élevé",
            "rejected_at": "2024-01-15T11:30:00Z"
        }
    }
}

# Exemples pour Notifications
NOTIFICATION_SEND_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Notification envoyée avec succès",
        "notification": {
            "id": 1,
            "recipient_id": 1,
            "title": "Nouvelle correspondance trouvée",
            "message": "Une correspondance a été trouvée pour votre expédition",
            "notification_type": "shipment_match",
            "is_read": False,
            "created_at": "2024-01-15T10:30:00Z"
        }
    }
}

NOTIFICATION_MARK_READ_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Notifications marquées comme lues",
        "updated_count": 3
    }
}

NOTIFICATION_TEMPLATE_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Modèle de notification créé avec succès",
        "template": {
            "id": 1,
            "name": "shipment_created",
            "subject": "Nouvelle expédition créée",
            "body": "Votre expédition {{shipment_id}} a été créée avec succès.",
            "notification_type": "email",
            "is_active": True,
            "created_at": "2024-01-15T10:30:00Z"
        }
    }
}

# Exemples pour Payments
PAYMENT_DEPOSIT_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Dépôt effectué avec succès",
        "transaction": {
            "id": 1,
            "transaction_type": "deposit",
            "amount": 500.00,
            "payment_method": "card",
            "status": "completed",
            "reference": "DEP123456",
            "created_at": "2024-01-15T10:30:00Z"
        },
        "new_balance": 500.00
    }
}

PAYMENT_WITHDRAW_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Demande de retrait soumise avec succès",
        "transaction": {
            "id": 2,
            "transaction_type": "withdrawal",
            "amount": 200.00,
            "payment_method": "bank_transfer",
            "status": "pending",
            "reference": "WIT789012",
            "created_at": "2024-01-15T11:30:00Z"
        }
    }
}

PAYMENT_TRANSFER_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Transfert effectué avec succès",
        "transaction": {
            "id": 3,
            "transaction_type": "transfer",
            "amount": 50.00,
            "recipient_id": 2,
            "status": "completed",
            "reference": "TRA345678",
            "created_at": "2024-01-15T12:30:00Z"
        },
        "new_balance": 450.00
    }
}

PAYMENT_REFUND_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Remboursement initié avec succès",
        "refund": {
            "id": 1,
            "original_transaction_id": 1,
            "amount": 125.50,
            "reason": "Service non fourni",
            "status": "pending",
            "created_at": "2024-01-15T13:30:00Z"
        }
    }
}

# Exemples pour Shipments
SHIPMENT_TRACKING_EXAMPLE = {
    "application/json": {
        "success": True,
        "shipment": {
            "id": 1,
            "tracking_number": "KL123456789",
            "status": "in_transit",
            "origin_address": "123 Rue de la Paix, 75001 Paris, France",
            "destination_address": "456 Avenue des Champs, 69001 Lyon, France",
            "estimated_delivery": "2024-01-22",
            "tracking_events": [
                {
                    "id": 1,
                    "event_type": "created",
                    "description": "Expédition créée",
                    "location": "Paris",
                    "timestamp": "2024-01-15T10:30:00Z"
                },
                {
                    "id": 2,
                    "event_type": "picked_up",
                    "description": "Colis récupéré",
                    "location": "Paris",
                    "timestamp": "2024-01-16T14:20:00Z"
                },
                {
                    "id": 3,
                    "event_type": "in_transit",
                    "description": "En cours de livraison",
                    "location": "En route",
                    "timestamp": "2024-01-17T09:15:00Z"
                }
            ]
        }
    }
}

SHIPMENT_UPDATE_STATUS_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Statut mis à jour avec succès",
        "tracking_event": {
            "id": 4,
            "event_type": "delivered",
            "description": "Livraison effectuée",
            "location": "Lyon",
            "timestamp": "2024-01-18T16:45:00Z"
        }
    }
}

SHIPMENT_DELIVERY_OTP_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "OTP de livraison généré",
        "delivery_otp": "123456",
        "expires_at": "2024-01-18T17:45:00Z"
    }
}

SHIPMENT_VERIFY_DELIVERY_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Livraison confirmée avec succès",
        "delivery_confirmation": {
            "delivered_at": "2024-01-18T16:45:00Z",
            "signed_by": "John Doe",
            "otp_verified": True
        }
    }
}

# Exemples pour Trips
TRIP_UPDATE_STATUS_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Statut du voyage mis à jour",
        "trip": {
            "id": 1,
            "status": "completed",
            "completed_at": "2024-01-18T16:45:00Z",
            "notes": "Voyage terminé avec succès"
        }
    }
}

TRIP_UPDATE_CAPACITY_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Capacité mise à jour avec succès",
        "trip": {
            "id": 1,
            "available_space": 80,
            "max_weight": 40,
            "updated_at": "2024-01-15T14:30:00Z"
        }
    }
}

TRIP_DOCUMENT_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Document de voyage uploadé",
        "document": {
            "id": 1,
            "trip_id": 1,
            "document_type": "vehicle_registration",
            "file_url": "/media/trip_documents/trip_1/vehicle_registration.pdf",
            "uploaded_at": "2024-01-15T10:30:00Z"
        }
    }
}

# Exemples pour Users
USER_REFRESH_TOKEN_EXAMPLE = {
    "application/json": {
        "success": True,
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}

USER_LOGOUT_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Déconnexion réussie"
    }
}

USER_VERIFICATION_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Demande de vérification soumise",
        "verification": {
            "id": 1,
            "verification_type": "identity",
            "status": "pending",
            "submitted_at": "2024-01-15T10:30:00Z"
        }
    }
}

USER_VERIFICATION_STATUS_EXAMPLE = {
    "application/json": {
        "success": True,
        "verification_status": "verified",
        "verifications": [
            {
                "id": 1,
                "type": "identity",
                "status": "verified",
                "verified_at": "2024-01-16T14:20:00Z"
            },
            {
                "id": 2,
                "type": "address",
                "status": "pending",
                "submitted_at": "2024-01-15T10:30:00Z"
            }
        ]
    }
}

# Exemples pour l'admin panel
ADMIN_USER_MANAGEMENT_EXAMPLE = {
    "application/json": {
        "success": True,
        "message": "Utilisateur suspendu avec succès"
    }
}

ADMIN_SYSTEM_STATS_EXAMPLE = {
    "application/json": {
        "success": True,
        "stats": {
            "total_users": 1250,
            "active_shipments": 45,
            "active_trips": 15,
            "total_revenue": 25000.00,
            "system_health": "good"
        }
    }
} 