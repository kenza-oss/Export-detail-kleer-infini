# DICTIONNAIRE DE DONNÉES - KLEER LOGISTICS API

## 📋 **Vue d'ensemble**

Ce dictionnaire de données documente l'ensemble des entités, attributs et relations de la base de données de l'API Kleer Logistics. Le système permet de connecter expéditeurs et voyageurs pour le transport de colis avec un système de matching intelligent.


---

## 🗂️ **1. MODULE USERS - Gestion des Utilisateurs**

### **1.1 User (Utilisateur)**
**Table principale des utilisateurs du système**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `username` | CharField | 150 | Oui | Unique | Nom d'utilisateur |
| `email` | EmailField | 254 | Oui | Unique | Adresse email |
| `password` | CharField | 128 | Oui | Hashé | Mot de passe |
| `first_name` | CharField | 150 | Non | - | Prénom |
| `last_name` | CharField | 150 | Non | - | Nom de famille |
| `role` | CharField | 10 | Oui | sender, traveler, admin, both | Rôle utilisateur |
| `phone_number` | CharField | 15 | Non | Unique, format: +?1?\d{9,15} | Numéro de téléphone |
| `is_phone_verified` | BooleanField | - | Oui | False | Statut vérification téléphone |
| `is_document_verified` | BooleanField | - | Oui | False | Statut vérification documents |
| `rating` | DecimalField | 3,2 | Oui | 0.00-9.99 | Note moyenne utilisateur |
| `total_trips` | PositiveIntegerField | - | Oui | 0 | Nombre total de trajets |
| `total_shipments` | PositiveIntegerField | - | Oui | 0 | Nombre total d'envois |
| `preferred_language` | CharField | 5 | Oui | fr | Langue préférée |
| `is_active_traveler` | BooleanField | - | Oui | False | Voyageur actif |
| `is_active_sender` | BooleanField | - | Oui | False | Expéditeur actif |
| `wallet_balance` | DecimalField | 10,2 | Oui | 0.00 | Solde portefeuille |
| `commission_rate` | DecimalField | 5,2 | Oui | 10.00 | Taux commission (%) |
| `is_active` | BooleanField | - | Oui | True | Compte actif |
| `is_staff` | BooleanField | - | Oui | False | Accès admin |
| `is_superuser` | BooleanField | - | Oui | False | Super utilisateur |
| `date_joined` | DateTimeField | - | Oui | Auto | Date d'inscription |
| `last_login` | DateTimeField | - | Non | - | Dernière connexion |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

**Relations :**
- `sent_shipments` → Shipment (One-to-Many)
- `trips` → Trip (One-to-Many)
- `wallet` → Wallet (One-to-One)
- `profile` → UserProfile (One-to-One)
- `documents` → UserDocument (One-to-Many)
- `otp_codes` → OTPCode (One-to-Many)

### **1.2 UserProfile (Profil Utilisateur)**
**Informations complémentaires du profil utilisateur**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `user` | OneToOneField | - | Oui | User | Référence utilisateur |
| `birth_date` | DateField | - | Non | - | Date de naissance |
| `address` | TextField | - | Non | - | Adresse complète |
| `city` | CharField | 100 | Non | - | Ville |
| `country` | CharField | 100 | Oui | Algeria | Pays |
| `avatar` | ImageField | - | Non | - | Photo de profil |
| `bio` | TextField | 500 | Non | - | Biographie |

### **1.3 UserDocument (Document Utilisateur)**
**Documents de vérification des utilisateurs**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `user` | ForeignKey | - | Oui | User | Utilisateur propriétaire |
| `document_type` | CharField | 20 | Oui | passport, national_id, flight_ticket, address_proof | Type de document |
| `document_file` | FileField | - | Oui | - | Fichier document |
| `status` | CharField | 10 | Oui | pending, approved, rejected | Statut vérification |
| `verified_at` | DateTimeField | - | Non | - | Date vérification |
| `verified_by` | ForeignKey | - | Non | User | Vérificateur |
| `rejection_reason` | TextField | - | Non | - | Raison rejet |
| `uploaded_at` | DateTimeField | - | Oui | Auto | Date upload |

### **1.4 OTPCode (Code OTP)**
**Codes OTP pour authentification et livraison**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `user` | ForeignKey | - | Non | User | Utilisateur associé |
| `phone_number` | CharField | 15 | Oui | - | Numéro téléphone |
| `code` | CharField | 64 | Oui | Hash SHA256 | Code OTP hashé |
| `is_used` | BooleanField | - | Oui | False | Code utilisé |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `expires_at` | DateTimeField | - | Oui | - | Date expiration |

### **1.5 DeliveryOTP (OTP de Livraison)**
**Codes OTP pour confirmation de livraison**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `shipment` | ForeignKey | - | Oui | Shipment | Envoi associé |
| `otp_code` | CharField | 6 | Oui | 6 chiffres | Code OTP de livraison |
| `recipient_phone` | CharField | 20 | Oui | - | Téléphone destinataire |
| `recipient_name` | CharField | 200 | Oui | - | Nom destinataire |
| `generated_by` | ForeignKey | - | Oui | User | Voyageur qui génère |
| `created_at` | DateTimeField | - | Oui | Auto | Date génération |
| `expires_at` | DateTimeField | - | Oui | 24h après création | Date expiration |
| `is_used` | BooleanField | - | Oui | False | OTP utilisé |
| `verified_at` | DateTimeField | - | Non | - | Date vérification |
| `verified_by` | ForeignKey | - | Non | User | Voyageur qui vérifie |
| `sms_sent` | BooleanField | - | Oui | False | SMS envoyé |
| `sms_sent_at` | DateTimeField | - | Non | - | Date envoi SMS |
| `sms_delivery_status` | CharField | 20 | Oui | pending, sent, delivered, failed | Statut SMS |

**Relations :**
- `shipment` → Shipment (Many-to-One)
- `generated_by` → User (Many-to-One)
- `verified_by` → User (Many-to-One)

---

## 📦 **2. MODULE SHIPMENTS - Gestion des Envois**

