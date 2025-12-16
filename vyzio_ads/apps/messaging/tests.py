"""
Tests unitaires pour le système de messagerie interne
Phase 7 - Messagerie interne & notifications
"""
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import CustomUser, SellerProfile
from apps.listings.models import Listing, Category
from apps.messaging.models import Conversation, Message, BlockedUser, Report


# Helper pour les URLs
def msg_url(name, **kwargs):
    """Helper pour générer les URLs avec namespace messaging"""
    return reverse(f'messaging:{name}', kwargs=kwargs) if kwargs else reverse(f'messaging:{name}')


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
def another_user(create_user):
    """Autre utilisateur pour les tests"""
    return create_user(
        email='another@example.com',
        username='another',
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
def conversation(buyer, seller, listing):
    """Conversation de test"""
    return Conversation.objects.create(
        buyer=buyer,
        seller=seller,
        listing=listing
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


# ==================== TESTS DES MODÈLES ====================

@pytest.mark.django_db
class TestConversationModel:
    """Tests pour le modèle Conversation"""
    
    def test_create_conversation(self, buyer, seller, listing):
        """Test création d'une conversation"""
        conversation = Conversation.objects.create(
            buyer=buyer,
            seller=seller,
            listing=listing
        )
        assert conversation.buyer == buyer
        assert conversation.seller == seller
        assert conversation.listing == listing
        assert conversation.is_active is True
    
    def test_conversation_str(self, conversation):
        """Test représentation string"""
        assert 'buyer@example.com' in str(conversation)
        assert 'seller@example.com' in str(conversation)
    
    def test_unique_constraint(self, buyer, seller, listing):
        """Test contrainte unique buyer-seller-listing"""
        Conversation.objects.create(
            buyer=buyer,
            seller=seller,
            listing=listing
        )
        with pytest.raises(Exception):
            Conversation.objects.create(
                buyer=buyer,
                seller=seller,
                listing=listing
            )


@pytest.mark.django_db
class TestMessageModel:
    """Tests pour le modèle Message"""
    
    def test_create_message(self, conversation, buyer):
        """Test création d'un message"""
        message = Message.objects.create(
            conversation=conversation,
            sender=buyer,
            content='Hello!'
        )
        assert message.content == 'Hello!'
        assert message.is_read is False
        assert message.sender == buyer
    
    def test_message_ordering(self, conversation, buyer, seller):
        """Test ordre des messages (chronologique)"""
        msg1 = Message.objects.create(
            conversation=conversation,
            sender=buyer,
            content='First'
        )
        msg2 = Message.objects.create(
            conversation=conversation,
            sender=seller,
            content='Second'
        )
        
        messages = list(conversation.messages.all())
        assert messages[0] == msg1
        assert messages[1] == msg2


@pytest.mark.django_db
class TestBlockedUserModel:
    """Tests pour le modèle BlockedUser"""
    
    def test_block_user(self, buyer, seller):
        """Test blocage d'un utilisateur"""
        blocked = BlockedUser.objects.create(
            blocker=buyer,
            blocked=seller
        )
        assert blocked.blocker == buyer
        assert blocked.blocked == seller
    
    def test_unique_block(self, buyer, seller):
        """Test qu'on ne peut pas bloquer deux fois"""
        BlockedUser.objects.create(blocker=buyer, blocked=seller)
        with pytest.raises(Exception):
            BlockedUser.objects.create(blocker=buyer, blocked=seller)


@pytest.mark.django_db
class TestReportModel:
    """Tests pour le modèle Report"""
    
    def test_create_report(self, buyer, seller, conversation):
        """Test création d'un signalement"""
        report = Report.objects.create(
            reporter=buyer,
            reported_user=seller,
            conversation=conversation,
            reason='spam',
            description='Spam messages'
        )
        assert report.reason == 'spam'
        assert report.is_resolved is False


# ==================== TESTS DES VUES API ====================

@pytest.mark.django_db
class TestConversationViewSet:
    """Tests pour le ViewSet des conversations"""
    
    def test_list_conversations(self, buyer_client, conversation):
        """Test liste des conversations"""
        client, buyer = buyer_client
        url = msg_url('conversations-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_list_conversations_only_participant(self, buyer_client, seller, another_user):
        """Test que seules les conversations de l'utilisateur sont visibles"""
        client, buyer = buyer_client
        
        # Créer une conversation avec l'autre utilisateur (pas le buyer)
        other_conv = Conversation.objects.create(
            buyer=another_user,
            seller=seller
        )
        
        url = msg_url('conversations-list')
        response = client.get(url)
        
        # Gérer la pagination si présente
        data = response.data
        if isinstance(data, dict) and 'results' in data:
            data = data['results']
        
        # Le buyer ne devrait pas voir la conversation de another_user
        conv_ids = [str(c['id']) for c in data] if isinstance(data, list) else []
        assert str(other_conv.id) not in conv_ids
    
    def test_retrieve_conversation(self, buyer_client, conversation):
        """Test détail d'une conversation"""
        client, buyer = buyer_client
        url = msg_url('conversations-detail', pk=conversation.id)
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'messages' in response.data
    
    def test_retrieve_conversation_non_participant(self, api_client, conversation, another_user):
        """Test qu'un non-participant ne peut pas voir la conversation"""
        api_client.force_authenticate(user=another_user)
        url = msg_url('conversations-detail', pk=conversation.id)
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_start_conversation(self, buyer_client, seller, listing):
        """Test démarrer une conversation"""
        client, buyer = buyer_client
        url = msg_url('conversations-start-conversation')
        
        response = client.post(url, {
            'seller_id': str(seller.id),
            'listing_id': str(listing.id)
        }, format='json')
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        assert Conversation.objects.filter(buyer=buyer, seller=seller).exists()
    
    def test_start_conversation_with_self(self, seller_client, seller):
        """Test qu'on ne peut pas démarrer une conversation avec soi-même"""
        client, _ = seller_client
        url = msg_url('conversations-start-conversation')
        
        response = client.post(url, {
            'seller_id': str(seller.id)
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_start_conversation_unauthenticated(self, api_client, seller):
        """Test qu'un utilisateur non authentifié ne peut pas démarrer"""
        url = msg_url('conversations-start-conversation')
        response = api_client.post(url, {
            'seller_id': str(seller.id)
        }, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestSendMessage:
    """Tests pour l'envoi de messages"""
    
    def test_send_message(self, buyer_client, conversation):
        """Test envoi d'un message"""
        client, buyer = buyer_client
        url = msg_url('conversations-send-message', pk=conversation.id)
        
        response = client.post(url, {
            'content': 'Hello, is this still available?'
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == 'Hello, is this still available?'
    
    def test_send_empty_message(self, buyer_client, conversation):
        """Test envoi d'un message vide"""
        client, buyer = buyer_client
        url = msg_url('conversations-send-message', pk=conversation.id)
        
        response = client.post(url, {
            'content': ''
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_send_message_blocked_user(self, buyer_client, conversation, seller):
        """Test qu'un utilisateur bloqué ne peut pas envoyer de message"""
        client, buyer = buyer_client
        
        # Le seller bloque le buyer
        BlockedUser.objects.create(blocker=seller, blocked=buyer)
        
        url = msg_url('conversations-send-message', pk=conversation.id)
        response = client.post(url, {
            'content': 'Hello!'
        }, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_send_message_non_participant(self, api_client, conversation, another_user):
        """Test qu'un non-participant ne peut pas envoyer de message"""
        api_client.force_authenticate(user=another_user)
        url = msg_url('conversations-send-message', pk=conversation.id)
        
        response = api_client.post(url, {
            'content': 'Hello!'
        }, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestMarkRead:
    """Tests pour marquer les messages comme lus"""
    
    def test_mark_read(self, seller_client, conversation, buyer):
        """Test marquer les messages comme lus"""
        client, seller = seller_client
        
        # Créer des messages non lus du buyer
        Message.objects.create(
            conversation=conversation,
            sender=buyer,
            content='Message 1',
            is_read=False
        )
        Message.objects.create(
            conversation=conversation,
            sender=buyer,
            content='Message 2',
            is_read=False
        )
        
        url = msg_url('conversations-mark-read', pk=conversation.id)
        response = client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Vérifier que les messages sont marqués comme lus
        unread = Message.objects.filter(
            conversation=conversation,
            sender=buyer,
            is_read=False
        ).count()
        assert unread == 0


@pytest.mark.django_db
class TestBlockUser:
    """Tests pour le blocage d'utilisateurs"""
    
    def test_block_user(self, buyer_client, conversation, seller):
        """Test bloquer un utilisateur"""
        client, buyer = buyer_client
        url = msg_url('conversations-block-user', pk=conversation.id)
        
        response = client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert BlockedUser.objects.filter(blocker=buyer, blocked=seller).exists()
    
    def test_block_user_twice(self, buyer_client, conversation, seller):
        """Test bloquer deux fois ne crée pas de doublon"""
        client, buyer = buyer_client
        url = msg_url('conversations-block-user', pk=conversation.id)
        
        client.post(url)
        client.post(url)
        
        # Devrait y avoir un seul blocage
        count = BlockedUser.objects.filter(blocker=buyer, blocked=seller).count()
        assert count == 1


@pytest.mark.django_db
class TestReportUser:
    """Tests pour les signalements"""
    
    def test_report_user(self, buyer_client, conversation, seller):
        """Test signaler un utilisateur"""
        client, buyer = buyer_client
        url = msg_url('conversations-report-user', pk=conversation.id)
        
        response = client.post(url, {
            'reason': 'spam',
            'description': 'This user is sending spam messages'
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Report.objects.filter(
            reporter=buyer,
            reported_user=seller,
            reason='spam'
        ).exists()
    
    def test_report_invalid_reason(self, buyer_client, conversation):
        """Test signalement avec raison invalide"""
        client, buyer = buyer_client
        url = msg_url('conversations-report-user', pk=conversation.id)
        
        response = client.post(url, {
            'reason': 'invalid_reason',
            'description': 'Test'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==================== TESTS DES SERIALIZERS ====================

@pytest.mark.django_db
class TestMessageSerializer:
    """Tests pour MessageSerializer"""
    
    def test_serialize_message(self, conversation, buyer):
        """Test sérialisation d'un message"""
        from apps.messaging.serializers import MessageSerializer
        
        message = Message.objects.create(
            conversation=conversation,
            sender=buyer,
            content='Test message'
        )
        
        serializer = MessageSerializer(message)
        data = serializer.data
        
        assert data['content'] == 'Test message'
        assert data['is_read'] is False
        assert 'sender' in data


@pytest.mark.django_db
class TestConversationSerializer:
    """Tests pour ConversationSerializer"""
    
    def test_serialize_conversation(self, conversation, buyer):
        """Test sérialisation d'une conversation"""
        from apps.messaging.serializers import ConversationSerializer
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = buyer
        
        serializer = ConversationSerializer(
            conversation,
            context={'request': request}
        )
        data = serializer.data
        
        assert 'buyer' in data
        assert 'seller' in data
        assert 'unread_count' in data
    
    def test_unread_count(self, conversation, buyer, seller):
        """Test comptage des messages non lus"""
        from apps.messaging.serializers import ConversationSerializer
        from rest_framework.test import APIRequestFactory
        
        # Créer des messages non lus
        Message.objects.create(
            conversation=conversation,
            sender=buyer,
            content='Message 1',
            is_read=False
        )
        Message.objects.create(
            conversation=conversation,
            sender=buyer,
            content='Message 2',
            is_read=False
        )
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = seller  # Le seller regarde
        
        serializer = ConversationSerializer(
            conversation,
            context={'request': request}
        )
        
        assert serializer.data['unread_count'] == 2


# ==================== TESTS D'INTÉGRATION ====================

@pytest.mark.django_db
class TestMessagingFlow:
    """Tests d'intégration du flux de messagerie"""
    
    def test_full_conversation_flow(self, buyer_client, seller_client, seller, listing):
        """Test flux complet de conversation"""
        client_buyer, buyer = buyer_client
        client_seller, _ = seller_client
        
        # 1. Buyer démarre une conversation (sans listing_id pour éviter les conflits)
        url = msg_url('conversations-start-conversation')
        response = client_buyer.post(url, {
            'seller_id': str(seller.id)
        }, format='json')
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED], f"Response: {response.data}"
        conv_id = response.data['id']
        
        # 2. Buyer envoie un message
        url = msg_url('conversations-send-message', pk=conv_id)
        response = client_buyer.post(url, {
            'content': 'Is this still available?'
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # 3. Seller voit la conversation
        url = msg_url('conversations-list')
        response = client_seller.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        
        # 4. Seller répond
        url = msg_url('conversations-send-message', pk=conv_id)
        response = client_seller.post(url, {
            'content': 'Yes, still available!'
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # 5. Vérifier les messages dans la conversation
        url = msg_url('conversations-detail', pk=conv_id)
        response = client_buyer.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['messages']) == 2
