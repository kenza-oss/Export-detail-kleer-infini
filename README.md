# Kleer Logistics API

**Backend Django API** pour connecter voyageurs et expéditeurs de colis avec matching intelligent et système de paiements.

## 🚀 **État du Projet**

### ✅ **Modules Fonctionnels**
- **🔐 Authentication** : JWT + OTP + Rôles + Permissions
- **👥 Users** : Profils, documents, vérification
- **📦 Shipments** : Création, tracking, OTP, validation
- **✈️ Trips** : Gestion trajets, capacité, documents
- **🎯 Matching** : **Algorithme intelligent v2.0 avec géolocalisation**
- **💰 Payments** : Portefeuilles, transactions, commissions
- **💬 Chat** : Messagerie, conversations, fichiers
- **⭐ Ratings** : Évaluations, commentaires, statistiques

## 🏗️ **Architecture**

```
kleerlogistics/
├── config/                 # Configuration Django
├── users/                  # ✅ Authentification & rôles
├── shipments/              # ✅ Gestion des envois
├── trips/                  # ✅ Gestion des trajets
├── matching/               # ✅ **Algorithme de matching v2.0**
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

## 🎯 **Matching Intelligent v2.0**

### **Algorithme Avancé**
- **Score Géographique (40%)** : Distance origine/destination avec formule de Haversine
- **Score de Capacité (25%)** : Compatibilité poids/volume/type de colis
- **Score Temporel (20%)** : Timing ramassage/livraison + flexibilité
- **Score Utilisateur (15%)** : Notes + correspondance préférences

### **Endpoints API**
```http
POST /api/v1/matching/find-matches/     # Matching intelligent
GET  /api/v1/matching/advanced-matches/ # Liste avec analytics
POST /api/v1/matching/optimize/         # Optimisation automatique
GET  /api/v1/matching/analytics/        # Analytics détaillés
```

## 🐳 **Installation avec Docker**

### **Démarrage Rapide**
```bash
# Cloner le projet
git clone https://github.com/kenza-oss/Export-detail-kleer-infini.git
cd Export-detail-kleer-infini

# Lancer avec Docker Compose
docker-compose up -d

# Vérifier les services
docker-compose ps
```

### **Accès**
- **API**: http://localhost:8000
- **Admin**: http://localhost:8000/admin
- **Swagger**: http://localhost:8000/swagger/

## 🔐 **Authentification**

### **JWT + OTP**
```http
POST /api/v1/users/auth/register/       # Inscription
POST /api/v1/users/auth/login/          # Connexion JWT
POST /api/v1/users/auth/otp/send/       # Envoyer OTP
POST /api/v1/users/auth/otp/verify/     # Vérifier OTP
```

### **Profils & Documents**
```http
GET  /api/v1/users/profile/             # Récupérer profil
PUT  /api/v1/users/profile/update/      # Mettre à jour profil
GET  /api/v1/users/documents/           # Liste documents
POST /api/v1/users/documents/upload/    # Upload document
```

## 📦 **Shipments & Trips**

### **Gestion des Envois**
```http
POST /api/v1/shipments/                 # Créer shipment
GET  /api/v1/shipments/                 # Liste shipments
GET  /api/v1/shipments/{id}/tracking/   # Tracking en temps réel
POST /api/v1/shipments/{id}/validate/   # Validation OTP
```

### **Gestion des Trajets**
```http
POST /api/v1/trips/                     # Créer trajet
GET  /api/v1/trips/                     # Liste trajets
GET  /api/v1/trips/{id}/documents/      # Documents trajet
```

## 💰 **Paiements & Chat**

### **Portefeuilles & Transactions**
```http
GET  /api/v1/payments/wallet/           # Solde portefeuille
GET  /api/v1/payments/transactions/     # Historique transactions
POST /api/v1/payments/transfer/         # Transfert
```

### **Messagerie**
```http
GET  /api/v1/chat/conversations/        # Conversations
POST /api/v1/chat/messages/             # Envoyer message
GET  /api/v1/chat/messages/{id}/        # Détail message
```

## ⭐ **Évaluations**
```http
POST /api/v1/ratings/                   # Créer évaluation
GET  /api/v1/ratings/user/{id}/         # Évaluations utilisateur
GET  /api/v1/ratings/stats/             # Statistiques
```

## 🛠️ **Commandes Utiles**

### **Docker**
```bash
docker-compose up -d                     # Lancer services
docker-compose logs -f                   # Voir logs
docker-compose down                      # Arrêter services
docker-compose build --no-cache         # Reconstruire image
```

### **Développement**
```bash
# Accéder au container
docker-compose exec kleerlogistics bash

# Créer superuser
docker-compose exec kleerlogistics python manage.py createsuperuser

# Migrations
docker-compose exec kleerlogistics python manage.py migrate

# Tests
curl http://localhost:8000/health/       # Health check
```

## 📊 **Base de Données**

### **Modèles Principaux**
- ✅ `User`, `UserProfile`, `UserDocument`, `OTPCode`
- ✅ `Shipment`, `ShipmentTracking`
- ✅ `Trip`, `TripDocument`
- ✅ `Match`, `MatchingPreferences`
- ✅ `Wallet`, `Transaction`, `Commission`
- ✅ `Conversation`, `Message`
- ✅ `Rating`

## 🔒 **Sécurité**

- ✅ **JWT** avec refresh tokens
- ✅ **OTP** pour livraisons sécurisées
- ✅ **Permissions** basées sur les rôles
- ✅ **Rate limiting** par endpoint
- ✅ **Validation** des données métier
- ✅ **Protection CSRF** et XSS

## 📈 **Monitoring**

```http
GET /health/              # Statut général
GET /health/db/           # Connexion base de données
GET /health/cache/        # Connexion Redis
GET /health/celery/       # Statut Celery
```

## 🎯 **Prochaines Étapes**

### **Phase 2 - Modules Restants**
1. **Documents** : Génération PDF avec WeasyPrint
2. **Notifications** : Email/SMS avec templates
3. **Verification** : Upload et validation documents
4. **Admin Panel** : Dashboard avec statistiques
5. **Analytics** : Métriques et rapports
6. **Internationalization** : Support FR/EN/AR

## 📞 **Support**

### **Accès Admin**
- **URL**: http://localhost:8000/admin/
- **Username**: `romualdo`
- **Password**: `passwordkleer`

### **Documentation API**
- **Swagger**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

---

**Développé avec ❤️ par l'équipe Kleer Logistics**
