# 🚀 Guide de Démarrage Rapide - Vyzio Ads

## Installation locale (Windows)

### 1. Prérequis
- Python 3.11+ installez depuis [python.org](https://www.python.org)
- PostgreSQL 13+ (optionnel, SQLite par défaut)
- Git

### 2. Installation du projet

```bash
# 1. Naviguer dans le dossier
cd vyzio_ads

# 2. Exécuter le script setup
setup.bat

# 3. Éditer le fichier .env
# Ouvrir .env et configurer vos variables si nécessaire
```

### 3. Lancer le serveur

```bash
# Activer l'environnement virtuel
venv\Scripts\activate.bat

# Démarrer le serveur
python manage.py runserver
```

Le serveur démarre sur `http://localhost:8000`

## Accès à l'administration

- **URL**: http://localhost:8000/admin/
- **Identifiant**: admin
- **Mot de passe**: Celui créé lors du setup

## Structure du projet

```
vyzio_ads/
├── config/              # Configuration Django
├── apps/
│   ├── users/          # Gestion des utilisateurs
│   ├── listings/       # Annonces
│   ├── messaging/      # Messagerie
│   ├── payments/       # Paiements Stripe
│   ├── reviews/        # Avis
│   └── admin_panel/    # Administration
├── static/             # Fichiers statiques
├── media/              # Fichiers upload
└── manage.py
```

## Configuration Stripe (Optionnel)

Pour activer les paiements Stripe:

1. Créer compte sur [stripe.com](https://stripe.com)
2. Récupérer vos clés API
3. Éditer `.env`:
   ```
   STRIPE_PUBLIC_KEY=pk_test_...
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

## Configuration Cloudinary (Optionnel)

Pour le stockage cloud des images:

1. Créer compte sur [cloudinary.com](https://cloudinary.com)
2. Récupérer vos identifiants
3. Éditer `.env`:
   ```
   CLOUDINARY_CLOUD_NAME=...
   CLOUDINARY_API_KEY=...
   CLOUDINARY_API_SECRET=...
   ```

## Commandes utiles

```bash
# Créer un superutilisateur (admin)
python manage.py createsuperuser

# Charger les données d'exemple
python manage.py load_fixtures

# Faire les migrations
python manage.py makemigrations
python manage.py migrate

# Lancer les tests
python manage.py test

# Générer les fichiers statiques
python manage.py collectstatic
```

## Utilisation avec Docker

```bash
# Démarrer tous les services
docker-compose up -d

# Logs
docker-compose logs -f web

# Arrêter
docker-compose down
```

## API Endpoints Principaux

### 📝 Authentification
```
POST   /api/users/                    # Créer compte
POST   /api/users/login/               # Se connecter
GET    /api/users/me/                  # Profil actuel
```

### 📋 Annonces
```
GET    /api/listings/                  # Lister (avec filtres)
GET    /api/listings/{id}/             # Détail
POST   /api/listings/                  # Créer
PUT    /api/listings/{id}/             # Modifier
DELETE /api/listings/{id}/             # Supprimer
GET    /api/listings/trending/         # Tendances
```

### 💬 Messagerie
```
GET    /api/messages/conversations/    # Mes conversations
POST   /api/messages/conversations/    # Nouvelle conversation
POST   /api/messages/conversations/{id}/send_message/  # Envoyer
```

### 💳 Paiements
```
GET    /api/payments/plans/            # Plans disponibles
POST   /api/payments/payments/create_checkout_session/  # Paiement
```

### ⭐ Avis
```
GET    /api/reviews/                   # Lister avis
POST   /api/reviews/                   # Créer avis
```

## Troubleshooting

### Port 8000 déjà utilisé
```bash
# Utiliser un autre port
python manage.py runserver 8001
```

### Erreur de base de données
```bash
# Réinitialiser la DB
python manage.py migrate zero apps.users
python manage.py migrate
```

### Problèmes d'authentification JWT
- Vérifier que `JWT_SECRET_KEY` est dans `.env`
- Vérifier le token dans l'header: `Authorization: Bearer <token>`

## Prochaines étapes

1. ✅ Frontend avec Next.js
2. ✅ Notifications email
3. ✅ WebSockets pour messagerie temps réel
4. ✅ Mobile app
5. ✅ Déploiement production

## Support

Pour toute question:
- Ouvrir une issue GitHub
- Consulter la documentation Django: https://docs.djangoproject.com
- Consulter la documentation DRF: https://www.django-rest-framework.org

---

**Bonne chance avec vyzio-ads! 🎉**
