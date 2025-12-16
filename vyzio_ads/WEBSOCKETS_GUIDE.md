# WebSockets - Guide d'utilisation

## 🔌 Installation des dépendances

```bash
pip install channels==4.0.0
pip install channels-redis==4.1.0
pip install daphne==4.0.0
```

Ou ajouter à `requirements.txt` :
```
channels==4.0.0
channels-redis==4.1.0
daphne==4.0.0
```

## ⚙️ Configuration

### 1. settings.py

```python
INSTALLED_APPS = [
    'daphne',  # Doit être en premier
    'channels',
    # ... reste des apps
]

ASGI_APPLICATION = 'config.asgi.application'

# Redis pour les channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
            'capacity': 1500,
            'expiry': 10,
        },
    },
}
```

### 2. Lancer avec Daphne

```bash
# Développement
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Ou avec Django
python manage.py runserver

# La migration automatique se fera vers Daphne si Django détecte une app WebSocket
```

## 💬 Consumer: Chat en temps réel

### Endpoint WebSocket
```
ws://localhost:8000/ws/chat/{conversation_id}/
```

### Client JavaScript

```javascript
const conversationId = 123;
const chatSocket = new WebSocket(
    `ws://${window.location.host}/ws/chat/${conversationId}/`
);

chatSocket.onopen = function(e) {
    console.log('Connected to chat');
};

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    if (data.type === 'message') {
        // Ajouter le message au DOM
        addMessage(data);
    }
};

chatSocket.onclose = function(e) {
    console.log('Chat connection closed');
};

// Envoyer un message
function sendMessage(content) {
    chatSocket.send(JSON.stringify({
        'message': content
    }));
}
```

### Événements reçus

```javascript
{
    "type": "message",
    "message_id": 123,
    "sender_id": 456,
    "sender_username": "john_doe",
    "content": "Bonjour!",
    "created_at": "2025-12-09T10:30:00Z",
    "is_read": false
}
```

## 🔔 Consumer: Notifications

### Endpoint WebSocket
```
ws://localhost:8000/ws/notifications/
```

### Client JavaScript

```javascript
const notificationSocket = new WebSocket(
    `ws://${window.location.host}/ws/notifications/`
);

notificationSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    // Afficher la notification
    showNotification(data.title, data.message);
};
```

### Événements possibles

```javascript
// Message reçu
{
    "type": "message_received",
    "title": "Nouveau message",
    "message": "John a envoyé un message",
    "data": {"conversation_id": 123}
}

// Paiement approuvé
{
    "type": "payment_completed",
    "title": "Paiement confirmé",
    "message": "Votre paiement a été traité",
    "data": {"payment_id": 789}
}

// Annonce publiée
{
    "type": "listing_published",
    "title": "Annonce publiée",
    "message": "Votre annonce est maintenant visible",
    "data": {"listing_id": 456}
}
```

## ⌨️ Consumer: Indicateur de frappe (Typing)

### Endpoint WebSocket
```
ws://localhost:8000/ws/typing/{conversation_id}/
```

### Client JavaScript

```javascript
const conversationId = 123;
const typingSocket = new WebSocket(
    `ws://${window.location.host}/ws/typing/${conversationId}/`
);

// Envoyer événement de frappe
const inputField = document.getElementById('message-input');

inputField.addEventListener('input', function() {
    typingSocket.send(JSON.stringify({
        'is_typing': true
    }));
});

inputField.addEventListener('blur', function() {
    typingSocket.send(JSON.stringify({
        'is_typing': false
    }));
});

// Recevoir les événements de frappe
typingSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    if (data.type === 'typing') {
        if (data.is_typing) {
            showTypingIndicator(data.username);
        } else {
            hideTypingIndicator(data.username);
        }
    }
};
```

## 🧪 Test avec WebSocket CLI

```bash
# Installer wscat
npm install -g wscat

# Se connecter à un WebSocket
wscat -c "ws://localhost:8000/ws/chat/123/"

# Envoyer un message (dans la connexion)
{"message": "Hello"}
```

## 🐳 Docker Compose avec Redis

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    
  web:
    build: .
    command: daphne -b 0.0.0.0 -p 8000 config.asgi:application
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
```

## 🔐 Authentification

Les WebSockets utilisent `AuthMiddlewareStack` pour l'authentification JWT.

```python
# config/asgi.py
from channels.auth import AuthMiddlewareStack

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(URLRouter(...))
})
```

Le token doit être passé en paramètre de requête:

```javascript
const token = localStorage.getItem('access_token');
const chatSocket = new WebSocket(
    `ws://localhost:8000/ws/chat/${conversationId}/?token=${token}`
);
```

## 📊 Architecture

```
Client (JavaScript)
    ↓
WebSocket Protocol
    ↓
Django Channels (Daphne)
    ↓
AuthMiddlewareStack (JWT auth)
    ↓
URLRouter (ws_routing.py)
    ↓
Consumer (ChatConsumer, NotificationConsumer, TypingIndicatorConsumer)
    ↓
Redis Channel Layer (broadcast)
    ↓
Broadcast à tous les clients
```

## 🚀 Déploiement en Production

### Avec Render.com

```yaml
services:
  - type: web
    name: vyzio-api
    env: python
    plan: standard
    buildCommand: pip install -r requirements.txt && python manage.py migrate
    startCommand: daphne -b 0.0.0.0 -p 10000 config.asgi:application
    envVars:
      - key: REDIS_URL
        value: redis://redis-server:6379/0
  
  - type: redis
    name: redis-server
    plan: starter
```

### Avec Railway.app

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "daphne -b 0.0.0.0 -p $PORT config.asgi:application"

[[services]]
name = "redis"
image = "redis:7-alpine"
port = 6379
```

## 📚 Ressources

- [Django Channels Documentation](https://channels.readthedocs.io/)
- [Daphne](https://github.com/django/daphne)
- [channels-redis](https://github.com/django/channels_redis)
- [WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)

## ✅ Checklist

- [ ] Installer les packages (channels, daphne, channels-redis)
- [ ] Configurer ASGI et ws_routing.py
- [ ] Ajouter CHANNEL_LAYERS à settings.py
- [ ] Démarrer Redis (`redis-server`)
- [ ] Lancer Daphne au lieu de Django runserver
- [ ] Tester avec wscat ou JavaScript
- [ ] Implémenter les consumers dans le frontend
- [ ] Configurer en production avec le bon app server

