"""
Tests Phase 4 - Recherche avancée & optimisation
Tests pour le full-text search, les filtres avancés, le tri et les performances.
"""
import pytest
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from apps.listings.models import Category, Listing, ListingImage
from apps.listings.search import ListingSearchEngine, perform_search, is_postgresql

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def seller_user(db):
    """Crée un utilisateur vendeur"""
    return User.objects.create_user(
        email='seller@test.com',
        password='TestPass123!',
        username='sellertest',
        role='seller',
        is_verified=True
    )


@pytest.fixture
def buyer_user(db):
    """Crée un utilisateur acheteur"""
    return User.objects.create_user(
        email='buyer@test.com',
        password='TestPass123!',
        username='buyertest',
        role='buyer',
        is_verified=True
    )


@pytest.fixture
def categories(db):
    """Crée plusieurs catégories pour les tests"""
    return [
        Category.objects.create(name='Électronique', slug='electronique'),
        Category.objects.create(name='Vêtements', slug='vetements'),
        Category.objects.create(name='Maison', slug='maison'),
        Category.objects.create(name='Auto', slug='auto'),
    ]


@pytest.fixture
def sample_listings(db, seller_user, categories):
    """Crée un ensemble d'annonces pour les tests de recherche"""
    listings = []
    
    # Électronique
    listings.append(Listing.objects.create(
        seller=seller_user,
        category=categories[0],
        title='iPhone 15 Pro Max neuf',
        description='Smartphone Apple dernière génération, 256GB, couleur noir spatial',
        price=Decimal('1299.99'),
        location='Paris',
        listing_type='product',
        status='published',
        latitude=Decimal('48.8566'),
        longitude=Decimal('2.3522'),
        views_count=150
    ))
    
    listings.append(Listing.objects.create(
        seller=seller_user,
        category=categories[0],
        title='MacBook Pro M3',
        description='Ordinateur portable Apple avec puce M3, 16GB RAM, 512GB SSD',
        price=Decimal('2499.00'),
        location='Lyon',
        listing_type='product',
        status='published',
        latitude=Decimal('45.7640'),
        longitude=Decimal('4.8357'),
        views_count=200
    ))
    
    listings.append(Listing.objects.create(
        seller=seller_user,
        category=categories[0],
        title='Samsung Galaxy S24 Ultra',
        description='Smartphone Samsung haut de gamme, 512GB, excellent état',
        price=Decimal('999.00'),
        location='Paris',
        listing_type='product',
        status='published',
        views_count=80
    ))
    
    # Vêtements
    listings.append(Listing.objects.create(
        seller=seller_user,
        category=categories[1],
        title='Veste en cuir vintage',
        description='Veste en cuir véritable, style motard, taille M',
        price=Decimal('150.00'),
        location='Marseille',
        listing_type='product',
        status='published',
        views_count=45
    ))
    
    listings.append(Listing.objects.create(
        seller=seller_user,
        category=categories[1],
        title='Sneakers Nike Air Max',
        description='Chaussures Nike Air Max 90, pointure 42, neuves',
        price=Decimal('180.00'),
        location='Paris',
        listing_type='product',
        status='published',
        views_count=120
    ))
    
    # Maison
    listings.append(Listing.objects.create(
        seller=seller_user,
        category=categories[2],
        title='Canapé cuir 3 places',
        description='Canapé en cuir véritable, couleur marron, très bon état',
        price=Decimal('450.00'),
        location='Bordeaux',
        listing_type='product',
        status='published',
        views_count=60
    ))
    
    # Auto - Service
    listings.append(Listing.objects.create(
        seller=seller_user,
        category=categories[3],
        title='Réparation automobile',
        description='Service de réparation et entretien automobile à domicile',
        price=Decimal('50.00'),
        location='Paris',
        listing_type='service',
        status='published',
        views_count=30
    ))
    
    # Annonce en brouillon (ne doit pas apparaître dans les recherches publiques)
    listings.append(Listing.objects.create(
        seller=seller_user,
        category=categories[0],
        title='iPhone brouillon',
        description='Ceci est un brouillon',
        price=Decimal('500.00'),
        location='Paris',
        listing_type='product',
        status='draft'
    ))
    
    # Ajouter des images aux premières annonces
    for listing in listings[:3]:
        ListingImage.objects.create(
            listing=listing,
            image='test.jpg',
            is_primary=True
        )
    
    return listings


