# 📚 INDEX VYZIO ADS - Guide de Navigation

## 🚀 COMMENCER ICI

### Pour démarrer rapidement (5-10 min)
1. 📖 Lire: [QUICK_START.md](QUICK_START.md)
2. ▶️ Exécuter: `setup.bat` (Windows) ou `bash setup.sh` (Mac/Linux)
3. 🌐 Visiter: http://localhost:8000

### Pour comprendre le projet
1. 📋 Lire: [README.md](README.md) - Vue d'ensemble
2. 📊 Lire: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Résumé exécutif
3. 📁 Consulter: [PROJECT_STRUCTURE.txt](PROJECT_STRUCTURE.txt) - Architecture

---

## 📚 DOCUMENTATION

### 🔧 Installation & Configuration
- **[QUICK_START.md](QUICK_START.md)** - Guide d'installation (5 min)
- **[README.md](README.md)** - Documentation principale
- **[.env.example](.env.example)** - Variables d'environnement

### 📖 API & Développement
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Endpoints complets avec exemples
  - Authentification JWT
  - Annonces (CRUD, recherche, filtres)
  - Messagerie
  - Paiements Stripe
  - Avis & Notation
  - Admin API

### 🚀 Déploiement
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production setup
  - Railway.app
  - Render.com
  - OVH/VPS manuel
  - Configuration SSL/HTTPS

### 🔧 Troubleshooting
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - FAQ et solutions
  - Erreurs couantes
  - Configuration
  - Debugging

### 📊 Résumés
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Vue d'ensemble complète
- **[PROJECT_STRUCTURE.txt](PROJECT_STRUCTURE.txt) - Organisation des fichiers

---

## 🗂️ STRUCTURE DU PROJET

```
vyzio_ads/
│
├── 📄 Documentation
│   ├── README.md
│   ├── QUICK_START.md
│   ├── API_DOCUMENTATION.md
│   ├── DEPLOYMENT.md
│   ├── TROUBLESHOOTING.md
│   ├── PROJECT_SUMMARY.md
│   └── PROJECT_STRUCTURE.txt
│
├── ⚙️ Configuration
│   ├── config/
│   │   ├── settings.py         ← Configuration Django
│   │   ├── urls.py             ← Routes principales
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   └── celery.py
│   ├── .env.example            ← Variables d'environnement
│   ├── requirements.txt        ← Dépendances Python
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── 📱 Applications Django
│   └── apps/
│       ├── users/              ← Gestion des comptes
│       │   ├── models.py       (CustomUser, SellerSubscription)
│       │   ├── views.py        (JWT, profil, stats)
│       │   ├── serializers.py
│       │   ├── urls.py
│       │   └── admin.py
│       │
│       ├── listings/           ← Annonces (CRUD)
│       │   ├── models.py       (Listing, Category, Image, Favorite)
│       │   ├── views.py        (Recherche, filtres, boost)
│       │   ├── serializers.py
│       │   ├── urls.py
│       │   ├── admin.py
│       │   └── management/commands/load_fixtures.py
│       │
│       ├── messaging/          ← Messagerie interne
│       │   ├── models.py       (Conversation, Message, Report)
│       │   ├── views.py        (Conversations, send, block)
│       │   ├── serializers.py
│       │   ├── urls.py
│       │   └── admin.py
│       │
│       ├── payments/           ← Paiements Stripe
│       │   ├── models.py       (Payment, Subscription, Invoice)
│       │   ├── views.py        (Checkout, webhook)
│       │   ├── serializers.py
│       │   ├── urls.py
│       │   └── admin.py
│       │
│       ├── reviews/            ← Avis & Notation
│       │   ├── models.py       (Review, ReviewPhoto)
│       │   ├── views.py        (Lister, créer, répondre)
│       │   ├── serializers.py
│       │   ├── urls.py
│       │   └── admin.py
│       │
│       └── admin_panel/        ← Modération
│           ├── models.py
│           ├── views.py        (Dashboard, users, listings, reports)
│           └── urls.py
│
├── 🛠️ Utilitaires
│   └── utils/
│       ├── stripe_webhooks.py  ← Webhook Stripe
│       └── __init__.py
│
├── 📁 Dossiers statiques
│   ├── static/                 (CSS, JS, images admin)
│   ├── media/                  (Uploads utilisateurs)
│   ├── logs/                   (Fichiers log)
│   └── staticfiles/            (Généré par collectstatic)
│
├── 🔧 Scripts
│   ├── setup.bat               (Installation Windows)
│   ├── setup.sh                (Installation Mac/Linux)
│   └── manage.py               (CLI Django)
```

---

## 📋 APPLICATIONS (Apps) DÉTAIL

### 1️⃣ **users** - Gestion des utilisateurs
**Fichiers clés**: `apps/users/`
- `models.py`: CustomUser (3 rôles), SellerSubscription
- `views.py`: Login, profil, stats vendeur
- `serializers.py`: UserRegistration, UserProfile, UserDetail

