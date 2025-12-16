"""
Services pour le tracking d'événements et calcul d'analytics
"""
from django.db.models import Sum, Count, Avg, F, Q
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class EventTracker:
    """Service pour tracker les événements"""
    
    @staticmethod
    def track(event_type, request=None, user=None, target_user=None, 
              listing=None, metadata=None):
        """
        Tracker un événement
        
        Args:
            event_type: Type d'événement (voir Event.EVENT_TYPES)
            request: HttpRequest (pour extraire IP, user agent, etc.)
            user: Utilisateur qui effectue l'action
            target_user: Utilisateur cible (ex: vendeur)
            listing: Annonce concernée
            metadata: Données additionnelles (dict)
        """
        from .models import Event, ListingStats
        
        try:
            event_data = {
                'event_type': event_type,
                'user': user,
                'target_user': target_user,
                'listing': listing,
                'metadata': metadata or {},
            }
            
            if request:
                event_data['ip_address'] = EventTracker._get_client_ip(request)
                event_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]
                event_data['referrer'] = request.META.get('HTTP_REFERER', '')[:500]
                event_data['session_id'] = request.session.session_key or ''
                
                # Si user non fourni, essayer de le récupérer de la request
                if not user and request.user.is_authenticated:
                    event_data['user'] = request.user
            
            event = Event.objects.create(**event_data)
            
            # Mettre à jour les stats de l'annonce si applicable
            if listing and event_type in ['listing_view', 'listing_click', 
                                          'listing_favorite', 'listing_share', 
                                          'listing_contact']:
                EventTracker._update_listing_stats(listing, event_type, user)
            
            return event
            
        except Exception as e:
            logger.error(f"Error tracking event {event_type}: {str(e)}")
            return None
    
    @staticmethod
    def _get_client_ip(request):
        """Extraire l'IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def _update_listing_stats(listing, event_type, user=None):
        """Mettre à jour les stats d'une annonce"""
        from .models import ListingStats
        
        stats, created = ListingStats.objects.get_or_create(listing=listing)
        
        field_mapping = {
            'listing_view': 'total_views',
            'listing_click': 'total_clicks',
            'listing_favorite': 'total_favorites',
            'listing_share': 'total_shares',
            'listing_contact': 'total_contacts',
        }
        
        field = field_mapping.get(event_type)
        if field:
            setattr(stats, field, F(field) + 1)
            stats.save(update_fields=[field, 'updated_at'])
            stats.refresh_from_db()
            stats.calculate_conversion_rate()
            stats.save(update_fields=['conversion_rate'])