# ==================== Tests du moteur de recherche ====================

@pytest.mark.django_db
class TestSearchEngine:
    """Tests pour le moteur de recherche ListingSearchEngine"""
    
    def test_basic_text_search(self, sample_listings):
        """Test recherche textuelle basique"""
        engine = ListingSearchEngine()
        results = engine.search({'q': 'iPhone'})
        
        # Doit trouver l'iPhone publié mais pas le brouillon
        titles = [r.title for r in results]
        assert 'iPhone 15 Pro Max neuf' in titles
        assert 'iPhone brouillon' not in titles
    
    def test_search_in_description(self, sample_listings):
        """Test recherche dans la description"""
        engine = ListingSearchEngine()
        results = engine.search({'q': 'Apple'})
        
        # Doit trouver iPhone et MacBook (mentions Apple dans description)
        assert results.count() >= 2
    
    def test_search_case_insensitive(self, sample_listings):
        """Test recherche insensible à la casse"""
        engine = ListingSearchEngine()
        
        results_lower = engine.search({'q': 'iphone'})
        results_upper = engine.search({'q': 'IPHONE'})
        results_mixed = engine.search({'q': 'IpHoNe'})
        
        assert results_lower.count() == results_upper.count() == results_mixed.count()
    
    def test_search_multiple_words(self, sample_listings):
        """Test recherche avec plusieurs mots"""
        engine = ListingSearchEngine()
        results = engine.search({'q': 'iPhone Pro'})
        
        # Doit trouver l'iPhone 15 Pro Max
        assert any('iPhone 15 Pro' in r.title for r in results)
    
    def test_search_no_results(self, sample_listings):
        """Test recherche sans résultats"""
        engine = ListingSearchEngine()
        results = engine.search({'q': 'xyznonexistent123'})
        
        assert results.count() == 0


@pytest.mark.django_db
class TestSearchFilters:
    """Tests pour les filtres de recherche"""
    
    def test_filter_by_category(self, sample_listings, categories):
        """Test filtre par catégorie"""
        engine = ListingSearchEngine()
        results = engine.search({'category': 'electronique'})
        
        # 3 annonces en électronique (publié), 1 en brouillon
        assert results.count() == 3
        assert all(r.category.slug == 'electronique' for r in results)
    
    def test_filter_by_category_id(self, sample_listings, categories):
        """Test filtre par ID de catégorie"""
        engine = ListingSearchEngine()
        results = engine.search({'category_id': categories[1].id})
        
        # 2 annonces en vêtements
        assert results.count() == 2
    
    def test_filter_by_price_range(self, sample_listings):
        """Test filtre par plage de prix"""
        engine = ListingSearchEngine()
        results = engine.search({
            'price_min': Decimal('100'),
            'price_max': Decimal('500')
        })
        
        for listing in results:
            assert Decimal('100') <= listing.price <= Decimal('500')
    
    def test_filter_by_price_min_only(self, sample_listings):
        """Test filtre prix minimum seul"""
        engine = ListingSearchEngine()
        results = engine.search({'price_min': Decimal('1000')})
        
        for listing in results:
            assert listing.price >= Decimal('1000')
    
    def test_filter_by_price_max_only(self, sample_listings):
        """Test filtre prix maximum seul"""
        engine = ListingSearchEngine()
        results = engine.search({'price_max': Decimal('200')})
        
        for listing in results:
            assert listing.price <= Decimal('200')
    
    def test_filter_by_city(self, sample_listings):
        """Test filtre par ville"""
        engine = ListingSearchEngine()
        results = engine.search({'city': 'Paris'})
        
        for listing in results:
            assert 'Paris' in listing.location
    
    def test_filter_by_listing_type(self, sample_listings):
        """Test filtre par type d'annonce"""
        engine = ListingSearchEngine()
        results = engine.search({'listing_type': 'service'})
        
        assert results.count() == 1
        assert results.first().listing_type == 'service'
    
    def test_combined_filters(self, sample_listings, categories):
        """Test filtres combinés"""
        engine = ListingSearchEngine()
        results = engine.search({
            'q': 'cuir',
            'price_max': Decimal('500'),
            'listing_type': 'product'
        })
        
        # Doit trouver veste en cuir et canapé cuir
        assert results.count() >= 1
        for listing in results:
            assert listing.price <= Decimal('500')
            assert listing.listing_type == 'product'


