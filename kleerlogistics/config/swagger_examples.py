"""
Exemples JSON pour la documentation Swagger de KleerLogistics
"""

# Exemples pour l'authentification et les utilisateurs
USER_REGISTRATION_EXAMPLE = {
    "request": {
        "email": "john.doe@example.com",
        "username": "johndoe",
        "first_name": "John",
        "last_name": "Doe",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!"
    },
    "response_success": {
        "success": True,
        "message": "Utilisateur créé avec succès",
        "user_id": 1,
        "email": "john.doe@example.com"
    },
    "response_error": {
        "success": False,
        "errors": {
            "email": ["Cet email est déjà utilisé."],
            "username": ["Ce nom d'utilisateur est déjà utilisé."],
            "password": ["Les mots de passe ne correspondent pas."]
        }
    }
}

USER_PROFILE_EXAMPLE = {
    "request_update": {
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+33123456789",
        "date_of_birth": "1990-05-15",
        "country": "France",
        "city": "Paris",
        "address": "123 Rue de la Paix, 75001 Paris",
        "bio": "Expéditeur expérimenté avec 5 ans d'expérience"
    },
    "response_get": {
        "success": True,
        "profile": {
            "user_type": "sender",
            "phone_number": "+33123456789",
            "phone_verified": True,
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-05-15",
            "country": "France",
            "city": "Paris",
            "address": "123 Rue de la Paix, 75001 Paris",
            "rating": 4.8,
            "total_trips": 15,
            "total_shipments": 45,
            "is_verified": True,
            "verification_status": "verified",
            "bio": "Expéditeur expérimenté avec 5 ans d'expérience"
        }
    }
}

PHONE_VERIFICATION_EXAMPLE = {
    "request_send_otp": {
        "phone_number": "+33123456789"
    },
    "request_verify_otp": {
        "phone": "+33123456789",
        "otp": "123456"
    },
    "response_send_otp": {
        "success": True,
        "message": "Code OTP envoyé avec succès",
        "phone_number": "+33123456789"
    },
    "response_verify_otp": {
        "success": True,
        "message": "Numéro de téléphone vérifié avec succès",
        "phone_verified": True
    }
}

PASSWORD_CHANGE_EXAMPLE = {
    "request": {
        "old_password": "OldPassword123!",
        "new_password": "NewSecurePass456!",
        "new_password_confirm": "NewSecurePass456!"
    },
    "response_success": {
        "success": True,
        "message": "Mot de passe modifié avec succès"
    },
    "response_error": {
        "success": False,
        "errors": {
            "old_password": ["Mot de passe incorrect"],
            "new_password": ["Les mots de passe ne correspondent pas"]
        }
    }
}

PASSWORD_RESET_EXAMPLE = {
    "request_reset": {
        "email": "john.doe@example.com"
    },
    "response_reset": {
        "success": True,
        "message": "Email de réinitialisation envoyé"
    }
}

# Exemples pour les documents utilisateur
USER_DOCUMENT_EXAMPLE = {
    "request_upload": {
        "document_type": "identity_card",
        "file": "(fichier binaire)"
    },
    "response_upload": {
        "success": True,
        "message": "Document uploadé avec succès",
        "document": {
            "id": 1,
            "document_type": "identity_card",
            "file_url": "/media/documents/user_1/identity_card.pdf",
            "uploaded_at": "2024-01-15T10:30:00Z",
            "status": "pending_verification"
        }
    },
    "response_list": {
        "success": True,
        "documents": [
            {
                "id": 1,
                "document_type": "identity_card",
                "file_url": "/media/documents/user_1/identity_card.pdf",
                "uploaded_at": "2024-01-15T10:30:00Z",
                "status": "verified"
            },
            {
                "id": 2,
                "document_type": "proof_of_address",
                "file_url": "/media/documents/user_1/address_proof.pdf",
                "uploaded_at": "2024-01-16T14:20:00Z",
                "status": "pending_verification"
            }
        ],
        "pagination": {
            "count": 2,
            "next": None,
            "previous": None
        }
    }
}

# Exemples pour la recherche d'utilisateurs
USER_SEARCH_EXAMPLE = {
    "request": {
        "query": "john",
        "user_type": "sender",
        "country": "France"
    },
    "response": {
        "success": True,
        "users": [
            {
                "id": 1,
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                    "user_type": "sender",
                    "country": "France",
                "city": "Paris",
                "rating": 4.8,
                "is_verified": True
            }
        ],
        "pagination": {
            "count": 1,
            "next": None,
            "previous": None
        }
    }
}

