# 🔧 Troubleshooting & FAQ

## Installation & Setup

### ❌ "ModuleNotFoundError: No module named 'django'"

**Solution:**
```bash
# Assurez-vous que l'environnement virtuel est activé
venv\Scripts\activate.bat  # Windows
source venv/bin/activate   # Mac/Linux

# Réinstallez les dépendances
pip install -r requirements.txt
```

### ❌ "Port 8000 already in use"

**Solution:**
```bash
# Utiliser un autre port
python manage.py runserver 8001

# Ou trouver le processus qui l'utilise
# Windows:
netstat -ano | findstr :8000

# Mac/Linux:
lsof -i :8000
```

### ❌ "No module named 'psycopg2'"

**Solution:**
```bash
# Installer le driver PostgreSQL
pip install psycopg2-binary

# ou (si erreur de compilation)
pip install --upgrade pip
pip install psycopg2-binary --force-reinstall
```

---

## Base de Données

### ❌ "django.db.utils.OperationalError: could not connect to server"

**Solution:**
```bash
# Vérifier que PostgreSQL est lancé
# Windows (PowerShell):
Get-Service PostgreSQL

# Mac:
brew services list

# Linux:
sudo service postgresql status

# Ou utiliser SQLite pour développement
# Modifier .env:
DB_ENGINE=django.db.backends.sqlite3
```

### ❌ "database does not exist"

**Solution:**
```bash
# Créer la base de données
createdb vyzio_ads_db

# Ou via psql
psql -U postgres
CREATE DATABASE vyzio_ads_db;
\q
```

### ❌ "relation ... does not exist"

**Solution:**
```bash
# Réappliquer les migrations
python manage.py migrate zero apps.listings
python manage.py migrate apps.listings

# Ou réinitialiser complètement
python manage.py flush  # Attention: efface les données!
python manage.py migrate
```

---

## Authentification & JWT

### ❌ "Invalid token" / "Token is blacklisted"

**Solution:**
```bash
# Utiliser le endpoint de login pour obtenir un nouveau token
POST /api/users/login/
{
  "email": "user@example.com",
  "password": "password123"
}

# Assurez-vous que le header est correct:
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### ❌ "Authentication credentials were not provided"

**Solution:**
```bash
# Vous devez être authentifié pour cet endpoint
# Ajouter le header Authorization
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/users/me/
```

---

## Uploads & Fichiers

### ❌ "The submitted file is empty"

**Solution:**
```bash
# Vérifier la taille maximale dans settings.py
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Ou dans la requête:
Content-Length ne doit pas dépasser 5MB
```

### ❌ "CSRF verification failed"

**Solution:**
```bash
# Ajouter le header CSRF
POST /api/listings/
X-CSRFToken: <token>
Content-Type: application/json

# Ou utiliser Django REST Framework qui gère automatiquement
```

### ❌ Cloudinary images not uploading

**Solution:**
```python
# Vérifier le .env
CLOUDINARY_CLOUD_NAME=your_actual_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Tester la connexion
python manage.py shell
>>> import cloudinary
>>> cloudinary.config()
```

---

## Paiements Stripe

### ❌ "No such object: cs_test_..."

**Solution:**
```bash
# Utiliser des clés de test valides
STRIPE_PUBLIC_KEY=pk_test_xxxxx
STRIPE_SECRET_KEY=sk_test_xxxxx

# Obtenir les clés sur dashboard.stripe.com
# (Test mode activé)
```

### ❌ "Webhook not working"

**Solution:**
```bash
# 1. Vérifier la signature du webhook
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# 2. Dans Stripe Dashboard:
# - Developers → Webhooks
# - Ajouter endpoint: https://your-domain.com/api/payments/webhook/
# - Sélectionner events à écouter

# 3. Tester avec Stripe CLI:
stripe listen --forward-to localhost:8000/api/payments/webhook/
stripe trigger payment_intent.succeeded
```

### ❌ "Webhook signature verification failed"

**Solution:**
```python
# Vérifier que STRIPE_WEBHOOK_SECRET est correct
# C'est un secret différent de STRIPE_SECRET_KEY