### **2.1 Shipment (Envoi)**
**Envois de colis créés par les expéditeurs**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `tracking_number` | CharField | 50 | Oui | Unique, format: KLxxxxxxxx | Numéro de suivi |
| `sender` | ForeignKey | - | Oui | User | Expéditeur |
| `package_type` | CharField | 20 | Oui | document, electronics, clothing, food, medicine, fragile, other | Type de colis |
| `description` | TextField | - | Oui | - | Description du colis |
| `weight` | DecimalField | 8,2 | Oui | 0.01-50.00 kg | Poids du colis |
| `dimensions` | JSONField | - | Non | {length, width, height} | Dimensions |
| `value` | DecimalField | 10,2 | Oui | 0.00 | Valeur déclarée |
| `is_fragile` | BooleanField | - | Oui | False | Colis fragile |
| `origin_city` | CharField | 100 | Oui | - | Ville d'origine |
| `origin_address` | TextField | - | Oui | - | Adresse d'origine |
| `destination_city` | CharField | 100 | Oui | - | Ville de destination |
| `destination_country` | CharField | 100 | Oui | - | Pays de destination |
| `destination_address` | TextField | - | Oui | - | Adresse de destination |
| `recipient_name` | CharField | 200 | Oui | - | Nom destinataire |
| `recipient_phone` | CharField | 20 | Oui | - | Téléphone destinataire |
| `recipient_email` | EmailField | - | Non | - | Email destinataire |
| `preferred_pickup_date` | DateTimeField | - | Oui | - | Date ramassage préférée |
| `max_delivery_date` | DateTimeField | - | Oui | - | Date livraison max |
| `urgency` | CharField | 10 | Oui | low, medium, high, urgent | Niveau urgence |
| `status` | CharField | 20 | Oui | draft, pending, matched, in_transit, delivered, cancelled, lost | Statut envoi |
| `matched_trip` | ForeignKey | - | Non | Trip | Trajet associé |
| `price` | DecimalField | 10,2 | Non | - | Prix transport |
| `is_paid` | BooleanField | - | Oui | False | Payé |
| `payment_method` | CharField | 20 | Non | wallet, card, cash, bank_transfer | Méthode paiement |
| `payment_status` | CharField | 20 | Oui | pending, paid, failed, refunded | Statut paiement |
| `payment_date` | DateTimeField | - | Non | - | Date paiement |
| `otp_code` | CharField | 6 | Non | - | Code OTP ramassage (obsolète) |
| `otp_generated_at` | DateTimeField | - | Non | - | Date génération OTP (obsolète) |
| `delivery_otp` | CharField | 6 | Non | - | Code OTP livraison (obsolète - remplacé par DeliveryOTP) |
| `delivery_date` | DateTimeField | - | Non | - | Date livraison effective |
| `delivery_notes` | TextField | - | Non | - | Notes sur la livraison |
| `recipient_signature` | CharField | 200 | Non | - | Signature du destinataire |
| `shipping_cost` | DecimalField | 10,2 | Non | - | Coût expédition |
| `special_instructions` | TextField | - | Non | - | Instructions spéciales |
| `insurance_requested` | BooleanField | - | Oui | False | Assurance demandée |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

**Relations :**
- `sender` → User (Many-to-One)
- `matched_trip` → Trip (Many-to-One)
- `matches` → Match (One-to-Many)
- `conversations` → Conversation (One-to-Many)
- `tracking_events` → ShipmentTracking (One-to-Many)
- `documents` → ShipmentDocument (One-to-Many)
- `package_details` → Package (One-to-One)
- `rating` → ShipmentRating (One-to-One)
- `delivery_otps` → DeliveryOTP (One-to-Many)

### **2.2 Package (Détails Colis)**
**Informations détaillées sur les colis**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `shipment` | OneToOneField | - | Oui | Shipment | Envoi associé |
| `category` | CharField | 20 | Oui | small, medium, large, oversized | Catégorie colis |
| `length` | DecimalField | 8,2 | Oui | > 0.01 | Longueur (cm) |
| `width` | DecimalField | 8,2 | Oui | > 0.01 | Largeur (cm) |
| `height` | DecimalField | 8,2 | Oui | > 0.01 | Hauteur (cm) |
| `volume` | DecimalField | 10,2 | Non | Calculé | Volume (cm³) |
| `requires_special_handling` | BooleanField | - | Oui | False | Manutention spéciale |
| `is_hazardous` | BooleanField | - | Oui | False | Matériaux dangereux |
| `temperature_sensitive` | BooleanField | - | Oui | False | Sensible température |
| `min_temperature` | DecimalField | 5,2 | Non | - | Température min (°C) |
| `max_temperature` | DecimalField | 5,2 | Non | - | Température max (°C) |
| `handling_instructions` | TextField | - | Non | - | Instructions manutention |
| `storage_requirements` | TextField | - | Non | - | Exigences stockage |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

### **2.3 ShipmentDocument (Document Envoi)**
**Documents associés aux envois**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `shipment` | ForeignKey | - | Oui | Shipment | Envoi associé |
| `document_type` | CharField | 20 | Oui | invoice, receipt, contract, insurance, customs, photo, other | Type document |
| `title` | CharField | 200 | Oui | - | Titre document |
| `file` | FileField | - | Oui | - | Fichier document |
| `description` | TextField | - | Non | - | Description |
| `file_size` | PositiveIntegerField | - | Non | - | Taille fichier (bytes) |
| `mime_type` | CharField | 100 | Non | - | Type MIME |
| `is_verified` | BooleanField | - | Oui | False | Document vérifié |
| `verified_by` | ForeignKey | - | Non | User | Vérificateur |
| `verified_at` | DateTimeField | - | Non | - | Date vérification |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

### **2.4 ShipmentRating (Évaluation Envoi)**
**Évaluations spécifiques aux envois**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `shipment` | OneToOneField | - | Oui | Shipment | Envoi évalué |
| `rater` | ForeignKey | - | Oui | User | Évaluateur |
| `overall_rating` | PositiveSmallIntegerField | - | Oui | 1-5 | Note globale |
| `delivery_speed` | PositiveSmallIntegerField | - | Oui | 1-5 | Vitesse livraison |
| `package_condition` | PositiveSmallIntegerField | - | Oui | 1-5 | État colis |
| `communication` | PositiveSmallIntegerField | - | Oui | 1-5 | Communication |
| `comment` | TextField | - | Non | - | Commentaire |
| `is_public` | BooleanField | - | Oui | True | Évaluation publique |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

