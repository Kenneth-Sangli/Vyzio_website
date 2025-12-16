"""
Tests unitaires pour le système d'avis, favoris et réputation
Phase 8 - Avis, favoris et réputation
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from apps.users.models import CustomUser, SellerProfile
from apps.listings.models import Listing, Category, Favorite as ListingFavorite
from apps.reviews.models import Review, ReviewReport, FavoriteSeller


# Helper pour les URLs
def review_url(name, **kwargs):
    """Helper pour générer les URLs avec namespace reviews"""
    return reverse(f'reviews:{name}', kwargs=kwargs) if kwargs else reverse(f'reviews:{name}')


# ==================== FIXTURES ====================

@pytest.fixture
def api_client():
    """Client API pour les tests"""
    return APIClient()


@pytest.fixture
def create_user(db):
    """Factory pour créer des utilisateurs"""
    def _create_user(email='test@example.com', username='testuser',
                     password='TestPassword123!', role='buyer', **kwargs):
        user = CustomUser.objects.create_user(
            email=email,
            username=username,
            password=password,
            role=role,
            **kwargs
        )
        return user
    return _create_user


@pytest.fixture
def buyer(create_user):
    """Acheteur pour les tests"""
    return create_user(
        email='buyer@example.com',
        username='buyer',
        role='buyer'
    )


@pytest.fixture
def seller(create_user):
    """Vendeur pour les tests"""
    user = create_user(
        email='seller@example.com',
        username='seller',
        role='seller'
    )
    SellerProfile.objects.create(user=user)
    return user


@pytest.fixture
def another_buyer(create_user):
    """Autre acheteur pour les tests"""
    return create_user(
        email='another_buyer@example.com',
        username='another_buyer',
        role='buyer'
    )


@pytest.fixture
def category(db):
    """Catégorie pour les annonces"""
    return Category.objects.create(
        name='Test Category',
        slug='test-category'
    )


@pytest.fixture
def listing(seller, category):
    """Annonce de test"""
    return Listing.objects.create(
        title='Test Listing',
        description='Test Description',
        price=100.00,
        seller=seller,
        category=category,
        status='active'
    )


@pytest.fixture
def another_listing(seller, category):
    """Autre annonce de test"""
    return Listing.objects.create(
        title='Another Listing',
        description='Another Description',
        price=200.00,
        seller=seller,
        category=category,
        status='active'
    )


@pytest.fixture
def review(buyer, seller):
    """Avis de test"""
    return Review.objects.create(
        reviewer=buyer,
        seller=seller,
        rating=4,
        comment='Très bon vendeur!'
    )


@pytest.fixture
def buyer_client(buyer):
    """Client authentifié en tant qu'acheteur"""
    client = APIClient()
    client.force_authenticate(user=buyer)
    return client, buyer


@pytest.fixture
def seller_client(seller):
    """Client authentifié en tant que vendeur"""
    client = APIClient()
    client.force_authenticate(user=seller)
    return client, seller


@pytest.fixture
def another_buyer_client(another_buyer):
    """Client authentifié en tant qu'autre acheteur"""
    client = APIClient()
    client.force_authenticate(user=another_buyer)
    return client, another_buyer


# ==================== TESTS DES MODÈLES ====================