# Chercher "whsec_" dans Stripe Dashboard
```

---

## Performance & Cache

### ❌ Site lent après quelques heures

**Solution:**
```bash
# Vérifier Redis
redis-cli ping
# Doit répondre "PONG"

# Vider le cache
redis-cli FLUSHALL

# Ou dans Python
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

### ❌ "Connection refused" pour Redis

**Solution:**
```bash
# Démarrer Redis
# Windows: redis-server
# Mac: brew services start redis
# Linux: sudo systemctl start redis-server

# Vérifier port
redis-cli -p 6379 ping
```

---

## API & Requêtes

### ❌ CORS error: "Access to XMLHttpRequest blocked"

**Solution:**
```python
# Vérifier settings.py
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # Frontend URL
    'http://127.0.0.1:3000',
]

# Ajouter votre domaine si en production
CORS_ALLOWED_ORIGINS = [
    'https://my-frontend.vercel.app',
]
```

### ❌ "404 Not Found" sur un endpoint correct

**Solution:**
```bash
# Vérifier l'URL
# Correct: /api/listings/listings/
# Incorrect: /api/listings/ (c'est juste un include)

# Lister tous les URLs disponibles
python manage.py show_urls
```

### ❌ "Method Not Allowed" (405)

**Solution:**
```bash
# Vérifier la méthode HTTP
# GET /listings/123/ ✅
# POST /listings/123/ ❌ (use PATCH)

# Consulter API_DOCUMENTATION.md
```

---

## Sécurité

### ❌ "DEBUG mode in production"

**Solution:**
```python
# .env
DEBUG=False

# Puis redémarrer
python manage.py collectstatic --noinput
```

### ❌ "SECRET_KEY appears in error page"

**Solution:**
```bash
# Générer une nouvelle clé
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())

# Mettre dans .env
SECRET_KEY=<nouvelle-clé>

# Redémarrer
```

### ❌ CSRF token mismatch

**Solution:**
```bash
# Inclure token CSRF
POST /api/listings/
X-CSRFToken: <csrf_token>
Content-Type: application/json

# Django REST Framework l'ajoute automatiquement
```

---

## Déploiement

### ❌ Erreur lors du push vers Railway/Render

**Solution:**
```bash
# 1. Vérifier Procfile existe
ls Procfile

# 2. Vérifier requirements.txt
pip freeze > requirements.txt

# 3. Vérifier build command
# Dans Railway/Render settings

# 4. Lire les logs du build
# Dashboard → Logs → Build
```

### ❌ Static files not serving

**Solution:**
```bash
# Collecter les fichiers statiques
python manage.py collectstatic --noinput --clear

# Vérifier STATIC_ROOT
ls staticfiles/

# En Nginx:
location /static/ {
    alias /path/to/staticfiles/;
}
```

### ❌ "ALLOWED_HOSTS" error en production

**Solution:**
```python
# .env
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Ou settings.py
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
```

---

## Emails

### ❌ Emails not sending

**Solution:**
```python
# .env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password  # Pas le vrai mot de passe!

# Gmail: Générer un "App Password" en 2FA
```

### ❌ "SMTPAuthenticationError"

**Solution:**
```bash
# Vérifier les identifiants
# Gmail: créer un "App Password"
# https://myaccount.google.com/apppasswords

# Test
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('test', 'test', 'from@gmail.com', ['to@example.com'])
```

---

## Logs & Debugging

### Activer les logs

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'DEBUG',
    },
}
```

### Déboguer une requête

```bash
python manage.py shell
>>> from apps.listings.models import Listing
>>> Listing.objects.all().count()
>>> l = Listing.objects.first()
>>> print(l.__dict__)
```

---

## Besoin d'aide supplémentaire?

- 📖 Documentation Django: https://docs.djangoproject.com
- 📖 Django REST Framework: https://www.django-rest-framework.org
- 🐛 GitHub Issues: https://github.com/yourusername/vyzio_ads/issues
- 💬 Django Discord: https://discord.gg/djangoproject

---

**Dernière mise à jour: Janvier 2025**
