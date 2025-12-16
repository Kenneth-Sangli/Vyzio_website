# 📚 Documentation API Vyzio Ads

Base URL: `http://localhost:8000/api`

## 🔐 Authentification

Tous les endpoints protégés nécessitent un token JWT dans l'header:

```
Authorization: Bearer <access_token>
```

### Obtenir un token

```http
POST /users/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {...}
}
```

### Rafraîchir le token

```http
POST /token/refresh/
Content-Type: application/json

{
  "refresh": "<refresh_token>"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## 👥 Utilisateurs

### Créer un compte

```http
POST /users/
Content-Type: application/json

{
  "email": "newuser@example.com",
  "username": "newuser",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePass123!",
  "password2": "SecurePass123!",
  "role": "buyer"  # ou "seller", "professional"
}

Response: 201 Created
{
  "id": "uuid",
  "email": "newuser@example.com",
  "username": "newuser",
  "role": "buyer"
}
```

### Obtenir le profil actuel

```http
GET /users/me/
Authorization: Bearer <token>

Response:
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "user",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+33612345678",
  "avatar": "https://...",
  "bio": "Bienvenue sur mon profil",
  "location": "Paris, France",
  "role": "seller",
  "shop_name": "Mon Magasin",
  "is_verified": true,
  "avg_rating": 4.5,
  "total_reviews": 12,
  "created_at": "2025-01-01T10:00:00Z",
  "seller_subscription": {
    "subscription_type": "pro",
    "is_active": true,
    "started_at": "2025-01-01T10:00:00Z",
    "ends_at": "2026-01-01T10:00:00Z",
    "listings_count": 5,
    "max_listings": -1,
    "can_boost": true,
    "boost_count": 2
  }
}
```

### Mettre à jour le profil

```http
PATCH /users/me/
Authorization: Bearer <token>
Content-Type: application/json

{
  "bio": "Nouveau texte bio",
  "phone": "+33698765432",
  "location": "Lyon, France"
}

Response: 200 OK
```

### Obtenir les statistiques vendeur

```http
GET /users/seller_stats/
Authorization: Bearer <token>

Response:
{
  "listings_count": 12,
  "avg_rating": 4.8,
  "total_reviews": 45,
  "subscription": {
    "subscription_type": "pro",
    "is_active": true
  }
}
```

---

## 📋 Annonces

### Lister les annonces

```http
GET /listings/listings/?page=1&limit=20&category=electronics&min_price=100&max_price=1000&location=Paris&search=iphone

Query Parameters:
- page: Numéro de page (default: 1)
- limit: Nombre par page (default: 20)
- category: Slug de catégorie
- min_price: Prix minimum
- max_price: Prix maximum
- location: Localisation
- search: Terme de recherche
- ordering: -created_at, price, -views_count

Response:
{
  "count": 150,
  "next": "http://.../listings/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "title": "iPhone 14 Pro",
      "slug": "iphone-14-pro",
      "price": "899.00",
      "location": "Paris",
      "listing_type": "product",
      "status": "published",
      "seller": {...},
      "category": {...},
      "primary_image": {...},
      "views_count": 245,
      "is_boosted": true,
      "created_at": "2025-01-01T10:00:00Z",
      "favorites_count": 15
    }
  ]
}
```

### Détail d'une annonce

```http
GET /listings/listings/{id}/
Authorization: Bearer <token> (optionnel)

Response:
{
  "id": "uuid",
  "title": "iPhone 14 Pro",
  "slug": "iphone-14-pro",
  "description": "Excellent condition, 256GB",
  "price": "899.00",
  "price_negotiable": true,
  "location": "Paris, 75001",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "listing_type": "product",
  "status": "published",
  "seller": {...},
  "category": {...},
  "images": [
    {
      "id": "img-id",
      "image": "https://...",
      "is_primary": true,
      "order": 0
    }
  ],
  "video": null,
  "stock": 1,
  "available": true,
  "views_count": 246,
  "is_boosted": true,
  "boost_end_date": "2025-01-15",
  "is_favorite": false,
  "created_at": "2025-01-01T10:00:00Z",
  "updated_at": "2025-01-05T15:30:00Z",
  "favorites_count": 15
}
```

Remarque: La première consultation incrémente le `views_count` automatiquement.

### Créer une annonce

```http
POST /listings/listings/
Authorization: Bearer <token>
Content-Type: multipart/form-data

{
  "title": "iPhone 14 Pro",
  "description": "Excellent condition, très peu utilisé",
  "price": "899.00",
  "price_negotiable": true,
  "location": "Paris",
  "listing_type": "product",
  "category": "uuid-category",
  "stock": 1,
  "available": true,
  "images": [file1, file2, file3]  # Multiple files
}

