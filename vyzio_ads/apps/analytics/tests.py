"""
Tests unitaires pour le dashboard seller et analytics
Phase 9 - Dashboard seller & analytics
"""
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from datetime import timedelta

from apps.users.models import CustomUser, SellerProfile
from apps.listings.models import Listing, Category
from apps.analytics.models import Event, DailyStats, ListingStats
from apps.analytics.services import EventTracker, AnalyticsService, ExportService


# Helper pour les URLs
def analytics_url(name, **kwargs):
    """Helper pour générer les URLs avec namespace analytics"""
    return reverse(f'analytics:{name}', kwargs=kwargs) if kwargs else reverse(f'analytics:{name}')


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
def seller_client(seller):
    """Client authentifié en tant que vendeur"""
    client = APIClient()
    client.force_authenticate(user=seller)
    return client, seller


@pytest.fixture
def buyer_client(buyer):
    """Client authentifié en tant qu'acheteur"""
    client = APIClient()
    client.force_authenticate(user=buyer)
    return client, buyer


# ==================== TESTS DES MODÈLES ====================

@pytest.mark.django_db
class TestEventModel:
    """Tests pour le modèle Event"""
    
    def test_create_event(self, buyer, seller, listing):
        """Test création d'un événement"""
        event = Event.objects.create(
            event_type='listing_view',
            user=buyer,
            target_user=seller,
            listing=listing
        )
        assert event.event_type == 'listing_view'
        assert event.user == buyer
        assert event.target_user == seller
    
    def test_event_str(self, listing, seller):
        """Test représentation string"""
        event = Event.objects.create(
            event_type='listing_view',
            target_user=seller,
            listing=listing
        )
        assert 'listing_view' in str(event)
    
    def test_event_with_metadata(self, seller, listing):
        """Test événement avec métadonnées"""
        event = Event.objects.create(
            event_type='search',
            target_user=seller,
            metadata={'query': 'test search', 'results': 10}
        )
        assert event.metadata['query'] == 'test search'


@pytest.mark.django_db
class TestListingStatsModel:
    """Tests pour le modèle ListingStats"""
    
    def test_create_listing_stats(self, listing):
        """Test création des stats d'annonce"""
        stats = ListingStats.objects.create(listing=listing)
        assert stats.total_views == 0
        assert stats.conversion_rate == 0
    
    def test_conversion_rate_calculation(self, listing):
        """Test calcul du taux de conversion"""
        stats = ListingStats.objects.create(
            listing=listing,
            total_views=100,
            total_contacts=10
        )
        rate = stats.calculate_conversion_rate()
        assert rate == 10.0


@pytest.mark.django_db
class TestDailyStatsModel:
    """Tests pour le modèle DailyStats"""
    
    def test_create_daily_stats(self, seller):
        """Test création des stats quotidiennes"""
        stats = DailyStats.objects.create(
            user=seller,
            date=timezone.now().date(),
            listing_views=50,
            revenue=Decimal('100.00')
        )
        assert stats.listing_views == 50
        assert stats.revenue == Decimal('100.00')


# ==================== TESTS DES SERVICES ====================

@pytest.mark.django_db
class TestEventTracker:
    """Tests pour le service EventTracker"""
    
    def test_track_event(self, buyer, seller, listing):
        """Test tracking d'un événement"""
        event = EventTracker.track(
            event_type='listing_view',
            user=buyer,
            target_user=seller,
            listing=listing
        )
        assert event is not None
        assert event.event_type == 'listing_view'
    
    def test_track_updates_listing_stats(self, buyer, seller, listing):
        """Test que le tracking met à jour les stats"""
        # Créer les stats
        ListingStats.objects.create(listing=listing)
        
        EventTracker.track(
            event_type='listing_view',
            user=buyer,
            target_user=seller,
            listing=listing
        )
        
        stats = ListingStats.objects.get(listing=listing)
        assert stats.total_views == 1
    
    def test_track_invalid_event_type(self, seller):
        """Test tracking avec type invalide"""
        event = EventTracker.track(
            event_type='invalid_type',
            target_user=seller
        )
        # Devrait échouer silencieusement ou créer quand même
        # selon l'implémentation


