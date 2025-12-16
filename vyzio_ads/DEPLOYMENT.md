# 🚀 Guide de Déploiement Vyzio Ads

## Option 1: Railway.app (Recommandé - Le Plus Simple)

### 1. Créer un compte Railway
- Aller sur [railway.app](https://railway.app)
- S'inscrire avec GitHub

### 2. Créer un nouveau projet
- Cliquer "New Project"
- Sélectionner "GitHub Repo"
- Connecter votre repo vyzio_ads

### 3. Ajouter PostgreSQL
- "Add" → "PostgreSQL"
- Attendre que la base soit créée

### 4. Variables d'environnement
Dans Railway dashboard:
```
DEBUG=False
SECRET_KEY=generate-une-clé-sécurisée
ALLOWED_HOSTS=yourdomain.railway.app
DB_ENGINE=django.db.backends.postgresql
DB_NAME=railway
DB_USER=postgres
DB_PASSWORD=(auto-générée)
DB_HOST=(auto-générée)
DB_PORT=5432

STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...

FRONTEND_URL=https://yourdomain.vercel.app
```

### 5. Procfile
Créer un fichier `Procfile` à la racine:
```
web: gunicorn config.wsgi:application
release: python manage.py migrate
worker: celery -A config worker -l info
```

### 6. Déployer
- Railway détecte automatiquement
- Suivre les logs dans le dashboard
- Visiter yourdomain.railway.app

---

## Option 2: Render.com

### 1. Créer un compte
- [render.com](https://render.com)
- S'inscrire avec GitHub

### 2. Créer un service
- "New +"
- "Web Service"
- Connecter repo GitHub

### 3. Configuration
```
Name: vyzio-ads
Runtime: Python 3.11
Build Command: pip install -r requirements.txt && python manage.py migrate
Start Command: gunicorn config.wsgi:application
```

### 4. Ajouter PostgreSQL
- "New +"
- "PostgreSQL"
- Copier CONNECTION_STRING

### 5. Variables d'environnement
```
DEBUG=False
SECRET_KEY=...
DATABASE_URL=(from PostgreSQL)
STRIPE_*=...
CLOUDINARY_*=...
```

### 6. Déployer
- Render déploie automatiquement à chaque push

---

## Option 3: OVH / VPS Classique

### 1. Commander un VPS
- CPU: 2+ cores
- RAM: 2GB minimum
- Storage: 20GB+ SSD

### 2. Installation serveur
```bash
# SSH into your server
ssh root@your-vps-ip

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3.11 python3.11-venv python3-pip
apt install -y postgresql postgresql-contrib
apt install -y nginx redis-server
apt install -y git curl wget

# Create app user
useradd -m -s /bin/bash vyzio
su - vyzio
```

### 3. Cloner et setup projet
```bash
# Clone repository
git clone https://github.com/yourusername/vyzio_ads.git
cd vyzio_ads

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Create .env
cp .env.example .env
# Edit with your values
nano .env

# Run migrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 4. Configurer Gunicorn
Créer `/home/vyzio/vyzio_ads/gunicorn_config.py`:
```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 60
"""

### 5. Systemd Service
Créer `/etc/systemd/system/vyzio.service`:
```ini
[Unit]
Description=Vyzio Ads Gunicorn Service
After=network.target

[Service]
Type=notify
User=vyzio
WorkingDirectory=/home/vyzio/vyzio_ads
ExecStart=/home/vyzio/vyzio_ads/venv/bin/gunicorn \
          --config gunicorn_config.py \
          config.wsgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activer le service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable vyzio
sudo systemctl start vyzio
```

### 6. Configurer Nginx
Créer `/etc/nginx/sites-available/vyzio.com`:
```nginx
upstream vyzio_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name vyzio.com www.vyzio.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://vyzio_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/vyzio/vyzio_ads/staticfiles/;
    }

    location /media/ {
        alias /home/vyzio/vyzio_ads/media/;
    }
}
```

Activer le site:
```bash
sudo ln -s /etc/nginx/sites-available/vyzio.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. SSL avec Certbot
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d vyzio.com -d www.vyzio.com
```

### 8. Configurer Celery (optionnel)
```bash
# Celery service
/etc/systemd/system/vyzio-celery.service
```

---

## Vérifications post-déploiement

```bash
# Santé du serveur
curl https://your-domain.com/api/users/

# Administrateur
https://your-domain.com/admin/

# Webhooks Stripe
# Ajouter en production:
# https://your-domain.com/api/payments/webhook/
```

## Configuration DNS

Si utiliser votre domaine:
```
A record: your-server-ip
CNAME: www → your-domain.com
```

## SSL/HTTPS

- Railway: Inclus automatiquement
- Render: Inclus automatiquement
- VPS: Utiliser Certbot (voir plus haut)

## Monitoring

### Logs
```bash
# Railway / Render: Dashboard UI

# VPS:
sudo journalctl -u vyzio -f
sudo tail -f /var/log/nginx/error.log
```

### Alertes
- Configurer monitoring dans settings.py
- Sentry pour error tracking (optionnel)

## Backup Base de données

```bash
# PostgreSQL backup
pg_dump vyzio_ads_db > backup.sql

# Restore
psql vyzio_ads_db < backup.sql
```

## Mise à jour

```bash
cd /home/vyzio/vyzio_ads
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart vyzio
```

---

**Vous êtes prêt pour la production! 🎉**
