"""
Tests unitaires pour le système de paiements (Stripe)
Phase 6 - Abonnements (Option A) + Pay-per-post (Option B)
"""
import pytest
import json
from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch, MagicMock, PropertyMock
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import CustomUser, SellerProfile
from apps.payments.models import (
    SubscriptionPlan, Subscription, Payment, Invoice,
    PostCreditPack, PostCredit, PostCreditTransaction,
    Coupon, WebhookEvent
)
from apps.payments.services.stripe_service import StripeService
from apps.payments.services.webhook_handler import WebhookHandler


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
def authenticated_client(api_client, create_user):
    """Client authentifié"""
    user = create_user()
    api_client.force_authenticate(user=user)
    return api_client, user


@pytest.fixture
def seller_client(api_client, create_user):
    """Client authentifié en tant que vendeur"""
    user = create_user(
        email='seller@example.com',
        username='seller',
        role='seller'
    )
    SellerProfile.objects.create(user=user)
    api_client.force_authenticate(user=user)
    return api_client, user


@pytest.fixture
def subscription_plan(db):
    """Plan d'abonnement de test"""
    return SubscriptionPlan.objects.create(
        name='Pro',
        slug='pro',
        plan_type='pro',
        billing_cycle='monthly',
        price=Decimal('29.99'),
        stripe_price_id='price_test_pro',
        stripe_product_id='prod_test_pro',
        max_listings=50,
        max_images_per_listing=10,
        can_boost=True,
        boost_count_per_month=5,
        featured_badge=True,
        priority_support=True,
        analytics_access=True,
        description='Plan Pro pour vendeurs professionnels',
        features_list=['50 annonces', 'Badge Pro', 'Support prioritaire'],
        is_active=True,
        is_popular=True
    )


@pytest.fixture
def basic_plan(db):
    """Plan basic de test pour éviter conflits unique"""
    return SubscriptionPlan.objects.create(
        name='Basic',
        slug='basic',
        plan_type='basic',
        billing_cycle='monthly',
        price=Decimal('9.99'),
        stripe_price_id='price_test_basic',
        stripe_product_id='prod_test_basic',
        max_listings=10,
        max_images_per_listing=5,
        can_boost=False,
        boost_count_per_month=0,
        featured_badge=False,
        priority_support=False,
        analytics_access=False,
        description='Plan Basic',
        is_active=True
    )


@pytest.fixture
def post_credit_pack(db):
    """Pack de crédits de test"""
    return PostCreditPack.objects.create(
        name='Pack Starter',
        slug='pack-starter',
        credits=10,
        price=Decimal('9.99'),
        stripe_price_id='price_test_pack',
        stripe_product_id='prod_test_pack',
        bonus_credits=2,
        description='10 crédits + 2 bonus',
        is_active=True,
        is_popular=True
    )


@pytest.fixture
def coupon(db):
    """Coupon de réduction de test"""
    return Coupon.objects.create(
        code='TEST20',
        discount_type='percentage',
        discount_value=Decimal('20.00'),
        applies_to_subscription=True,
        applies_to_post_credit=True,
        max_uses=100,
        max_uses_per_user=1,
        valid_from=timezone.now() - timedelta(days=1),
        valid_until=timezone.now() + timedelta(days=30),
        is_active=True,
        stripe_coupon_id='coupon_test'
    )


@pytest.fixture
def mock_stripe():
    """Mock des appels Stripe"""
    with patch('apps.payments.services.stripe_service.get_stripe') as mock_get:
        mock = MagicMock()
        mock_get.return_value = mock
        
        # Mock Customer
        mock.Customer.create.return_value = MagicMock(id='cus_test123')
        mock.Customer.retrieve.return_value = MagicMock(id='cus_test123')
        
        # Mock Checkout Session
        mock.checkout.Session.create.return_value = MagicMock(
            id='cs_test123',
            url='https://checkout.stripe.com/test'
        )
        
        # Mock Subscription
        mock.Subscription.retrieve.return_value = MagicMock(
            id='sub_test123',
            status='active',
            current_period_start=1234567890,
            current_period_end=1237159890
        )
        mock.Subscription.modify.return_value = MagicMock(id='sub_test123')
        mock.Subscription.cancel.return_value = MagicMock(id='sub_test123', status='canceled')
        
        # Mock Billing Portal
        mock.billing_portal.Session.create.return_value = MagicMock(
            url='https://billing.stripe.com/test'
        )
        
        # Mock Webhook
        mock.Webhook.construct_event.return_value = MagicMock(
            id='evt_test123',
            type='checkout.session.completed'
        )
        
        yield mock


