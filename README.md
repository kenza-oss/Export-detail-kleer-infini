# 🚚 Kleer Logistics - Plateforme d'Envoi Collaboratif International

## 📋 Vue d'ensemble

Kleer Logistics est une plateforme web et mobile qui met en relation des expéditeurs résidant en Algérie avec des voyageurs algériens se rendant à l'étranger, pour le transport sécurisé de colis légers contre rémunération.

### 🎯 Objectifs du Projet

- ✅ **Faciliter l'envoi** de colis légers entre particuliers à l'étranger
- ✅ **Alternative économique** aux services express classiques (DHL, FedEx)
- ✅ **Service humain** et personnalisé
- ✅ **Exploitation légale** du code exportation Kleer Infini
- ✅ **Modèle économique** collaboratif et rentable

## 🏗️ Architecture Technique

### Stack Technologique

- **Backend** : Django 4.2 + Django REST Framework
- **Base de données** : PostgreSQL
- **Authentification** : JWT (JSON Web Tokens)
- **SMS** : Twilio/Vonage (production), Console (développement)
- **Paiements** : CIB, Eddahabia, Espèces, Wallet intégré
- **Documentation API** : Swagger/OpenAPI
- **Sécurité** : Django Axes, Rate Limiting, OTP sécurisés

### Structure du Projet

```
kleerlogistics/
├── users/                 # ✅ Gestion des utilisateurs et authentification
├── shipments/             # ✅ Gestion des envois et OTP de livraison
├── trips/                 # ✅ Gestion des trajets
├── matching/              # ✅ Système de matching intelligent
├── payments/              # ✅ Gestion des paiements et portefeuille
├── chat/                  # 🔄 Messagerie interne
├── notifications/         # 🔄 Notifications SMS/Email
├── documents/             # 🔄 Génération de documents
├── analytics/             # 🔄 Statistiques et métriques
├── admin_panel/           # ✅ Interface d'administration
├── internationalization/  # ✅ Gestion multilingue (FR/EN/AR)
└── verification/          # ✅ Vérification des documents
```

## 📊 Statut d'Implémentation des Modules

### ✅ Modules Complétés (100% Fonctionnels)

#### 1. **Module Users** - Authentification & Rôles
- **Gestion des rôles** : Expéditeur, Voyageur, Admin, Both
- **Vérification d'identité** : Téléphone + Documents
- **Système OTP sécurisé** : Authentification et vérification
- **Portefeuille intégré** : Gestion des paiements
- **Système de notation** : Évaluations utilisateurs
- **Permissions granulaires** : Contrôle d'accès avancé
- **API Endpoints** : CRUD complet avec validation

#### 2. **Module Shipments** - Gestion des Envois
- **Création d'envois** : Détails complets des colis
- **Système de matching** : Association automatique avec trajets
- **OTP de livraison** : Confirmation sécurisée selon cahier des charges
- **Suivi en temps réel** : Statuts et événements
- **Gestion des paiements** : Intégration complète
- **Documents automatiques** : Génération de reçus
- **API Endpoints** : Gestion complète du cycle de vie

#### 3. **Module Trips** - Gestion des Trajets
- **Création de trajets** : Détails complets (départ, arrivée, dates)
- **Gestion des disponibilités** : Poids et type d'objets acceptés
- **Validation des documents** : Passeport et billet d'avion
- **Statuts de trajet** : Planifié, En cours, Terminé
- **API Endpoints** : CRUD complet avec validation

#### 4. **Module Matching** - Système de Mise en Relation
- **Algorithme intelligent** : Croisement automatique envois ↔ trajets
- **Critères de matching** : Géolocalisation, dates, poids, type
- **Notifications automatiques** : Propositions aux voyageurs
- **Gestion des acceptations** : Workflow de validation
- **API Endpoints** : Matching automatique et manuel

#### 5. **Module Payments** - Gestion des Paiements
- **Méthodes de paiement** : CIB, Eddahabia, Espèces, Wallet
- **Portefeuille intégré** : Gestion des soldes
- **Système de commissions** : Calcul automatique (20-30%)
- **Virements et retraits** : Gestion des flux financiers
- **Sécurité** : Validation et audit des transactions
- **API Endpoints** : Paiements sécurisés et gestion de portefeuille

