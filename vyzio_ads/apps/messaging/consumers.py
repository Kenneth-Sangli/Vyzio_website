"""
WebSockets consumers pour messagerie temps réel
Utilisé avec Django Channels et Redis
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from apps.messaging.models import Conversation, Message
from apps.users.models import CustomUser


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket pour les conversations temps réel
    
    Connect URL: ws://localhost:8000/ws/chat/{conversation_id}/
    """
    
    async def connect(self):
        """
        Établir la connexion WebSocket
        """
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.user = self.scope['user']
        self.room_group_name = f'chat_{self.conversation_id}'
        
        # Vérifier les permissions
        is_participant = await self.check_participant()
        if not is_participant:
            await self.close()
            return
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notifier que l'utilisateur s'est connecté
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_online',
                'user_id': self.user.id,
                'username': self.user.username,
            }
        )
    
    async def disconnect(self, close_code):
        """
        Fermer la connexion WebSocket
        """
        # Notifier que l'utilisateur s'est déconnecté
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_offline',
                'user_id': self.user.id,
                'username': self.user.username,
            }
        )
        
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Recevoir les messages du client
        """
        try:
            data = json.loads(text_data)
            message_text = data.get('message', '').strip()
            
            if not message_text:
                return
            
            # Créer le message en base de données
            message = await self.save_message(message_text)
            
            # Envoyer au groupe
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_id': message.id,
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,
                    'content': message_text,
                    'created_at': message.created_at.isoformat(),
                    'is_read': False,
                }
            )
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Message invalide'
            }))
    
    # Événements reçus du groupe
    async def chat_message(self, event):
        """
        Envoyer le message au client
        """
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'content': event['content'],
            'created_at': event['created_at'],
            'is_read': event['is_read'],
        }))
    
    async def user_online(self, event):
        """
        Notifier qu'un utilisateur s'est connecté
        """
        if event['user_id'] != self.user.id:  # Ne pas envoyer à soi-même
            await self.send(text_data=json.dumps({
                'type': 'user_status',
                'status': 'online',
                'user_id': event['user_id'],
                'username': event['username'],
            }))
    
    async def user_offline(self, event):
        """
        Notifier qu'un utilisateur s'est déconnecté
        """
        if event['user_id'] != self.user.id:  # Ne pas envoyer à soi-même
            await self.send(text_data=json.dumps({
                'type': 'user_status',
                'status': 'offline',
                'user_id': event['user_id'],
                'username': event['username'],
            }))
    
    async def typing_status(self, event):
        """
        Notifier qu'un utilisateur tape
        """
        if event['user_id'] != self.user.id:  # Ne pas envoyer à soi-même
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing'],
            }))
    
    # Méthodes de base de données
    @database_sync_to_async
    def check_participant(self):
        """
        Vérifier que l'utilisateur participe à cette conversation
        """
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return (
                self.user == conversation.buyer or 
                self.user == conversation.seller
            )
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content):
        """
        Sauvegarder le message en base de données
        """
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content,
            created_at=timezone.now()
        )
        return message


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket pour les notifications temps réel
    
    Connect URL: ws://localhost:8000/ws/notifications/
    """
    
    async def connect(self):
        """
        Établir la connexion WebSocket
        """
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.room_group_name = f'notifications_{self.user.id}'
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """
        Fermer la connexion WebSocket
        """
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def send_notification(self, event):
        """
        Envoyer une notification au client
        """
        await self.send(text_data=json.dumps({
            'type': event['notification_type'],
            'title': event['title'],
            'message': event['message'],
            'data': event.get('data', {}),
            'created_at': timezone.now().isoformat(),
        }))


class TypingIndicatorConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket pour l'indicateur de frappe (typing indicator)
    
    Connect URL: ws://localhost:8000/ws/typing/{conversation_id}/
    """
    
    async def connect(self):
        """
        Établir la connexion WebSocket
        """
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.user = self.scope['user']
        self.room_group_name = f'typing_{self.conversation_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """
        Fermer la connexion WebSocket
        """
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Recevoir l'événement de frappe
        """
        try:
            data = json.loads(text_data)
            is_typing = data.get('is_typing', False)
            
            # Envoyer au groupe
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_status',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_typing': is_typing,
                }
            )
        
        except json.JSONDecodeError:
            pass
    
    async def typing_status(self, event):
        """
        Envoyer le statut de frappe au client
        """
        if event['user_id'] != self.user.id:  # Ne pas envoyer à soi-même
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing'],
            }))