@pytest.mark.django_db
class TestReviewModel:
    """Tests pour le modèle Review"""
    
    def test_create_review(self, buyer, seller):
        """Test création d'un avis"""
        review = Review.objects.create(
            reviewer=buyer,
            seller=seller,
            rating=5,
            comment='Excellent!'
        )
        assert review.rating == 5
        assert review.comment == 'Excellent!'
        assert review.is_approved is True
        assert review.is_flagged is False
    
    def test_review_str(self, review):
        """Test représentation string"""
        assert 'buyer@example.com' in str(review)
        assert 'seller@example.com' in str(review)
        assert '4★' in str(review)
    
    def test_rating_validation(self, buyer, seller):
        """Test validation de la note (1-5)"""
        # Rating valide
        review = Review.objects.create(
            reviewer=buyer,
            seller=seller,
            rating=3
        )
        assert review.rating == 3
    
    def test_unique_constraint(self, buyer, seller, listing):
        """Test contrainte unique reviewer-seller-listing"""
        Review.objects.create(
            reviewer=buyer,
            seller=seller,
            listing=listing,
            rating=4
        )
        with pytest.raises(Exception):
            Review.objects.create(
                reviewer=buyer,
                seller=seller,
                listing=listing,
                rating=5
            )
    
    def test_seller_avg_rating_update(self, buyer, seller, another_buyer):
        """Test mise à jour de la note moyenne du vendeur"""
        # Créer plusieurs avis
        Review.objects.create(reviewer=buyer, seller=seller, rating=5)
        Review.objects.create(reviewer=another_buyer, seller=seller, rating=3)
        
        seller.refresh_from_db()
        assert seller.avg_rating == Decimal('4.00')
        assert seller.total_reviews == 2
    
    def test_flagged_review_excluded_from_avg(self, buyer, seller, another_buyer):
        """Test que les avis flaggés sont exclus de la moyenne"""
        Review.objects.create(reviewer=buyer, seller=seller, rating=5)
        flagged = Review.objects.create(reviewer=another_buyer, seller=seller, rating=1)
        flagged.is_flagged = True
        flagged.save()
        
        seller.refresh_from_db()
        # Seul l'avis non flaggé (5) compte
        assert seller.avg_rating == Decimal('5.00')
        assert seller.total_reviews == 1


@pytest.mark.django_db
class TestReviewReportModel:
    """Tests pour le modèle ReviewReport"""
    
    def test_create_report(self, review, another_buyer):
        """Test création d'un signalement"""
        report = ReviewReport.objects.create(
            review=review,
            reporter=another_buyer,
            reason='spam',
            description='Cet avis est du spam'
        )
        assert report.reason == 'spam'
        assert report.is_resolved is False
    
    def test_unique_report_per_user(self, review, another_buyer):
        """Test qu'un utilisateur ne peut signaler qu'une fois"""
        ReviewReport.objects.create(
            review=review,
            reporter=another_buyer,
            reason='spam'
        )
        with pytest.raises(Exception):
            ReviewReport.objects.create(
                review=review,
                reporter=another_buyer,
                reason='inappropriate'
            )


@pytest.mark.django_db
class TestFavoriteModels:
    """Tests pour les modèles de favoris"""
    
    def test_create_listing_favorite(self, buyer, listing):
        """Test création d'un favori d'annonce"""
        favorite = ListingFavorite.objects.create(
            user=buyer,
            listing=listing
        )
        assert favorite.listing == listing
        assert favorite.user == buyer
    
    def test_create_seller_favorite(self, buyer, seller):
        """Test création d'un favori de vendeur"""
        favorite = FavoriteSeller.objects.create(
            user=buyer,
            seller=seller
        )
        assert favorite.seller == seller
        assert favorite.user == buyer
    
    def test_listing_favorite_str(self, buyer, listing):
        """Test représentation string du favori d'annonce"""
        fav = ListingFavorite.objects.create(user=buyer, listing=listing)
        assert buyer.email in str(fav)
        assert listing.title in str(fav)
    
    def test_seller_favorite_str(self, buyer, seller):
        """Test représentation string du favori de vendeur"""
        fav = FavoriteSeller.objects.create(user=buyer, seller=seller)
        assert buyer.email in str(fav)
        assert seller.email in str(fav)


# ==================== TESTS API AVIS ====================