#### 6. **Module Admin Panel** - Interface d'Administration
- **Dashboard complet** : Vue d'ensemble des opérations
- **Gestion des utilisateurs** : CRUD et modération
- **Suivi des envois** : Statuts et événements
- **Gestion des paiements** : Transactions et commissions
- **Statistiques** : Métriques en temps réel
- **Interface web** : Interface d'administration intuitive

#### 7. **Module Internationalization** - Gestion Multilingue
- **Langues supportées** : Français (FR), Anglais (EN), Arabe (AR)
- **Traductions complètes** : Interface utilisateur et API
- **Fichiers de traduction** : PO/MO avec gettext
- **Détection automatique** : Basée sur les préférences utilisateur
- **API Endpoints** : Gestion des langues et traductions

#### 8. **Module Verification** - Vérification des Documents
- **Upload sécurisé** : Carte d'identité, passeport, billet d'avion
- **Validation automatique** : OCR et vérification des documents
- **Workflow de validation** : Processus admin avec approbation
- **Stockage conforme** : RGPD et sécurité des données
- **API Endpoints** : Gestion complète de la vérification

### 🔄 Modules en Développement

#### 9. **Module Analytics** - Statistiques et Métriques
- **KPIs utilisateurs** : Taux de vérification, répartition par rôle
- **Métriques envois** : Volume, taux de livraison, temps moyen
- **Statistiques financières** : Revenus, commissions, portefeuilles
- **Rapports automatisés** : Export et visualisation
- **API Endpoints** : Données statistiques en temps réel

#### 10. **Module Chat** - Messagerie Interne
- **Messagerie sécurisée** : Communication expéditeur ↔ voyageur
- **Appels VoIP** : Communication vocale intégrée
- **Historique des conversations** : Sauvegarde sécurisée
- **Notifications en temps réel** : WebSocket

#### 10. **Module Notifications** - Système de Notifications
- **SMS automatiques** : Twilio/Vonage
- **Emails transactionnels** : Confirmations et rappels
- **Notifications push** : Application mobile
- **Templates personnalisables** : Multilingue

#### 11. **Module Documents** - Génération de Documents
- **PDF automatiques** : WeasyPrint/xhtml2pdf
- **Templates sécurisés** : Engagement, reçu, contrat
- **Cachet et signature** : Intégration logo entreprise
- **Stockage sécurisé** : Documents chiffrés

#### 12. **Module Verification** - Vérification des Documents
- **Upload sécurisé** : Carte d'identité, passeport
- **Validation automatique** : OCR et vérification
- **Workflow de validation** : Processus admin
- **Stockage conforme** : RGPD et sécurité

## 👥 Acteurs du Système

### 1. **Expéditeur**
- Personne vivant en Algérie souhaitant envoyer un colis
- Crée des demandes d'envoi avec détails et paiement
- Suit le statut de son envoi en temps réel

### 2. **Voyageur**
- Algérien voyageant à l'étranger
- Publie ses trajets et accepte des missions
- Transporte les colis et confirme les livraisons

### 3. **Entreprise (Kleer Infini)**
- Intermédiaire sécurisé
- Vérifie le contenu des colis
- Gère les paiements et commissions
- Assure la traçabilité avec code export

## 💳 Système de Paiements Algériens (Implémenté)

### Méthodes de Paiement Supportées

#### 🏦 Cartes Bancaires Algériennes
- **CIB** : Cartes bancaires CIB (Crédit Industriel et Commercial)
- **Eddahabia** : Cartes bancaires Eddahabia (Poste Algérienne)

#### 💰 Paiement en Espèces
- **Bureau Kleer Infini** : Paiement en espèces au bureau
- **Confirmation admin** : Validation par le personnel

### Endpoints API Paiements

