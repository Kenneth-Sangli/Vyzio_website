"""
Health check views for vyzio_ads project.
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import os


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Basic health check endpoint.
    Returns 200 if the API is running.
    
    GET /api/health/
    """
    return Response({
        'status': 'healthy',
        'message': 'Vyzio Ads API is running',
        'version': '1.0.0',
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check_detailed(request):
    """
    Detailed health check endpoint.
    Checks database, cache, and other services.
    
    GET /api/health/detailed/
    """
    health_status = {
        'status': 'healthy',
        'checks': {}
    }
    
    # Check Database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': str(e)
        }
    
    # Check Redis/Cache
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['checks']['cache'] = {
                'status': 'healthy',
                'message': 'Cache connection successful'
            }
        else:
            raise Exception('Cache read failed')
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'degraded',
            'message': f'Cache not available: {str(e)}'
        }
    
    # Check disk space (simplified)
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_percent = (free / total) * 100
        health_status['checks']['disk'] = {
            'status': 'healthy' if free_percent > 10 else 'warning',
            'message': f'{free_percent:.1f}% free disk space',
            'free_gb': round(free / (1024**3), 2)
        }
    except Exception as e:
        health_status['checks']['disk'] = {
            'status': 'unknown',
            'message': str(e)
        }
    
    # Overall status
    if any(check.get('status') == 'unhealthy' for check in health_status['checks'].values()):
        health_status['status'] = 'unhealthy'
    elif any(check.get('status') in ['degraded', 'warning'] for check in health_status['checks'].values()):
        health_status['status'] = 'degraded'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return Response(health_status, status=status_code)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """
    API root endpoint.
    Returns available endpoints and API information.
    
    GET /api/
    """
    return Response({
        'name': 'Vyzio Ads API',
        'version': '1.0.0',
        'description': 'Marketplace API for buying and selling items',
        'endpoints': {
            'health': '/api/health/',
            'health_detailed': '/api/health/detailed/',
            'users': '/api/users/',
            'listings': '/api/listings/',
            'messages': '/api/messages/',
            'payments': '/api/payments/',
            'reviews': '/api/reviews/',
            'admin': '/api/admin/',
        },
        'documentation': {
            'swagger': '/api/docs/',
            'redoc': '/api/redoc/',
        },
        'authentication': {
            'type': 'JWT',
            'header': 'Authorization: Bearer <token>',
            'login': '/api/users/login/',
            'refresh': '/api/users/token/refresh/',
        }
    })
