"""
Routage WebSocket pour Django Channels
"""
from django.urls import re_path
from apps.messaging.consumers import ChatConsumer, NotificationConsumer, TypingIndicatorConsumer

websocket_urlpatterns = [
    # Chat temps réel par conversation
    re_path(
        r'ws/chat/(?P<conversation_id>\d+)/$',
        ChatConsumer.as_asgi(),
        name='ws_chat'
    ),
    
    # Notifications temps réel pour l'utilisateur
    re_path(
        r'ws/notifications/$',
        NotificationConsumer.as_asgi(),
        name='ws_notifications'
    ),
    
    # Indicateur de frappe (typing indicator)
    re_path(
        r'ws/typing/(?P<conversation_id>\d+)/$',
        TypingIndicatorConsumer.as_asgi(),
        name='ws_typing'
    ),
]
