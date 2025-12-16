# 🎨 VYZIO ADS - Vue Visuelle du Projet

## 🏛️ Architecture Globale

```
┌──────────────────────────────────────────────────────────────┐
│                    VYZIO ADS MARKETPLACE                     │
└──────────────────────────────────────────────────────────────┘

                         ┌─────────────┐
                         │  Frontend   │  (À faire)
                         │  Next.js    │
                         └──────┬──────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
              ┌─────▼──────────────┐    ┌──▼──────────────┐
              │   API REST         │    │  WebSockets    │
              │   (Django DRF)     │    │  (Real-time)   │
              └─────┬──────────────┘    └────────────────┘
                    │
        ┌───────────┼───────────┬───────────┬───────────┐
        │           │           │           │           │
    ┌───▼───┐  ┌───▼───┐  ┌───▼───┐  ┌───▼───┐  ┌───▼───┐
    │ Users │  │Listing│  │Messag│  │Payment│  │ Reviews│
    └───────┘  └───────┘  └───────┘  └───────┘  └───────┘
        │           │           │           │           │
    ┌───▴─────────────────────────────────────────────────┐
    │                  PostgreSQL                         │
    │  (Toutes les données centralisées)                  │
    └───────────────────────────────────────────────────┘
```

---

## 🔄 Flux de Données Utilisateur

### 👤 Inscription Acheteur
```
Signup Form
    ↓
CustomUser créé (role=buyer)
    ↓
Email de vérification envoyé
    ↓
Confirmation email
    ↓
Profil complet (bio, avatar, localisation)
```

### 🛒 Inscription Vendeur
```
Signup Form
    ↓
CustomUser créé (role=seller)
    ↓
Email vérification
    ↓
Plan selection (Basic/Pro)
    ↓
Paiement Stripe
    ↓
SellerSubscription créée
    ↓
Dashboard vendeur actif
```

### 📢 Publication Annonce
```
Formulaire création
    ↓
Listing créée (status=draft)
    ↓
Upload images (Cloudinary)
    ↓
Validation contenu
    ↓
Envoi modération
    ↓
Admin approuve
    ↓
Status = published
    ↓
Visible publiquement
```

### 💬 Interaction Acheteur-Vendeur
```
Acheteur consulte annonce
    ↓
Clique "Contacter vendeur"
    ↓
Conversation créée
    ↓
Acheteur envoie message
    ↓
Notification vendeur
    ↓
Vendeur répond
    ↓
Historique messages sauvegardé
```

### 💳 Processus de Paiement
```
Vendeur clique "S'abonner"
    ↓
Sélectionne plan (Basic/Pro)
    ↓
Applique coupon (optionnel)
    ↓
Redirect Stripe Checkout
    ↓
Paiement carte
    ↓
Webhook Stripe received
    ↓
Payment status = completed
    ↓
Subscription créée
    ↓
Email de confirmation
```

---

## 🗂️ Arborescence Données

```
VYZIO_ADS
│
├── USERS
│   ├── Acheteurs (role=buyer)
│   ├── Vendeurs (role=seller)
│   │   └── SellerSubscriptions
│   │       ├── Basic (5 annonces)
│   │       └── Pro (illimitées + boosts)
│   └── Professionnels (role=professional)
│
├── LISTINGS
│   ├── Catégories
│   │   ├── Électronique
│   │   ├── Vêtements
│   │   ├── Meubles
│   │   ├── Véhicules
│   │   ├── Services
│   │   └── Immobilier
│   │
│   ├── Annonces (par seller)
│   │   ├── Statut: draft/published/sold/archived
│   │   ├── Images (Cloudinary)
│   │   ├── Statistiques (views, favorites)
│   │   ├── Boosts (optionnel)
│   │   └── Modération
│   │
│   └── Favoris (par buyer)
│
├── MESSAGING
│   ├── Conversations (buyer ↔ seller)
│   │   ├── Messages
│   │   └── Historique
│   │
│   ├── Blocking
│   │   └── Users bloqués
│   │
│   └── Reports
│       └── Signalements abusifs
│
├── PAYMENTS
│   ├── Transactions
│   ├── Abonnements actifs
│   ├── Factures
│   └── Coupons
│
└── REVIEWS
    ├── Avis (5 étoiles)
    ├── Commentaires
    ├── Photos
    └── Réponses vendeur
```

---

## 🎯 Fonctionnalités par Rôle

### 👤 ACHETEUR (Non-payant)
```
✅ Consulter annonces
✅ Rechercher & filtrer
✅ Voir détails + photos
✅ Ajouter favoris
✅ Contacter vendeur
✅ Consulter avis vendeur
✅ Laisser avis après achat
✅ Créer compte gratuit
```

