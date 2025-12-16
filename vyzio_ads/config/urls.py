"""
URL configuration for vyzio_ads project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from apps.health import health_check, health_check_detailed, api_root


def home_view(request):
    """Page d'accueil de l'API Vyzio"""
    return JsonResponse({
        'name': 'Vyzio API',
        'version': '1.0.0',
        'description': 'API de marketplace pour équipements électroniques',
        'endpoints': {
            'api_root': '/api/',
            'admin': '/admin/',
            'health': '/health/',
            'auth': '/api/auth/',
            'users': '/api/users/',
            'listings': '/api/listings/',
            'messages': '/api/messages/',
            'payments': '/api/payments/',
            'reviews': '/api/reviews/',
            'analytics': '/api/analytics/',
        },
        'documentation': 'Visitez /api/ pour explorer les endpoints disponibles',
    })


urlpatterns = [
    # Page d'accueil
    path('', home_view, name='home'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Health checks
    path('health/', health_check, name='health_check'),
    path('api/health/', health_check, name='api_health'),
    path('api/health/detailed/', health_check_detailed, name='api_health_detailed'),
    
    # API Root
    path('api/', api_root, name='api_root'),
    
    # Authentication (dédié)
    path('api/auth/', include('apps.users.auth_urls')),
    
    # API endpoints
    path('api/users/', include('apps.users.urls')),
    path('api/listings/', include('apps.listings.urls')),
    path('api/messages/', include('apps.messaging.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/reviews/', include('apps.reviews.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/admin/', include('apps.admin_panel.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