# Exemples pour les expéditions
SHIPMENT_CREATE_EXAMPLE = {
    "request": {
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
    },
    "response_success": {
        "success": True,
        "message": "Expédition créée avec succès",
        "shipment": {
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
    }
}

SHIPMENT_LIST_EXAMPLE = {
    "request": {
            "status": "pending",
        "date_from": "2024-01-01",
        "date_to": "2024-01-31"
    },
    "response": {
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
        "pagination": {
            "count": 1,
            "next": None,
            "previous": None
        }
    }
}

SHIPMENT_UPDATE_EXAMPLE = {
    "request": {
        "title": "Livraison de documents urgents - Mise à jour",
        "description": "Documents importants à livrer rapidement - Urgent",
        "urgent": True,
        "delivery_deadline": "2024-01-22"
    },
    "response": {
        "success": True,
        "message": "Expédition mise à jour avec succès",
        "shipment": {
            "id": 1,
            "title": "Livraison de documents urgents - Mise à jour",
            "description": "Documents importants à livrer rapidement - Urgent",
            "urgent": True,
            "delivery_deadline": "2024-01-22",
            "updated_at": "2024-01-16T14:20:00Z"
        }
    }
}

# Exemples pour les voyages
TRIP_CREATE_EXAMPLE = {
    "request": {
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
    },
    "response_success": {
        "success": True,
        "message": "Voyage créé avec succès",
        "trip": {
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
            "created_at": "2024-01-15T10:30:00Z"
        }
    }
}

TRIP_SEARCH_EXAMPLE = {
    "request": {
        "origin": "Paris",
        "destination": "Lyon",
        "date_from": "2024-01-20",
        "date_to": "2024-01-30",
        "max_price": 3.0,
        "vehicle_type": "van"
    },
    "response": {
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
        "pagination": {
            "count": 1,
            "next": None,
            "previous": None
        }
    }
}

# Exemples pour les paiements
PAYMENT_CREATE_EXAMPLE = {
    "request": {
        "amount": 125.50,
        "currency": "EUR",
        "payment_method": "card",
        "description": "Paiement pour expédition #1",
        "shipment_id": 1
    },
    "response_success": {
        "success": True,
        "message": "Paiement initié avec succès",
        "payment": {
            "id": 1,
            "amount": 125.50,
            "currency": "EUR",
            "payment_method": "card",
            "status": "pending",
            "description": "Paiement pour expédition #1",
            "shipment_id": 1,
            "created_at": "2024-01-15T10:30:00Z"
        }
    }
}

PAYMENT_WEBHOOK_EXAMPLE = {
    "request": {
        "payment_id": "pay_abc123",
        "status": "succeeded",
        "amount": 7550,
        "currency": "eur",
        "metadata": {
            "shipment_id": 1
        }
    },
    "response": {
        "success": True,
        "message": "Webhook traité avec succès"
    }
}

# Exemples pour les notifications
NOTIFICATION_EXAMPLE = {
    "request_send": {
        "recipient_id": 1,
        "title": "Nouvelle correspondance trouvée",
        "message": "Une correspondance a été trouvée pour votre expédition",
        "notification_type": "shipment_match",
        "data": {
            "shipment_id": 1,
            "trip_id": 2
        }
    },
    "response_send": {
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
    },
    "response_list": {
        "success": True,
        "notifications": [
            {
                "id": 1,
                "title": "Nouvelle correspondance trouvée",
                "message": "Une correspondance a été trouvée pour votre expédition",
                "notification_type": "shipment_match",
                "is_read": False,
                "created_at": "2024-01-15T10:30:00Z"
            },
            {
                "id": 2,
                "title": "Paiement reçu",
                "message": "Votre paiement de 125.50€ a été confirmé",
                "notification_type": "payment_received",
                "is_read": True,
                "created_at": "2024-01-14T15:20:00Z"
            }
        ],
        "pagination": {
            "count": 2,
            "next": None,
            "previous": None
        }
    }
}

# Exemples pour les évaluations
RATING_CREATE_EXAMPLE = {
    "request": {
        "rating": 5,
        "comment": "Service excellent, livraison rapide et soignée",
        "shipment_id": 1,
        "rated_user_id": 2
    },
    "response_success": {
        "success": True,
        "message": "Évaluation créée avec succès",
        "rating": {
            "id": 1,
            "rating": 5,
            "comment": "Service excellent, livraison rapide et soignée",
            "shipment_id": 1,
            "rater_id": 1,
            "rated_user_id": 2,
            "created_at": "2024-01-15T10:30:00Z"
        }
    }
}

# Exemples pour les erreurs communes
ERROR_EXAMPLES = {
    "validation_error": {
        "success": False,
        "message": "Erreur de validation",
        "errors": {
            "field_name": ["Ce champ est requis."],
            "email": ["Format d'email invalide."]
        }
    },
    "not_found_error": {
        "success": False,
        "message": "Ressource non trouvée",
        "error_code": "NOT_FOUND"
    },
    "authentication_error": {
        "success": False,
        "message": "Authentification requise",
        "error_code": "UNAUTHORIZED"
    },
    "permission_error": {
        "success": False,
        "message": "Permissions insuffisantes",
        "error_code": "FORBIDDEN"
    }
}

# Exemples pour les correspondances (matching)
MATCHING_EXAMPLE = {
    "request_create": {
        "shipment_id": 1,
        "trip_id": 2,
        "proposed_price": 150.00,
        "message": "Je peux transporter votre colis"
    },
    "response_create": {
        "success": True,
        "message": "Correspondance créée avec succès",
        "matching": {
            "id": 1,
            "shipment_id": 1,
            "trip_id": 2,
            "status": "pending",
            "proposed_price": 150.00,
            "message": "Je peux transporter votre colis",
            "created_at": "2024-01-15T10:30:00Z"
        }
    },
    "response_list": {
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
        "pagination": {
            "count": 1,
            "next": None,
            "previous": None
        }
    }
}

# Exemples pour les conversations (chat)
CHAT_EXAMPLE = {
    "request_create_conversation": {
        "shipment_id": 1,
        "participant_ids": [1, 2]
    },
    "response_create_conversation": {
        "success": True,
        "message": "Conversation créée avec succès",
        "conversation": {
            "id": 1,
            "shipment_id": 1,
            "participants": [
                {"id": 1, "username": "johndoe"},
                {"id": 2, "username": "driver1"}
            ],
            "created_at": "2024-01-15T10:30:00Z"
        }
    },
    "request_send_message": {
        "content": "Bonjour, quand pouvez-vous récupérer le colis ?",
        "message_type": "text"
    },
    "response_send_message": {
        "success": True,
        "message": "Message envoyé avec succès",
        "message": {
            "id": 1,
            "conversation_id": 1,
            "sender_id": 1,
            "content": "Bonjour, quand pouvez-vous récupérer le colis ?",
            "message_type": "text",
            "created_at": "2024-01-15T10:30:00Z"
        }
    },
    "response_list_messages": {
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
            },
            {
                "id": 2,
                "sender": {
                    "id": 2,
                    "username": "driver1",
                    "first_name": "Jean",
                    "last_name": "Martin"
                },
                "content": "Je peux passer demain à 14h",
                "message_type": "text",
                "created_at": "2024-01-15T10:35:00Z"
            }
        ],
    "pagination": {
            "count": 2,
            "next": None,
            "previous": None
        }
    }
}