@pytest.fixture
def mock_stripe_configured():
    """Mock Stripe configuré"""
    with patch('apps.payments.services.stripe_service.is_stripe_configured', return_value=True):
        with patch('apps.payments.services.stripe_service.get_stripe') as mock_get:
            mock = MagicMock()
            mock_get.return_value = mock
            
            mock.Customer.create.return_value = MagicMock(id='cus_test123')
            mock.checkout.Session.create.return_value = MagicMock(
                id='cs_test123',
                url='https://checkout.stripe.com/test'
            )
            mock.Subscription.modify.return_value = MagicMock(id='sub_test123')
            mock.billing_portal.Session.create.return_value = MagicMock(
                url='https://billing.stripe.com/test'
            )
            
            yield mock


# ==================== TESTS DES MODÈLES ====================

@pytest.mark.django_db
class TestSubscriptionPlanModel:
    """Tests pour le modèle SubscriptionPlan"""
    
    def test_create_subscription_plan(self, subscription_plan):
        """Test création d'un plan"""
        assert subscription_plan.name == 'Pro'
        assert subscription_plan.price == Decimal('29.99')
        assert subscription_plan.max_listings == 50
        assert subscription_plan.can_boost is True
    
    def test_subscription_plan_str(self, subscription_plan):
        """Test représentation string"""
        # Format: "Pro - Mensuel (29.99€)"
        assert 'Pro' in str(subscription_plan)
        assert '29.99' in str(subscription_plan)
    
    def test_unique_plan_type_billing_cycle(self, db, subscription_plan):
        """Test contrainte unique plan_type + billing_cycle"""
        with pytest.raises(Exception):
            SubscriptionPlan.objects.create(
                name='Pro Duplicate',
                slug='pro-dup',
                plan_type='pro',
                billing_cycle='monthly',
                price=Decimal('29.99'),
                stripe_price_id='price_test_dup',
                stripe_product_id='prod_test_dup',
                max_listings=50
            )


@pytest.mark.django_db
class TestSubscriptionModel:
    """Tests pour le modèle Subscription"""
    
    def test_create_subscription(self, create_user, subscription_plan):
        """Test création d'un abonnement"""
        user = create_user()
        subscription = Subscription.objects.create(
            user=user,
            plan=subscription_plan,
            status='active',
            stripe_subscription_id='sub_test123',
            stripe_customer_id='cus_test123',
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=30)
        )
        assert subscription.is_active is True
        assert subscription.can_create_listing is True
    
    def test_subscription_remaining_listings(self, create_user, subscription_plan):
        """Test calcul des annonces restantes"""
        user = create_user()
        subscription = Subscription.objects.create(
            user=user,
            plan=subscription_plan,
            status='active',
            stripe_subscription_id='sub_test123',
            stripe_customer_id='cus_test123',
            listings_used=10
        )
        assert subscription.remaining_listings == 40  # 50 - 10
    
    def test_subscription_inactive_when_cancelled(self, create_user, subscription_plan):
        """Test abonnement inactif si annulé"""
        user = create_user()
        subscription = Subscription.objects.create(
            user=user,
            plan=subscription_plan,
            status='cancelled',
            stripe_subscription_id='sub_test123',
            stripe_customer_id='cus_test123',
        )
        assert subscription.is_active is False


@pytest.mark.django_db
class TestPostCreditModel:
    """Tests pour le modèle PostCredit"""
    
    def test_create_post_credit(self, create_user):
        """Test création de crédits"""
        user = create_user()
        credit = PostCredit.objects.create(
            user=user,
            balance=10,
            total_purchased=10
        )
        assert credit.balance == 10
        # Pas de propriété can_post, on vérifie juste le balance > 0
        assert credit.balance > 0
    
    def test_use_credit(self, create_user):
        """Test utilisation d'un crédit"""
        user = create_user()
        credit = PostCredit.objects.create(
            user=user,
            balance=10,
            total_purchased=10
        )
        # use_credit retourne le nouveau solde
        new_balance = credit.use_credit()
        assert new_balance == 9
        assert credit.balance == 9
        assert credit.total_used == 1
    
    def test_use_credit_no_balance(self, create_user):
        """Test utilisation sans solde - doit lever ValueError"""
        user = create_user()
        credit = PostCredit.objects.create(
            user=user,
            balance=0,
            total_purchased=0
        )
        with pytest.raises(ValueError, match="Pas assez de crédits"):
            credit.use_credit()
    
    def test_add_credits(self, create_user):
        """Test ajout de crédits"""
        user = create_user()
        credit = PostCredit.objects.create(
            user=user,
            balance=5,
            total_purchased=5
        )
        credit.add_credits(10)
        assert credit.balance == 15
        assert credit.total_purchased == 15


