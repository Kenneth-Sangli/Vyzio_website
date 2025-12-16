"""
Module de recherche avancée pour les annonces.
Supporte PostgreSQL full-text search avec fallback SQLite.
"""
from django.db import connection
from django.db.models import Q, F, Value, FloatField, Case, When
from django.db.models.functions import Coalesce
from rest_framework import serializers
from .models import Listing
import re
import math


def is_postgresql():
    """Vérifie si la base de données est PostgreSQL"""
    return connection.vendor == 'postgresql'


# Import conditionnel des modules PostgreSQL
# Ils ne sont disponibles que si psycopg2 est installé
_postgres_search_available = False
SearchVector = None
SearchQuery = None
SearchRank = None
TrigramSimilarity = None

try:
    if is_postgresql():
        from django.contrib.postgres.search import (
            SearchVector, SearchQuery, SearchRank, TrigramSimilarity
        )
        _postgres_search_available = True
except ImportError:
    pass


class SearchQueryParams(serializers.Serializer):
    """Validateur pour les paramètres de recherche"""
    
    q = serializers.CharField(required=False, allow_blank=True, help_text="Terme de recherche")
    category = serializers.CharField(required=False, help_text="Slug de la catégorie")
    category_id = serializers.IntegerField(required=False, help_text="ID de la catégorie")
    listing_type = serializers.ChoiceField(
        choices=['product', 'service', 'rental', 'job'],
        required=False,
        help_text="Type d'annonce"
    )
    price_min = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        help_text="Prix minimum"
    )
    price_max = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        help_text="Prix maximum"
    )
    city = serializers.CharField(required=False, help_text="Ville (recherche partielle)")
    location = serializers.CharField(required=False, help_text="Localisation (recherche partielle)")
    
    # Géolocalisation
    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False,
        help_text="Latitude pour recherche par rayon"
    )
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False,
        help_text="Longitude pour recherche par rayon"
    )
    radius_km = serializers.DecimalField(
        max_digits=6, decimal_places=2, required=False, default=10,
        help_text="Rayon de recherche en km (défaut: 10)"
    )
    
    # Tri
    sort = serializers.ChoiceField(
        choices=['recent', 'oldest', 'price_asc', 'price_desc', 'relevance', 'popular'],
        required=False,
        default='recent',
        help_text="Ordre de tri"
    )
    
    # Pagination
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=20, min_value=1, max_value=100)
    
    # Filtres supplémentaires
    is_boosted = serializers.BooleanField(required=False)
    featured = serializers.BooleanField(required=False)
    seller = serializers.CharField(required=False, help_text="Username du vendeur")


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcule la distance en km entre deux points GPS avec la formule haversine.
    Pour PostgreSQL, on utilise une annotation SQL.
    Pour SQLite, on filtre en Python (moins performant mais fonctionnel).
    """
    R = 6371  # Rayon de la Terre en km
    
    lat1_rad = math.radians(float(lat1))
    lat2_rad = math.radians(float(lat2))
    delta_lat = math.radians(float(lat2) - float(lat1))
    delta_lon = math.radians(float(lon2) - float(lon1))
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


class ListingSearchEngine:
    """
    Moteur de recherche avancé pour les annonces.
    Utilise PostgreSQL full-text search si disponible, sinon fallback sur icontains.
    """
    
    def __init__(self, queryset=None):
        self.queryset = queryset if queryset is not None else Listing.objects.filter(status='published')
        self.is_pg = is_postgresql()
        self.search_term = None
    
    def search(self, params: dict):
        """
        Exécute la recherche avec tous les filtres et le tri.
        
        Args:
            params: Dictionnaire des paramètres de recherche validés
            
        Returns:
            QuerySet des annonces filtrées et triées
        """
        qs = self.queryset.select_related('seller', 'category').prefetch_related('images')
        
        # Recherche textuelle
        q = params.get('q', '').strip()
        if q:
            self.search_term = q
            qs = self._apply_text_search(qs, q)
        
        # Filtres de base
        qs = self._apply_filters(qs, params)
        
        # Filtre géographique
        qs = self._apply_geo_filter(qs, params)
        
        # Tri
        qs = self._apply_sorting(qs, params.get('sort', 'recent'))
        
        return qs
    
    def _apply_text_search(self, qs, search_term):
        """
        Applique la recherche textuelle.
        PostgreSQL: Full-text search avec ranking
        SQLite: icontains fallback
        """
        if self.is_pg and _postgres_search_available:
            return self._postgres_full_text_search(qs, search_term)
        else:
            return self._sqlite_search(qs, search_term)
    
    def _postgres_full_text_search(self, qs, search_term):
        """
        Recherche full-text PostgreSQL avec:
        - SearchVector sur titre (poids A) et description (poids B)
        - SearchQuery pour le terme de recherche
        - SearchRank pour le scoring
        - TrigramSimilarity pour les fautes de frappe
        """
        # Fallback si les modules PostgreSQL ne sont pas disponibles
        if not _postgres_search_available:
            return self._sqlite_search(qs, search_term)
        
        # Configuration du SearchVector avec poids
        search_vector = (
            SearchVector('title', weight='A', config='french') +
            SearchVector('description', weight='B', config='french') +
            SearchVector('location', weight='C', config='french')
        )
        
        # SearchQuery avec configuration française
        search_query = SearchQuery(search_term, config='french')
        
        # Ajouter le ranking et le trigram similarity
        qs = qs.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query),
            title_similarity=TrigramSimilarity('title', search_term),
            desc_similarity=TrigramSimilarity('description', search_term),
        ).annotate(
            # Score combiné: rank + similarité trigram
            search_score=F('rank') + (F('title_similarity') * 0.5) + (F('desc_similarity') * 0.2)
        ).filter(
            Q(search=search_query) |  # Match full-text
            Q(title_similarity__gt=0.3) |  # Ou similarité titre > 0.3
            Q(desc_similarity__gt=0.2)  # Ou similarité description > 0.2
        )
        
        return qs
    
    def _sqlite_search(self, qs, search_term):
        """
        Recherche SQLite avec icontains et scoring simulé.
        """
        # Tokenize search term
        words = search_term.lower().split()
        
        # Construire la requête Q pour chaque mot
        q_filter = Q()
        for word in words:
            word_filter = (
                Q(title__icontains=word) |
                Q(description__icontains=word) |
                Q(location__icontains=word) |
                Q(category__name__icontains=word)
            )
            q_filter &= word_filter  # AND entre les mots
        
        qs = qs.filter(q_filter)
        
        # Simuler un score de pertinence basique
        # On utilise Case/When pour donner plus de poids aux matches dans le titre
        qs = qs.annotate(
            search_score=Case(
                When(title__icontains=search_term, then=Value(1.0)),
                When(description__icontains=search_term, then=Value(0.5)),
                When(location__icontains=search_term, then=Value(0.3)),
                default=Value(0.1),
                output_field=FloatField()
            )
        )
        
        return qs
    
    def _apply_filters(self, qs, params):
        """Applique les filtres de base"""
        
        # Catégorie (par slug ou id)
        if params.get('category'):
            qs = qs.filter(category__slug=params['category'])
        elif params.get('category_id'):
            qs = qs.filter(category_id=params['category_id'])
        
        # Type d'annonce
        if params.get('listing_type'):
            qs = qs.filter(listing_type=params['listing_type'])
        
        # Plage de prix
        if params.get('price_min') is not None:
            qs = qs.filter(price__gte=params['price_min'])
        if params.get('price_max') is not None:
            qs = qs.filter(price__lte=params['price_max'])
        
        # Localisation/Ville
        if params.get('city'):
            qs = qs.filter(location__icontains=params['city'])
        elif params.get('location'):
            qs = qs.filter(location__icontains=params['location'])
        
        # Boosted/Featured
        if params.get('is_boosted') is not None:
            qs = qs.filter(is_boosted=params['is_boosted'])
        if params.get('featured') is not None:
            qs = qs.filter(featured=params['featured'])
        
        # Vendeur
        if params.get('seller'):
            qs = qs.filter(seller__username=params['seller'])
        
        return qs
    
    def _apply_geo_filter(self, qs, params):
        """
        Applique le filtre géographique par rayon.
        Nécessite latitude, longitude et optionnellement radius_km.
        """
        lat = params.get('latitude')
        lon = params.get('longitude')
        radius = params.get('radius_km', 10)
        
        if lat is None or lon is None:
            return qs
        
        lat = float(lat)
        lon = float(lon)
        radius = float(radius)
        
        if self.is_pg:
            # PostgreSQL: Utiliser une expression SQL pour le calcul de distance
            # Formule Haversine simplifiée
            from django.db.models.functions import Radians, Sin, Cos, ASin, Sqrt, Power
            from django.db.models import ExpressionWrapper
            
            # Pour simplicité, on utilise une approximation avec degrees
            # Distance approximative (assez précise pour de petites distances)
            lat_diff = F('latitude') - lat
            lon_diff = F('longitude') - lon
            
            # Approximation simple: 1 degré lat ≈ 111km, 1 degré lon ≈ 111km * cos(lat)
            approx_distance_sq = (
                Power(lat_diff * 111.0, 2) + 
                Power(lon_diff * 111.0 * 0.7, 2)  # cos(45°) ≈ 0.7 approximation
            )
            
            qs = qs.filter(
                latitude__isnull=False,
                longitude__isnull=False
            ).annotate(
                distance_sq=approx_distance_sq
            ).filter(
                distance_sq__lte=radius**2
            )
        else:
            # SQLite: Filtrer en mémoire (moins performant)
            # D'abord filtrer les annonces avec coordonnées
            qs = qs.filter(latitude__isnull=False, longitude__isnull=False)
            
            # On doit convertir en liste et filtrer en Python
            # Ceci est inefficace pour de gros datasets mais fonctionne pour le dev
            listing_ids = []
            for listing in qs.only('id', 'latitude', 'longitude'):
                if listing.latitude and listing.longitude:
                    distance = haversine_distance(lat, lon, listing.latitude, listing.longitude)
                    if distance <= radius:
                        listing_ids.append(listing.id)
            
            qs = Listing.objects.filter(id__in=listing_ids, status='published')
            qs = qs.select_related('seller', 'category').prefetch_related('images')
        
        return qs
    
    def _apply_sorting(self, qs, sort):
        """Applique le tri"""
        
        sort_mapping = {
            'recent': ['-created_at'],
            'oldest': ['created_at'],
            'price_asc': ['price', '-created_at'],
            'price_desc': ['-price', '-created_at'],
            'popular': ['-views_count', '-favorites_count', '-created_at'],
        }
        
        if sort == 'relevance' and self.search_term:
            # Tri par score de pertinence (si recherche textuelle)
            if hasattr(qs.model, 'search_score') or 'search_score' in qs.query.annotations:
                return qs.order_by('-search_score', '-created_at')
            else:
                # Fallback si pas de score
                return qs.order_by('-created_at')
        
        ordering = sort_mapping.get(sort, ['-created_at'])
        return qs.order_by(*ordering)


def perform_search(params: dict, base_queryset=None):
    """
    Fonction utilitaire pour effectuer une recherche.
    
    Args:
        params: Paramètres de recherche (déjà validés ou bruts)
        base_queryset: QuerySet de base (optionnel)
        
    Returns:
        tuple: (queryset, metadata)
    """
    # Valider les paramètres si nécessaire
    if not isinstance(params, dict):
        raise ValueError("params doit être un dictionnaire")
    
    # Créer le moteur de recherche
    engine = ListingSearchEngine(base_queryset)
    
    # Effectuer la recherche
    queryset = engine.search(params)
    
    # Métadonnées
    metadata = {
        'search_term': params.get('q', ''),
        'filters_applied': {
            k: v for k, v in params.items() 
            if v is not None and k not in ['page', 'page_size', 'sort']
        },
        'sort': params.get('sort', 'recent'),
        'is_postgresql': engine.is_pg,
    }
    
    return queryset, metadata