### 🏪 VENDEUR BASIC (9.99€/mois)
```
✅ Tout du Basic BUYER +
✅ Publier 5 annonces/mois
✅ Dashboard simple
✅ Répondre aux messages
✅ Consulter stats vues/messages
✅ Répondre aux avis
✅ Profil vendeur
❌ Booster annonces
❌ Annonces illimitées
```

### 🏢 VENDEUR PRO (29.99€/mois)
```
✅ Tout du BASIC +
✅ Annonces ILLIMITÉES
✅ 2 Boosts/mois inclus
✅ Featured listing
✅ Dashboard avancé
✅ Accès API full
✅ Analytics détaillées
✅ Support prioritaire
```

### 👨‍💼 ADMIN
```
✅ Tout du VENDEUR PRO +
✅ Valider annonces
✅ Modérer signalements
✅ Bannir utilisateurs
✅ Consulter statistiques globales
✅ Gérer coupons
✅ Approuver/rejeter contenu
✅ Support utilisateurs
```

---

## 📊 Modèles Relationnel (ERD)

```
                    ┌─────────────┐
                    │ CustomUser  │
                    │─────────────│
                    │ id (UUID)   │
                    │ email       │
                    │ role        │
                    │ avatar      │
                    │ subscription│
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
       ┌───▼───┐      ┌───▼────┐    ┌───▼─────┐
       │ Lists │      │ Messag │    │ Reviews │
       └───────┘      └───┬────┘    └─────────┘
           │               │
    ┌─────▼─────┐  ┌──────▼────────┐
    │ Category  │  │ Conversation  │
    └───────────┘  │ (buyer-seller)│
                   └───────────────┘

       ┌──────────────┐
       │ SellerSub   │
       │ (subscription)
       └──────────────┘

       ┌──────────────┐
       │ Payment      │
       │ (Stripe)     │
       └──────────────┘
```

---

## 🔐 Sécurité & Authentification

```
┌────────────────────────────────────────┐
│     AUTHENTICATION FLOW                 │
└────────────────────────────────────────┘

1. User envoie email/password
        ↓
2. Backend valide credentials
        ↓
3. JWT tokens créés
   ├─ access_token (24h)
   └─ refresh_token (30j)
        ↓
4. Tokens renvoyés au client
        ↓
5. Client stocke tokens
        ↓
6. Chaque requête inclut Authorization header
   Authorization: Bearer <access_token>
        ↓
7. Backend valide le token
        ↓
8. Requête exécutée (ou rejetée si non-autorisé)

┌─ Token Refresh ─┐
│ Si access expiré:
│ 1. Envoyer refresh_token
│ 2. Reçevoir nouveau access_token
│ 3. Continuer avec nouveau token
└─────────────────┘
```

---

## 💳 Intégration Stripe

```
┌─────────────────────────────────────────┐
│    PAYMENT FLOW WITH STRIPE             │
└─────────────────────────────────────────┘

Frontend                Backend              Stripe
  │                       │                    │
  │ Click "S'abonner"     │                    │
  ├──────────────────────>│                    │
  │                       │ Create Checkout    │
  │                       ├───────────────────>│
  │                       │<─── Checkout URL ──┤
  │<── Redirect URL ──────┤                    │
  │                       │                    │
  │ Paiement Carte        │                    │
  ├───────────────────────────────────────────>│
  │                       │ Webhook: paid      │
  │                       │<───────────────────┤
  │                       │                    │
  │                       │ Créer Subscription │
  │                       │ Email confirmation │
  │                       │                    │
  │<─── Succès Page ──────┤                    │
  │                       │                    │
  │ Dashboard actif       │                    │
```

---

## 📈 Exemple Publication Annonce

```
SELLER DASHBOARD
    │
    ├─ Créer nouvelle annonce
    │      │
    │      ├─ Titre: "iPhone 14 Pro"
    │      ├─ Description: "Excellent condition..."
    │      ├─ Prix: 899.00€
    │      ├─ Catégorie: Électronique
    │      ├─ Type: Produit
    │      ├─ Localisation: Paris
    │      ├─ Stock: 1
    │      └─ Photos: [upload 1,2,3]
    │
    ├─ Sauvegarder (status=draft)
    │
    ├─ Publier (status=pending)
    │      │
    │      └─ Modération
    │         Admin review
    │         ├─ Approuvé ✓
    │         └─ Status=published
    │
    ├─ Visible sur marketplace
    │      │
    │      ├─ Apparait dans recherche
    │      ├─ Statistiques vues en temps réel
    │      ├─ Messages des acheteurs
    │      └─ Avis après vente
    │
    └─ Options premium (Pro plan)
       ├─ Booster annonce (+3€)
       │   └─ Plus visible 7 jours
       └─ Épingler
           └─ Apparait en top
```