@pytest.mark.django_db
class TestPaymentModel:
    """Tests pour le modèle Payment"""
    
    def test_create_payment(self, create_user, subscription_plan):
        """Test création d'un paiement"""
        user = create_user()
        payment = Payment.objects.create(
            user=user,
            amount=Decimal('29.99'),
            currency='EUR',
            payment_type='subscription',
            status='pending',
            subscription_plan=subscription_plan
        )
        assert payment.status == 'pending'
        assert payment.payment_type == 'subscription'
    
    def test_payment_complete(self, create_user):
        """Test completion d'un paiement"""
        user = create_user()
        payment = Payment.objects.create(
            user=user,
            amount=Decimal('9.99'),
            currency='EUR',
            payment_type='post_credit',
            status='pending'
        )
        payment.mark_completed()
        assert payment.status == 'completed'
        assert payment.completed_at is not None
    
    def test_payment_failed(self, create_user):
        """Test échec d'un paiement"""
        user = create_user()
        payment = Payment.objects.create(
            user=user,
            amount=Decimal('9.99'),
            currency='EUR',
            payment_type='post_credit',
            status='pending'
        )
        payment.mark_failed('Carte refusée')
        assert payment.status == 'failed'
        assert payment.error_message == 'Carte refusée'


@pytest.mark.django_db
class TestCouponModel:
    """Tests pour le modèle Coupon"""
    
    def test_coupon_is_valid(self, coupon):
        """Test validité du coupon"""
        # is_valid est une méthode, pas une propriété
        assert coupon.is_valid() is True
    
    def test_coupon_expired(self, db):
        """Test coupon expiré"""
        coupon = Coupon.objects.create(
            code='EXPIRED',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            valid_from=timezone.now() - timedelta(days=30),
            valid_until=timezone.now() - timedelta(days=1),
            is_active=True
        )
        assert coupon.is_valid() is False
    
    def test_coupon_max_uses_reached(self, db):
        """Test coupon max utilisations atteint"""
        coupon = Coupon.objects.create(
            code='MAXED',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            max_uses=10,
            uses_count=10,
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=30),
            is_active=True
        )
        assert coupon.is_valid() is False
    
    def test_coupon_inactive(self, db):
        """Test coupon désactivé"""
        coupon = Coupon.objects.create(
            code='INACTIVE',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=30),
            is_active=False
        )
        assert coupon.is_valid() is False


@pytest.mark.django_db
class TestWebhookEventModel:
    """Tests pour le modèle WebhookEvent"""
    
    def test_create_webhook_event(self, db):
        """Test création d'un événement webhook"""
        event = WebhookEvent.objects.create(
            stripe_event_id='evt_test123',
            event_type='checkout.session.completed',
            payload={'test': 'data'}
        )
        assert event.processed is False
        assert event.retry_count == 0
    
    def test_webhook_event_idempotence(self, db):
        """Test idempotence des événements"""
        WebhookEvent.objects.create(
            stripe_event_id='evt_unique',
            event_type='checkout.session.completed',
            payload={}
        )
        # Tentative de doublon
        with pytest.raises(Exception):
            WebhookEvent.objects.create(
                stripe_event_id='evt_unique',
                event_type='checkout.session.completed',
                payload={}
            )


@pytest.mark.django_db
class TestPostCreditPackModel:
    """Tests pour le modèle PostCreditPack"""
    
    def test_create_pack(self, post_credit_pack):
        """Test création d'un pack"""
        assert post_credit_pack.credits == 10
        assert post_credit_pack.bonus_credits == 2
        assert post_credit_pack.total_credits == 12
    
    def test_price_per_credit(self, post_credit_pack):
        """Test calcul du prix par crédit"""
        expected = Decimal('9.99') / 12
        assert post_credit_pack.price_per_credit == expected


