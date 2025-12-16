"""
Fixtures pour tester avec des données
"""
import json
from django.core.management import BaseCommand
from apps.users.models import CustomUser
from apps.listings.models import Category, Listing

class Command(BaseCommand):
    help = 'Load sample data'
    
    def handle(self, *args, **options):
        # Create categories
        categories_data = [
            {'name': 'Électronique', 'description': 'Téléphones, ordinateurs, etc.'},
            {'name': 'Vêtements', 'description': 'Habits, chaussures, accessoires'},
            {'name': 'Meubles', 'description': 'Canapés, tables, chaises'},
            {'name': 'Véhicules', 'description': 'Voitures, motos, vélos'},
            {'name': 'Services', 'description': 'Services et prestations'},
            {'name': 'Immobilier', 'description': 'Location et vente'},
        ]
        
        for cat_data in categories_data:
            Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
        
        self.stdout.write(self.style.SUCCESS('✅ Données d\'exemple chargées'))