### **2.5 ShipmentTracking (Suivi Envoi)**
**Événements de suivi des envois**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `shipment` | ForeignKey | - | Oui | Shipment | Envoi suivi |
| `status` | CharField | 20 | Oui | created, pending_pickup, picked_up, in_transit, out_for_delivery, delivered, failed_delivery, returned | Statut |
| `event_type` | CharField | 20 | Oui | created, pending_pickup, picked_up, in_transit, out_for_delivery, delivered, failed_delivery, returned | Type événement |
| `description` | TextField | - | Oui | - | Description événement |
| `location` | CharField | 200 | Non | - | Localisation |
| `timestamp` | DateTimeField | - | Oui | Auto | Horodatage |
| `created_by` | ForeignKey | - | Non | User | Créateur événement |

---

## ✈️ **3. MODULE TRIPS - Gestion des Trajets**

### **3.1 Trip (Trajet)**
**Trajets proposés par les voyageurs**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `traveler` | ForeignKey | - | Oui | User | Voyageur |
| `origin_city` | CharField | 100 | Oui | - | Ville d'origine |
| `origin_country` | CharField | 100 | Oui | - | Pays d'origine |
| `destination_city` | CharField | 100 | Oui | - | Ville destination |
| `destination_country` | CharField | 100 | Oui | - | Pays destination |
| `departure_date` | DateTimeField | - | Oui | - | Date départ |
| `arrival_date` | DateTimeField | - | Oui | - | Date arrivée |
| `flexible_dates` | BooleanField | - | Oui | False | Dates flexibles |
| `flexibility_days` | PositiveIntegerField | - | Oui | 0-30 | Jours flexibilité |
| `max_weight` | DecimalField | 8,2 | Oui | > 0.01 | Poids max (kg) |
| `remaining_weight` | DecimalField | 8,2 | Oui | - | Poids restant (kg) |
| `max_packages` | PositiveIntegerField | - | Oui | 1 | Nombre max colis |
| `remaining_packages` | PositiveIntegerField | - | Oui | - | Colis restants |
| `accepted_package_types` | JSONField | - | Oui | [] | Types acceptés |
| `min_price_per_kg` | DecimalField | 8,2 | Oui | > 0.01 | Prix min/kg |
| `accepts_fragile` | BooleanField | - | Oui | False | Accepte fragile |
| `status` | CharField | 20 | Oui | draft, active, in_progress, completed, cancelled, expired | Statut trajet |
| `is_verified` | BooleanField | - | Oui | False | Trajet vérifié |
| `notes` | TextField | - | Non | - | Notes |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

**Relations :**
- `traveler` → User (Many-to-One)
- `matches` → Match (One-to-Many)
- `matched_shipments` → Shipment (One-to-Many)
- `documents` → TripDocument (One-to-Many)

### **3.2 TripDocument (Document Trajet)**
**Documents associés aux trajets**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `trip` | ForeignKey | - | Oui | Trip | Trajet associé |
| `document_type` | CharField | 20 | Oui | flight_ticket, passport_copy, visa, boarding_pass, travel_insurance, other | Type document |
| `file` | FileField | - | Oui | - | Fichier document |
| `is_verified` | BooleanField | - | Oui | False | Document vérifié |
| `verification_date` | DateTimeField | - | Non | - | Date vérification |
| `verification_notes` | TextField | - | Non | - | Notes vérification |
| `uploaded_at` | DateTimeField | - | Oui | Auto | Date upload |

**Relations :**
- `trip` → Trip (Many-to-One)

---

## 🎯 **4. MODULE MATCHING - Algorithme de Matching**

### **4.1 Match (Association)**
**Associations entre envois et trajets**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `shipment` | ForeignKey | - | Oui | Shipment | Envoi |
| `trip` | ForeignKey | - | Oui | Trip | Trajet |
| `compatibility_score` | DecimalField | 5,2 | Oui | 0.00-100.00 | Score compatibilité |
| `proposed_price` | DecimalField | 10,2 | Oui | - | Prix proposé |
| `status` | CharField | 20 | Oui | pending, accepted, rejected, expired, cancelled | Statut |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `expires_at` | DateTimeField | - | Oui | - | Date expiration |
| `responded_at` | DateTimeField | - | Non | - | Date réponse |
| `algorithm_version` | CharField | 20 | Oui | 1.0 | Version algorithme |
| `matching_factors` | JSONField | - | Oui | {} | Facteurs matching |

**Relations :**
- `shipment` → Shipment (Many-to-One)
- `trip` → Trip (Many-to-One)

---

## 💰 **5. MODULE PAYMENTS - Système de Paiements**

### **5.1 Wallet (Portefeuille)**
**Portefeuilles virtuels des utilisateurs**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `user` | OneToOneField | - | Oui | User | Propriétaire |
| `balance` | DecimalField | 12,2 | Oui | 0.00 | Solde disponible |
| `pending_balance` | DecimalField | 12,2 | Oui | 0.00 | Solde en attente |
| `total_earned` | DecimalField | 12,2 | Oui | 0.00 | Total gagné |
| `total_spent` | DecimalField | 12,2 | Oui | 0.00 | Total dépensé |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