**Endpoints**:
```
POST   /api/users/              Créer compte
POST   /api/users/login/        Se connecter
GET    /api/users/me/           Profil courant
PATCH  /api/users/me/           Mettre à jour profil
GET    /api/users/seller_stats/ Stats vendeur
```

### 2️⃣ **listings** - Annonces
**Fichiers clés**: `apps/listings/`
- `models.py`: Listing, Category, ListingImage, Favorite, ViewHistory
- `views.py`: CRUD, recherche, filtres, boost, trending
- `serializers.py`: ListingList, ListingDetail, ListingCreate

**Endpoints**:
```
GET    /api/listings/listings/                    Lister (filtrable)
GET    /api/listings/listings/{id}/               Détail
POST   /api/listings/listings/                    Créer
PATCH  /api/listings/listings/{id}/               Modifier
DELETE /api/listings/listings/{id}/               Supprimer
POST   /api/listings/listings/{id}/toggle_favorite/  Favori
POST   /api/listings/listings/{id}/boost/         Booster (premium)
GET    /api/listings/listings/trending/           Tendances
GET    /api/listings/listings/my_listings/        Mes annonces
GET    /api/listings/categories/                  Catégories
```

### 3️⃣ **messaging** - Messagerie
**Fichiers clés**: `apps/messaging/`
- `models.py`: Conversation, Message, BlockedUser, Report
- `views.py`: Lister conversations, envoyer message, bloquer, signaler
- `serializers.py`: Conversation, Message, Report

**Endpoints**:
```
GET    /api/messages/conversations/                       Lister
GET    /api/messages/conversations/{id}/                  Détail
POST   /api/messages/conversations/start_conversation/   Créer
POST   /api/messages/conversations/{id}/send_message/    Envoyer
POST   /api/messages/conversations/{id}/mark_read/       Marquer lu
POST   /api/messages/conversations/{id}/block_user/      Bloquer
POST   /api/messages/conversations/{id}/report_user/     Signaler
```

### 4️⃣ **payments** - Paiements Stripe
**Fichiers clés**: `apps/payments/`
- `models.py`: Payment, SubscriptionPlan, Subscription, Invoice, Coupon
- `views.py`: Checkout Stripe, webhook, historique paiements
- `serializers.py`: Payment, Subscription, Plan

**Endpoints**:
```
GET    /api/payments/plans/                           Plans disponibles
POST   /api/payments/payments/create_checkout_session/ Créer session Stripe
GET    /api/payments/payments/                        Historique
```

### 5️⃣ **reviews** - Avis & Notation
**Fichiers clés**: `apps/reviews/`
- `models.py`: Review, ReviewPhoto
- `views.py`: Créer avis, répondre, lister par vendeur
- `serializers.py`: Review, ReviewCreate

**Endpoints**:
```
GET    /api/reviews/                          Lister avis
GET    /api/reviews/?seller_id=<id>          Avis d'un vendeur
POST   /api/reviews/                          Créer avis
POST   /api/reviews/{id}/add_response/       Répondre (vendeur)
GET    /api/reviews/seller_reviews/          Stats vendeur
```

### 6️⃣ **admin_panel** - Modération & Admin
**Fichiers clés**: `apps/admin_panel/`
- `views.py`: Dashboard, gestion utilisateurs, listings, reports
- `urls.py`: Routes admin

**Endpoints**:
```
GET    /api/admin/dashboard-stats/            Statistiques
GET    /api/admin/users/                      Lister utilisateurs
POST   /api/admin/ban-user/                   Bannir
POST   /api/admin/unban-user/                 Débannir
GET    /api/admin/pending-listings/           Annonces en attente
POST   /api/admin/approve-listing/            Approuver
POST   /api/admin/reject-listing/             Rejeter
GET    /api/admin/reports/                    Signalements
POST   /api/admin/resolve-report/             Résoudre
```

---

## 🔐 MODÈLES DE DONNÉES

### Users
```
CustomUser
├── email (unique)
├── username
├── password (hashed)
├── first_name, last_name
├── role: buyer | seller | professional
├── phone
├── avatar (Cloudinary)
├── bio
├── location
├── subscription_type: free | basic | pro
├── subscription_start/end
├── avg_rating (1-5)
├── total_reviews
├── is_verified
├── is_banned
└── is_active_seller

SellerSubscription
├── user (OneToOne)
├── subscription_type
├── stripe_subscription_id
├── is_active
├── listings_count
├── max_listings
├── can_boost
└── boost_count
```

### Listings
```
Listing
├── id (UUID)
├── seller (FK User)
├── category (FK Category)
├── title
├── slug (unique)
├── description
├── price
├── price_negotiable
├── listing_type: product | service | rental | job
├── status: draft | published | sold | archived
├── location
├── latitude, longitude
├── stock
├── available
├── views_count
├── is_boosted
├── boost_end_date
├── is_approved
├── is_flagged
├── flag_reason
└── created_at/updated_at

ListingImage
├── listing (FK)
├── image (Cloudinary)
├── is_primary
└── order

Category
├── name (unique)
├── slug (unique)
├── description
├── icon
└── is_active

Favorite
├── user (FK)
├── listing (FK)
└── created_at

ViewHistory
├── user (FK, nullable)
├── listing (FK)
├── ip_address
└── created_at
```

