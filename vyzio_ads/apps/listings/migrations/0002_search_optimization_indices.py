"""
Migration pour ajouter les indices optimisés pour la recherche avancée.
Phase 4 - Recherche avancée & optimisation
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Ajoute des indices pour optimiser:
    - Recherche par prix
    - Recherche par ville/location
    - Recherche par catégorie
    - Tri par date de création
    - Recherche full-text (préparation PostgreSQL)
    """
    
    dependencies = [
        ('listings', '0001_initial'),
    ]
    
    operations = [
        # Index sur le prix pour les filtres price_min/price_max
        migrations.AddIndex(
            model_name='listing',
            index=models.Index(fields=['price'], name='listings_price_idx'),
        ),
        
        # Index sur la location pour les recherches par ville
        migrations.AddIndex(
            model_name='listing',
            index=models.Index(fields=['location'], name='listings_location_idx'),
        ),
        
        # Index sur category_id pour les filtres par catégorie
        migrations.AddIndex(
            model_name='listing',
            index=models.Index(fields=['category'], name='listings_category_fk_idx'),
        ),
        
        # Index sur created_at pour le tri par date
        migrations.AddIndex(
            model_name='listing',
            index=models.Index(fields=['-created_at'], name='listings_created_desc_idx'),
        ),
        
        # Index composé pour les filtres courants: status + category + price
        migrations.AddIndex(
            model_name='listing',
            index=models.Index(
                fields=['status', 'category', 'price'],
                name='listings_filter_combo_idx'
            ),
        ),
        
        # Index composé pour les recherches géographiques
        migrations.AddIndex(
            model_name='listing',
            index=models.Index(
                fields=['latitude', 'longitude'],
                name='listings_geo_idx'
            ),
        ),
        
        # Index sur listing_type
        migrations.AddIndex(
            model_name='listing',
            index=models.Index(fields=['listing_type'], name='listings_type_idx'),
        ),
        
        # Index sur is_boosted pour prioriser les annonces boostées
        migrations.AddIndex(
            model_name='listing',
            index=models.Index(fields=['is_boosted', '-created_at'], name='listings_boosted_idx'),
        ),
        
        # Index sur views_count pour le tri par popularité
        migrations.AddIndex(
            model_name='listing',
            index=models.Index(fields=['-views_count'], name='listings_views_idx'),
        ),
    ]