### **5.2 Transaction (Transaction)**
**Transactions financières**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `transaction_id` | CharField | 50 | Oui | Unique, format: TXNxxxxxxxxxxxx | ID transaction |
| `user` | ForeignKey | - | Oui | User | Utilisateur |
| `type` | CharField | 20 | Oui | deposit, withdrawal, payment, earning, refund, transfer, commission | Type transaction |
| `amount` | DecimalField | 12,2 | Oui | - | Montant |
| `currency` | CharField | 3 | Oui | DZD | Devise |
| `status` | CharField | 20 | Oui | pending, processing, completed, failed, cancelled, refunded | Statut |
| `shipment` | ForeignKey | - | Non | Shipment | Envoi associé |
| `related_transaction` | ForeignKey | - | Non | Transaction | Transaction liée |
| `payment_method` | CharField | 20 | Non | wallet, card, cib, eddahabia, cash, bank_transfer, chargily | Méthode paiement |
| `payment_gateway` | CharField | 20 | Non | cib, eddahabia, chargily, stripe, manual | Passerelle |
| `card_type` | CharField | 20 | Non | cib, eddahabia, visa, mastercard | Type de carte |
| `card_last_four` | CharField | 4 | Non | - | 4 derniers chiffres |
| `card_holder_name` | CharField | 100 | Non | - | Nom titulaire |
| `cash_payment_reference` | CharField | 50 | Non | - | Référence espèces |
| `cash_payment_location` | CharField | 200 | Non | - | Bureau de paiement |
| `cash_payment_date` | DateTimeField | - | Non | - | Date paiement espèces |
| `cash_payment_confirmed_by` | ForeignKey | - | Non | User | Confirmé par |
| `description` | TextField | - | Non | - | Description |
| `metadata` | JSONField | - | Oui | {} | Métadonnées |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `completed_at` | DateTimeField | - | Non | - | Date finalisation |

### **5.3 PaymentMethod (Méthode de Paiement)**
**Méthodes de paiement disponibles**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `name` | CharField | 50 | Oui | Unique | Nom de la méthode |
| `method_type` | CharField | 20 | Oui | card, cib, eddahabia, cash, bank_transfer, chargily | Type de méthode |
| `is_active` | BooleanField | - | Oui | True | Méthode active |
| `is_online` | BooleanField | - | Oui | True | Paiement en ligne |
| `min_amount` | DecimalField | 10,2 | Oui | 0.01 | Montant minimum |
| `max_amount` | DecimalField | 10,2 | Oui | 100000.00 | Montant maximum |
| `processing_fee` | DecimalField | 5,2 | Oui | 0.00 | Frais % |
| `fixed_fee` | DecimalField | 10,2 | Oui | 0.00 | Frais fixes |
| `office_locations` | JSONField | - | Oui | [] | Bureaux disponibles |
| `office_hours` | CharField | 200 | Non | - | Heures d'ouverture |
| `office_instructions` | TextField | - | Non | - | Instructions bureau |
| `description` | TextField | - | Non | - | Description |
| `icon_url` | URLField | - | Non | - | URL icône |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

---

## 💬 **6. MODULE CHAT - Messagerie (🔄 En cours)**

### **6.1 Conversation (Conversation)**
**Conversations entre expéditeurs et voyageurs**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `shipment` | ForeignKey | - | Oui | Shipment | Envoi associé |
| `sender` | ForeignKey | - | Oui | User | Expéditeur |
| `traveler` | ForeignKey | - | Oui | User | Voyageur |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `last_message_at` | DateTimeField | - | Oui | Auto | Dernier message |
| `is_active` | BooleanField | - | Oui | True | Conversation active |

**Relations :**
- `shipment` → Shipment (Many-to-One)
- `sender` → User (Many-to-One)
- `traveler` → User (Many-to-One)
- `messages` → Message (One-to-Many)

### **6.2 Message (Message)**
**Messages dans les conversations**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `conversation` | ForeignKey | - | Oui | Conversation | Conversation |
| `sender` | ForeignKey | - | Oui | User | Expéditeur |
| `content` | TextField | - | Oui | - | Contenu message |
| `message_type` | CharField | 20 | Oui | text, image, file, location, system | Type message |
| `metadata` | JSONField | - | Oui | {} | Métadonnées |
| `is_read` | BooleanField | - | Oui | False | Message lu |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |

**Relations :**
- `conversation` → Conversation (Many-to-One)
- `sender` → User (Many-to-One)

---

## ⭐ **7. MODULE RATINGS - Évaluations**

### **7.1 Rating (Évaluation)**
**Évaluations entre utilisateurs**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `rater` | ForeignKey | - | Oui | User | Évaluateur |
| `rated_user` | ForeignKey | - | Oui | User | Utilisateur évalué |
| `shipment` | ForeignKey | - | Oui | Shipment | Envoi associé |
| `rating` | IntegerField | - | Oui | 1-5 | Note |
| `comment` | TextField | 500 | Non | - | Commentaire |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

---

## 📊 **8. MODULE ANALYTICS - Statistiques**

### **8.1 AnalyticsEvent (Événement Analytics)**
**Événements d'analytics**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `event_id` | UUIDField | - | Oui | Unique | ID événement |
| `event_type` | CharField | 20 | Oui | page_view, api_call, user_action, error, performance | Type événement |
| `event_name` | CharField | 100 | Oui | - | Nom événement |
| `user` | ForeignKey | - | Non | User | Utilisateur |
| `event_data` | JSONField | - | Oui | {} | Données événement |
| `session_id` | CharField | 100 | Non | - | ID session |
| `ip_address` | GenericIPAddressField | - | Non | - | Adresse IP |
| `user_agent` | TextField | - | Non | - | User Agent |
| `duration` | FloatField | - | Non | - | Durée (secondes) |
| `success` | BooleanField | - | Oui | True | Succès |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |

### **8.2 DashboardMetric (Métrique Dashboard)**
**Métriques du tableau de bord**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `metric_id` | UUIDField | - | Oui | Unique | ID métrique |
| `name` | CharField | 100 | Oui | - | Nom métrique |
| `metric_type` | CharField | 20 | Oui | count, sum, average, percentage, trend | Type métrique |
| `current_value` | FloatField | - | Oui | - | Valeur actuelle |
| `previous_value` | FloatField | - | Non | - | Valeur précédente |
| `target_value` | FloatField | - | Non | - | Valeur cible |
| `unit` | CharField | 20 | Non | - | Unité |
| `description` | TextField | - | Non | - | Description |
| `is_active` | BooleanField | - | Oui | True | Métrique active |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |
| `last_calculated` | DateTimeField | - | Non | - | Dernier calcul |

---

## 📧 **9. MODULE NOTIFICATIONS - Notifications (🔄 En cours)**