# ==================== TESTS DES SERVICES ====================

@pytest.mark.django_db
class TestStripeService:
    """Tests pour StripeService"""
    
    def test_get_or_create_customer_new_unconfigured(self, create_user):
        """Test création customer quand Stripe non configuré (mode test)"""
        user = create_user()
        service = StripeService()
        
        with patch('apps.payments.services.stripe_service.is_stripe_configured', return_value=False):
            customer_id = service.get_or_create_customer(user)
        
        # Devrait retourner un ID de test
        assert customer_id.startswith('cus_test_')
    
    def test_get_or_create_customer_existing_from_payment(self, create_user):
        """Test récupération d'un customer existant depuis un paiement"""
        user = create_user()
        
        # Créer un paiement avec un customer ID
        Payment.objects.create(
            user=user,
            amount=Decimal('10.00'),
            payment_type='subscription',
            stripe_customer_id='cus_existing_123'
        )
        
        service = StripeService()
        with patch('apps.payments.services.stripe_service.is_stripe_configured', return_value=True):
            customer_id = service.get_or_create_customer(user)
        
        assert customer_id == 'cus_existing_123'
    
    def test_service_initialization(self):
        """Test initialisation du service"""
        service = StripeService()
        assert service.stripe is not None


# ==================== TESTS DES VUES API ====================