```http
# Méthodes de paiement disponibles
GET /api/v1/payments/methods/

# Paiement par carte algérienne
POST /api/v1/payments/card/
{
    "amount": 5000.00,
    "card_type": "cib",
    "card_number": "1234567890123456",
    "card_holder_name": "Ahmed Benali",
    "cvv": "123",
    "expiry_month": "12",
    "expiry_year": "2025"
}

# Paiement en espèces
POST /api/v1/payments/cash/
{
    "amount": 2500.00,
    "office_location": "Bureau Kleer Infini - Alger Centre"
}

# Confirmation paiement espèces (Admin)
POST /api/v1/payments/cash/{transaction_id}/confirm/

# Calcul des frais
GET /api/v1/payments/fees/?amount=5000&payment_method=cib
```

### Sécurité des Paiements

- ✅ **Validation** : Numéro de carte, CVV, dates d'expiration
- ✅ **Limites** : Montants maximum par méthode
- ✅ **Chiffrement** : Données sensibles sécurisées
- ✅ **Audit** : Toutes les transactions loggées

## 🔐 Système OTP de Livraison (Implémenté)

### Fonctionnement

Le système OTP de livraison implémente le processus de confirmation sécurisé :

1. **Voyageur prend le colis** → Initie le processus de livraison
2. **OTP généré automatiquement** → Code à 6 chiffres envoyé au destinataire
3. **Destinataire reçoit SMS** → "Code de livraison: 123456"
4. **Voyageur arrive à destination** → Destinataire remet le code
5. **Voyageur vérifie le code** → Saisit l'OTP dans l'application
6. **Livraison confirmée** → Paiement libéré automatiquement

### Endpoints API OTP

```http
# Initier le processus de livraison
POST /api/v1/shipments/{tracking_number}/delivery/initiate/

# Générer OTP de livraison
POST /api/v1/shipments/{tracking_number}/delivery/otp/generate/

# Vérifier statut OTP
GET /api/v1/shipments/{tracking_number}/delivery/otp/status/

# Renvoyer OTP
POST /api/v1/shipments/{tracking_number}/delivery/otp/resend/

# Vérifier OTP et confirmer livraison
POST /api/v1/shipments/{tracking_number}/delivery/otp/verify/
```

### Sécurité OTP

- ✅ **Authentification** : JWT requis
- ✅ **Autorisation** : Seul le voyageur associé peut vérifier
- ✅ **Expiration** : 24 heures
- ✅ **Rate Limiting** : Protection contre les abus
- ✅ **Audit** : Toutes les actions loggées

## 💰 Modèle Économique

### Sources de Revenus

- **Commission** : 20-30% sur chaque envoi
- **Frais de service** : 500-1000 DA (emballage)
- **Paiement premium** : Livraison express
- **Abonnements** : Voyageur Gold

### Répartition des Paiements

```
Exemple : Envoi 5000 DA
├── 1500 DA → Commission Kleer Infini
├── 500 DA → Frais d'emballage
└── 3000 DA → Voyageur (libéré après livraison)
```

## 🛡️ Sécurité et Conformité

### Vérifications d'Identité

- **Expéditeur** : Documents d'identité vérifiés
- **Voyageur** : Passeport et billet d'avion
- **Contenu** : Inspection par le bureau Kleer Infini
- **Code Export** : Utilisation légale du code Kleer Infini

### Protection des Données

- **Chiffrement** : Mots de passe hashés SHA256
- **OTP Sécurisés** : Double hachage, expiration
- **JWT** : Tokens d'authentification sécurisés
- **Rate Limiting** : Protection contre les abus

## 🚀 Installation et Démarrage

### Prérequis

- Python 3.8+
- PostgreSQL 12+
- Redis (pour le cache)
- Compte Twilio/Vonage (SMS)

### Installation

```bash
# Cloner le projet
git clone https://github.com/kleer-infini/kleer-logistics.git
cd kleer-logistics

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configuration
cp env.example .env
# Éditer .env avec vos paramètres

# Base de données
python kleerlogistics/manage.py migrate
python kleerlogistics/manage.py createsuperuser

# Démarrer le serveur
python kleerlogistics/manage.py runserver
```