# Exemples pour l'internationalisation
INTERNATIONALIZATION_EXAMPLE = {
    "request_translate": {
        "text": "Hello, how are you?",
        "source_language": "en",
        "target_language": "fr"
    },
    "response_translate": {
        "success": True,
        "translated_text": "Bonjour, comment allez-vous ?",
        "source_language": "en",
        "target_language": "fr"
    },
    "response_languages": {
        "success": True,
        "languages": [
            {"code": "fr", "name": "Français", "native_name": "Français"},
            {"code": "en", "name": "English", "native_name": "English"},
            {"code": "ar", "name": "Arabic", "native_name": "العربية"}
        ]
    }
}

# Exemples pour Analytics
ANALYTICS_DASHBOARD_EXAMPLE = {
    "request": {
        "date_from": "2024-01-01",
        "date_to": "2024-01-31"
    },
    "response": {
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
            },
            "financial": {
                "total_balance": 1250.50,
                "total_deposits": 3000.00,
                "total_withdrawals": 1500.00,
                "total_transactions": 25,
                "monthly_revenue": [
                    {"month": "2024-01", "amount": 2500.00},
                    {"month": "2024-02", "amount": 2800.00}
                ]
            },
            "charts": {
                "shipment_status_chart": [
                    {"status": "pending", "count": 8},
                    {"status": "in_transit", "count": 12},
                    {"status": "delivered", "count": 20},
                    {"status": "cancelled", "count": 5}
                ],
                "monthly_shipments": [
                    {"month": "2024-01", "count": 15},
                    {"month": "2024-02", "count": 18}
                ],
                "top_destinations": [
                    {"destination": "Lyon", "count": 8},
                    {"destination": "Marseille", "count": 6},
                    {"destination": "Toulouse", "count": 4}
                ]
            }
        }
    }
}

