#!/bin/bash
# Setup script for vyzio_ads

set -e

echo "🚀 Installation de Vyzio Ads..."

# Create virtual environment
echo "📦 Création de l'environnement virtuel..."
python -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installation des dépendances..."
pip install -r requirements.txt

# Create .env file
if [ ! -f .env ]; then
    echo "🔧 Création du fichier .env..."
    cp .env.example .env
    echo "⚠️  Veuillez éditer .env avec vos variables d'environnement"
fi

# Create directories
mkdir -p logs media staticfiles

# Run migrations
echo "🗄️  Exécution des migrations..."
python manage.py migrate

# Create superuser
echo "👤 Création du superutilisateur admin..."
python manage.py createsuperuser

# Collect static files
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "✅ Installation terminée !"
echo ""
echo "Pour démarrer le serveur:"
echo "  python manage.py runserver"
echo ""
echo "Admin panel:"
echo "  http://localhost:8000/admin/"