---

## 🚀 CI/CD Pipeline (Déploiement)

```
┌──────────┐
│   Code   │ Push to main branch
│  Change  │
└────┬─────┘
     │
     ├─ Git Hook
     │
     ├─ Tests locaux
     │
     └─ Push GitHub
        │
        ├─ GitHub Actions (optionnel)
        │
        ├─ Railway/Render détecte
        │
        ├─ Build
        │  ├─ pip install requirements
        │  ├─ collectstatic
        │  └─ migrate
        │
        ├─ Tests
        │
        ├─ Deploy
        │  ├─ Start gunicorn
        │  ├─ Nginx proxy
        │  └─ SSL/HTTPS
        │
        └─ Live! 🎉
           https://vyzio.com
```

---

## 📱 Statut des Annonces

```
┌─────────────────────────────────────────┐
│         LISTING STATUS FLOW             │
└─────────────────────────────────────────┘

draft
 │
 ├─ Seller crée, pas encore publié
 │
 ├─> publish
 │   │
 │   └─> pending
 │       │
 │       ├─ Admin modère
 │       │
 │       ├─> published ✓
 │       │   │
 │       │   ├─ Visible publiquement
 │       │   │
 │       │   ├─> sold
 │       │   │   └─ Vendu (optionnel)
 │       │   │
 │       │   └─> archived
 │       │       └─ Plus disponible
 │       │
 │       └─> rejected ✗
 │           └─ Contenu inadapté
 │
 └─> archived
     └─ Seller archive avant publication
```

---

## 🔄 Cycle de Vie Abonnement

```
┌────────────────────────────────┐
│  SUBSCRIPTION LIFECYCLE        │
└────────────────────────────────┘

FREE
 │
 ├─ Seller sans abonnement
 │
 ├─> BASIC (9.99€/month)
 │   ├─ Paiement via Stripe
 │   ├─ Stripe Sub ID créé
 │   ├─ Webhook: subscription.created
 │   │
 │   ├─ ACTIVE (30 jours)
 │   │  ├─ 5 annonces disponibles
 │   │  ├─ Messages acheteurs
 │   │  └─ Avis clients
 │   │
 │   ├─ Renouvellement auto
 │   │  └─ Webhook: invoice.paid
 │   │
 │   ├─> CANCELLED
 │   │   └─ Seller ou système
 │   │
 │   └─> EXPIRED
 │       └─ Plus de premium
 │
 └─> PRO (29.99€/month)
     ├─ Annonces ILLIMITÉES
     ├─ 2 Boosts/mois
     ├─ Featured listings
     └─ Analytics avancées
```

---

## 🎯 KPIs & Métriques

```
USER METRICS
├─ Total Users
├─ Acheteurs (role=buyer)
├─ Vendeurs (role=seller)
├─ Vendeurs Pro (subscription=pro)
└─ Utilisateurs actifs (last 30 days)

LISTING METRICS
├─ Total listings
├─ Published listings
├─ Pending modération
├─ Views per listing
├─ Average favorites per listing
└─ Boost conversions

PAYMENT METRICS
├─ MRR (Monthly Recurring Revenue)
├─ Paiements completés
├─ Taux de conversion subscription
├─ Revenu total
└─ Refunds

ENGAGEMENT METRICS
├─ Messages par jour
├─ Taux de réponse vendeur
├─ Average rating (étoiles)
├─ Avis soumis
└─ Conversations activées
```

---

## 📚 Documentation Map

```
START HERE
    │
    ├─ QUICK_START.md ──── 5-minute setup
    │
    ├─ README.md ────────── Full overview
    │
    ├─ PROJECT_SUMMARY.md ─ Executive summary
    │
    ├─ API_DOCUMENTATION ── Endpoints (avec exemples)
    │   ├─ Users
    │   ├─ Listings
    │   ├─ Messaging
    │   ├─ Payments
    │   ├─ Reviews
    │   └─ Admin
    │
    ├─ DEPLOYMENT.md ────── Production setup
    │   ├─ Railway
    │   ├─ Render
    │   └─ OVH/VPS
    │
    ├─ TROUBLESHOOTING.md ─ FAQ & problems
    │
    ├─ PROJECT_STRUCTURE ── File organization
    │
    └─ INDEX.md ─────────── Navigation guide
```

---

**Vyzio Ads - Marketplace Complete** 🚀

Version 1.0 | Décembre 2025 | Kenneth Sangli
