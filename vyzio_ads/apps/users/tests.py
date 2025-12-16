"""
Tests unitaires pour l'authentification et la gestion des utilisateurs
"""
import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import CustomUser, UserVerificationToken, SellerProfile, PasswordResetToken


# ==================== FIXTURES ====================

@pytest.fixture
def api_client():
    """Client API pour les tests"""
    return APIClient()


@pytest.fixture
def user_data():
    """Données pour créer un utilisateur"""
    return {
        'email': 'test@example.com',
        'username': 'testuser',
        'first_name': 'Test',
        'last_name': 'User',
        'password': 'TestPassword123!',
        'password2': 'TestPassword123!',
        'role': 'buyer'
    }


@pytest.fixture
def seller_data():
    """Données pour créer un vendeur"""
    return {
        'email': 'seller@example.com',
        'username': 'testseller',
        'first_name': 'Test',
        'last_name': 'Seller',
        'password': 'TestPassword123!',
        'password2': 'TestPassword123!',
        'role': 'seller'
    }


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


# ==================== TESTS D'INSCRIPTION ====================

@pytest.mark.django_db
class TestRegistration:
    """Tests pour l'inscription"""
    
    def test_register_success(self, api_client, user_data):
        """Test inscription réussie"""
        url = reverse('auth_register')
        response = api_client.post(url, user_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'tokens' in response.data
        assert response.data['user']['email'] == user_data['email']
        
        # Vérifier que l'utilisateur existe
        assert CustomUser.objects.filter(email=user_data['email']).exists()
        
        # Vérifier que le token de vérification a été créé
        user = CustomUser.objects.get(email=user_data['email'])
        assert UserVerificationToken.objects.filter(user=user).exists()
    
    def test_register_seller_creates_profile(self, api_client, seller_data):
        """Test que l'inscription d'un vendeur crée un SellerProfile"""
        url = reverse('auth_register')
        response = api_client.post(url, seller_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        user = CustomUser.objects.get(email=seller_data['email'])
        assert hasattr(user, 'seller_profile')
        assert SellerProfile.objects.filter(user=user).exists()
    
    def test_register_password_mismatch(self, api_client, user_data):
        """Test inscription avec mots de passe différents"""
        user_data['password2'] = 'DifferentPassword123!'
        url = reverse('auth_register')
        response = api_client.post(url, user_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data
    
    def test_register_duplicate_email(self, api_client, user_data, create_user):
        """Test inscription avec email déjà utilisé"""
        create_user(email=user_data['email'])
        
        url = reverse('auth_register')
        response = api_client.post(url, user_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data
    
    def test_register_weak_password(self, api_client, user_data):
        """Test inscription avec mot de passe faible"""
        user_data['password'] = '123'
        user_data['password2'] = '123'
        
        url = reverse('auth_register')
        response = api_client.post(url, user_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==================== TESTS DE CONNEXION ====================

@pytest.mark.django_db
class TestLogin:
    """Tests pour la connexion"""
    
    def test_login_success(self, api_client, create_user):
        """Test connexion réussie"""
        user = create_user()
        
        url = reverse('auth_login')
        response = api_client.post(url, {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'tokens' in response.data
        assert 'user' in response.data
        assert response.data['tokens']['access']
        assert response.data['tokens']['refresh']
    
    def test_login_wrong_password(self, api_client, create_user):
        """Test connexion avec mauvais mot de passe"""
        create_user()
        
        url = reverse('auth_login')
        response = api_client.post(url, {
            'email': 'test@example.com',
            'password': 'WrongPassword123!'
        }, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in response.data
    
    def test_login_nonexistent_user(self, api_client):
        """Test connexion avec utilisateur inexistant"""
        url = reverse('auth_login')
        response = api_client.post(url, {
            'email': 'nonexistent@example.com',
            'password': 'TestPassword123!'
        }, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_banned_user(self, api_client, create_user):
        """Test connexion avec utilisateur banni"""
        user = create_user()
        user.is_banned = True
        user.save()
        
        url = reverse('auth_login')
        response = api_client.post(url, {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ==================== TESTS DU PROFIL (ME) ====================

@pytest.mark.django_db
class TestMe:
    """Tests pour l'endpoint /me/"""
    
    def test_get_me_authenticated(self, authenticated_client):
        """Test récupération du profil authentifié"""
        client, user = authenticated_client
        
        url = reverse('auth_me')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email
        assert response.data['id'] == str(user.id)
    
    def test_get_me_unauthenticated(self, api_client):
        """Test accès non authentifié"""
        url = reverse('auth_me')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_me(self, authenticated_client):
        """Test mise à jour du profil"""
        client, user = authenticated_client
        
        url = reverse('auth_me')
        response = client.patch(url, {
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': 'Ma nouvelle bio'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        user.refresh_from_db()
        assert user.first_name == 'Updated'
        assert user.last_name == 'Name'
        assert user.bio == 'Ma nouvelle bio'


# ==================== TESTS PASSWORD RESET ====================

@pytest.mark.django_db
class TestPasswordReset:
    """Tests pour la réinitialisation du mot de passe"""
    
    def test_password_reset_request(self, api_client, create_user):
        """Test demande de réinitialisation"""
        user = create_user()
        
        url = reverse('auth_password_reset')
        response = api_client.post(url, {
            'email': user.email
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert PasswordResetToken.objects.filter(user=user).exists()
    
    def test_password_reset_request_nonexistent_email(self, api_client):
        """Test demande avec email inexistant (ne révèle pas l'info)"""
        url = reverse('auth_password_reset')
        response = api_client.post(url, {
            'email': 'nonexistent@example.com'
        }, format='json')
        
        # Doit retourner succès même si l'email n'existe pas
        assert response.status_code == status.HTTP_200_OK
    
    def test_password_reset_confirm(self, api_client, create_user):
        """Test confirmation de réinitialisation"""
        user = create_user()
        
        # Créer un token
        token = PasswordResetToken.objects.create(
            user=user,
            token='test-reset-token-123',
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        url = reverse('auth_password_reset_confirm')
        response = api_client.post(url, {
            'token': 'test-reset-token-123',
            'new_password': 'NewPassword123!',
            'new_password2': 'NewPassword123!'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Vérifier que le mot de passe a changé
        user.refresh_from_db()
        assert user.check_password('NewPassword123!')
        
        # Vérifier que le token est marqué utilisé
        token.refresh_from_db()
        assert token.is_used
    
    def test_password_reset_expired_token(self, api_client, create_user):
        """Test avec token expiré"""
        user = create_user()
        
        # Créer un token expiré
        PasswordResetToken.objects.create(
            user=user,
            token='expired-token-123',
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        url = reverse('auth_password_reset_confirm')
        response = api_client.post(url, {
            'token': 'expired-token-123',
            'new_password': 'NewPassword123!',
            'new_password2': 'NewPassword123!'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==================== TESTS EMAIL VERIFICATION ====================

@pytest.mark.django_db
class TestEmailVerification:
    """Tests pour la vérification email"""
    
    def test_verify_email_success(self, api_client, create_user):
        """Test vérification email réussie"""
        user = create_user()
        assert not user.is_verified
        
        # Créer un token
        UserVerificationToken.objects.create(
            user=user,
            token='verification-token-123',
            expires_at=timezone.now() + timedelta(days=1)
        )
        
        url = reverse('auth_verify_email')
        response = api_client.post(url, {
            'token': 'verification-token-123'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        user.refresh_from_db()
        assert user.is_verified
    
    def test_verify_email_invalid_token(self, api_client):
        """Test avec token invalide"""
        url = reverse('auth_verify_email')
        response = api_client.post(url, {
            'token': 'invalid-token'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_resend_verification(self, authenticated_client):
        """Test renvoi du mail de vérification"""
        client, user = authenticated_client
        user.is_verified = False
        user.save()
        
        url = reverse('auth_resend_verification')
        response = client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert UserVerificationToken.objects.filter(user=user).exists()


# ==================== TESTS PERMISSIONS ====================

@pytest.mark.django_db
class TestPermissions:
    """Tests pour les permissions"""
    
    def test_is_seller_permission(self, seller_client):
        """Test permission IsSellerOrReadOnly"""
        client, user = seller_client
        assert user.is_seller()
        assert user.role == 'seller'
    
    def test_buyer_is_not_seller(self, authenticated_client):
        """Test qu'un acheteur n'est pas vendeur"""
        client, user = authenticated_client
        assert not user.is_seller()
        assert user.role == 'buyer'
    
    def test_unauthenticated_cannot_access_me(self, api_client):
        """Test accès non authentifié à /me/"""
        url = reverse('auth_me')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================== TESTS TOKEN REFRESH ====================

@pytest.mark.django_db
class TestTokenRefresh:
    """Tests pour le rafraîchissement des tokens"""
    
    def test_refresh_token(self, api_client, create_user):
        """Test rafraîchissement de token"""
        user = create_user()
        
        # D'abord se connecter pour obtenir un refresh token
        login_url = reverse('auth_login')
        login_response = api_client.post(login_url, {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }, format='json')
        
        refresh_token = login_response.data['tokens']['refresh']
        
        # Utiliser le refresh token
        url = reverse('auth_token_refresh')
        response = api_client.post(url, {
            'refresh': refresh_token
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
    
    def test_refresh_invalid_token(self, api_client):
        """Test avec token invalide"""
        url = reverse('auth_token_refresh')
        response = api_client.post(url, {
            'refresh': 'invalid-token'
        }, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================== TESTS MODÈLES ====================

@pytest.mark.django_db
class TestModels:
    """Tests pour les modèles"""
    
    def test_custom_user_str(self, create_user):
        """Test __str__ de CustomUser"""
        user = create_user(first_name='John', last_name='Doe')
        assert 'John Doe' in str(user)
    
    def test_seller_profile_creation(self, create_user):
        """Test création de SellerProfile"""
        user = create_user(role='seller')
        profile = SellerProfile.objects.create(user=user, shop_name='Ma Boutique')
        
        assert profile.shop_name == 'Ma Boutique'
        assert profile.user == user
        assert str(profile) == f"Profil vendeur: {user.email}"
    
    def test_user_is_seller_method(self, create_user):
        """Test méthode is_seller()"""
        buyer = create_user(email='buyer@test.com', username='buyer', role='buyer')
        seller = create_user(email='seller@test.com', username='seller', role='seller')
        pro = create_user(email='pro@test.com', username='pro', role='professional')
        
        assert not buyer.is_seller()
        assert seller.is_seller()
        assert pro.is_seller()


# ==================== TESTS ADMIN ACTIONS ====================

@pytest.mark.django_db
class TestAdminActions:
    """Tests pour les actions admin (à exécuter manuellement ou via Django admin)"""
    
    def test_verify_user(self, create_user):
        """Test vérification utilisateur"""
        user = create_user()
        assert not user.is_verified
        
        user.is_verified = True
        user.save()
        
        user.refresh_from_db()
        assert user.is_verified
    
    def test_ban_user(self, create_user):
        """Test bannissement utilisateur"""
        user = create_user()
        assert not user.is_banned
        
        user.is_banned = True
        user.save()
        
        user.refresh_from_db()
        assert user.is_banned
    
    def test_upgrade_to_seller(self, create_user):
        """Test passage en vendeur"""
        user = create_user(role='buyer')
        assert user.role == 'buyer'
        
        user.role = 'seller'
        user.save()
        SellerProfile.objects.create(user=user)
        
        user.refresh_from_db()
        assert user.role == 'seller'
        assert hasattr(user, 'seller_profile')
