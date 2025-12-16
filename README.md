# 🛒 Vyzio - Marketplace d'Annonces

<div align="center">

![Vyzio Logo](https://via.placeholder.com/200x80?text=Vyzio)

**Plateforme web de publication d'annonces moderne et performante**

[![Django](https://img.shields.io/badge/Django-6.0-green.svg)](https://www.djangoproject.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Demo](https://vyzio.com) · [Documentation](docs/) · [Report Bug](issues) · [Request Feature](issues)

</div>

---

## 📋 Table des matières

- [À propos](#-à-propos)
- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Démarrage](#-démarrage)
- [API Documentation](#-api-documentation)
- [Tests](#-tests)
- [Déploiement](#-déploiement)
- [Contribution](#-contribution)
- [Licence](#-licence)

---

## 🎯 À propos

Vyzio est une marketplace d'annonces inspirée de Leboncoin, permettant aux utilisateurs de :
- **Vendre** : Publier des annonces de produits, services ou locations
- **Acheter** : Rechercher et contacter des vendeurs
- **Communiquer** : Messagerie sécurisée en temps réel
- **Évaluer** : Système de notation et d'avis

### Public cible
- Vendeurs particuliers
- Vendeurs professionnels  
- Acheteurs occasionnels
- Utilisateurs cherchant des services locaux

---

## ✨ Fonctionnalités

### 👤 Gestion des Utilisateurs
- ✅ Authentification JWT sécurisée
- ✅ Profils utilisateurs (Acheteur, Vendeur, Pro)
- ✅ Vérification email
- ✅ Gestion des abonnements (Free, Basic, Pro)
- ✅ Système de réputation et badges

### 📦 Gestion des Annonces
- ✅ CRUD complet avec images multiples
- ✅ Catégories et sous-catégories
- ✅ Recherche full-text PostgreSQL
- ✅ Filtres avancés (prix, localisation, état)
- ✅ Système de boost premium
- ✅ Favoris utilisateur

### 💬 Messagerie
- ✅ Conversations temps réel (WebSocket)
- ✅ Historique des messages
- ✅ Notifications email
- ✅ Blocage utilisateurs
- ✅ Signalement de contenu

### 💳 Paiements
- ✅ Intégration Stripe complète
- ✅ Abonnements mensuels/annuels
- ✅ Paiement par annonce
- ✅ Boost d'annonces payant
- ✅ Gestion des factures

### ⭐ Avis et Réputation
- ✅ Notation 1-5 étoiles
- ✅ Commentaires avec photos
- ✅ Réponses des vendeurs
- ✅ Calcul automatique de moyenne

### 🛡️ Administration
- ✅ Dashboard admin complet
- ✅ Modération des annonces
- ✅ Gestion des signalements
- ✅ Statistiques globales
- ✅ Suspension de comptes

---

## 🏗️ Architecture

```
vyzio_website/
├── vyzio_ads/                 # Backend Django
│   ├── apps/
│   │   ├── users/             # Authentification & profils
│   │   ├── listings/          # Annonces & catégories
│   │   ├── messaging/         # Messagerie temps réel
│   │   ├── payments/          # Stripe & abonnements
│   │   ├── reviews/           # Avis & réputation
│   │   ├── analytics/         # Statistiques
│   │   └── admin_panel/       # Back-office
│   ├── config/
│   │   ├── settings/          # Settings modulaires
│   │   ├── urls.py
│   │   └── asgi.py            # WebSocket support
│   └── manage.py
│
├── frontend/                   # Frontend Next.js
│   ├── src/
│   │   ├── app/               # Pages (App Router)
│   │   ├── components/        # Composants React
│   │   ├── lib/               # API & utils
│   │   ├── stores/            # État global (Zustand)
│   │   └── hooks/             # Hooks personnalisés
│   └── package.json
│
└── docs/                       # Documentation
```

### Stack Technique

| Composant | Technologie |
|-----------|-------------|
| Backend | Django 6.0 + DRF |
| Frontend | Next.js 14 + TypeScript |
| Base de données | PostgreSQL |
| Cache | Redis |
| WebSocket | Django Channels |
| Paiements | Stripe |
| Stockage | Cloudinary |
| CI/CD | GitHub Actions |
| Déploiement | Render / Docker |

---

## 🚀 Installation

### Prérequis

- Python 3.11+
- Node.js 18+
- PostgreSQL 13+ (optionnel, SQLite en dev)
- Redis (optionnel, pour WebSocket/cache)

### Backend

```bash
# Cloner le repo
git clone https://github.com/Kenneth-Sangli/Vyzio_website.git
cd Vyzio_website/vyzio_ads

# Environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Dépendances
pip install -r requirements.txt

# Pre-commit hooks
pre-commit install

# Variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs

# Migrations
python manage.py migrate

# Créer superuser
python manage.py createsuperuser
```

### Frontend

```bash
cd frontend

# Dépendances
npm install

# Variables d'environnement
cp .env.local.example .env.local
# Éditer .env.local avec vos valeurs
```

---

## ⚙️ Configuration

### Variables d'environnement Backend (.env)

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3
# DATABASE_URL=postgres://user:pass@localhost:5432/vyzio

# Redis (optionnel)
REDIS_URL=redis://localhost:6379

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-app-password

# Stripe
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Cloudinary
CLOUDINARY_CLOUD_NAME=xxx
CLOUDINARY_API_KEY=xxx
CLOUDINARY_API_SECRET=xxx
```

### Variables d'environnement Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_xxx
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

---

## 🎮 Démarrage

### Mode développement

**Terminal 1 - Backend:**
```bash
cd vyzio_ads
python manage.py runserver 0.0.0.0:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Accès:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/
- Admin Django: http://localhost:8000/admin/

### Avec Docker

```bash
docker-compose up -d
```

---

## 📚 API Documentation

### Endpoints principaux

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/auth/register/` | Inscription |
| POST | `/api/auth/login/` | Connexion |
| GET | `/api/auth/me/` | Profil utilisateur |
| GET | `/api/listings/` | Liste des annonces |
| POST | `/api/listings/` | Créer une annonce |
| GET | `/api/listings/{id}/` | Détail annonce |
| GET | `/api/messages/conversations/` | Conversations |
| POST | `/api/payments/create-subscription-session/` | Abonnement |

Documentation complète: [API_DOCUMENTATION.md](vyzio_ads/API_DOCUMENTATION.md)

---

## 🧪 Tests

### Backend

```bash
cd vyzio_ads

# Tous les tests
pytest

# Avec couverture
pytest --cov=apps --cov-report=html

# Tests spécifiques
pytest apps/users/tests/ -v
```

### Frontend

```bash
cd frontend

# Tests unitaires
npm run test

# Tests E2E
npm run test:e2e
```

---

## 🚢 Déploiement

### Render (Recommandé)

1. Connecter le repo GitHub à Render
2. Le fichier `render.yaml` configure automatiquement:
   - Web service (Django + Gunicorn)
   - PostgreSQL
   - Redis

### Docker Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Documentation détaillée: [DEPLOYMENT.md](vyzio_ads/DEPLOYMENT.md)

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Consultez notre [Guide de Contribution](vyzio_ads/CONTRIBUTING.md).

### Workflow

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amazing-feature`)
3. Commit (`git commit -m 'feat: add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

Voir [BRANCHING_STRATEGY.md](vyzio_ads/BRANCHING_STRATEGY.md) pour notre stratégie de branches.

---

## 📄 Licence

Distribué sous la licence MIT. Voir `LICENSE` pour plus d'informations.

---

## 👥 Équipe

- **Kenneth Sangli** - *Développeur Principal* - [@Kenneth-Sangli](https://github.com/Kenneth-Sangli)

---

## 🙏 Remerciements

- [Django](https://www.djangoproject.com/)
- [Next.js](https://nextjs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Stripe](https://stripe.com/)
- [Lucide Icons](https://lucide.dev/)

---

<div align="center">

**[⬆ Retour en haut](#-vyzio---marketplace-dannonces)**

Made with ❤️ by Kenneth Sangli

</div>
