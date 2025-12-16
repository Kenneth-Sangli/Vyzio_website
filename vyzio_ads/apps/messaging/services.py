"""
Services pour la messagerie interne.
Phase 7 - Notifications email et onsite.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service de notifications pour la messagerie.
    Gère les notifications email et temps réel (WebSocket).
    """
    
    # ==================== Email Notifications ====================
    
    @staticmethod
    def send_new_message_email(recipient, sender, conversation, message):
        """
        Envoie une notification email pour un nouveau message.
        
        Args:
            recipient: User qui reçoit la notification
            sender: User qui a envoyé le message
            conversation: Conversation concernée
            message: Message envoyé
        """
        try:
            subject = f"Nouveau message de {sender.username} sur Vyzio"
            
            # Contexte pour le template
            context = {
                'recipient': recipient,
                'sender': sender,
                'message_preview': message.content[:100] + '...' if len(message.content) > 100 else message.content,
                'conversation_id': conversation.id,
                'listing_title': conversation.listing.title if conversation.listing else 'Conversation directe',
                'frontend_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
            }
            
            # Template HTML
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #4F46E5; padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0;">Vyzio</h1>
                </div>
                <div style="padding: 20px; background-color: #f9fafb;">
                    <h2>Bonjour {recipient.first_name or recipient.username},</h2>
                    <p>Vous avez reçu un nouveau message de <strong>{sender.username}</strong>.</p>
                    
                    <div style="background-color: white; padding: 15px; border-radius: 8px; border-left: 4px solid #4F46E5;">
                        <p style="margin: 0; color: #374151;">{context['message_preview']}</p>
                    </div>
                    
                    <p style="margin-top: 20px;">
                        <a href="{context['frontend_url']}/messages/{conversation.id}" 
                           style="background-color: #4F46E5; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 6px; display: inline-block;">
                            Voir la conversation
                        </a>
                    </p>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                    <p style="color: #6b7280; font-size: 12px;">
                        Vous recevez cet email car vous avez un compte sur Vyzio.
                        <br>
                        <a href="{context['frontend_url']}/settings/notifications">Gérer mes notifications</a>
                    </p>
                </div>
            </body>
            </html>
            """
            
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                html_message=html_message,
                fail_silently=True,
            )
            
            logger.info(f"Email notification sent to {recipient.email} for message from {sender.email}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    @staticmethod
    def send_new_conversation_email(seller, buyer, conversation):
        """
        Envoie une notification email pour une nouvelle conversation.
        
        Args:
            seller: Vendeur qui reçoit la notification
            buyer: Acheteur qui a initié la conversation
            conversation: Nouvelle conversation
        """
        try:
            listing_title = conversation.listing.title if conversation.listing else 'votre profil'
            subject = f"Nouvelle conversation de {buyer.username} sur Vyzio"
            
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #4F46E5; padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0;">Vyzio</h1>
                </div>
                <div style="padding: 20px; background-color: #f9fafb;">
                    <h2>Bonjour {seller.first_name or seller.username},</h2>
                    <p><strong>{buyer.username}</strong> vous a contacté à propos de <strong>{listing_title}</strong>.</p>
                    
                    <p style="margin-top: 20px;">
                        <a href="{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/messages/{conversation.id}" 
                           style="background-color: #4F46E5; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 6px; display: inline-block;">
                            Répondre au message
                        </a>
                    </p>
                </div>
            </body>
            </html>
            """
            
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[seller.email],
                html_message=html_message,
                fail_silently=True,
            )
            
            logger.info(f"New conversation email sent to {seller.email}")
            
        except Exception as e:
            logger.error(f"Failed to send new conversation email: {e}")
    
    # ==================== WebSocket Notifications ====================
    
    @staticmethod
    def send_realtime_notification(user_id, notification_type, title, message, data=None):
        """
        Envoie une notification en temps réel via WebSocket.
        
        Args:
            user_id: ID de l'utilisateur à notifier
            notification_type: Type de notification (new_message, etc.)
            title: Titre de la notification
            message: Message de la notification
            data: Données additionnelles (optionnel)
        """
        try:
            channel_layer = get_channel_layer()
            
            async_to_sync(channel_layer.group_send)(
                f'notifications_{user_id}',
                {
                    'type': 'send_notification',
                    'notification_type': notification_type,
                    'title': title,
                    'message': message,
                    'data': data or {},
                }
            )
            
            logger.info(f"Realtime notification sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send realtime notification: {e}")
    
    @staticmethod
    def notify_new_message(recipient, sender, conversation, message):
        """
        Notifie un utilisateur d'un nouveau message (email + temps réel).
        
        Args:
            recipient: User qui reçoit la notification
            sender: User qui a envoyé le message
            conversation: Conversation concernée
            message: Message envoyé
        """
        # Notification temps réel
        NotificationService.send_realtime_notification(
            user_id=str(recipient.id),
            notification_type='new_message',
            title=f'Nouveau message de {sender.username}',
            message=message.content[:50] + '...' if len(message.content) > 50 else message.content,
            data={
                'conversation_id': str(conversation.id),
                'sender_id': str(sender.id),
                'sender_username': sender.username,
            }
        )
        
        # Notification email (en arrière-plan pour ne pas bloquer)
        # TODO: Utiliser Celery pour envoyer les emails en arrière-plan
        NotificationService.send_new_message_email(
            recipient=recipient,
            sender=sender,
            conversation=conversation,
            message=message
        )