### Variables d'Environnement

```env
# Base de données
DATABASE_URL=postgresql://user:pass@localhost/kleerlogistics

# SMS (Twilio/Vonage)
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_FROM_NUMBER=+1234567890

# Sécurité
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Paiements (CIB, Eddahabia)
CIB_MAX_AMOUNT=100000
EDDAHABIA_MAX_AMOUNT=100000
CASH_MAX_AMOUNT=50000
```

## 📱 API Documentation

### Swagger UI

Accédez à la documentation interactive de l'API :

```
http://localhost:8000/api/docs/
```

### Tests API

Utilisez les fichiers de test HTTP inclus :

```bash
# Tests OTP de livraison
api_tests/delivery_otp.http

# Tests utilisateurs
api_tests/users.http

# Tests envois
api_tests/shipments.http

# Tests paiements algériens
api_tests/payments.http

# Tests trajets
api_tests/trips.http

# Tests matching
api_tests/matching.http

# Tests admin panel
api_tests/admin_panel.http

# Tests internationalization
api_tests/internationalization.http
```

## 📈 Métriques et Statistiques

### KPIs Principaux

- **Utilisateurs** : Taux de vérification, répartition par rôle
- **Envois** : Taux de livraison, temps moyen, confirmation OTP
- **Paiements** : Volume, taux de succès, libération après OTP
- **OTP** : Taux de vérification, temps moyen, renvois
- **Matching** : Taux de succès, temps de traitement
- **Trajets** : Volume, taux d'utilisation, destinations populaires

## 🔧 Développement

### Structure des Migrations

```bash
# Créer une migration
python manage.py makemigrations app_name

# Appliquer les migrations
python manage.py migrate

# Voir le statut
python manage.py showmigrations
```

### Tests

```bash
# Tests unitaires
python manage.py test

# Tests avec couverture
coverage run --source='.' manage.py test
coverage report
```

### Linting et Formatage

```bash
# Flake8
flake8 kleerlogistics/

# Black
black kleerlogistics/

# Isort
isort kleerlogistics/
```

## 📋 Roadmap

### Phase 1 - Core (✅ Terminé)
- [x] Module Users avec OTP sécurisé
- [x] Module Shipments avec OTP de livraison
- [x] Module Trips avec gestion complète
- [x] Module Matching intelligent
- [x] Module Payments avec méthodes algériennes
- [x] Module Admin Panel avec dashboard
- [x] Module Internationalization multilingue
- [x] Module Verification des documents
- [x] Système d'authentification JWT
- [x] API REST complète

### Phase 2 - Communication & Documents (🔄 En cours)
- [ ] Module Analytics avec métriques et statistiques
- [ ] Module Chat avec messagerie sécurisée
- [ ] Module Notifications (SMS/Email)
- [ ] Module Documents avec génération PDF

### Phase 3 - Advanced Features (📅 Planifié)
- [ ] Intégration code export Kleer Infini
- [ ] Système de notifications push
- [ ] Optimisations de performance
- [ ] Tests de charge et sécurité

## 🤝 Contribution

### Standards de Code

- **Python** : PEP 8, type hints
- **Django** : Best practices, DRY principle
- **API** : RESTful, OpenAPI 3.0
- **Tests** : Coverage > 80%

## 📞 Support

### Contact

- **Email** : romualdosebany@gmail.com

### Documentation

- **API Docs** : `/api/docs/`
- **Dictionnaire de données** : `DICTIONNAIRE_DONNEES.md`
- **Tests OTP** : `api_tests/delivery_otp.http`

## 📄 Licence

Ce projet est propriétaire de Kleer Infini. Tous droits réservés.

---

**Version** : 3.0  
**Dernière mise à jour** : 24 Août 2025 
**Statut** : ✅ 8 modules sur 12 complétés (67% du backend)  
**Modules terminés** : Users, Shipments, Trips, Matching, Payments, Admin Panel, Internationalization, Verification  
**Modules en cours** : Analytics, Chat, Notifications, Documents