ANALYTICS_SHIPMENT_EXAMPLE = {
    "request": {
        "date_from": "2024-01-01",
        "date_to": "2024-01-31"
    },
    "response": {
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
            ],
            "revenue_analysis": {
                "total_revenue": 2500.00,
                "average_revenue_per_shipment": 55.56,
                "revenue_by_category": [
                    {"category": "documents", "revenue": 800.00},
                    {"category": "electronics", "revenue": 1200.00},
                    {"category": "clothing", "revenue": 500.00}
                ]
            },
            "delivery_performance": {
                "average_delivery_time": 3.2,
                "on_time_deliveries": 18,
                "late_deliveries": 2,
                "delivery_success_rate": 90.0
            }
        }
    }
}

ANALYTICS_TRIP_EXAMPLE = {
    "request": {
        "date_from": "2024-01-01",
        "date_to": "2024-01-31"
    },
    "response": {
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
            ],
            "earnings_analysis": {
                "total_earnings": 1800.00,
                "average_earnings_per_trip": 120.00,
                "earnings_by_vehicle": [
                    {"vehicle": "car", "earnings": 800.00},
                    {"vehicle": "van", "earnings": 1000.00}
                ]
            },
            "performance_metrics": {
                "average_rating": 4.8,
                "total_reviews": 12,
                "completion_rate": 85.7,
                "customer_satisfaction": 92.0
            }
        }
    }
}

ANALYTICS_FINANCIAL_EXAMPLE = {
    "request": {
        "date_from": "2024-01-01",
        "date_to": "2024-01-31"
    },
    "response": {
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
            ],
            "payment_methods": [
                {"method": "card", "count": 12, "amount": 1800.00},
                {"method": "bank_transfer", "count": 8, "amount": 1200.00},
                {"method": "paypal", "count": 5, "amount": 750.00}
            ],
            "cash_flow": {
                "inflow": 3000.00,
                "outflow": 1500.00,
                "net_cash_flow": 1500.00,
                "cash_flow_trend": "positive"
            }
        }
    }
}

ANALYTICS_EVENT_EXAMPLE = {
    "request": {
        "event_type": "shipment_created",
        "event_data": {
            "shipment_id": 1,
            "user_id": 1,
            "amount": 125.50
        },
        "timestamp": "2024-01-15T10:30:00Z"
    },
    "response": {
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
    "request": {
        "document_type": "identity_card",
        "file": "(fichier binaire)",
        "description": "Carte d'identité française"
    },
    "response": {
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
    "request": {
        "document_type": "identity_card",
        "status": "verified"
    },
    "response": {
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
            },
            {
                "id": 2,
                "document_type": "proof_of_address",
                "file_url": "/media/documents/user_1/address_proof.pdf",
                "file_size": "1.8 MB",
                "uploaded_at": "2024-01-16T14:20:00Z",
                "status": "pending_verification",
                "description": "Justificatif de domicile"
            }
        ],
        "pagination": {
            "count": 2,
            "next": None,
            "previous": None
        }
    }
}