### **9.1 Notification (Notification)**
**Notifications système**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `notification_id` | UUIDField | - | Oui | Unique | ID notification |
| `notification_type` | CharField | 20 | Oui | email, sms, push, in_app | Type notification |
| `status` | CharField | 20 | Oui | pending, sent, delivered, failed, read | Statut |
| `user` | ForeignKey | - | Oui | User | Destinataire |
| `subject` | CharField | 200 | Oui | - | Sujet |
| `message` | TextField | - | Oui | - | Message |
| `template_data` | JSONField | - | Oui | {} | Données template |
| `priority` | IntegerField | - | Oui | 1 | Priorité |
| `is_read` | BooleanField | - | Oui | False | Lu |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `sent_at` | DateTimeField | - | Non | - | Date envoi |
| `read_at` | DateTimeField | - | Non | - | Date lecture |

**Relations :**
- `user` → User (Many-to-One)
- `shipment_notifications` → ShipmentNotification (One-to-Many)

### **9.2 EmailTemplate (EmailTemplate)**
**Templates d'email**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `name` | CharField | 100 | Oui | - | Nom du template |
| `subject` | CharField | 200 | Oui | - | Sujet |
| `html_content` | TextField | - | Oui | - | Contenu HTML |
| `text_content` | TextField | - | Oui | - | Contenu texte |
| `is_active` | BooleanField | - | Oui | True | Template actif |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

### **9.3 SMSTemplate (SMSTemplate)**
**Templates SMS**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `name` | CharField | 100 | Oui | - | Nom du template |
| `message` | TextField | 160 | Oui | - | Message SMS |
| `is_active` | BooleanField | - | Oui | True | Template actif |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

### **9.4 ShipmentNotification (ShipmentNotification)**
**Notifications liées aux envois**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `notification` | OneToOneField | - | Oui | Notification | Notification associée |
| `shipment_id` | IntegerField | - | Oui | - | ID de l'envoi |
| `event_type` | CharField | 20 | Oui | created, status_changed, delivered, problem | Type d'événement |
| `tracking_number` | CharField | 50 | Non | - | Numéro de suivi |

---

## 📄 **10. MODULE DOCUMENTS - Génération Documents (🔄 En cours)**

### **10.1 DocumentTemplate (DocumentTemplate)**
**Templates pour génération de documents**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `name` | CharField | 100 | Oui | - | Nom template |
| `document_type` | CharField | 20 | Oui | invoice, receipt, contract, custom | Type template |
| `template_file` | FileField | - | Oui | - | Fichier template |
| `is_active` | BooleanField | - | Oui | True | Template actif |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

**Relations :**
- `documents` → Document (One-to-Many)

### **10.2 Document (Document)**
**Documents générés**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `document_id` | UUIDField | - | Oui | Unique | ID document |
| `title` | CharField | 200 | Oui | - | Titre document |
| `document_type` | CharField | 20 | Oui | invoice, receipt, contract, custom | Type document |
| `status` | CharField | 20 | Oui | draft, generated, sent, archived | Statut |
| `user` | ForeignKey | - | Oui | User | Utilisateur |
| `template` | ForeignKey | - | Non | DocumentTemplate | Template utilisé |
| `content_data` | JSONField | - | Oui | {} | Données contenu |
| `generated_file` | FileField | - | Non | - | Fichier généré |
| `reference_number` | CharField | 50 | Oui | Unique | Numéro référence |
| `description` | TextField | - | Non | - | Description |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |
| `generated_at` | DateTimeField | - | Non | - | Date génération |

**Relations :**
- `user` → User (Many-to-One)
- `template` → DocumentTemplate (Many-to-One)
- `invoice` → Invoice (One-to-One)
- `receipt` → Receipt (One-to-One)

### **10.3 Invoice (Invoice)**
**Factures générées**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `document` | OneToOneField | - | Oui | Document | Document associé |
| `client_name` | CharField | 200 | Oui | - | Nom du client |
| `client_email` | EmailField | - | Oui | - | Email du client |
| `client_address` | TextField | - | Oui | - | Adresse du client |
| `invoice_number` | CharField | 50 | Oui | Unique | Numéro de facture |
| `issue_date` | DateField | - | Oui | - | Date d'émission |
| `due_date` | DateField | - | Oui | - | Date d'échéance |
| `subtotal` | DecimalField | 10,2 | Oui | - | Sous-total |
| `tax_amount` | DecimalField | 10,2 | Oui | 0.00 | Montant des taxes |
| `total_amount` | DecimalField | 10,2 | Oui | - | Montant total |
| `is_paid` | BooleanField | - | Oui | False | Facture payée |
| `paid_at` | DateTimeField | - | Non | - | Date de paiement |

**Relations :**
- `document` → Document (One-to-One)

### **10.4 Receipt (Receipt)**
**Reçus générés**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `document` | OneToOneField | - | Oui | Document | Document associé |
| `client_name` | CharField | 200 | Oui | - | Nom du client |
| `client_email` | EmailField | - | Oui | - | Email du client |
| `receipt_number` | CharField | 50 | Oui | Unique | Numéro de reçu |
| `payment_date` | DateTimeField | - | Oui | - | Date de paiement |
| `payment_method` | CharField | 50 | Oui | - | Méthode de paiement |
| `amount_paid` | DecimalField | 10,2 | Oui | - | Montant payé |
| `transaction_id` | CharField | 100 | Non | - | ID de transaction |

**Relations :**
- `document` → Document (One-to-One)

## 🔍 **11. MODULE VERIFICATION - Vérification des Documents (✅ Complété)**

