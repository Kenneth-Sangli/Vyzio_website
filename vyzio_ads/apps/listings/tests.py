"""
Tests pour l'application Listings - Phase 3
"""
import pytest
from decimal import Decimal
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import CustomUser
from apps.listings.models import Category, Listing, ListingImage, Favorite


# ============== FIXTURES ==============

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def category(db):
    return Category.objects.create(
        name='Électronique',
        slug='electronique',
        description='Produits électroniques'
    )


@pytest.fixture
def category2(db):
    return Category.objects.create(
        name='Véhicules',
        slug='vehicules',
        description='Voitures, motos, etc.'
    )


@pytest.fixture
def buyer_user(db):
    return CustomUser.objects.create_user(
        email='buyer@test.com',
        username='buyer',
        password='BuyerPass123!',
        first_name='Buyer',
        last_name='Test',
        role='buyer'
    )


@pytest.fixture
def seller_user(db):
    return CustomUser.objects.create_user(
        email='seller@test.com',
        username='seller',
        password='SellerPass123!',
        first_name='Seller',
        last_name='Test',
        role='seller'
    )


@pytest.fixture
def seller_user2(db):
    return CustomUser.objects.create_user(
        email='seller2@test.com',
        username='seller2',
        password='SellerPass123!',
        first_name='Seller2',
        last_name='Test',
        role='seller'
    )


@pytest.fixture
def authenticated_buyer(api_client, buyer_user):
    api_client.force_authenticate(user=buyer_user)
    return api_client


@pytest.fixture
def authenticated_seller(api_client, seller_user):
    api_client.force_authenticate(user=seller_user)
    return api_client


@pytest.fixture
def authenticated_seller2(seller_user2):
    client = APIClient()
    client.force_authenticate(user=seller_user2)
    return client


@pytest.fixture
def draft_listing(db, seller_user, category):
    return Listing.objects.create(
        seller=seller_user,
        category=category,
        title='iPhone 15 Pro',
        description='iPhone en excellent état',
        price=Decimal('999.99'),
        location='Paris',
        listing_type='product',
        status='draft'
    )


@pytest.fixture
def published_listing(db, seller_user, category):
    listing = Listing.objects.create(
        seller=seller_user,
        category=category,
        title='MacBook Pro M3',
        description='MacBook Pro 14 pouces',
        price=Decimal('2499.00'),
        location='Lyon',
        listing_type='product',
        status='published'
    )
    # Ajouter une image
    ListingImage.objects.create(
        listing=listing,
        image=SimpleUploadedFile('test.jpg', b'image_content', content_type='image/jpeg'),
        is_primary=True
    )
    return listing


@pytest.fixture
def published_listing2(db, seller_user2, category2):
    listing = Listing.objects.create(
        seller=seller_user2,
        category=category2,
        title='Renault Clio',
        description='Voiture en bon état',
        price=Decimal('8500.00'),
        location='Marseille',
        listing_type='product',
        status='published'
    )
    ListingImage.objects.create(
        listing=listing,
        image=SimpleUploadedFile('car.jpg', b'image_content', content_type='image/jpeg'),
        is_primary=True
    )
    return listing


@pytest.fixture
def sample_image():
    """Créer une image de test"""
    return SimpleUploadedFile(
        name='test_image.jpg',
        content=b'\x47\x49\x46\x38\x89\x61' + b'\x00' * 100,  # GIF header
        content_type='image/jpeg'
    )


# ============== TESTS CATEGORIES ==============

