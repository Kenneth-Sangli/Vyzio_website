from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from .models import Conversation, Message, BlockedUser, Report, Notification
from .serializers import ConversationSerializer, ConversationDetailSerializer, MessageSerializer, ReportSerializer, NotificationSerializer
from .services import NotificationService, AntiSpamService
import logging

logger = logging.getLogger(__name__)



class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(
            Q(buyer=user) | Q(seller=user)
        ).select_related('buyer', 'seller', 'listing')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ConversationDetailSerializer
        return ConversationSerializer
    
    @action(detail=False, methods=['post'])
    def start_conversation(self, request):
        """Start a new conversation"""
        seller_id = request.data.get('seller_id')
        listing_id = request.data.get('listing_id')
        initial_message = request.data.get('content', '').strip()
        
        if not seller_id:
            return Response({'error': 'seller_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Rate limiting anti-spam
        is_allowed, error_msg = AntiSpamService.check_rate_limit(request.user, 'conversation')
        if not is_allowed:
            return Response({'error': error_msg}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        from apps.users.models import CustomUser
        from apps.listings.models import Listing
        
        try:
            seller = CustomUser.objects.get(id=seller_id)
            listing = None
            if listing_id:
                listing = Listing.objects.get(id=listing_id)
        except:
            return Response({'error': 'Invalid seller or listing'}, status=status.HTTP_400_BAD_REQUEST)
        
        if request.user == seller:
            return Response({'error': 'Cannot message yourself'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si l'utilisateur est bloqué
        if BlockedUser.objects.filter(blocker=seller, blocked=request.user).exists():
            return Response({'error': 'Cannot contact this user'}, status=status.HTTP_403_FORBIDDEN)
        
        conversation, created = Conversation.objects.get_or_create(
            buyer=request.user,
            seller=seller,
            listing=listing,
            defaults={'is_active': True}
        )
        
        # Si un message initial est fourni, le créer
        if initial_message:
            # Anti-spam: vérifier le contenu
            is_valid, error_msg = AntiSpamService.check_content(initial_message)
            if not is_valid:
                return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
            
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=initial_message
            )
            conversation.last_message_date = timezone.now()
            conversation.save()
        
        # Envoyer notification au seller si nouvelle conversation
        if created:
            try:
                NotificationService.send_new_conversation_email(
                    seller=seller,
                    buyer=request.user,
                    conversation=conversation
                )
                NotificationService.send_realtime_notification(
                    user_id=str(seller.id),
                    notification_type='new_conversation',
                    title=f'Nouvelle conversation',
                    message=f'{request.user.username} vous a contacté',
                    data={'conversation_id': str(conversation.id)}
                )
            except Exception as e:
                logger.error(f"Failed to send new conversation notification: {e}")
        
        serializer = ConversationSerializer(conversation, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send message in conversation"""
        conversation = self.get_object()
        
        # Check if users are blocked
        if BlockedUser.objects.filter(
            Q(blocker=request.user, blocked__in=[conversation.buyer, conversation.seller]) |
            Q(blocker__in=[conversation.buyer, conversation.seller], blocked=request.user)
        ).exists():
            return Response({'error': 'Cannot send message'}, status=status.HTTP_403_FORBIDDEN)
        
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Message content required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Anti-spam: vérifier le contenu
        is_valid, error_msg = AntiSpamService.check_content(content)
        if not is_valid:
            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
        
        # Anti-spam: rate limiting
        is_allowed, error_msg = AntiSpamService.check_rate_limit(request.user, 'message')
        if not is_allowed:
            return Response({'error': error_msg}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )
        
        conversation.last_message_date = timezone.now()
        conversation.save()
        
        # Notifier le destinataire
        recipient = conversation.seller if request.user == conversation.buyer else conversation.buyer
        try:
            NotificationService.notify_new_message(
                recipient=recipient,
                sender=request.user,
                conversation=conversation,
                message=message
            )
        except Exception as e:
            logger.error(f"Failed to send message notification: {e}")
        
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark messages as read"""
        conversation = self.get_object()
        
        messages = conversation.messages.filter(
            sender__in=[conversation.buyer, conversation.seller],
            is_read=False
        ).exclude(sender=request.user)
        
        messages.update(is_read=True, read_at=timezone.now())
        
        return Response({'status': 'marked as read'})
    
    @action(detail=True, methods=['post'])
    def block_user(self, request, pk=None):
        """Block a user"""
        conversation = self.get_object()
        other_user = conversation.seller if request.user == conversation.buyer else conversation.buyer
        
        BlockedUser.objects.get_or_create(blocker=request.user, blocked=other_user)
        
        return Response({'status': 'user blocked'})
    
    @action(detail=True, methods=['post'])
    def report_user(self, request, pk=None):
        """Report inappropriate behavior"""
        conversation = self.get_object()
        other_user = conversation.seller if request.user == conversation.buyer else conversation.buyer
        
        serializer = ReportSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(
                reporter=request.user,
                reported_user=other_user,
                conversation=conversation
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les notifications utilisateur.
    
    GET /api/messages/notifications/ - Liste des notifications
    GET /api/messages/notifications/{id}/ - Détail d'une notification
    POST /api/messages/notifications/{id}/mark_read/ - Marquer comme lue
    POST /api/messages/notifications/mark_all_read/ - Tout marquer comme lu
    DELETE /api/messages/notifications/{id}/ - Supprimer une notification
    GET /api/messages/notifications/unread_count/ - Nombre de non lues
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """Permet de supprimer une notification"""
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Marquer une notification comme lue"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Marquer toutes les notifications comme lues"""
        self.get_queryset().filter(is_read=False).update(
            is_read=True, 
            read_at=timezone.now()
        )
        return Response({'status': 'all marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Retourne le nombre de notifications non lues"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})