### **11.1 DocumentVerification (DocumentVerification)**
**Vérification des documents utilisateur**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | UUIDField | - | Oui | Unique | Identifiant unique |
| `user` | ForeignKey | - | Oui | User | Utilisateur |
| `document` | ForeignKey | - | Oui | UserDocument | Document à vérifier |
| `status` | CharField | 25 | Oui | pending, processing, approved, rejected, requires_manual_review, expired | Statut vérification |
| `verification_method` | CharField | 20 | Oui | automatic, manual, hybrid | Méthode vérification |
| `verified_at` | DateTimeField | - | Non | - | Date vérification |
| `verified_by` | ForeignKey | - | Non | User | Vérificateur |
| `rejection_reason` | TextField | - | Non | - | Raison rejet |
| `ocr_data` | JSONField | - | Oui | {} | Données extraites par OCR |
| `validation_score` | DecimalField | 5,2 | Non | 0.00-100.00 | Score validation |
| `fraud_detection_score` | DecimalField | 5,2 | Non | 0.00-100.00 | Score détection fraude |
| `verification_notes` | TextField | - | Non | - | Notes vérification |
| `verification_duration` | DurationField | - | Non | - | Durée vérification |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

**Relations :**
- `user` → User (Many-to-One)
- `document` → UserDocument (Many-to-One)
- `verified_by` → User (Many-to-One)
- `logs` → VerificationLog (One-to-Many)

### **11.2 DocumentValidationRule (DocumentValidationRule)**
**Règles de validation des documents**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `name` | CharField | 100 | Oui | - | Nom de la règle |
| `document_type` | CharField | 25 | Oui | passport, national_id, flight_ticket, address_proof, driver_license, birth_certificate, marriage_certificate | Type document |
| `validation_type` | CharField | 25 | Oui | ocr_extraction, format_validation, expiry_check, fraud_detection, data_consistency, image_quality | Type validation |
| `is_active` | BooleanField | - | Oui | True | Règle active |
| `priority` | PositiveIntegerField | - | Oui | 1 | Priorité d'exécution |
| `validation_config` | JSONField | - | Oui | {} | Configuration règle |
| `threshold_score` | DecimalField | 5,2 | Oui | 80.00 | Score seuil validation |
| `description` | TextField | - | Non | - | Description règle |
| `notes` | TextField | - | Non | - | Notes additionnelles |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

**Relations :**
- Aucune relation directe

### **11.3 VerificationWorkflow (VerificationWorkflow)**
**Workflows de vérification**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `name` | CharField | 100 | Oui | - | Nom workflow |
| `workflow_type` | CharField | 20 | Oui | standard, premium, express, manual | Type workflow |
| `is_active` | BooleanField | - | Oui | True | Workflow actif |
| `steps` | JSONField | - | Oui | [] | Étapes workflow |
| `auto_approval_threshold` | DecimalField | 5,2 | Oui | 90.00 | Seuil approbation auto |
| `requires_manual_review` | BooleanField | - | Oui | False | Vérification manuelle |
| `max_processing_time` | DurationField | - | Non | - | Temps max traitement |
| `description` | TextField | - | Non | - | Description workflow |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

**Relations :**
- Aucune relation directe

### **11.4 VerificationLog (VerificationLog)**
**Historique des vérifications**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `verification` | ForeignKey | - | Oui | DocumentVerification | Vérification associée |
| `log_level` | CharField | 10 | Oui | info, warning, error, success | Niveau log |
| `message` | TextField | - | Oui | - | Message log |
| `details` | JSONField | - | Oui | {} | Détails additionnels |
| `timestamp` | DateTimeField | - | Oui | Auto | Horodatage |
| `user` | ForeignKey | - | Non | User | Utilisateur associé |

**Relations :**
- `verification` → DocumentVerification (Many-to-One)
- `user` → User (Many-to-One)

### **11.5 DocumentTemplate (DocumentTemplate)**
**Templates de documents acceptés**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `name` | CharField | 100 | Oui | - | Nom template |
| `document_type` | CharField | 25 | Oui | passport, national_id, flight_ticket, address_proof | Type document |
| `country` | CharField | 5 | Oui | DZ, FR, US, GB, DE, IT, ES, CA, AU, OTHER | Pays origine |
| `is_active` | BooleanField | - | Oui | True | Template actif |
| `sample_image` | ImageField | - | Non | - | Image exemple |
| `validation_zones` | JSONField | - | Oui | {} | Zones validation |
| `required_fields` | JSONField | - | Oui | [] | Champs requis |
| `description` | TextField | - | Non | - | Description template |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

**Relations :**
- Aucune relation directe

---

## 🌍 **12. MODULE INTERNATIONALIZATION - Gestion Multilingue (✅ Complété)**

### **12.1 TranslationCategory (TranslationCategory)**
**Catégories de traductions**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `name` | CharField | 100 | Oui | - | Nom catégorie |
| `code` | CharField | 50 | Oui | Unique | Code catégorie |
| `description` | TextField | - | Non | - | Description |
| `is_active` | BooleanField | - | Oui | True | Catégorie active |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

**Relations :**
- `translation_keys` → TranslationKey (One-to-Many)

### **12.2 TranslationKey (TranslationKey)**
**Clés de traduction**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `key` | CharField | 200 | Oui | Unique | Clé traduction |
| `category` | ForeignKey | - | Oui | TranslationCategory | Catégorie |
| `description` | TextField | - | Non | - | Description |
| `context` | TextField | - | Non | - | Contexte utilisation |
| `is_active` | BooleanField | - | Oui | True | Clé active |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

**Relations :**
- `category` → TranslationCategory (Many-to-One)
- `translations` → Translation (One-to-Many)

### **12.3 Translation (Translation)**
**Traductions par langue**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `key` | ForeignKey | - | Oui | TranslationKey | Clé traduction |
| `language_code` | CharField | 2 | Oui | fr, en, ar | Code langue |
| `text` | TextField | - | Oui | - | Texte traduit |
| `is_approved` | BooleanField | - | Oui | False | Traduction approuvée |
| `approved_by` | ForeignKey | - | Non | User | Approuvé par |
| `approved_at` | DateTimeField | - | Non | - | Date approbation |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

**Relations :**
- `key` → TranslationKey (Many-to-One)
- `approved_by` → User (Many-to-One)

### **12.4 UserLanguagePreference (UserLanguagePreference)**
**Préférences de langue utilisateur**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `user` | OneToOneField | - | Oui | User | Utilisateur |
| `preferred_language` | CharField | 2 | Oui | fr, en, ar | Langue préférée |
| `fallback_language` | CharField | 2 | Oui | fr, en, ar | Langue secours |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