@pytest.mark.django_db
class TestSearchSorting:
    """Tests pour le tri des résultats"""
    
    def test_sort_recent(self, sample_listings):
        """Test tri par date récente"""
        engine = ListingSearchEngine()
        results = list(engine.search({'sort': 'recent'}))
        
        for i in range(len(results) - 1):
            assert results[i].created_at >= results[i + 1].created_at
    
    def test_sort_oldest(self, sample_listings):
        """Test tri par date ancienne"""
        engine = ListingSearchEngine()
        results = list(engine.search({'sort': 'oldest'}))
        
        for i in range(len(results) - 1):
            assert results[i].created_at <= results[i + 1].created_at
    
    def test_sort_price_asc(self, sample_listings):
        """Test tri par prix croissant"""
        engine = ListingSearchEngine()
        results = list(engine.search({'sort': 'price_asc'}))
        
        for i in range(len(results) - 1):
            assert results[i].price <= results[i + 1].price
    
    def test_sort_price_desc(self, sample_listings):
        """Test tri par prix décroissant"""
        engine = ListingSearchEngine()
        results = list(engine.search({'sort': 'price_desc'}))
        
        for i in range(len(results) - 1):
            assert results[i].price >= results[i + 1].price
    
    def test_sort_popular(self, sample_listings):
        """Test tri par popularité (views_count)"""
        engine = ListingSearchEngine()
        results = list(engine.search({'sort': 'popular'}))
        
        for i in range(len(results) - 1):
            assert results[i].views_count >= results[i + 1].views_count
    
    def test_sort_relevance_with_search(self, sample_listings):
        """Test tri par pertinence avec recherche"""
        engine = ListingSearchEngine()
        results = engine.search({'q': 'iPhone', 'sort': 'relevance'})
        
        # Le premier résultat devrait être le plus pertinent
        assert results.count() > 0


# ==================== Tests des endpoints API ====================

