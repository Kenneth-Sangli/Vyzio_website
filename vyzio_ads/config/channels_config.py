"""
Configuration Django Channels pour WebSockets
À ajouter au settings.py et installer les dépendances
"""

# settings.py - À ajouter à INSTALLED_APPS
INSTALLED_APPS = [
    # ...
    'daphne',  # WebSocket support
    'channels',
    # ...
]

# À ajouter à settings.py
ASGI_APPLICATION = 'config.asgi.application'

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

# Pour développement (sans Redis)
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels.layers.InMemoryChannelLayer'
#     }
# }

# Requirements à ajouter à requirements.txt
# channels==4.0.0
# channels-redis==4.1.0
# daphne==4.0.0