Response: 201 Created
{
  "id": "new-uuid",
  ...
}
```

### Modifier une annonce

```http
PATCH /listings/listings/{id}/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "iPhone 14 Pro - Updated Price",
  "price": "799.00"
}

Response: 200 OK
```

### Supprimer une annonce

```http
DELETE /listings/listings/{id}/
Authorization: Bearer <token>

Response: 204 No Content
```

### Mes annonces

```http
GET /listings/listings/my_listings/
Authorization: Bearer <token>

Response: [...]
```

### Ajouter/Retirer des favoris

```http
POST /listings/listings/{id}/toggle_favorite/
Authorization: Bearer <token>

Response:
{
  "id": "uuid",
  "listing": {...},
  "created_at": "2025-01-01T10:00:00Z"
}
```

### Booster une annonce

```http
POST /listings/listings/{id}/boost/
Authorization: Bearer <token>

Response:
{
  "status": "boosted"
}
```

Durée: 7 jours  
Consommation: 1 boost (dépend de l'abonnement)

### Annonces tendances

```http
GET /listings/listings/trending/

Response: [10 annonces les plus consultées]
```

### Catégories

```http
GET /listings/categories/

Response:
{
  "count": 6,
  "results": [
    {
      "id": "cat-uuid",
      "name": "Électronique",
      "slug": "electronique",
      "description": "Téléphones, ordinateurs...",
      "icon": "https://..."
    }
  ]
}
```

---

## 💬 Messagerie

### Lister les conversations

```http
GET /messages/conversations/
Authorization: Bearer <token>

Response:
{
  "count": 5,
  "results": [
    {
      "id": "conv-uuid",
      "buyer": {...},
      "seller": {...},
      "is_active": true,
      "last_message": {
        "id": "msg-uuid",
        "sender": {...},
        "content": "Dernière message...",
        "is_read": false,
        "created_at": "2025-01-05T15:30:00Z"
      },
      "unread_count": 2,
      "last_message_date": "2025-01-05T15:30:00Z"
    }
  ]
}
```

### Détail d'une conversation

```http
GET /messages/conversations/{id}/
Authorization: Bearer <token>

Response:
{
  "id": "conv-uuid",
  "buyer": {...},
  "seller": {...},
  "is_active": true,
  "messages": [
    {
      "id": "msg-id",
      "sender": {...},
      "content": "Bonjour, le produit est-il disponible?",
      "is_read": true,
      "created_at": "2025-01-01T10:00:00Z"
    }
  ],
  "created_at": "2025-01-01T09:00:00Z"
}
```

### Démarrer une conversation

```http
POST /messages/conversations/start_conversation/
Authorization: Bearer <token>
Content-Type: application/json

{
  "seller_id": "seller-uuid",
  "listing_id": "listing-uuid"  # optionnel
}

Response: 201 Created / 200 OK if exists
```

### Envoyer un message

```http
POST /messages/conversations/{id}/send_message/
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "Bonjour, le produit est toujours disponible?"
}

Response: 201 Created
```

### Marquer comme lu

```http
POST /messages/conversations/{id}/mark_read/
Authorization: Bearer <token>

Response: 200 OK
```

### Bloquer un utilisateur

```http
POST /messages/conversations/{id}/block_user/
Authorization: Bearer <token>

Response: 200 OK
```

### Signaler un utilisateur

```http
POST /messages/conversations/{id}/report_user/
Authorization: Bearer <token>
Content-Type: application/json

{
  "reason": "spam",  # spam, inappropriate, scam, offensive, other
  "description": "Cet utilisateur essaie d'arnaquer..."
}

Response: 201 Created
```

---

## 💳 Paiements

### Lister les plans

```http
GET /payments/plans/
Authorization: Bearer <token>

Response:
{
  "count": 2,
  "results": [
    {
      "id": "plan-uuid",
      "name": "Basic",
      "plan_type": "basic",
      "billing_cycle": "monthly",
      "price": "9.99",
      "max_listings": 5,
      "can_boost": false,
      "boost_count": 0,
      "featured": false,
      "description": "5 annonces par mois"
    },
    {
      "id": "plan-uuid",
      "name": "Pro",
      "plan_type": "pro",
      "billing_cycle": "monthly",
      "price": "29.99",
      "max_listings": -1,  # Illimité
      "can_boost": true,
      "boost_count": 2,
      "featured": false,
      "description": "Annonces illimitées + 2 boosts/mois"
    }
  ]
}
```

### Créer une session de paiement Stripe

```http
POST /payments/payments/create_checkout_session/
Authorization: Bearer <token>
Content-Type: application/json