@pytest.mark.django_db
class TestCategories:
    
    def test_list_categories(self, api_client, category, category2):
        """GET /api/categories/ retourne toutes les catégories actives"""
        url = reverse('categories-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
    
    def test_retrieve_category(self, api_client, category):
        """GET /api/categories/{id}/ retourne une catégorie"""
        url = reverse('categories-detail', args=[category.id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Électronique'
        assert response.data['slug'] == 'electronique'


# ============== TESTS CRUD LISTINGS ==============

@pytest.mark.django_db
class TestListingCRUD:
    
    def test_list_published_listings(self, api_client, published_listing, draft_listing):
        """GET /api/listings/ retourne seulement les annonces publiées"""
        url = reverse('listings-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Seulement la published, pas la draft
        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == 'MacBook Pro M3'
    
    def test_retrieve_listing(self, api_client, published_listing):
        """GET /api/listings/{id}/ retourne le détail d'une annonce"""
        url = reverse('listings-detail', args=[published_listing.id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'MacBook Pro M3'
        assert response.data['price'] == '2499.00'
        assert 'images' in response.data
        assert 'seller' in response.data
    
    def test_retrieve_increments_views(self, api_client, published_listing):
        """Chaque visite incrémente le compteur de vues"""
        initial_views = published_listing.views_count
        url = reverse('listings-detail', args=[published_listing.id])
        
        api_client.get(url)
        published_listing.refresh_from_db()
        
        assert published_listing.views_count == initial_views + 1
    
    def test_create_listing_as_seller(self, authenticated_seller, category):
        """POST /api/listings/ - un seller peut créer une annonce"""
        url = reverse('listings-list')
        data = {
            'title': 'Nouveau Produit',
            'description': 'Description du produit',
            'price': '150.00',
            'location': 'Bordeaux',
            'listing_type': 'product',
            'category': category.id
        }
        response = authenticated_seller.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Nouveau Produit'
        assert response.data['status'] == 'draft'  # Créé en brouillon
    
    def test_create_listing_as_buyer_forbidden(self, authenticated_buyer, category):
        """POST /api/listings/ - un buyer ne peut PAS créer une annonce"""
        url = reverse('listings-list')
        data = {
            'title': 'Tentative Buyer',
            'description': 'Description',
            'price': '100.00',
            'location': 'Nice',
            'listing_type': 'product',
            'category': category.id
        }
        response = authenticated_buyer.post(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_listing_unauthenticated(self, api_client, category):
        """POST /api/listings/ - non authentifié = 401"""
        url = reverse('listings-list')
        data = {
            'title': 'Test',
            'description': 'Desc',
            'price': '50.00',
            'location': 'Test',
            'listing_type': 'product',
            'category': category.id
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_own_listing(self, authenticated_seller, draft_listing):
        """PUT /api/listings/{id}/ - un seller peut modifier SON annonce"""
        url = reverse('listings-detail', args=[draft_listing.id])
        data = {
            'title': 'iPhone 15 Pro Max',
            'description': 'Mise à jour description',
            'price': '1199.99',
            'location': 'Paris',
            'listing_type': 'product',
            'category': draft_listing.category.id
        }
        response = authenticated_seller.put(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        draft_listing.refresh_from_db()
        assert draft_listing.title == 'iPhone 15 Pro Max'
        assert draft_listing.price == Decimal('1199.99')
    
    def test_partial_update_own_listing(self, authenticated_seller, draft_listing):
        """PATCH /api/listings/{id}/ - mise à jour partielle"""
        url = reverse('listings-detail', args=[draft_listing.id])
        data = {'price': '899.00'}
        response = authenticated_seller.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        draft_listing.refresh_from_db()
        assert draft_listing.price == Decimal('899.00')
    
    def test_update_other_user_listing_forbidden(self, authenticated_seller2, draft_listing):
        """PUT /api/listings/{id}/ - impossible de modifier l'annonce d'un autre"""
        url = reverse('listings-detail', args=[draft_listing.id])
        data = {
            'title': 'Tentative modification',
            'description': 'Hack',
            'price': '1.00',
            'location': 'Hack',
            'listing_type': 'product',
            'category': draft_listing.category.id
        }
        response = authenticated_seller2.put(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_own_listing(self, authenticated_seller, seller_user, category):
        """DELETE /api/listings/{id}/ - un seller peut supprimer SON annonce"""
        listing = Listing.objects.create(
            seller=seller_user,
            category=category,
            title='À supprimer',
            description='Test',
            price=Decimal('10.00'),
            location='Test',
            status='draft'
        )
        url = reverse('listings-detail', args=[listing.id])
        response = authenticated_seller.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Listing.objects.filter(id=listing.id).exists()
    
    def test_delete_other_user_listing_forbidden(self, authenticated_seller2, draft_listing):
        """DELETE /api/listings/{id}/ - impossible de supprimer l'annonce d'un autre"""
        url = reverse('listings-detail', args=[draft_listing.id])
        response = authenticated_seller2.delete(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============== TESTS FILTRES ==============

@pytest.mark.django_db
class TestListingFilters:
    
    def test_filter_by_category(self, api_client, published_listing, published_listing2):
        """Filtre par catégorie (slug)"""
        url = reverse('listings-list')
        response = api_client.get(url, {'category': 'electronique'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == 'MacBook Pro M3'
    
    def test_filter_by_price_range(self, api_client, published_listing, published_listing2):
        """Filtre par fourchette de prix"""
        url = reverse('listings-list')
        
        # Prix entre 1000 et 5000
        response = api_client.get(url, {'price_min': '1000', 'price_max': '5000'})
        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == 'MacBook Pro M3'
        
        # Prix max 1000
        response = api_client.get(url, {'price_max': '1000'})
        assert response.data['count'] == 0
    
    def test_filter_by_city(self, api_client, published_listing, published_listing2):
        """Filtre par ville (location)"""
        url = reverse('listings-list')
        response = api_client.get(url, {'city': 'Lyon'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['location'] == 'Lyon'
    
    def test_filter_by_listing_type(self, api_client, published_listing):
        """Filtre par type d'annonce"""
        url = reverse('listings-list')
        response = api_client.get(url, {'listing_type': 'product'})
        
        assert response.status_code == status.HTTP_200_OK
        assert all(r['listing_type'] == 'product' for r in response.data['results'])
    
    def test_search_filter(self, api_client, published_listing, published_listing2):
        """Recherche full-text"""
        url = reverse('listings-list')
        
        # Recherche "MacBook"
        response = api_client.get(url, {'search': 'MacBook'})
        assert response.data['count'] == 1
        assert 'MacBook' in response.data['results'][0]['title']
        
        # Recherche "voiture"
        response = api_client.get(url, {'search': 'voiture'})
        assert response.data['count'] == 1
    
    def test_ordering(self, api_client, published_listing, published_listing2):
        """Tri des résultats par prix"""
        url = reverse('listings-list')
        
        # Les deux annonces ont des prix différents: 2499 et 8500
        # Tri par prix croissant (utilise le ordering de DRF, pas le filtre)
        response = api_client.get(url + '?ordering=price')
        assert response.status_code == status.HTTP_200_OK
        
        results = response.data.get('results', [])
        assert len(results) == 2
        
        # Le premier doit être le moins cher (MacBook 2499)
        assert Decimal(results[0]['price']) < Decimal(results[1]['price'])
        
        # Tri par prix décroissant
        response = api_client.get(url + '?ordering=-price')
        assert response.status_code == status.HTTP_200_OK
        
        results = response.data.get('results', [])
        # Le premier doit être le plus cher (Renault 8500)
        assert Decimal(results[0]['price']) > Decimal(results[1]['price'])


# ============== TESTS PAGINATION ==============

@pytest.mark.django_db
class TestPagination:
    
    def test_pagination_structure(self, api_client, published_listing):
        """Vérifie la structure de pagination"""
        url = reverse('listings-list')
        response = api_client.get(url)
        
        assert 'count' in response.data
        assert 'next' in response.data
        assert 'previous' in response.data
        assert 'results' in response.data
    
    def test_page_size_param(self, api_client, seller_user, category):
        """Test du paramètre page_size"""
        # Créer plusieurs annonces publiées
        for i in range(25):
            listing = Listing.objects.create(
                seller=seller_user,
                category=category,
                title=f'Produit {i}',
                description='Description',
                price=Decimal('100.00'),
                location='Paris',
                status='published'
            )
            ListingImage.objects.create(
                listing=listing,
                image=SimpleUploadedFile(f'img{i}.jpg', b'content', content_type='image/jpeg'),
                is_primary=True
            )
        
        url = reverse('listings-list')
        
        # Page size par défaut (20)
        response = api_client.get(url)
        assert len(response.data['results']) == 20
        
        # Page size custom
        response = api_client.get(url, {'page_size': '10'})
        assert len(response.data['results']) == 10


# ============== TESTS IMAGES ==============

@pytest.mark.django_db
class TestListingImages:
    
    def test_upload_images(self, authenticated_seller, draft_listing):
        """POST /api/listings/{id}/upload_images/ - upload d'images"""
        url = reverse('listings-upload-images', args=[draft_listing.id])
        
        image = SimpleUploadedFile(
            name='new_image.jpg',
            content=b'\x47\x49\x46\x38\x89\x61' + b'\x00' * 100,
            content_type='image/jpeg'
        )
        
        response = authenticated_seller.post(url, {'images': [image]}, format='multipart')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert draft_listing.images.count() == 1
    
    def test_upload_images_other_user_forbidden(self, authenticated_seller2, draft_listing):
        """Un autre utilisateur ne peut pas uploader d'images"""
        url = reverse('listings-upload-images', args=[draft_listing.id])
        
        image = SimpleUploadedFile(
            name='hack.jpg',
            content=b'\x47\x49\x46\x38\x89\x61' + b'\x00' * 100,
            content_type='image/jpeg'
        )
        
        response = authenticated_seller2.post(url, {'images': [image]}, format='multipart')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_upload_no_images_error(self, authenticated_seller, draft_listing):
        """Erreur si aucune image fournie"""
        url = reverse('listings-upload-images', args=[draft_listing.id])
        response = authenticated_seller.post(url, {}, format='multipart')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============== TESTS PUBLISH ==============

@pytest.mark.django_db
class TestPublishListing:
    
    def test_publish_listing_success(self, authenticated_seller, draft_listing):
        """POST /api/listings/{id}/publish/ - publier une annonce avec image"""
        # Ajouter une image d'abord
        ListingImage.objects.create(
            listing=draft_listing,
            image=SimpleUploadedFile('img.jpg', b'content', content_type='image/jpeg'),
            is_primary=True
        )
        
        url = reverse('listings-publish', args=[draft_listing.id])
        response = authenticated_seller.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        draft_listing.refresh_from_db()
        assert draft_listing.status == 'published'
    
    def test_publish_listing_without_image_fails(self, authenticated_seller, draft_listing):
        """Impossible de publier sans image"""
        url = reverse('listings-publish', args=[draft_listing.id])
        response = authenticated_seller.post(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'image' in response.data['error'].lower()
    
    def test_publish_other_user_listing_forbidden(self, authenticated_seller2, draft_listing):
        """Impossible de publier l'annonce d'un autre"""
        ListingImage.objects.create(
            listing=draft_listing,
            image=SimpleUploadedFile('img.jpg', b'content', content_type='image/jpeg'),
            is_primary=True
        )
        
        url = reverse('listings-publish', args=[draft_listing.id])
        response = authenticated_seller2.post(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============== TESTS MY LISTINGS ==============

@pytest.mark.django_db
class TestMyListings:
    
    def test_my_listings(self, authenticated_seller, draft_listing, published_listing):
        """GET /api/listings/my_listings/ - retourne les annonces du user"""
        url = reverse('listings-my-listings')
        response = authenticated_seller.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Le seller a 2 annonces (draft + published)
        titles = [r['title'] for r in response.data['results']]
        assert 'iPhone 15 Pro' in titles
        assert 'MacBook Pro M3' in titles
    
    def test_my_listings_unauthenticated(self, api_client):
        """my_listings nécessite une authentification"""
        url = reverse('listings-my-listings')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============== TESTS FAVORITES ==============

@pytest.mark.django_db
class TestFavorites:
    
    def test_toggle_favorite_add(self, authenticated_buyer, published_listing):
        """POST /api/listings/{id}/toggle_favorite/ - ajouter aux favoris"""
        url = reverse('listings-toggle-favorite', args=[published_listing.id])
        response = authenticated_buyer.post(url)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Favorite.objects.filter(listing=published_listing).exists()
    
    def test_toggle_favorite_remove(self, authenticated_buyer, buyer_user, published_listing):
        """POST /api/listings/{id}/toggle_favorite/ - retirer des favoris"""
        # Ajouter d'abord
        Favorite.objects.create(user=buyer_user, listing=published_listing)
        
        url = reverse('listings-toggle-favorite', args=[published_listing.id])
        response = authenticated_buyer.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'removed'
        assert not Favorite.objects.filter(listing=published_listing).exists()


# ============== TESTS MODELS ==============

@pytest.mark.django_db
class TestModels:
    
    def test_listing_str(self, published_listing):
        """Test __str__ du modèle Listing"""
        assert 'MacBook Pro M3' in str(published_listing)
    
    def test_category_str(self, category):
        """Test __str__ du modèle Category"""
        assert str(category) == 'Électronique'
    
    def test_listing_slug_auto_generation(self, seller_user, category):
        """Le slug est généré automatiquement"""
        listing = Listing.objects.create(
            seller=seller_user,
            category=category,
            title='Mon Super Produit',
            description='Description',
            price=Decimal('100.00'),
            location='Paris',
            status='draft'
        )
        assert listing.slug == 'mon-super-produit'
    
    def test_listing_slug_uniqueness(self, seller_user, category):
        """Les slugs sont uniques"""
        Listing.objects.create(
            seller=seller_user,
            category=category,
            title='Produit Test',
            description='Description',
            price=Decimal('100.00'),
            location='Paris',
            status='draft'
        )
        listing2 = Listing.objects.create(
            seller=seller_user,
            category=category,
            title='Produit Test',
            description='Description',
            price=Decimal('100.00'),
            location='Paris',
            status='draft'
        )
        assert listing2.slug == 'produit-test-1'