@pytest.mark.django_db
class TestSearchEndpoint:
    """Tests pour l'endpoint GET /api/search/"""
    
    def test_search_endpoint_basic(self, api_client, sample_listings):
        """Test endpoint recherche basique"""
        response = api_client.get('/api/listings/search/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert 'count' in response.data
        assert 'search_metadata' in response.data
    
    def test_search_with_query(self, api_client, sample_listings):
        """Test recherche avec terme"""
        response = api_client.get('/api/listings/search/', {'q': 'iPhone'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1
        assert response.data['search_metadata']['query'] == 'iPhone'
    
    def test_search_with_filters(self, api_client, sample_listings, categories):
        """Test recherche avec filtres"""
        response = api_client.get('/api/listings/search/', {
            'category': 'electronique',
            'price_min': 500,
            'price_max': 1500
        })
        
        assert response.status_code == status.HTTP_200_OK
        # Vérifie que les filtres sont appliqués
        for listing in response.data['results']:
            assert 500 <= float(listing['price']) <= 1500
    
    def test_search_pagination(self, api_client, sample_listings):
        """Test pagination des résultats"""
        response = api_client.get('/api/listings/search/', {'page_size': 2})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) <= 2
        assert 'total_pages' in response.data
        assert 'current_page' in response.data
    
    def test_search_invalid_params(self, api_client):
        """Test avec paramètres invalides"""
        response = api_client.get('/api/listings/search/', {
            'price_min': 'invalid',
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_search_sort_options(self, api_client, sample_listings):
        """Test différentes options de tri"""
        sort_options = ['recent', 'oldest', 'price_asc', 'price_desc', 'popular']
        
        for sort in sort_options:
            response = api_client.get('/api/listings/search/', {'sort': sort})
            assert response.status_code == status.HTTP_200_OK
            assert response.data['search_metadata']['sort'] == sort


@pytest.mark.django_db
class TestSearchSuggestEndpoint:
    """Tests pour l'endpoint GET /api/search/suggest/"""
    
    def test_suggest_endpoint(self, api_client, sample_listings, categories):
        """Test suggestions de recherche"""
        response = api_client.get('/api/listings/search/suggest/', {'q': 'iPh'})
        
        assert response.status_code == status.HTTP_200_OK
        assert 'suggestions' in response.data
        assert 'categories' in response.data
    
    def test_suggest_minimum_chars(self, api_client):
        """Test minimum de caractères requis"""
        response = api_client.get('/api/listings/search/suggest/', {'q': 'i'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['suggestions'] == []
    
    def test_suggest_returns_titles(self, api_client, sample_listings):
        """Test que les suggestions contiennent des titres"""
        response = api_client.get('/api/listings/search/suggest/', {'q': 'iPhone'})
        
        assert response.status_code == status.HTTP_200_OK
        # Devrait trouver iPhone dans les suggestions
        assert any('iPhone' in s for s in response.data['suggestions'])


@pytest.mark.django_db
class TestSearchStatsEndpoint:
    """Tests pour l'endpoint GET /api/search/stats/"""
    
    def test_stats_endpoint(self, api_client, sample_listings, categories):
        """Test statistiques de recherche"""
        response = api_client.get('/api/listings/search/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_count' in response.data
        assert 'facets' in response.data
        assert 'price_range' in response.data
    
    def test_stats_facets(self, api_client, sample_listings, categories):
        """Test facettes de recherche"""
        response = api_client.get('/api/listings/search/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        facets = response.data['facets']
        
        assert 'categories' in facets
        assert 'listing_types' in facets
        assert 'locations' in facets
    
    def test_stats_with_search_query(self, api_client, sample_listings):
        """Test stats avec terme de recherche"""
        response = api_client.get('/api/listings/search/stats/', {'q': 'iPhone'})
        
        assert response.status_code == status.HTTP_200_OK
        # Le total devrait être filtré
        assert response.data['total_count'] >= 1


# ==================== Tests de performance ====================

@pytest.mark.django_db
class TestSearchPerformance:
    """Tests de performance pour la recherche"""
    
    def test_large_dataset_search(self, db, seller_user, categories):
        """Test recherche sur un grand dataset"""
        import time
        import uuid
        
        # Créer 100 annonces
        listings = []
        for i in range(100):
            listings.append(Listing(
                seller=seller_user,
                category=categories[i % len(categories)],
                title=f'Produit test numéro {i}',
                slug=f'produit-test-{i}-{uuid.uuid4().hex[:8]}',
                description=f'Description du produit {i} avec des mots clés variés',
                price=Decimal(str(50 + i * 10)),
                location=['Paris', 'Lyon', 'Marseille', 'Bordeaux'][i % 4],
                listing_type='product',
                status='published'
            ))
        Listing.objects.bulk_create(listings)
        
        # Mesurer le temps de recherche
        engine = ListingSearchEngine()
        
        start = time.time()
        results = list(engine.search({'q': 'produit'}))
        end = time.time()
        
        search_time = end - start
        
        # La recherche doit être rapide (moins de 1 seconde)
        assert search_time < 1.0, f"Recherche trop lente: {search_time:.2f}s"
        assert len(results) == 100
    
    def test_complex_filter_performance(self, db, seller_user, categories):
        """Test performance avec filtres complexes"""
        import time
        import uuid
        
        # Créer des annonces
        listings = []
        for i in range(50):
            listings.append(Listing(
                seller=seller_user,
                category=categories[i % len(categories)],
                title=f'Annonce complexe {i}',
                slug=f'annonce-complexe-{i}-{uuid.uuid4().hex[:8]}',
                description=f'Description longue avec beaucoup de mots pour tester la recherche full-text {i}',
                price=Decimal(str(100 + i * 20)),
                location=['Paris', 'Lyon'][i % 2],
                listing_type=['product', 'service'][i % 2],
                status='published'
            ))
        Listing.objects.bulk_create(listings)
        
        engine = ListingSearchEngine()
        
        start = time.time()
        results = list(engine.search({
            'q': 'annonce',
            'category': 'electronique',
            'price_min': Decimal('200'),
            'price_max': Decimal('800'),
            'city': 'Paris',
            'sort': 'price_desc'
        }))
        end = time.time()
        
        # Les filtres complexes doivent rester rapides
        assert (end - start) < 0.5, f"Filtres complexes trop lents: {end - start:.2f}s"


# ==================== Tests d'intégration ====================

@pytest.mark.django_db
class TestSearchIntegration:
    """Tests d'intégration pour la recherche"""
    
    def test_search_excludes_drafts(self, api_client, sample_listings):
        """Test que les brouillons sont exclus des recherches"""
        response = api_client.get('/api/listings/search/', {'q': 'brouillon'})
        
        assert response.status_code == status.HTTP_200_OK
        # Aucun résultat car l'annonce "iPhone brouillon" est en draft
        assert response.data['count'] == 0
    
    def test_search_returns_published_only(self, api_client, sample_listings):
        """Test que seules les annonces publiées sont retournées"""
        response = api_client.get('/api/listings/search/')
        
        assert response.status_code == status.HTTP_200_OK
        for listing in response.data['results']:
            assert listing['status'] == 'published'
    
    def test_search_with_special_characters(self, api_client, sample_listings):
        """Test recherche avec caractères spéciaux"""
        response = api_client.get('/api/listings/search/', {'q': 'iPhone & Mac'})
        
        # Ne doit pas planter
        assert response.status_code == status.HTTP_200_OK
    
    def test_search_empty_query(self, api_client, sample_listings):
        """Test recherche avec requête vide"""
        response = api_client.get('/api/listings/search/', {'q': ''})
        
        assert response.status_code == status.HTTP_200_OK
        # Retourne toutes les annonces publiées
        assert response.data['count'] > 0


# ==================== Tests du backend PostgreSQL/SQLite ====================

@pytest.mark.django_db
class TestDatabaseBackend:
    """Tests spécifiques au backend de base de données"""
    
    def test_is_postgresql_function(self):
        """Test détection du backend"""
        result = is_postgresql()
        # En dev, on utilise SQLite
        assert isinstance(result, bool)
    
    def test_search_works_regardless_of_backend(self, sample_listings):
        """Test que la recherche fonctionne quel que soit le backend"""
        engine = ListingSearchEngine()
        results = engine.search({'q': 'iPhone'})
        
        # Doit fonctionner avec SQLite ou PostgreSQL
        assert results.count() >= 1


# ==================== Tests de perform_search ====================

@pytest.mark.django_db
class TestPerformSearchFunction:
    """Tests pour la fonction utilitaire perform_search"""
    
    def test_perform_search_returns_tuple(self, sample_listings):
        """Test que perform_search retourne un tuple (queryset, metadata)"""
        queryset, metadata = perform_search({'q': 'iPhone'})
        
        assert queryset is not None
        assert isinstance(metadata, dict)
        assert 'search_term' in metadata
        assert 'is_postgresql' in metadata
    
    def test_perform_search_metadata(self, sample_listings):
        """Test métadonnées de perform_search"""
        _, metadata = perform_search({
            'q': 'test',
            'category': 'electronique',
            'sort': 'price_asc'
        })
        
        assert metadata['search_term'] == 'test'
        assert metadata['sort'] == 'price_asc'
        assert 'category' in metadata['filters_applied']