@pytest.mark.django_db
class TestSubscriptionPlanViewSet:
    """Tests pour les plans d'abonnement"""
    
    def test_list_plans(self, api_client, subscription_plan):
        """Test liste des plans"""
        url = reverse('payments:plans-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_retrieve_plan(self, api_client, subscription_plan):
        """Test détail d'un plan"""
        url = reverse('payments:plans-detail', kwargs={'pk': subscription_plan.pk})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Pro'


@pytest.mark.django_db
class TestPostCreditPackViewSet:
    """Tests pour les packs de crédits"""
    
    def test_list_packs(self, api_client, post_credit_pack):
        """Test liste des packs"""
        url = reverse('payments:credit-packs-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_retrieve_pack(self, api_client, post_credit_pack):
        """Test détail d'un pack"""
        url = reverse('payments:credit-packs-detail', kwargs={'pk': post_credit_pack.pk})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Pack Starter'


@pytest.mark.django_db
class TestSubscriptionCheckoutView:
    """Tests pour la création de session checkout abonnement"""
    
    def test_create_subscription_checkout_unauthenticated(self, api_client, subscription_plan):
        """Test création checkout sans authentification"""
        url = reverse('payments:create-subscription-session')
        
        response = api_client.post(url, {
            'plan_id': subscription_plan.id,
            'success_url': 'https://example.com/success',
            'cancel_url': 'https://example.com/cancel'
        }, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_subscription_checkout_invalid_plan(self, seller_client):
        """Test création checkout avec plan invalide"""
        client, user = seller_client
        url = reverse('payments:create-subscription-session')
        
        response = client.post(url, {
            'plan_id': 99999,
            'success_url': 'https://example.com/success',
            'cancel_url': 'https://example.com/cancel'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestMySubscriptionView:
    """Tests pour la vue mon abonnement"""
    
    def test_get_my_subscription(self, seller_client, subscription_plan):
        """Test récupération de mon abonnement"""
        client, user = seller_client
        
        Subscription.objects.create(
            user=user,
            plan=subscription_plan,
            status='active',
            stripe_subscription_id='sub_test',
            stripe_customer_id='cus_test',
            current_period_end=timezone.now() + timedelta(days=30)
        )
        
        url = reverse('payments:my-subscription')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['plan']['name'] == 'Pro'
        assert response.data['status'] == 'active'
    
    def test_get_my_subscription_none(self, seller_client):
        """Test récupération sans abonnement"""
        client, user = seller_client
        url = reverse('payments:my-subscription')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestMyCreditsView:
    """Tests pour la vue mes crédits"""
    
    def test_get_my_credits(self, seller_client):
        """Test récupération de mes crédits"""
        client, user = seller_client
        
        PostCredit.objects.create(
            user=user,
            balance=15,
            total_purchased=20,
            total_used=5
        )
        
        url = reverse('payments:my-credits')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['balance'] == 15
        assert response.data['total_purchased'] == 20
    
    def test_get_my_credits_none(self, seller_client):
        """Test récupération sans crédits - crée automatiquement ou 404"""
        client, user = seller_client
        url = reverse('payments:my-credits')
        response = client.get(url)
        
        # Selon l'implémentation, peut créer automatiquement ou retourner 404
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.django_db
class TestCancelSubscriptionView:
    """Tests pour l'annulation d'abonnement"""
    
    def test_cancel_subscription_no_subscription(self, seller_client):
        """Test annulation sans abonnement"""
        client, user = seller_client
        url = reverse('payments:cancel-subscription')
        response = client.post(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestValidateCouponView:
    """Tests pour la validation de coupon"""
    
    def test_validate_valid_coupon(self, authenticated_client, coupon):
        """Test validation d'un coupon valide"""
        client, user = authenticated_client
        url = reverse('payments:validate-coupon')
        
        response = client.post(url, {
            'code': 'TEST20',
            'payment_type': 'subscription'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is True
        # Le coupon est dans un objet imbriqué
        assert response.data['coupon']['discount_type'] == 'percentage'
    
    def test_validate_invalid_coupon(self, authenticated_client):
        """Test validation d'un coupon invalide"""
        client, user = authenticated_client
        url = reverse('payments:validate-coupon')
        
        response = client.post(url, {
            'code': 'INVALID',
            'payment_type': 'subscription'
        }, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestStripeWebhookView:
    """Tests pour le webhook Stripe"""
    
    def test_webhook_missing_signature(self, api_client):
        """Test webhook sans signature"""
        url = reverse('payments:stripe-webhook')
        response = api_client.post(
            url,
            data='{}',
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==================== TESTS DES SERIALIZERS ====================

@pytest.mark.django_db
class TestSubscriptionPlanSerializer:
    """Tests pour SubscriptionPlanSerializer"""
    
    def test_serialize_plan(self, subscription_plan):
        """Test sérialisation d'un plan"""
        from apps.payments.serializers import SubscriptionPlanSerializer
        
        serializer = SubscriptionPlanSerializer(subscription_plan)
        data = serializer.data
        
        assert data['name'] == 'Pro'
        assert data['price'] == '29.99'
        assert data['max_listings'] == 50
        assert data['can_boost'] is True


@pytest.mark.django_db
class TestSubscriptionSerializer:
    """Tests pour SubscriptionSerializer"""
    
    def test_serialize_subscription(self, create_user, subscription_plan):
        """Test sérialisation d'un abonnement"""
        from apps.payments.serializers import SubscriptionSerializer
        
        user = create_user()
        subscription = Subscription.objects.create(
            user=user,
            plan=subscription_plan,
            status='active',
            stripe_subscription_id='sub_test',
            stripe_customer_id='cus_test',
        )
        
        serializer = SubscriptionSerializer(subscription)
        data = serializer.data
        
        assert data['status'] == 'active'
        assert data['is_active'] is True
        assert 'plan' in data


# ==================== TESTS D'INTÉGRATION ====================

@pytest.mark.django_db
class TestPaymentHistory:
    """Tests pour l'historique des paiements"""
    
    def test_payment_history_list(self, seller_client, subscription_plan):
        """Test liste des paiements d'un utilisateur"""
        client, user = seller_client
        
        # Créer quelques paiements
        Payment.objects.create(
            user=user,
            amount=Decimal('29.99'),
            payment_type='subscription',
            status='completed',
            subscription_plan=subscription_plan
        )
        Payment.objects.create(
            user=user,
            amount=Decimal('9.99'),
            payment_type='post_credit',
            status='completed'
        )
        
        url = reverse('payments:payment-history')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2


@pytest.mark.django_db
class TestCreditTransactionHistory:
    """Tests pour l'historique des transactions de crédits"""
    
    def test_credit_transactions(self, seller_client):
        """Test liste des transactions de crédits"""
        client, user = seller_client
        
        # Créer des crédits et une transaction
        credit = PostCredit.objects.create(
            user=user,
            balance=10,
            total_purchased=10
        )
        
        PostCreditTransaction.objects.create(
            post_credit=credit,
            transaction_type='purchase',
            amount=10,
            balance_after=10,
            description='Achat initial'
        )
        
        url = reverse('payments:credit-transactions')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