class AnalyticsService:
    """Service pour calculer les analytics et KPIs"""
    
    @staticmethod
    def get_seller_dashboard(seller, days=30):
        """
        Obtenir les données du dashboard vendeur
        
        Args:
            seller: Utilisateur vendeur
            days: Nombre de jours à analyser
        
        Returns:
            dict avec toutes les métriques
        """
        from .models import Event, DailyStats
        from apps.listings.models import Listing
        from apps.messaging.models import Conversation, Message
        from apps.payments.models import Payment
        from apps.reviews.models import Review
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Récupérer les annonces du vendeur
        listings = Listing.objects.filter(seller=seller)
        listing_ids = list(listings.values_list('id', flat=True))
        
        # Métriques d'engagement
        events = Event.objects.filter(
            target_user=seller,
            created_at__gte=start_date
        )
        
        engagement = {
            'total_views': events.filter(event_type='listing_view').count(),
            'total_clicks': events.filter(event_type='listing_click').count(),
            'profile_views': events.filter(event_type='profile_view').count(),
            'favorites_received': events.filter(event_type='listing_favorite').count(),
        }
        
        # Métriques de messagerie
        conversations = Conversation.objects.filter(seller=seller)
        messages_received = Message.objects.filter(
            conversation__seller=seller,
            created_at__gte=start_date
        ).exclude(sender=seller).count()
        
        messaging = {
            'total_conversations': conversations.count(),
            'active_conversations': conversations.filter(is_active=True).count(),
            'messages_received': messages_received,
        }
        
        # Métriques financières
        payments = Payment.objects.filter(
            listing__seller=seller,
            status='completed',
            created_at__gte=start_date
        )
        
        financial = {
            'total_payments': payments.count(),
            'total_revenue': payments.aggregate(total=Sum('amount'))['total'] or Decimal('0'),
            'avg_transaction': payments.aggregate(avg=Avg('amount'))['avg'] or Decimal('0'),
        }
        
        # Métriques de réputation
        reviews = Review.objects.filter(seller=seller, is_approved=True)
        recent_reviews = reviews.filter(created_at__gte=start_date)
        
        reputation = {
            'total_reviews': seller.total_reviews,
            'avg_rating': float(seller.avg_rating),
            'recent_reviews': recent_reviews.count(),
        }
        
        # Annonces
        listings_data = {
            'total_listings': listings.count(),
            'active_listings': listings.filter(status='active').count(),
            'sold_listings': listings.filter(status='sold').count(),
            'draft_listings': listings.filter(status='draft').count(),
        }
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days,
            },
            'engagement': engagement,
            'messaging': messaging,
            'financial': financial,
            'reputation': reputation,
            'listings': listings_data,
        }
    
    @staticmethod
    def get_listing_analytics(listing, days=30):
        """Obtenir les analytics d'une annonce spécifique"""
        from .models import Event, ListingStats
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Stats globales
        stats, _ = ListingStats.objects.get_or_create(listing=listing)
        
        # Événements récents
        events = Event.objects.filter(
            listing=listing,
            created_at__gte=start_date
        )
        
        # Statistiques par jour
        daily_views = events.filter(event_type='listing_view').annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        daily_clicks = events.filter(event_type='listing_click').annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        return {
            'listing_id': str(listing.id),
            'title': listing.title,
            'totals': {
                'views': stats.total_views,
                'clicks': stats.total_clicks,
                'favorites': stats.total_favorites,
                'shares': stats.total_shares,
                'contacts': stats.total_contacts,
                'conversion_rate': float(stats.conversion_rate),
            },
            'period_stats': {
                'views': events.filter(event_type='listing_view').count(),
                'clicks': events.filter(event_type='listing_click').count(),
                'favorites': events.filter(event_type='listing_favorite').count(),
                'contacts': events.filter(event_type='listing_contact').count(),
            },
            'daily_views': list(daily_views),
            'daily_clicks': list(daily_clicks),
        }
    
    @staticmethod
    def get_revenue_analytics(seller, days=30):
        """Obtenir les analytics de revenus"""
        from apps.payments.models import Payment
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        payments = Payment.objects.filter(
            listing__seller=seller,
            status='completed',
            created_at__gte=start_date
        )
        
        # Revenus par jour
        daily_revenue = payments.annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('day')
        
        # Revenus par type de paiement
        by_type = payments.values('payment_type').annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Top annonces par revenus
        top_listings = payments.values(
            'listing__id', 'listing__title'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:5]
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'totals': {
                'revenue': payments.aggregate(total=Sum('amount'))['total'] or Decimal('0'),
                'transactions': payments.count(),
            },
            'daily_revenue': list(daily_revenue),
            'by_type': list(by_type),
            'top_listings': list(top_listings),
        }
    
    @staticmethod
    def get_trends(seller, days=30):
        """Calculer les tendances (comparaison avec période précédente)"""
        from .models import Event
        from apps.payments.models import Payment
        
        end_date = timezone.now()
        mid_date = end_date - timedelta(days=days)
        start_date = mid_date - timedelta(days=days)
        
        # Période actuelle
        current_events = Event.objects.filter(
            target_user=seller,
            created_at__gte=mid_date
        )
        current_payments = Payment.objects.filter(
            listing__seller=seller,
            status='completed',
            created_at__gte=mid_date
        )
        
        # Période précédente
        previous_events = Event.objects.filter(
            target_user=seller,
            created_at__gte=start_date,
            created_at__lt=mid_date
        )
        previous_payments = Payment.objects.filter(
            listing__seller=seller,
            status='completed',
            created_at__gte=start_date,
            created_at__lt=mid_date
        )
        
        def calculate_change(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return round(((current - previous) / previous) * 100, 1)
        
        current_views = current_events.filter(event_type='listing_view').count()
        previous_views = previous_events.filter(event_type='listing_view').count()
        
        current_revenue = current_payments.aggregate(t=Sum('amount'))['t'] or 0
        previous_revenue = previous_payments.aggregate(t=Sum('amount'))['t'] or 0
        
        return {
            'views': {
                'current': current_views,
                'previous': previous_views,
                'change': calculate_change(current_views, previous_views),
            },
            'revenue': {
                'current': float(current_revenue),
                'previous': float(previous_revenue),
                'change': calculate_change(float(current_revenue), float(previous_revenue)),
            },
        }


class ExportService:
    """Service pour l'export de données"""
    
    @staticmethod
    def export_listings_csv(seller):
        """Exporter les annonces en CSV"""
        import csv
        from io import StringIO
        from apps.listings.models import Listing
        from .models import ListingStats
        
        output = StringIO()
        writer = csv.writer(output)
        
        # En-têtes
        writer.writerow([
            'ID', 'Titre', 'Prix', 'Catégorie', 'Statut', 
            'Vues', 'Clics', 'Favoris', 'Contacts', 'Taux conversion',
            'Créé le', 'Mis à jour le'
        ])
        
        listings = Listing.objects.filter(seller=seller).select_related('category')
        
        for listing in listings:
            stats = ListingStats.objects.filter(listing=listing).first()
            writer.writerow([
                str(listing.id),
                listing.title,
                str(listing.price),
                listing.category.name if listing.category else '',
                listing.status,
                stats.total_views if stats else 0,
                stats.total_clicks if stats else 0,
                stats.total_favorites if stats else 0,
                stats.total_contacts if stats else 0,
                f"{stats.conversion_rate:.2f}%" if stats else '0%',
                listing.created_at.strftime('%Y-%m-%d'),
                listing.updated_at.strftime('%Y-%m-%d'),
            ])
        
        return output.getvalue()
    
    @staticmethod
    def export_payments_csv(seller):
        """Exporter les paiements en CSV"""
        import csv
        from io import StringIO
        from apps.payments.models import Payment
        
        output = StringIO()
        writer = csv.writer(output)
        
        # En-têtes
        writer.writerow([
            'ID', 'Date', 'Annonce', 'Acheteur', 'Montant', 
            'Type', 'Statut', 'Transaction Stripe'
        ])
        
        payments = Payment.objects.filter(
            listing__seller=seller
        ).select_related('listing', 'user').order_by('-created_at')
        
        for payment in payments:
            writer.writerow([
                str(payment.id),
                payment.created_at.strftime('%Y-%m-%d %H:%M'),
                payment.listing.title if payment.listing else '',
                payment.user.email if payment.user else '',
                str(payment.amount),
                payment.payment_type,
                payment.status,
                payment.stripe_payment_intent_id or '',
            ])
        
        return output.getvalue()
    
    @staticmethod
    def export_reviews_csv(seller):
        """Exporter les avis en CSV"""
        import csv
        from io import StringIO
        from apps.reviews.models import Review
        
        output = StringIO()
        writer = csv.writer(output)
        
        # En-têtes
        writer.writerow([
            'ID', 'Date', 'Acheteur', 'Note', 'Commentaire',
            'Vérifié', 'Réponse', 'Date réponse'
        ])
        
        reviews = Review.objects.filter(
            seller=seller
        ).select_related('reviewer').order_by('-created_at')
        
        for review in reviews:
            writer.writerow([
                str(review.id),
                review.created_at.strftime('%Y-%m-%d'),
                review.reviewer.username if review.reviewer else '',
                review.rating,
                review.comment,
                'Oui' if review.is_verified_buyer else 'Non',
                review.seller_response,
                review.seller_response_date.strftime('%Y-%m-%d') if review.seller_response_date else '',
            ])
        
        return output.getvalue()
