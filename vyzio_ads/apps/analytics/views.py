"""
Vues pour le dashboard seller et analytics
Phase 9 - Dashboard seller & analytics
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta

from .models import Event, DailyStats, ListingStats
from .serializers import (
    EventSerializer, EventCreateSerializer, DailyStatsSerializer,
    ListingStatsSerializer, DashboardSummarySerializer,
    ListingAnalyticsSerializer, RevenueAnalyticsSerializer,
    TrendsSerializer, QuickListingSerializer
)
from .services import EventTracker, AnalyticsService, ExportService
from apps.users.permissions import IsSeller


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet pour le dashboard vendeur
    Fournit toutes les données nécessaires au dashboard
    """
    permission_classes = [IsAuthenticated, IsSeller]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Obtenir le résumé du dashboard
        GET /api/analytics/dashboard/summary/?days=30
        """
        days = int(request.query_params.get('days', 30))
        days = min(max(days, 7), 365)  # Entre 7 et 365 jours
        
        data = AnalyticsService.get_seller_dashboard(request.user, days)
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """
        Obtenir les tendances (comparaison périodes)
        GET /api/analytics/dashboard/trends/?days=30
        """
        days = int(request.query_params.get('days', 30))
        
        data = AnalyticsService.get_trends(request.user, days)
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def revenue(self, request):
        """
        Obtenir les analytics de revenus
        GET /api/analytics/dashboard/revenue/?days=30
        """
        days = int(request.query_params.get('days', 30))
        
        data = AnalyticsService.get_revenue_analytics(request.user, days)
        
        # Convertir les Decimal en float pour JSON
        if data['totals']['revenue']:
            data['totals']['revenue'] = float(data['totals']['revenue'])
        
        for item in data['daily_revenue']:
            if item.get('total'):
                item['total'] = float(item['total'])
        
        for item in data['by_type']:
            if item.get('total'):
                item['total'] = float(item['total'])
        
        for item in data['top_listings']:
            if item.get('total'):
                item['total'] = float(item['total'])
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def listings(self, request):
        """
        Obtenir les stats de toutes les annonces du vendeur
        GET /api/analytics/dashboard/listings/
        """
        from apps.listings.models import Listing
        
        listings = Listing.objects.filter(seller=request.user)
        
        result = []
        for listing in listings:
            stats, _ = ListingStats.objects.get_or_create(listing=listing)
            result.append({
                'id': str(listing.id),
                'title': listing.title,
                'price': str(listing.price),
                'status': listing.status,
                'created_at': listing.created_at.isoformat(),
                'stats': ListingStatsSerializer(stats).data
            })
        
        return Response(result)
    
    @action(detail=False, methods=['get'], url_path='listing/(?P<listing_id>[^/.]+)')
    def listing_detail(self, request, listing_id=None):
        """
        Obtenir les analytics détaillées d'une annonce
        GET /api/analytics/dashboard/listing/<listing_id>/?days=30
        """
        from apps.listings.models import Listing
        
        try:
            listing = Listing.objects.get(id=listing_id, seller=request.user)
        except Listing.DoesNotExist:
            return Response(
                {'error': 'Annonce non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        days = int(request.query_params.get('days', 30))
        data = AnalyticsService.get_listing_analytics(listing, days)
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def payments(self, request):
        """
        Obtenir l'historique des paiements
        GET /api/analytics/dashboard/payments/?page=1&limit=20
        """
        from apps.payments.models import Payment
        
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        limit = min(limit, 100)
        
        offset = (page - 1) * limit
        
        payments = Payment.objects.filter(
            listing__seller=request.user
        ).select_related('listing', 'user').order_by('-created_at')
        
        total = payments.count()
        payments = payments[offset:offset + limit]
        
        result = []
        for payment in payments:
            result.append({
                'id': str(payment.id),
                'date': payment.created_at.isoformat(),
                'listing': {
                    'id': str(payment.listing.id) if payment.listing else None,
                    'title': payment.listing.title if payment.listing else None,
                },
                'buyer': {
                    'id': str(payment.user.id) if payment.user else None,
                    'username': payment.user.username if payment.user else None,
                },
                'amount': str(payment.amount),
                'payment_type': payment.payment_type,
                'status': payment.status,
            })
        
        return Response({
            'payments': result,
            'total': total,
            'page': page,
            'pages': (total + limit - 1) // limit
        })
    
    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """
        Obtenir l'activité récente
        GET /api/analytics/dashboard/recent_activity/?limit=20
        """
        limit = int(request.query_params.get('limit', 20))
        limit = min(limit, 50)
        
        events = Event.objects.filter(
            target_user=request.user
        ).select_related('user', 'listing').order_by('-created_at')[:limit]
        
        result = []
        for event in events:
            result.append({
                'id': str(event.id),
                'type': event.event_type,
                'type_display': dict(Event.EVENT_TYPES).get(event.event_type, event.event_type),
                'user': event.user.username if event.user else 'Visiteur',
                'listing': {
                    'id': str(event.listing.id) if event.listing else None,
                    'title': event.listing.title if event.listing else None,
                },
                'created_at': event.created_at.isoformat(),
            })
        
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def quick_listing(self, request):
        """
        Création rapide d'une annonce depuis le dashboard
        POST /api/analytics/dashboard/quick_listing/
        """
        from apps.listings.models import Listing, Category
        
        serializer = QuickListingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            category = Category.objects.get(id=serializer.validated_data['category_id'])
        except Category.DoesNotExist:
            return Response(
                {'error': 'Catégorie non trouvée'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Valeurs par défaut pour les champs obligatoires
        location = serializer.validated_data.get('location') or "Non précisé"
        listing_type = serializer.validated_data.get('listing_type', 'product')
        
        listing = Listing.objects.create(
            seller=request.user,
            title=serializer.validated_data['title'],
            description=serializer.validated_data['description'],
            price=serializer.validated_data['price'],
            category=category,
            status='draft',
            location=location,
            listing_type=listing_type
        )
        
        # Créer les stats pour l'annonce
        ListingStats.objects.create(listing=listing)
        
        return Response({
            'id': str(listing.id),
            'title': listing.title,
            'status': listing.status,
            'message': 'Annonce créée en brouillon'
        }, status=status.HTTP_201_CREATED)


class EventTrackingView(APIView):
    """
    Vue pour tracker les événements
    Peut être appelée par le frontend
    """
    permission_classes = []  # Permet les visiteurs anonymes
    
    def post(self, request):
        """
        Tracker un événement
        POST /api/analytics/track/
        """
        serializer = EventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        listing = None
        target_user = None
        
        listing_id = serializer.validated_data.get('listing_id')
        if listing_id:
            from apps.listings.models import Listing
            try:
                listing = Listing.objects.get(id=listing_id)
                target_user = listing.seller
            except Listing.DoesNotExist:
                pass
        
        user = request.user if request.user.is_authenticated else None
        
        event = EventTracker.track(
            event_type=serializer.validated_data['event_type'],
            request=request,
            user=user,
            target_user=target_user,
            listing=listing,
            metadata=serializer.validated_data.get('metadata', {})
        )
        
        if event:
            return Response({'status': 'tracked', 'event_id': str(event.id)})
        else:
            return Response(
                {'error': 'Failed to track event'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExportView(APIView):
    """
    Vue pour l'export de données en CSV
    """
    permission_classes = [IsAuthenticated, IsSeller]
    
    def get(self, request, export_type):
        """
        Exporter des données en CSV
        GET /api/analytics/export/listings/
        GET /api/analytics/export/payments/
        GET /api/analytics/export/reviews/
        """
        export_functions = {
            'listings': ExportService.export_listings_csv,
            'payments': ExportService.export_payments_csv,
            'reviews': ExportService.export_reviews_csv,
        }
        
        if export_type not in export_functions:
            return Response(
                {'error': 'Type d\'export invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        csv_content = export_functions[export_type](request.user)
        
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{export_type}_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        return response


class KPIView(APIView):
    """
    Vue pour obtenir les KPIs principaux rapidement
    """
    permission_classes = [IsAuthenticated, IsSeller]
    
    def get(self, request):
        """
        Obtenir les KPIs principaux
        GET /api/analytics/kpis/
        """
        from apps.listings.models import Listing
        from apps.payments.models import Payment
        from django.db.models import Sum
        
        user = request.user
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # KPIs annonces
        listings = Listing.objects.filter(seller=user)
        active_listings = listings.filter(status='active').count()
        
        # KPIs événements (7 derniers jours)
        week_events = Event.objects.filter(
            target_user=user,
            created_at__date__gte=week_ago
        )
        week_views = week_events.filter(event_type='listing_view').count()
        
        # KPIs revenus (30 derniers jours)
        month_payments = Payment.objects.filter(
            listing__seller=user,
            status='completed',
            created_at__date__gte=month_ago
        )
        month_revenue = month_payments.aggregate(total=Sum('amount'))['total'] or 0
        
        return Response({
            'active_listings': active_listings,
            'week_views': week_views,
            'month_revenue': float(month_revenue),
            'avg_rating': float(user.avg_rating),
            'total_reviews': user.total_reviews,
        })
