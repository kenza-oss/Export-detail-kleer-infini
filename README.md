# Export-detail-kleer-infini

**Backend Django API** pour connecter voyageurs et expéditeurs de colis avec matching intelligent et système de paiements.

## 📊 **État du Projet - IMPLÉMENTATION COMPLÈTE**

### ✅ **Modules Implémentés (100%)**

| Module | Statut | Fonctionnalités |
|--------|--------|-----------------|
| **Users** | ✅ COMPLET | Authentification JWT, rôles, profils, documents |
| **Shipments** | ✅ COMPLET | Création, tracking, OTP, validation |
| **Trips** | ✅ COMPLET | Gestion trajets, capacité, documents |
| **Matching** | ✅ COMPLET | Algorithme intelligent, scoring, préférences |
| **Payments** | ✅ COMPLET | Portefeuilles, transactions, commissions |
| **Chat** | ✅ COMPLET | Messagerie, conversations, fichiers |
| **Ratings** | ✅ COMPLET | Évaluations, commentaires, statistiques |

### 🏗️ **Architecture Technique**

```
kleerlogistics/
├── config/                 # Configuration Django
├── users/                  # ✅ Authentification & rôles
├── shipments/              # ✅ Gestion des envois
├── trips/                  # ✅ Gestion des trajets
├── matching/               # ✅ Algorithme de matching
├── payments/               # ✅ Système de paiements
├── chat/                   # ✅ Messagerie
├── ratings/                # ✅ Système d'évaluations
├── documents/              # 🔄 Génération PDF
├── notifications/          # 🔄 Emails/SMS
├── verification/           # 🔄 Upload documents
├── admin_panel/            # 🔄 Dashboard admin
├── analytics/              # 🔄 Statistiques
└── internationalization/   # 🔄 Multilingue
```

## 🐳 **Installation avec Docker**

### Prérequis
- Docker & Docker Compose
- Git

### 🚀 **Démarrage Rapide**

1. **Cloner le projet**
```bash
git clone https://github.com/kenza-oss/Export-detail-kleer-infini.git
cd Export-detail-kleer-infini
```

2. **Lancer avec Docker Compose**
```bash
docker-compose up -d
```

3. **Vérifier les services**
```bash
docker-compose ps
```

4. **Accéder à l'application**
- **API**: http://localhost:8000
- **Admin**: http://localhost:8000/admin
- **Swagger**: http://localhost:8000/swagger/

### 🔧 **Configuration Docker**

```yaml
# docker-compose.yml
services:
  kleerlogistics:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      - DEBUG=True
      - DB_HOST=postgres
      - REDIS_URL=redis://redis:6379

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=kleerlogistics
      - POSTGRES_USER=kleerlogistics
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
```

## 📋 **API Endpoints Disponibles**

### 🔐 **Authentification**
```
POST /api/v1/users/auth/token/          # Connexion JWT
POST /api/v1/users/auth/token/refresh/  # Refresh token
POST /api/v1/users/auth/token/verify/   # Vérification token
```

### 👥 **Utilisateurs**
```
GET    /api/v1/users/users/             # Liste utilisateurs
POST   /api/v1/users/users/             # Créer utilisateur
GET    /api/v1/users/users/me/          # Utilisateur connecté
PUT    /api/v1/users/users/{id}/        # Modifier utilisateur
```

### 📦 **Envois (Shipments)**
```
GET    /api/v1/shipments/shipments/     # Liste envois
POST   /api/v1/shipments/shipments/     # Créer envoi
GET    /api/v1/shipments/shipments/{id}/ # Détail envoi
PUT    /api/v1/shipments/shipments/{id}/ # Modifier envoi
POST   /api/v1/shipments/shipments/{id}/submit/ # Soumettre envoi
POST   /api/v1/shipments/shipments/{id}/generate_otp/ # Générer OTP
POST   /api/v1/shipments/shipments/{id}/verify_otp/ # Vérifier OTP
GET    /api/v1/shipments/shipments/{id}/tracking/ # Historique tracking
```

### ✈️ **Trajets (Trips)**
```
GET    /api/v1/trips/trips/             # Liste trajets
POST   /api/v1/trips/trips/             # Créer trajet
GET    /api/v1/trips/trips/{id}/        # Détail trajet
PUT    /api/v1/trips/trips/{id}/        # Modifier trajet
```

### 🎯 **Matching**
```
GET    /api/v1/matching/matches/        # Liste matches
POST   /api/v1/matching/matches/        # Créer match
GET    /api/v1/matching/matches/{id}/   # Détail match
PUT    /api/v1/matching/matches/{id}/   # Modifier match
```

### 💰 **Paiements**
```
GET    /api/v1/payments/wallets/        # Liste portefeuilles
GET    /api/v1/payments/wallets/{id}/   # Détail portefeuille
GET    /api/v1/payments/transactions/   # Liste transactions
POST   /api/v1/payments/transactions/   # Créer transaction
```

### 💬 **Chat**
```
GET    /api/v1/chat/conversations/      # Liste conversations
POST   /api/v1/chat/conversations/      # Créer conversation
GET    /api/v1/chat/messages/           # Liste messages
POST   /api/v1/chat/messages/           # Envoyer message
```