**Relations :**
- `user` → User (One-to-One)

### **12.5 TranslationTemplate (TranslationTemplate)**
**Modèles de traduction**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `name` | CharField | 100 | Oui | - | Nom template |
| `template_type` | CharField | 20 | Oui | email, sms, notification, document, ui | Type template |
| `key` | CharField | 200 | Oui | Unique | Clé template |
| `variables` | JSONField | - | Oui | [] | Variables disponibles |
| `category` | ForeignKey | - | Oui | TranslationCategory | Catégorie |
| `is_active` | BooleanField | - | Oui | True | Template actif |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

**Relations :**
- `category` → TranslationCategory (Many-to-One)
- `contents` → TranslationTemplateContent (One-to-Many)

### **12.6 TranslationTemplateContent (TranslationTemplateContent)**
**Contenu des modèles par langue**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `template` | ForeignKey | - | Oui | TranslationTemplate | Template |
| `language_code` | CharField | 2 | Oui | fr, en, ar | Code langue |
| `subject` | CharField | 200 | Non | - | Sujet |
| `content` | TextField | - | Oui | - | Contenu |
| `is_approved` | BooleanField | - | Oui | False | Contenu approuvé |
| `approved_by` | ForeignKey | - | Non | User | Approuvé par |
| `approved_at` | DateTimeField | - | Non | - | Date approbation |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |
| `updated_at` | DateTimeField | - | Oui | Auto | Date modification |

**Relations :**
- `template` → TranslationTemplate (Many-to-One)
- `approved_by` → User (Many-to-One)

### **12.7 TranslationCache (TranslationCache)**
**Cache des traductions**

| **Champ** | **Type** | **Taille** | **Obligatoire** | **Valeurs** | **Description** |
|-----------|----------|------------|-----------------|-------------|-----------------|
| `id` | Integer | - | Oui | Auto-incrémenté | Identifiant unique |
| `cache_key` | CharField | 255 | Oui | Unique | Clé cache |
| `language_code` | CharField | 2 | Oui | fr, en, ar | Code langue |
| `content` | TextField | - | Oui | - | Contenu cache |
| `expires_at` | DateTimeField | - | Oui | - | Date expiration |
| `created_at` | DateTimeField | - | Oui | Auto | Date création |

**Relations :**
- Aucune relation directe

---

## 🔗 **RELATIONS ENTRE ENTITÉS**

### **Diagramme des Relations Principales**

```
User (1) ←→ (1) UserProfile
User (1) ←→ (1) Wallet
User (1) ←→ (1) UserLanguagePreference
User (1) ←→ (N) Shipment (sent_shipments)
User (1) ←→ (N) Trip
User (1) ←→ (N) UserDocument
User (1) ←→ (N) OTPCode
User (1) ←→ (N) DocumentVerification
User (1) ←→ (N) Translation (approved_by)
User (1) ←→ (N) TranslationTemplateContent (approved_by)
User (1) ←→ (N) AdminAuditLog
User (1) ←→ (N) AdminNotification
User (1) ←→ (N) Notification
User (1) ←→ (N) Document
User (1) ←→ (N) Conversation (sender)
User (1) ←→ (N) Conversation (traveler)
User (1) ←→ (N) Message

Shipment (1) ←→ (1) Package
Shipment (1) ←→ (N) ShipmentDocument
Shipment (1) ←→ (N) ShipmentTracking
Shipment (1) ←→ (1) ShipmentRating
Shipment (1) ←→ (N) Match
Shipment (1) ←→ (N) Conversation
Shipment (1) ←→ (N) DeliveryOTP
Shipment (1) ←→ (N) Transaction
Shipment (1) ←→ (1) Commission

Trip (1) ←→ (N) Match
Trip (1) ←→ (N) TripDocument

Match (N) ←→ (1) Shipment
Match (N) ←→ (1) Trip

Conversation (1) ←→ (N) Message
Conversation (N) ←→ (1) Shipment
Conversation (N) ←→ (1) User (sender)
Conversation (N) ←→ (1) User (traveler)

Wallet (1) ←→ (N) Transaction
Transaction (N) ←→ (1) User
Transaction (N) ←→ (1) Shipment

Rating (N) ←→ (1) User (rater)
Rating (N) ←→ (1) User (rated_user)
Rating (N) ←→ (1) Shipment

DocumentVerification (N) ←→ (1) User
DocumentVerification (N) ←→ (1) UserDocument
DocumentVerification (N) ←→ (1) User (verified_by)
DocumentVerification (1) ←→ (N) VerificationLog

TranslationCategory (1) ←→ (N) TranslationKey
TranslationKey (1) ←→ (N) Translation
TranslationKey (1) ←→ (N) TranslationTemplate
TranslationTemplate (1) ←→ (N) TranslationTemplateContent

DocumentTemplate (1) ←→ (N) Document
Document (N) ←→ (1) User
Document (N) ←→ (1) DocumentTemplate
Document (1) ←→ (1) Invoice
Document (1) ←→ (1) Receipt

Notification (N) ←→ (1) User
Notification (1) ←→ (1) ShipmentNotification
```

---

### **Sécurité et Contrôles**

- **Authentification** : JWT requis pour tous les endpoints
- **Autorisation** : Seul le voyageur associé peut utiliser les OTP
- **Rate Limiting** : Protection contre les abus
- **Expiration** : OTP expire après 24h
- **Audit** : Toutes les actions sont loggées

---

## 📈 **MÉTRIQUES ET STATISTIQUES**

### **Indicateurs Clés de Performance (KPI)**

1. **Utilisateurs**
   - Nombre total d'utilisateurs
   - Taux de vérification (téléphone + documents)
   - Répartition par rôle (expéditeur/voyageur)
   - Utilisateurs actifs

2. **Envois**
   - Nombre total d'envois
   - Taux de livraison réussie
   - Temps moyen de livraison
   - Répartition par statut
   - Taux de confirmation OTP
   - Temps moyen de vérification OTP

3. **Trajets**
   - Nombre total de trajets
   - Taux d'utilisation des trajets
   - Répartition géographique