### Messaging
```
Conversation
├── buyer (FK User)
├── seller (FK User)
├── listing (FK, optional)
├── is_active
└── created_at/updated_at

Message
├── conversation (FK)
├── sender (FK User)
├── content
├── is_read
└── read_at

BlockedUser
├── blocker (FK User)
├── blocked (FK User)
└── created_at

Report
├── reporter (FK User)
├── reported_user (FK User)
├── conversation (FK, optional)
├── reason: spam | inappropriate | scam | offensive | other
├── description
├── is_resolved
└── created_at/updated_at
```

### Payments
```
Payment
├── user (FK)
├── amount (Decimal)
├── currency (default: EUR)
├── payment_type: subscription | boost | commission
├── status: pending | completed | failed | refunded
├── stripe_payment_id
├── stripe_customer_id
├── subscription (FK SubscriptionPlan)
├── listing (FK, optional)
└── created_at/completed_at

SubscriptionPlan
├── name
├── plan_type: basic | pro
├── billing_cycle: monthly | yearly
├── price
├── stripe_price_id
├── max_listings
├── can_boost
├── boost_count
├── featured
└── is_active

Subscription
├── user (OneToOne)
├── plan (FK SubscriptionPlan)
├── status: active | cancelled | expired
├── stripe_subscription_id
├── started_at
├── ends_at
├── cancelled_at
├── auto_renew
└── created_at/updated_at

Invoice
├── user (FK)
├── payment (FK)
├── invoice_number (unique)
├── amount
├── tax_amount
├── issued_at
├── due_at
├── paid_at
├── pdf_file
└── created_at

Coupon
├── code (unique)
├── discount_type: percentage | fixed
├── discount_value
├── max_uses
├── uses_count
├── valid_from/until
├── is_active
└── created_at
```

### Reviews
```
Review
├── reviewer (FK User)
├── seller (FK User)
├── listing (FK, optional)
├── rating (1-5)
├── comment
├── is_verified_buyer
├── is_approved
├── seller_response
├── seller_response_date
└── created_at/updated_at

ReviewPhoto
├── review (FK)
├── image (Cloudinary)
└── created_at
```

---

## 🔑 POINTS D'ENTRÉE

### 🌐 Serveur Web
- **Local**: http://localhost:8000
- **Admin**: http://localhost:8000/admin
- **API**: http://localhost:8000/api

### 📡 Base de Données
- **PostgreSQL** sur localhost:5432 (local)
- **SQLite** db.sqlite3 (par défaut développement)

### 🔄 Services
- **Redis**: localhost:6379 (cache & Celery)
- **Celery**: Background tasks

### 🔐 Authentification
- **Endpoint**: POST /api/users/login/
- **Header**: `Authorization: Bearer <token>`

---

## 📝 FLUX UTILISATEUR

### 1. Acheteur
```
1. Créer compte (email, password)
2. Valider email
3. Consulter annonces (filtrage)
4. Ajouter favoris
5. Contacter vendeur (messagerie)
6. Laisser avis après achat
```

### 2. Vendeur
```
1. Créer compte + choisir "Seller"
2. Souscrire plan (Basic ou Pro) via Stripe
3. Créer annonces (titre, description, photos)
4. Publier annonce
5. Booster si Plan Pro
6. Répondre aux messages acheteurs
7. Recevoir avis clients
8. Consulter dashboard/stats
9. Renouveler abonnement
```

### 3. Admin
```
1. Accéder http://localhost:8000/admin
2. Valider annonces en attente
3. Modérer signalements
4. Bannir utilisateurs abusifs
5. Consulter statistiques
6. Gérer coupons
```

---

## 🎯 COMMANDES UTILES

### Développement
```bash
# Démarrer serveur
python manage.py runserver

# Shell Django (teste modèles)
python manage.py shell

# Créer migrations
python manage.py makemigrations

# Appliquer migrations
python manage.py migrate

# Charger données test
python manage.py load_fixtures

# Tests
python manage.py test
```

### Production
```bash
# Collecter fichiers statiques
python manage.py collectstatic --noinput

# Créer superuser
python manage.py createsuperuser

# Backup BD
pg_dump vyzio_ads_db > backup.sql

# Logs
tail -f logs/debug.log
```

---

## 📞 SUPPORT

- 📖 Documentation: Ce dossier
- 🐛 Bugs: GitHub Issues
- 💬 Questions: GitHub Discussions
- 📧 Contact: (à définir)

---

## ✅ CHECKLIST DÉMARRAGE

- [ ] Lire QUICK_START.md
- [ ] Exécuter setup script
- [ ] Accéder http://localhost:8000/admin
- [ ] Créer annonces de test
- [ ] Tester les endpoints API
- [ ] Lire API_DOCUMENTATION.md complet
- [ ] Configurer Stripe (optionnel)
- [ ] Configurer Cloudinary (optionnel)

---

**Bienvenue dans vyzio-ads! 🚀**

Pour questions: Consulter les .md correspondants ou GitHub Issues