{
  "plan_id": "plan-uuid",
  "coupon_code": "WELCOME2025"  # optionnel
}

Response:
{
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_test_..."
}
```

Redirigez l'utilisateur vers `checkout_url`.

### Historique des paiements

```http
GET /payments/payments/
Authorization: Bearer <token>

Response:
{
  "count": 3,
  "results": [
    {
      "id": "payment-uuid",
      "amount": "9.99",
      "currency": "EUR",
      "payment_type": "subscription",
      "status": "completed",
      "subscription": {...},
      "description": "Abonnement Basic",
      "created_at": "2025-01-01T10:00:00Z",
      "completed_at": "2025-01-01T10:05:00Z"
    }
  ]
}
```

---

## ⭐ Avis

### Lister les avis

```http
GET /reviews/?seller_id=seller-uuid

Response:
{
  "count": 5,
  "results": [
    {
      "id": "review-uuid",
      "reviewer": {...},
      "rating": 5,
      "comment": "Excellent vendeur, très rapide!",
      "photos": [
        {
          "id": "photo-uuid",
          "image": "https://..."
        }
      ],
      "seller_response": "Merci beaucoup!",
      "seller_response_date": "2025-01-02T10:00:00Z",
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

### Créer un avis

```http
POST /reviews/
Authorization: Bearer <token>
Content-Type: application/json

{
  "seller_id": "seller-uuid",
  "rating": 5,
  "comment": "Super qualité, livraison rapide"
}

Response: 201 Created
```

### Répondre à un avis (vendeur)

```http
POST /reviews/{id}/add_response/
Authorization: Bearer <token>
Content-Type: application/json

{
  "response": "Merci pour cet avis!"
}

Response: 200 OK
```

### Avis d'un vendeur

```http
GET /reviews/seller_reviews/?seller_id=seller-uuid

Response:
{
  "reviews": [...],
  "count": 15,
  "average_rating": 4.7
}
```

---

## 🔐 Admin

Tous les endpoints admin nécessitent `is_staff=true` et `is_superuser=true`.

### Statistiques du tableau de bord

```http
GET /admin/dashboard-stats/
Authorization: Bearer <admin_token>

Response:
{
  "users_count": 250,
  "sellers_count": 45,
  "listings_count": 1200,
  "published_listings": 1150,
  "pending_listings": 50,
  "total_revenue": "25000.00",
  "pending_reports": 3
}
```

### Lister les utilisateurs

```http
GET /admin/users/?role=seller&is_banned=false
Authorization: Bearer <admin_token>

Response:
{
  "count": 45,
  "users": [
    {
      "id": "user-uuid",
      "email": "seller@example.com",
      "role": "seller",
      "is_banned": false,
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

### Bannir un utilisateur

```http
POST /admin/ban-user/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "user_id": "user-uuid",
  "reason": "Comportement abusif"
}

Response: 200 OK
```

### Débannir un utilisateur

```http
POST /admin/unban-user/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "user_id": "user-uuid"
}

Response: 200 OK
```

### Annonces en attente

```http
GET /admin/pending-listings/
Authorization: Bearer <admin_token>

Response:
{
  "count": 50,
  "listings": [...]
}
```

### Approuver une annonce

```http
POST /admin/approve-listing/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "listing_id": "listing-uuid"
}

Response: 200 OK
```

### Rejeter une annonce

```http
POST /admin/reject-listing/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "listing_id": "listing-uuid",
  "reason": "Contenu inapproprié"
}

Response: 200 OK
```

### Signalements

```http
GET /admin/reports/?is_resolved=false
Authorization: Bearer <admin_token>

Response:
{
  "count": 3,
  "reports": [...]
}
```

### Résoudre un signalement

```http
POST /admin/resolve-report/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "report_id": "report-uuid",
  "action": "ban_user"
}

Response: 200 OK
```

---

## 🔄 Codes de réponse HTTP

| Code | Signification |
|------|---|
| 200 | OK - Succès |
| 201 | Created - Ressource créée |
| 204 | No Content - Succès (pas de contenu) |
| 400 | Bad Request - Erreur de requête |
| 401 | Unauthorized - Authentification requise |
| 403 | Forbidden - Accès refusé |
| 404 | Not Found - Ressource non trouvée |
| 500 | Server Error - Erreur serveur |

---

## 📋 Filtres et Recherche

Tous les endpoints list supportent:

```
?search=terme             # Recherche par mots-clés
?ordering=-created_at     # Tri (- pour décroissant)
?page=2                   # Pagination
?limit=50                 # Nombre de résultats
```

---

Dernière mise à jour: Janvier 2025