class AntiSpamService:
    """
    Service anti-spam pour la messagerie.
    Rate-limiting et filtrage de contenu.
    """
    
    # Mots-clés blacklistés
    BLACKLIST_KEYWORDS = [
        'scam', 'arnaque', 'bitcoin', 'crypto', 
        'gagner argent', 'investissement rapide',
        'cliquez ici', 'offre limitée',
    ]
    
    # Rate limits
    MAX_MESSAGES_PER_MINUTE = 10
    MAX_CONVERSATIONS_PER_HOUR = 20
    
    @staticmethod
    def check_content(content: str) -> tuple[bool, str]:
        """
        Vérifie si le contenu est acceptable.
        
        Returns:
            (is_valid, error_message)
        """
        content_lower = content.lower()
        
        for keyword in AntiSpamService.BLACKLIST_KEYWORDS:
            if keyword in content_lower:
                return False, f"Le message contient un terme interdit: {keyword}"
        
        # Vérifier la longueur
        if len(content) > 5000:
            return False, "Le message est trop long (max 5000 caractères)"
        
        if len(content) < 2:
            return False, "Le message est trop court"
        
        return True, ""
    
    @staticmethod
    def check_rate_limit(user, action_type='message') -> tuple[bool, str]:
        """
        Vérifie si l'utilisateur n'a pas dépassé le rate limit.
        
        Args:
            user: Utilisateur à vérifier
            action_type: 'message' ou 'conversation'
            
        Returns:
            (is_allowed, error_message)
        """
        from django.utils import timezone
        from datetime import timedelta
        from apps.messaging.models import Message, Conversation
        
        now = timezone.now()
        
        if action_type == 'message':
            # Compter les messages de la dernière minute
            one_minute_ago = now - timedelta(minutes=1)
            recent_count = Message.objects.filter(
                sender=user,
                created_at__gte=one_minute_ago
            ).count()
            
            if recent_count >= AntiSpamService.MAX_MESSAGES_PER_MINUTE:
                return False, "Trop de messages envoyés. Veuillez patienter."
        
        elif action_type == 'conversation':
            # Compter les conversations de la dernière heure
            one_hour_ago = now - timedelta(hours=1)
            recent_count = Conversation.objects.filter(
                buyer=user,
                created_at__gte=one_hour_ago
            ).count()
            
            if recent_count >= AntiSpamService.MAX_CONVERSATIONS_PER_HOUR:
                return False, "Trop de conversations créées. Veuillez patienter."
        
        return True, ""