DOCUMENT_VERIFY_EXAMPLE = {
    "request": {
        "status": "verified",
        "verification_notes": "Document vérifié et approuvé"
    },
    "response": {
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
    "request": {
        "shipment_id": 1,
        "trip_id": 2,
        "proposed_price": 150.00,
        "message": "Je peux transporter votre colis"
    },
    "response": {
        "success": True,
        "message": "Correspondance créée avec succès",
        "matching": {
            "id": 1,
            "shipment_id": 1,
            "trip_id": 2,
            "status": "pending",
            "proposed_price": 150.00,
            "message": "Je peux transporter votre colis",
            "created_at": "2024-01-15T10:30:00Z"
        }
    }
}

MATCHING_ACCEPT_EXAMPLE = {
    "request": {
        "accepted_price": 150.00,
        "message": "J'accepte votre proposition"
    },
    "response": {
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
    "request": {
        "reason": "Prix trop élevé",
        "message": "Merci mais le prix ne me convient pas"
    },
    "response": {
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

MATCHING_LIST_EXAMPLE = {
    "request": {
        "status": "pending",
        "shipment_id": 1
    },
    "response": {
        "success": True,
        "matchings": [
            {
                "id": 1,
                "shipment": {
                    "id": 1,
                    "title": "Livraison de documents urgents",
                    "origin_address": "123 Rue de la Paix, 75001 Paris, France",
                    "destination_address": "456 Avenue des Champs, 69001 Lyon, France",
                    "weight": 2.5,
                    "fragile": True,
        "urgent": True
                },
                "trip": {
                    "id": 2,
                    "title": "Voyage Paris-Lyon",
                    "departure_date": "2024-01-25T08:00:00Z",
                    "arrival_date": "2024-01-25T12:00:00Z",
                    "available_space": 100,
                    "price_per_kg": 2.5
                },
                "status": "pending",
                "proposed_price": 150.00,
                "created_at": "2024-01-15T10:30:00Z"
            }
        ],
        "pagination": {
            "count": 1,
            "next": None,
            "previous": None
        }
    }
}

# Exemples pour Notifications
NOTIFICATION_SEND_EXAMPLE = {
    "request": {
        "recipient_id": 1,
        "title": "Nouvelle correspondance trouvée",
        "message": "Une correspondance a été trouvée pour votre expédition",
        "notification_type": "shipment_match",
        "data": {
            "shipment_id": 1,
            "trip_id": 2
        }
    },
    "response": {
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
    "request": {
        "notification_ids": [1, 2, 3]
    },
    "response": {
        "success": True,
        "message": "Notifications marquées comme lues",
        "updated_count": 3
    }
}

NOTIFICATION_TEMPLATE_EXAMPLE = {
    "request": {
        "name": "shipment_created",
        "subject": "Nouvelle expédition créée",
        "body": "Votre expédition {{shipment_id}} a été créée avec succès.",
        "notification_type": "email"
    },
    "response": {
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
    "request": {
        "amount": 500.00,
        "payment_method": "card",
        "description": "Dépôt initial"
    },
    "response": {
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
    "request": {
        "amount": 200.00,
        "bank_account": "FR7630001007941234567890185",
        "description": "Retrait vers compte bancaire"
    },
    "response": {
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
    "request": {
        "recipient_id": 2,
        "amount": 50.00,
        "description": "Paiement pour service"
    },
    "response": {
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
    "request": {
        "transaction_id": 1,
        "reason": "Service non fourni",
        "amount": 125.50
    },
    "response": {
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
    "request": {
        "tracking_number": "KL123456789"
    },
    "response": {
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
    "request": {
        "status": "delivered",
        "location": "Lyon",
        "description": "Livraison effectuée"
    },
    "response": {
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
    "request": {
        "tracking_number": "KL123456789"
    },
    "response": {
        "success": True,
        "message": "OTP de livraison généré",
        "delivery_otp": "123456",
        "expires_at": "2024-01-18T17:45:00Z"
    }
}

SHIPMENT_VERIFY_DELIVERY_EXAMPLE = {
    "request": {
        "tracking_number": "KL123456789",
        "otp": "123456",
        "signature": "John Doe"
    },
    "response": {
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
    "request": {
        "status": "completed",
        "notes": "Voyage terminé avec succès"
    },
    "response": {
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
    "request": {
        "available_space": 80,
        "max_weight": 40
    },
    "response": {
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
    "request": {
        "document_type": "vehicle_registration",
        "file": "(fichier binaire)",
        "description": "Carte grise du véhicule"
    },
    "response": {
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
USER_LOGIN_EXAMPLE = {
    "request": {
        "username": "johndoe",
        "password": "SecurePass123!"
    },
    "response": {
        "success": True,
        "message": "Connexion réussie",
        "tokens": {
            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        },
        "user": {
            "id": 1,
            "username": "johndoe",
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
    }
}

USER_REFRESH_TOKEN_EXAMPLE = {
    "request": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    },
    "response": {
        "success": True,
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}

USER_LOGOUT_EXAMPLE = {
    "request": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    },
    "response": {
        "success": True,
        "message": "Déconnexion réussie"
    }
}

USER_VERIFICATION_EXAMPLE = {
    "request": {
        "verification_type": "identity",
        "documents": ["(fichier binaire)"],
        "additional_info": "Informations supplémentaires"
    },
    "response": {
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
    "response": {
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