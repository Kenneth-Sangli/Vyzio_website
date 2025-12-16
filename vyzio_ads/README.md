# Vyzio Ads - Marketplace d'annonces

Plateforme web de publication d'annonces (produits, services, locations, prestations) inspirée de Leboncoin.

## ✨ Fonctionnalités

### Gestion des Utilisateurs
- ✅ Authentification JWT
- ✅ Profils utilisateurs (Acheteur, Vendeur, Vendeur Pro)
- ✅ Abonnements vendeurs (Basic, Pro)
- ✅ Système de notation et avis
- ✅ Vérification d'email

### Gestion des Annonces
- ✅ Création/Modification/Suppression d'annonces
- ✅ Support multiple images/vidéos
- ✅ Catégories d'annonces
- ✅ Statuts : Brouillon, Publié, Vendu, Archivé
- ✅ Boost premium (mise en avant)
- ✅ Système de favoris
- ✅ Recherche et filtres avancés (prix, localisation, catégorie, type)
- ✅ Suivi des vues et statistiques

### Messagerie
- ✅ Conversation vendeur-acheteur
- ✅ Historique des messages
- ✅ Notification de messages lus
- ✅ Blocage d'utilisateurs
- ✅ Système de signalement

### Paiements
- ✅ Intégration Stripe
- ✅ Abonnements mensuels/annuels
- ✅ Boost d'annonces payants
- ✅ Gestion des factures
- ✅ Coupons de réduction

### Avis et Réputation
- ✅ Notation vendeur (1-5 étoiles)
- ✅ Commentaires et photos
- ✅ Réponse du vendeur aux avis
- ✅ Calcul automatique de moyenne

### Modération & Admin
- ✅ Tableau de bord administrateur
- ✅ Approbation des annonces
- ✅ Gestion des signalements
- ✅ Suspension de comptes
- ✅ Statistiques globales

## 🛠️ Technologies

- **Backend**: Django 4.2 + Django REST Framework
- **Base de données**: PostgreSQL
- **Cache**: Redis
- **Stockage fichiers**: Cloudinary
- **Paiements**: Stripe
- **Queue**: Celery
- **Deployment**: Docker, Gunicorn

## 📦 Installation

### Prérequis
- Python 3.11+
- PostgreSQL 13+
- Redis
- Compte Stripe (optionnel)
- Compte Cloudinary (optionnel)

### Setup Local

1. **Cloner et installer**
```bash
cd vyzio_ads
pip install -r requirements.txt
```

2. **Configurer l'environnement**
```bash
cp .env.example .env
# Éditer .env avec vos variables
```

3. **Créer la base de données**
```bash
python manage.py migrate
python manage.py createsuperuser
```

4. **Démarrer le serveur**
```bash
python manage.py runserver
```

### Avec Docker

```bash
docker-compose up -d
```

Accédez à `http://localhost:8000`

## 📚 API Endpoints

### Authentification
- `POST /api/users/` - Créer compte
- `POST /api/users/login/` - Login
- `GET /api/users/me/` - Profil courant

### Annonces
- `GET /api/listings/` - Lister annonces
- `GET /api/listings/{id}/` - Détail annonce
- `POST /api/listings/` - Créer annonce
- `PUT /api/listings/{id}/` - Modifier annonce
- `DELETE /api/listings/{id}/` - Supprimer annonce
- `GET /api/listings/my_listings/` - Mes annonces
- `POST /api/listings/{id}/toggle_favorite/` - Favori

### Messagerie
- `GET /api/messages/conversations/` - Conversations
- `POST /api/messages/conversations/start_conversation/` - Nouvelle conversation
- `POST /api/messages/conversations/{id}/send_message/` - Envoyer message

### Paiements
- `GET /api/payments/plans/` - Plans d'abonnement
- `POST /api/payments/payments/create_checkout_session/` - Créer session Stripe

### Avis
- `GET /api/reviews/` - Lister avis
- `POST /api/reviews/` - Créer avis
- `GET /api/reviews/seller_reviews/` - Avis vendeur

### Admin
- `GET /api/admin/dashboard-stats/` - Statistiques
- `GET /api/admin/users/` - Lister utilisateurs
- `POST /api/admin/ban-user/` - Bannir utilisateur
- `GET /api/admin/pending-listings/` - Annonces en attente

## 🔐 Sécurité

- JWT pour l'authentification
- CORS configuré
- Protection CSRF
- Validation des données
- Hachage des mots de passe (bcrypt)
- Permissions par rôle (Buyer/Seller/Admin)

## 📝 Variables d'environnement

```
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=vyzio_ads_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Stripe
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Frontend
FRONTEND_URL=http://localhost:3000

# Redis
REDIS_URL=redis://localhost:6379/0
```

## 🚀 Déploiement

### Railway / Render
- Connecter le repo Git
- Configurer variables d'environnement
- Ajouter PostgreSQL addon
- Déployer

### OVH / VPS
- Cloner le repo
- Installer Docker
- `docker-compose up -d`

## 📊 Roadmap

- [ ] Frontend Next.js
- [ ] WebSockets pour messagerie temps réel
- [ ] Notifications email automatisées
- [ ] SMS notifications
- [ ] Analytics avancées
- [ ] Mobile app
- [ ] API v2 avec GraphQL
- [ ] Système de commission
- [ ] Vérification KYC vendeurs pro
- [ ] Escrow pour transactions

## 📄 Licence

MIT License

## 👤 Auteur

Kenneth Sangli - [GitHub](https://github.com/Kenneth-Sangli)

## 💬 Support

Pour toute question ou issue: ouvrir une issue GitHub

---

**Version**: 1.0.0  
**Dernière mise à jour**: Décembre 2025