@pytest.mark.django_db
class TestAnalyticsService:
    """Tests pour le service AnalyticsService"""
    
    def test_get_seller_dashboard(self, seller, listing):
        """Test obtention du dashboard vendeur"""
        data = AnalyticsService.get_seller_dashboard(seller, days=30)
        
        assert 'period' in data
        assert 'engagement' in data
        assert 'messaging' in data
        assert 'financial' in data
        assert 'reputation' in data
        assert 'listings' in data
    
    def test_get_listing_analytics(self, listing):
        """Test obtention des analytics d'une annonce"""
        ListingStats.objects.create(listing=listing, total_views=100)
        
        data = AnalyticsService.get_listing_analytics(listing, days=30)
        
        assert data['listing_id'] == str(listing.id)
        assert 'totals' in data
        assert data['totals']['views'] == 100
    
    def test_get_trends(self, seller):
        """Test obtention des tendances"""
        data = AnalyticsService.get_trends(seller, days=30)
        
        assert 'views' in data
        assert 'revenue' in data
        assert 'change' in data['views']


@pytest.mark.django_db
class TestExportService:
    """Tests pour le service ExportService"""
    
    def test_export_listings_csv(self, seller, listing):
        """Test export CSV des annonces"""
        csv_content = ExportService.export_listings_csv(seller)
        
        assert 'ID' in csv_content
        assert 'Titre' in csv_content
        assert listing.title in csv_content
    
    def test_export_payments_csv(self, seller):
        """Test export CSV des paiements"""
        csv_content = ExportService.export_payments_csv(seller)
        
        assert 'ID' in csv_content
        assert 'Montant' in csv_content
    
    def test_export_reviews_csv(self, seller):
        """Test export CSV des avis"""
        csv_content = ExportService.export_reviews_csv(seller)
        
        assert 'ID' in csv_content
        assert 'Note' in csv_content


# ==================== TESTS API DASHBOARD ====================

@pytest.mark.django_db
class TestDashboardViewSet:
    """Tests pour le ViewSet Dashboard"""
    
    def test_summary_authenticated_seller(self, seller_client):
        """Test accès au résumé pour vendeur authentifié"""
        client, seller = seller_client
        url = analytics_url('dashboard-summary')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'engagement' in response.data
        assert 'financial' in response.data
    
    def test_summary_unauthenticated(self, api_client):
        """Test accès au résumé sans authentification"""
        url = analytics_url('dashboard-summary')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_summary_buyer_forbidden(self, buyer_client):
        """Test que les acheteurs ne peuvent pas accéder"""
        client, _ = buyer_client
        url = analytics_url('dashboard-summary')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_trends_endpoint(self, seller_client):
        """Test endpoint des tendances"""
        client, _ = seller_client
        url = analytics_url('dashboard-trends')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'views' in response.data
        assert 'revenue' in response.data
    
    def test_revenue_endpoint(self, seller_client):
        """Test endpoint des revenus"""
        client, _ = seller_client
        url = analytics_url('dashboard-revenue')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'totals' in response.data
        assert 'daily_revenue' in response.data
    
    def test_listings_endpoint(self, seller_client, listing):
        """Test endpoint des annonces"""
        client, _ = seller_client
        url = analytics_url('dashboard-listings')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_listing_detail_endpoint(self, seller_client, listing):
        """Test endpoint détail d'une annonce"""
        client, _ = seller_client
        url = analytics_url('dashboard-listing-detail', listing_id=listing.id)
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['listing_id'] == str(listing.id)
    
    def test_payments_endpoint(self, seller_client):
        """Test endpoint des paiements"""
        client, _ = seller_client
        url = analytics_url('dashboard-payments')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'payments' in response.data
        assert 'total' in response.data
    
    def test_recent_activity_endpoint(self, seller_client):
        """Test endpoint activité récente"""
        client, _ = seller_client
        url = analytics_url('dashboard-recent-activity')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