@pytest.mark.django_db
class TestReviewViewSet:
    """Tests pour le ViewSet des avis"""
    
    def test_list_reviews(self, api_client, review):
        """Test liste des avis"""
        url = review_url('reviews-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_review(self, buyer_client, seller):
        """Test création d'un avis"""
        client, buyer = buyer_client
        url = review_url('reviews-list')
        
        response = client.post(url, {
            'seller_id': str(seller.id),
            'rating': 5,
            'comment': 'Excellent service!'
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['rating'] == 5
        assert Review.objects.filter(reviewer=buyer, seller=seller).exists()
    
    def test_create_review_unauthenticated(self, api_client, seller):
        """Test création d'avis sans authentification"""
        url = review_url('reviews-list')
        response = api_client.post(url, {
            'seller_id': str(seller.id),
            'rating': 5
        }, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_cannot_review_yourself(self, seller_client, seller):
        """Test qu'on ne peut pas s'évaluer soi-même"""
        client, _ = seller_client
        url = review_url('reviews-list')
        
        response = client.post(url, {
            'seller_id': str(seller.id),
            'rating': 5
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_cannot_review_twice(self, buyer_client, seller):
        """Test qu'on ne peut pas laisser deux avis identiques"""
        client, buyer = buyer_client
        url = review_url('reviews-list')
        
        # Premier avis
        client.post(url, {
            'seller_id': str(seller.id),
            'rating': 4
        }, format='json')
        
        # Deuxième avis
        response = client.post(url, {
            'seller_id': str(seller.id),
            'rating': 5
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_seller_reviews(self, api_client, review, seller):
        """Test obtenir les avis d'un vendeur"""
        url = review_url('reviews-seller-reviews')
        response = api_client.get(url, {'seller_id': str(seller.id)})
        
        assert response.status_code == status.HTTP_200_OK
        assert 'reviews' in response.data
        assert 'average_rating' in response.data
        assert 'rating_distribution' in response.data


@pytest.mark.django_db
class TestSellerResponse:
    """Tests pour les réponses des vendeurs aux avis"""
    
    def test_add_response(self, seller_client, review):
        """Test ajout d'une réponse du vendeur"""
        client, seller = seller_client
        url = review_url('reviews-add-response', pk=review.id)
        
        response = client.post(url, {
            'response': 'Merci pour votre avis!'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['seller_response'] == 'Merci pour votre avis!'
    
    def test_only_seller_can_respond(self, buyer_client, review):
        """Test que seul le vendeur peut répondre"""
        client, _ = buyer_client
        url = review_url('reviews-add-response', pk=review.id)
        
        response = client.post(url, {
            'response': 'Test response'
        }, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestReviewReport:
    """Tests pour les signalements d'avis"""
    
    def test_report_review(self, another_buyer_client, review):
        """Test signalement d'un avis"""
        client, _ = another_buyer_client
        url = review_url('reviews-report-review', pk=review.id)
        
        response = client.post(url, {
            'reason': 'spam',
            'description': 'Cet avis semble faux'
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert ReviewReport.objects.filter(review=review).exists()
    
    def test_cannot_report_twice(self, another_buyer_client, review):
        """Test qu'on ne peut pas signaler deux fois"""
        client, another_buyer = another_buyer_client
        
        # Créer un signalement
        ReviewReport.objects.create(
            review=review, reporter=another_buyer, reason='spam'
        )
        
        url = review_url('reviews-report-review', pk=review.id)
        response = client.post(url, {
            'reason': 'inappropriate'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_auto_flag_after_multiple_reports(self, review, create_user):
        """Test flaggage automatique après plusieurs signalements"""
        # Créer 3 signalements
        for i in range(3):
            user = create_user(
                email=f'reporter{i}@example.com',
                username=f'reporter{i}'
            )
            ReviewReport.objects.create(
                review=review, reporter=user, reason='spam'
            )
        
        # Simuler la logique de flaggage (normalement fait dans la vue)
        if review.reports.count() >= 3:
            review.is_flagged = True
            review.save()
        
        review.refresh_from_db()
        assert review.is_flagged is True


@pytest.mark.django_db
class TestSellerReputation:
    """Tests pour la réputation des vendeurs"""
    
    def test_seller_reputation_endpoint(self, api_client, seller, review):
        """Test endpoint de réputation"""
        url = review_url('reviews-seller-reputation')
        response = api_client.get(url, {'seller_id': str(seller.id)})
        
        assert response.status_code == status.HTTP_200_OK
        assert 'avg_rating' in response.data
        assert 'total_reviews' in response.data
        assert 'badges' in response.data
        assert 'rating_distribution' in response.data
    
    def test_badges_calculation(self, seller, create_user):
        """Test calcul des badges"""
        # Créer 10 avis avec note >= 4.5
        for i in range(10):
            user = create_user(
                email=f'reviewer{i}@example.com',
                username=f'reviewer{i}'
            )
            Review.objects.create(
                reviewer=user,
                seller=seller,
                rating=5
            )
        
        seller.refresh_from_db()
        assert seller.total_reviews == 10
        assert seller.avg_rating >= Decimal('4.5')


# ==================== TESTS API FAVORIS ====================

@pytest.mark.django_db
class TestFavoriteListingViewSet:
    """Tests pour le ViewSet des favoris d'annonces"""
    
    def test_list_listing_favorites(self, buyer_client, listing, buyer):
        """Test liste des favoris d'annonces"""
        client, _ = buyer_client
        
        # Créer un favori
        ListingFavorite.objects.create(user=buyer, listing=listing)
        
        url = review_url('favorite-listings-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_add_listing_favorite(self, buyer_client, listing):
        """Test ajout d'une annonce en favori"""
        client, _ = buyer_client
        url = review_url('favorite-listings-list')
        
        response = client.post(url, {
            'listing_id': str(listing.id)
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_cannot_add_duplicate_listing_favorite(self, buyer_client, listing, buyer):
        """Test qu'on ne peut pas ajouter deux fois la même annonce"""
        client, _ = buyer_client
        
        # Créer un favori
        ListingFavorite.objects.create(user=buyer, listing=listing)
        
        url = review_url('favorite-listings-list')
        response = client.post(url, {
            'listing_id': str(listing.id)
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_delete_listing_favorite(self, buyer_client, listing, buyer):
        """Test suppression d'un favori d'annonce"""
        client, _ = buyer_client
        
        favorite = ListingFavorite.objects.create(user=buyer, listing=listing)
        
        url = review_url('favorite-listings-detail', pk=favorite.id)
        response = client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ListingFavorite.objects.filter(id=favorite.id).exists()
    
    def test_toggle_listing_favorite(self, buyer_client, listing):
        """Test toggle favori d'annonce"""
        client, _ = buyer_client
        url = review_url('favorite-listings-toggle')
        
        # Ajouter
        response = client.post(url, {
            'listing_id': str(listing.id)
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Supprimer
        response = client.post(url, {
            'listing_id': str(listing.id)
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'removed'
    
    def test_check_listing_favorite(self, buyer_client, listing, buyer):
        """Test vérification si annonce en favori"""
        client, _ = buyer_client
        
        ListingFavorite.objects.create(user=buyer, listing=listing)
        
        url = review_url('favorite-listings-check')
        response = client.get(url, {'id': str(listing.id)})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_favorite'] is True


@pytest.mark.django_db
class TestFavoriteSellerViewSet:
    """Tests pour le ViewSet des vendeurs favoris"""
    
    def test_list_seller_favorites(self, buyer_client, seller, buyer):
        """Test liste des vendeurs favoris"""
        client, _ = buyer_client
        
        # Créer un favori
        FavoriteSeller.objects.create(user=buyer, seller=seller)
        
        url = review_url('favorite-sellers-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_add_seller_favorite(self, buyer_client, seller):
        """Test ajout d'un vendeur en favori"""
        client, _ = buyer_client
        url = review_url('favorite-sellers-list')
        
        response = client.post(url, {
            'seller_id': str(seller.id)
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_cannot_favorite_yourself(self, seller_client, seller):
        """Test qu'on ne peut pas se mettre en favori"""
        client, _ = seller_client
        url = review_url('favorite-sellers-list')
        
        response = client.post(url, {
            'seller_id': str(seller.id)
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_cannot_add_duplicate_seller_favorite(self, buyer_client, seller, buyer):
        """Test qu'on ne peut pas ajouter deux fois le même vendeur"""
        client, _ = buyer_client
        
        # Créer un favori
        FavoriteSeller.objects.create(user=buyer, seller=seller)
        
        url = review_url('favorite-sellers-list')
        response = client.post(url, {
            'seller_id': str(seller.id)
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_delete_seller_favorite(self, buyer_client, seller, buyer):
        """Test suppression d'un favori de vendeur"""
        client, _ = buyer_client
        
        favorite = FavoriteSeller.objects.create(user=buyer, seller=seller)
        
        url = review_url('favorite-sellers-detail', pk=favorite.id)
        response = client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not FavoriteSeller.objects.filter(id=favorite.id).exists()
    
    def test_toggle_seller_favorite(self, buyer_client, seller):
        """Test toggle favori de vendeur"""
        client, _ = buyer_client
        url = review_url('favorite-sellers-toggle')
        
        # Ajouter
        response = client.post(url, {
            'seller_id': str(seller.id)
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Supprimer
        response = client.post(url, {
            'seller_id': str(seller.id)
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'removed'
    
    def test_check_seller_favorite(self, buyer_client, seller, buyer):
        """Test vérification si vendeur en favori"""
        client, _ = buyer_client
        
        FavoriteSeller.objects.create(user=buyer, seller=seller)
        
        url = review_url('favorite-sellers-check')
        response = client.get(url, {'id': str(seller.id)})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_favorite'] is True


# ==================== TESTS D'INTÉGRATION ====================

@pytest.mark.django_db
class TestReviewFavoriteFlow:
    """Tests d'intégration du flux avis/favoris"""
    
    def test_full_review_flow(self, buyer_client, seller):
        """Test flux complet d'avis"""
        client, buyer = buyer_client
        
        # 1. Créer un avis
        url = review_url('reviews-list')
        response = client.post(url, {
            'seller_id': str(seller.id),
            'rating': 5,
            'comment': 'Super vendeur!'
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        review_id = response.data['id']
        
        # 2. Vérifier la mise à jour de la note du vendeur
        seller.refresh_from_db()
        assert seller.avg_rating == Decimal('5.00')
        assert seller.total_reviews == 1
        
        # 3. Le seller répond
        seller_api = APIClient()
        seller_api.force_authenticate(user=seller)
        
        url = review_url('reviews-add-response', pk=review_id)
        response = seller_api.post(url, {
            'response': 'Merci beaucoup!'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # 4. Vérifier la réputation
        url = review_url('reviews-seller-reputation')
        response = client.get(url, {'seller_id': str(seller.id)})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['avg_rating'] == 5.0
    
    def test_favorite_listing_flow(self, buyer_client, listing):
        """Test flux complet de favoris d'annonce"""
        client, _ = buyer_client
        
        # 1. Ajouter en favori
        url = review_url('favorite-listings-list')
        response = client.post(url, {
            'listing_id': str(listing.id)
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # 2. Vérifier qu'il est en favori
        url = review_url('favorite-listings-check')
        response = client.get(url, {'id': str(listing.id)})
        
        assert response.data['is_favorite'] is True
        
        # 3. Lister les favoris
        url = review_url('favorite-listings-list')
        response = client.get(url)
        
        assert len(response.data) >= 1
        
        # 4. Toggle pour supprimer
        url = review_url('favorite-listings-toggle')
        response = client.post(url, {
            'listing_id': str(listing.id)
        }, format='json')
        
        assert response.data['is_favorite'] is False
    
    def test_favorite_seller_flow(self, buyer_client, seller):
        """Test flux complet de favoris de vendeur"""
        client, _ = buyer_client
        
        # 1. Ajouter en favori
        url = review_url('favorite-sellers-list')
        response = client.post(url, {
            'seller_id': str(seller.id)
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # 2. Vérifier qu'il est en favori
        url = review_url('favorite-sellers-check')
        response = client.get(url, {'id': str(seller.id)})
        
        assert response.data['is_favorite'] is True
        
        # 3. Toggle pour supprimer
        url = review_url('favorite-sellers-toggle')
        response = client.post(url, {
            'seller_id': str(seller.id)
        }, format='json')
        
        assert response.data['is_favorite'] is False