### ⭐ **Évaluations**
```
GET    /api/v1/ratings/ratings/         # Liste évaluations
POST   /api/v1/ratings/ratings/         # Créer évaluation
GET    /api/v1/ratings/ratings/{id}/    # Détail évaluation
```

## 🚀 **Fonctionnalités Avancées Implémentées**

### 🎯 **Matching Intelligent**
- **Algorithme de scoring** (0-100%)
- **Facteurs multiples** : géographique, poids, type, fragilité, dates
- **Gestion de la flexibilité** des dates
- **Préférences utilisateur** et blacklist
- **Auto-acceptation** selon seuils

### 📦 **Système de Tracking**
- **Événements en temps réel** pour chaque shipment
- **Statuts multiples** : draft, pending, matched, in_transit, delivered
- **Historique complet** des événements
- **Géolocalisation** des événements

### 💰 **Gestion des Portefeuilles**
- **Soldes disponibles** et en attente
- **Transactions sécurisées** avec historique
- **Mise en attente** de fonds pour transactions
- **Support multi-devises** (DZD par défaut)
- **Système de commissions** automatique

### 🔐 **Système OTP**
- **Génération automatique** de codes OTP à 6 chiffres
- **Validation sécurisée** pour livraison
- **Expiration automatique** des codes
- **Sécurité renforcée** pour les livraisons

### 💬 **Messagerie Intégrée**
- **Conversations** entre expéditeurs et voyageurs
- **Messages texte, images, fichiers, localisation**
- **Statut de lecture** des messages
- **Métadonnées** pour les fichiers
- **Messages système** automatiques

### ⭐ **Système d'Évaluations**
- **Évaluations 1-5 étoiles** avec commentaires
- **Validation des permissions** et relations
- **Mise à jour automatique** des notes moyennes
- **Statistiques détaillées** par utilisateur
- **API REST complète** avec filtrage

## 🛠️ **Commandes Utiles**

### Docker
```bash
# Lancer les services
docker-compose up -d

# Voir les logs
docker-compose logs -f kleerlogistics

# Arrêter les services
docker-compose down

# Reconstruire l'image
docker-compose build --no-cache
```

### Développement
```bash
# Accéder au container
docker-compose exec kleerlogistics bash

# Créer un superuser
docker-compose exec kleerlogistics python manage.py createsuperuser

# Appliquer les migrations
docker-compose exec kleerlogistics python manage.py migrate

# Collecter les fichiers statiques
docker-compose exec kleerlogistics python manage.py collectstatic
```

### Tests
```bash
# Tester l'API
curl -X POST http://localhost:8000/api/v1/users/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "romualdo", "password": "passwordkleer"}'

# Health check
curl http://localhost:8000/health/
```

## 📊 **Base de Données**

### **Modèles Implémentés (15/15)**
- ✅ `User`, `UserProfile`, `UserDocument`
- ✅ `Shipment`, `ShipmentTracking`
- ✅ `Trip`, `TripDocument`
- ✅ `Match`, `MatchingPreferences`
- ✅ `Wallet`, `Transaction`, `Commission`
- ✅ `Conversation`, `Message`
- ✅ `Rating`

### **Relations ER (100%)**
- ✅ Toutes les relations du diagramme ER implémentées
- ✅ Cardinalités respectées
- ✅ Contraintes d'intégrité
- ✅ Index optimisés

## 🔒 **Sécurité**

### **Authentification**
- ✅ **JWT** avec refresh tokens
- ✅ **OTP** pour livraisons sécurisées
- ✅ **Permissions** basées sur les rôles
- ✅ **Rate limiting** par endpoint

### **Validation**
- ✅ **Validation des données** métier
- ✅ **Contraintes** de base de données
- ✅ **Messages d'erreur** explicites
- ✅ **Protection CSRF** et XSS

## 📈 **Monitoring**

### **Health Checks**
```
GET /health/              # Statut général
GET /health/db/           # Connexion base de données
GET /health/cache/        # Connexion Redis
GET /health/celery/       # Statut Celery
```

### **Logs**
```bash
# Logs Django
docker-compose logs kleerlogistics

# Logs PostgreSQL
docker-compose logs postgres

# Logs Redis
docker-compose logs redis
```

## 🎯 **Prochaines Étapes**

### **Phase 2 - Modules Restants**
1. **Documents** : Génération PDF avec WeasyPrint
2. **Notifications** : Email/SMS avec templates
3. **Verification** : Upload et validation documents
4. **Admin Panel** : Dashboard avec statistiques
5. **Analytics** : Métriques et rapports
6. **Internationalization** : Support FR/EN/AR

### **Phase 3 - Améliorations**
1. **Tests unitaires** et d'intégration
2. **Optimisation performances** et cache
3. **Intégration Chargily Pay** pour paiements
4. **Monitoring avancé** avec Sentry
5. **Documentation API** complète

## 📞 **Support**

### **Accès Admin**
- **URL**: http://localhost:8000/admin/
- **Username**: `romualdo`
- **Password**: `passwordkleer`

### **Documentation API**
- **Swagger**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

### **Logs et Debugging**
```bash
# Voir les logs en temps réel
docker-compose logs -f

# Accéder à la base de données
docker-compose exec postgres psql -U kleerlogistics -d kleerlogistics

# Shell Django
docker-compose exec kleerlogistics python manage.py shell
```

---