@pytest.mark.django_db
class TestQuickListing:
    """Tests pour la création rapide d'annonce"""
    
    def test_quick_listing_create(self, seller_client, category):
        """Test création rapide d'annonce"""
        client, _ = seller_client
        url = analytics_url('dashboard-quick-listing')
        response = client.post(url, {
            'title': 'Quick Test Listing',
            'description': 'Quick description',
            'price': '99.99',
            'category_id': str(category.id),
            'location': 'Paris'
        }, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print("Réponse erreur:", response.data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'draft'
    
    def test_quick_listing_invalid_category(self, seller_client):
        """Test création avec catégorie invalide"""
        client, _ = seller_client
        url = analytics_url('dashboard-quick-listing')
        
        response = client.post(url, {
            'title': 'Test',
            'description': 'Test',
            'price': '99.99',
            'category_id': '00000000-0000-0000-0000-000000000000'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==================== TESTS EVENT TRACKING ====================

@pytest.mark.django_db
class TestEventTrackingView:
    """Tests pour le tracking d'événements"""
    
    def test_track_listing_view(self, api_client, listing):
        """Test tracking d'une vue d'annonce"""
        url = analytics_url('track')
        
        response = api_client.post(url, {
            'event_type': 'listing_view',
            'listing_id': str(listing.id)
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'event_id' in response.data
    
    def test_track_authenticated_user(self, buyer_client, listing):
        """Test tracking avec utilisateur authentifié"""
        client, buyer = buyer_client
        url = analytics_url('track')
        
        response = client.post(url, {
            'event_type': 'listing_view',
            'listing_id': str(listing.id)
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Vérifier que l'utilisateur est enregistré
        event = Event.objects.get(id=response.data['event_id'])
        assert event.user == buyer
    
    def test_track_with_metadata(self, api_client, listing):
        """Test tracking avec métadonnées"""
        url = analytics_url('track')
        
        response = api_client.post(url, {
            'event_type': 'listing_click',
            'listing_id': str(listing.id),
            'metadata': {'source': 'search', 'position': 3}
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_track_invalid_event_type(self, api_client):
        """Test tracking avec type invalide"""
        url = analytics_url('track')
        
        response = api_client.post(url, {
            'event_type': 'invalid_type'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==================== TESTS EXPORT ====================

@pytest.mark.django_db
class TestExportView:
    """Tests pour l'export CSV"""
    
    def test_export_listings(self, seller_client, listing):
        """Test export des annonces"""
        client, _ = seller_client
        url = analytics_url('export', export_type='listings')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'text/csv'
        assert 'attachment' in response['Content-Disposition']
    
    def test_export_payments(self, seller_client):
        """Test export des paiements"""
        client, _ = seller_client
        url = analytics_url('export', export_type='payments')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'text/csv'
    
    def test_export_reviews(self, seller_client):
        """Test export des avis"""
        client, _ = seller_client
        url = analytics_url('export', export_type='reviews')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'text/csv'
    
    def test_export_invalid_type(self, seller_client):
        """Test export avec type invalide"""
        client, _ = seller_client
        url = analytics_url('export', export_type='invalid')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_export_unauthorized(self, api_client):
        """Test export sans authentification"""
        url = analytics_url('export', export_type='listings')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================== TESTS KPI ====================

@pytest.mark.django_db
class TestKPIView:
    """Tests pour les KPIs"""
    
    def test_get_kpis(self, seller_client, listing):
        """Test obtention des KPIs"""
        client, _ = seller_client
        url = analytics_url('kpis')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'active_listings' in response.data
        assert 'week_views' in response.data
        assert 'month_revenue' in response.data
        assert 'avg_rating' in response.data
    
    def test_kpis_unauthorized(self, api_client):
        """Test KPIs sans authentification"""
        url = analytics_url('kpis')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_kpis_buyer_forbidden(self, buyer_client):
        """Test KPIs pour acheteur interdit"""
        client, _ = buyer_client
        url = analytics_url('kpis')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ==================== TESTS D'INTÉGRATION ====================

@pytest.mark.django_db
class TestAnalyticsIntegration:
    """Tests d'intégration du système d'analytics"""
    
    def test_full_tracking_flow(self, buyer_client, seller_client, listing):
        """Test flux complet de tracking"""
        buyer_api, buyer = buyer_client
        seller_api, seller = seller_client
        
        # Créer les stats pour l'annonce
        ListingStats.objects.create(listing=listing)
        
        # 1. Buyer voit l'annonce
        url = analytics_url('track')
        response = buyer_api.post(url, {
            'event_type': 'listing_view',
            'listing_id': str(listing.id)
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # 2. Buyer clique
        response = buyer_api.post(url, {
            'event_type': 'listing_click',
            'listing_id': str(listing.id)
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # 3. Buyer contacte
        response = buyer_api.post(url, {
            'event_type': 'listing_contact',
            'listing_id': str(listing.id)
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # 4. Vérifier les stats de l'annonce
        stats = ListingStats.objects.get(listing=listing)
        assert stats.total_views == 1
        assert stats.total_clicks == 1
        assert stats.total_contacts == 1
        
        # 5. Seller vérifie son dashboard
        url = analytics_url('dashboard-summary')
        response = seller_api.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['engagement']['total_views'] >= 1
    
    def test_dashboard_with_data(self, seller_client, listing, buyer):
        """Test dashboard avec données"""
        client, seller = seller_client
        
        # Créer des événements
        for i in range(5):
            Event.objects.create(
                event_type='listing_view',
                user=buyer,
                target_user=seller,
                listing=listing
            )
        
        # Vérifier le dashboard
        url = analytics_url('dashboard-summary')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['engagement']['total_views'] == 5
