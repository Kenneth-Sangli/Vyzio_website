from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
    verbose_name = 'Commandes & Wallet'
    
    def ready(self):
        # Import signals si nécessaire
        pass
