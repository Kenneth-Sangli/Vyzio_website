"""
Django simplified development settings - WITHOUT Daphne for faster startup.
Use this when you need to quickly test the site without WebSocket features.
"""
from .dev import *

# Remove daphne from INSTALLED_APPS for faster startup
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'daphne']

# Use WSGI instead of ASGI
ASGI_APPLICATION = None

# Disable Channels completely for this config
CHANNEL_LAYERS = {}

print("🚀 Running with SIMPLIFIED DEV settings (no Daphne/Channels)")
