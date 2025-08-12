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
- **Paiements** : Stripe, Wallet intégré
- **Documentation API** : Swagger/OpenAPI
- **Sécurité** : Django Axes, Rate Limiting, OTP sécurisés

### Structure du Projet

```
kleerlogistics/
├── users/                 # Gestion des utilisateurs et authentification
├── shipments/             # Gestion des envois et OTP de livraison
├── trips/                 # Gestion des trajets
├── matching/              # Système de matching intelligent
├── payments/              # Gestion des paiements et portefeuille
├── chat/                  # Messagerie interne
├── notifications/         # Notifications SMS/Email
├── documents/             # Génération de documents
├── analytics/             # Statistiques et métriques
└── admin_panel/           # Interface d'administration
```

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

## 🔐 Système OTP de Livraison (Nouveau)

### Fonctionnement selon le Cahier des Charges

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

## 📊 Fonctionnalités Principales

### ✅ Module Users (100% Conforme)

- **Gestion des rôles** : Expéditeur, Voyageur, Admin, Both
- **Vérification d'identité** : Téléphone + Documents
- **Système OTP sécurisé** : Authentification et vérification
- **Portefeuille intégré** : Gestion des paiements
- **Système de notation** : Évaluations utilisateurs
- **Permissions granulaires** : Contrôle d'accès avancé

### ✅ Module Shipments (100% Conforme)

- **Création d'envois** : Détails complets des colis
- **Système de matching** : Association automatique avec trajets
- **OTP de livraison** : Confirmation sécurisée selon cahier des charges
- **Suivi en temps réel** : Statuts et événements
- **Gestion des paiements** : Intégration complète
- **Documents automatiques** : Génération de reçus

### 🔄 Modules en Développement

- **Trips** : Gestion des trajets voyageurs
- **Matching** : Algorithme de mise en relation
- **Payments** : Intégration Stripe et wallet
- **Chat** : Messagerie interne sécurisée
- **Notifications** : SMS et emails automatiques

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

# Paiements (Stripe)
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
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
```

## 📈 Métriques et Statistiques

### KPIs Principaux

- **Utilisateurs** : Taux de vérification, répartition par rôle
- **Envois** : Taux de livraison, temps moyen, confirmation OTP
- **Paiements** : Volume, taux de succès, libération après OTP
- **OTP** : Taux de vérification, temps moyen, renvois

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
- [x] Système d'authentification JWT
- [x] API REST complète

### Phase 2 - Business Logic (🔄 En cours)
- [ ] Module Trips
- [ ] Système de Matching intelligent
- [ ] Intégration paiements Stripe
- [ ] Messagerie interne

### Phase 3 - Advanced Features (📅 Planifié)
- [ ] Dashboard analytics avancé
- [ ] Intégration code export Kleer Infini
- [ ] Système de notifications push

## 🤝 Contribution

### Standards de Code

- **Python** : PEP 8, type hints
- **Django** : Best practices, DRY principle
- **API** : RESTful, OpenAPI 3.0
- **Tests** : Coverage > 80%

## 📞 Support

### Contact

- **Email** : support@kleer-infini.com
- **Téléphone** : +213 XXX XXX XXX
- **Adresse** : Alger Centre, Algérie

### Documentation

- **API Docs** : `/api/docs/`
- **Dictionnaire de données** : `DICTIONNAIRE_DONNEES.md`
- **Tests OTP** : `api_tests/delivery_otp.http`

## 📄 Licence

Ce projet est propriétaire de Kleer Infini. Tous droits réservés.

---

**Version** : 2.0  
**Dernière mise à jour** : 12 Août 2025  
**Statut** : ✅ Système OTP de livraison implémenté selon cahier des charges