4. **Matching**
   - Taux de matching réussi
   - Score de compatibilité moyen
   - Temps de réponse aux propositions

5. **Paiements**
   - Volume total des transactions
   - Répartition par méthode de paiement (CIB, Eddahabia, Espèces)
   - Taux de succès des paiements
   - Paiements libérés après confirmation OTP
   - Statistiques des cartes algériennes
   - Paiements en espèces confirmés
   - Frais de traitement par méthode

6. **OTP de Livraison**
   - Nombre d'OTP générés
   - Taux de vérification réussie
   - Temps moyen de vérification
   - Nombre de renvois d'OTP
   - Taux d'expiration des OTP

7. **Évaluations**
   - Note moyenne globale
   - Répartition des notes
   - Taux de réponse aux évaluations

8. **Vérification des Documents**
   - Taux de vérification automatique
   - Temps moyen de traitement
   - Score de validation moyen
   - Taux de détection de fraude

9. **Internationalisation**
   - Répartition par langue (FR/EN/AR)
   - Taux de traduction par langue
   - Utilisation du cache de traductions

10. **Génération de Documents**
    - Nombre de documents générés par type
    - Temps moyen de génération
    - Taux de succès de génération

11. **Chat et Communication**
    - Nombre de conversations actives
    - Temps moyen de réponse
    - Taux d'utilisation des fonctionnalités

---

## 🔒 **SÉCURITÉ ET CONFORMITÉ**

### **Données Sensibles**
- **Chiffrement** : Mots de passe hashés (SHA256)
- **OTP Authentification** : Codes temporaires avec expiration (10 min)
- **OTP Livraison** : Codes à 6 chiffres avec expiration (24h)
- **Documents** : Stockage sécurisé avec validation OCR et détection de fraude
- **Paiements** : Conformité PCI DSS, cartes algériennes sécurisées
- **Vérification** : Processus de validation multi-étapes avec audit complet
- **Internationalisation** : Cache sécurisé des traductions avec expiration

### **Contrôles d'Accès**
- **Rôles** : Expéditeur, Voyageur, Admin
- **Permissions** : Basées sur les rôles
- **JWT** : Tokens d'authentification sécurisés
- **Rate Limiting** : Protection contre les abus
- **OTP Livraison** : Seul le voyageur associé peut vérifier l'OTP

---

## 📝 **NOTES TECHNIQUES**

### **Contraintes de Validation**
- **Poids** : 0.01kg - 50kg pour les colis
- **Notes** : 1-5 étoiles pour les évaluations
- **Téléphone** : Format international
- **Dates** : Validation logique (départ < arrivée)
- **OTP Livraison** : 6 chiffres exactement, expiration 24h
- **Renvois OTP** : Maximum 3 renvois par envoi

### **Contraintes Métier Spécifiques**
- **Origine des trajets** : Doit être en Algérie uniquement
- **Destination des trajets** : Ne peut pas être en Algérie (trajets internationaux uniquement)
- **Types de colis acceptés** : Validation stricte des types autorisés
- **Dates de départ** : Doivent être dans le futur
- **Flexibilité des dates** : 0-30 jours maximum
- **Vérification des trajets** : Seuls les trajets vérifiés peuvent accepter des colis
- **Vérification des documents** : Processus multi-étapes avec scores de validation
- **Internationalisation** : Support obligatoire FR/EN/AR avec fallback automatique
- **Génération de documents** : Templates sécurisés avec validation des variables
- **Chat et communication** : Messages chiffrés avec historique d'audit

### **Règles de Validation Géographique**
- **Trajets internationaux uniquement** : Origine en Algérie, destination hors Algérie
- **Validation des pays** : Liste des pays autorisés pour les destinations
- **Contraintes douanières** : Respect des réglementations d'import/export

### **Règles de Validation Temporelle**
- **Dates de départ** : Doivent être dans le futur (minimum 24h)
- **Dates d'arrivée** : Doivent être après la date de départ
- **Flexibilité** : Maximum 30 jours de flexibilité autorisés
- **Expiration automatique** : Trajets expirés automatiquement marqués comme "expired"

### **Index de Performance**
- Index sur les champs de recherche fréquents
- Index sur les relations clés
- Index sur les dates pour le tri

### **Intégrité des Données**
- Contraintes d'unicité sur les identifiants
- Validation des données métier
- Cascade sur les suppressions critiques

---

## 💳 **PAIEMENTS ALGÉRIENS - CIB & EDDAHABIA**

### **Méthodes de Paiement Supportées**
- **CIB** : Cartes bancaires CIB (Crédit Industriel et Commercial)
- **Eddahabia** : Cartes bancaires Eddahabia (Poste Algérienne)
- **Espèces** : Paiement en espèces au bureau Kleer Infini

### **Endpoints API Paiements**
- `GET /api/v1/payments/methods/` - Méthodes disponibles
- `POST /api/v1/payments/card/` - Paiement carte algérienne
- `POST /api/v1/payments/cash/` - Paiement en espèces
- `POST /api/v1/payments/cash/{id}/confirm/` - Confirmation espèces (Admin)
- `GET /api/v1/payments/fees/` - Calcul des frais
- `GET /api/v1/payments/statistics/` - Statistiques (Admin)

### **Sécurité des Paiements**
- **Validation** : Numéro de carte, CVV, dates d'expiration
- **Limites** : Montants maximum par méthode
- **Chiffrement** : Données sensibles sécurisées
- **Audit** : Toutes les transactions sont loggées

### **Flux de Paiement**
1. **Carte Bancaire** : Validation → Traitement → Confirmation automatique
2. **Espèces** : Création → Paiement bureau → Confirmation admin → Finalisation

---

**Document créé le :** 12 Août 2025  
**Version :** 3.0  
**Projet :** Kleer Logistics API  
**Statut :** ✅ 9 modules sur 12 complétés (75% du backend)  
**Modules terminés :** Users, Shipments, Trips, Matching, Payments, Admin Panel, Internationalization, Verification  
**Modules en cours :** Analytics, Chat, Notifications, Documents  
**Dernière mise à jour :** 24 Août 2025  
