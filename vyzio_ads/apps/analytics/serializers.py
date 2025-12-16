"""
Serializers pour analytics
"""
from rest_framework import serializers
from .models import Event, DailyStats, ListingStats


class EventSerializer(serializers.ModelSerializer):
    """Serializer pour les événements"""
    
    class Meta:
        model = Event
        fields = ('id', 'event_type', 'listing', 'metadata', 'created_at')
        read_only_fields = ('id', 'created_at')


class EventCreateSerializer(serializers.Serializer):
    """Serializer pour créer un événement"""
    event_type = serializers.ChoiceField(choices=Event.EVENT_TYPES)
    listing_id = serializers.UUIDField(required=False, allow_null=True)
    metadata = serializers.DictField(required=False, default=dict)


class DailyStatsSerializer(serializers.ModelSerializer):
    """Serializer pour les stats quotidiennes"""
    
    class Meta:
        model = DailyStats
        fields = (
            'date', 'listing_views', 'listing_clicks', 'profile_views',
            'messages_received', 'messages_sent', 'favorites_received',
            'payments_received', 'revenue', 'reviews_received', 'avg_rating_day'
        )


class ListingStatsSerializer(serializers.ModelSerializer):
    """Serializer pour les stats d'annonces"""
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_id = serializers.UUIDField(source='listing.id', read_only=True)
    
    class Meta:
        model = ListingStats
        fields = (
            'listing_id', 'listing_title',
            'total_views', 'total_clicks', 'total_favorites',
            'total_shares', 'total_contacts', 'unique_views',
            'unique_clicks', 'conversion_rate', 'updated_at'
        )


class DashboardSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé du dashboard"""
    
    period = serializers.DictField()
    engagement = serializers.DictField()
    messaging = serializers.DictField()
    financial = serializers.DictField()
    reputation = serializers.DictField()
    listings = serializers.DictField()


class ListingAnalyticsSerializer(serializers.Serializer):
    """Serializer pour les analytics d'une annonce"""
    
    listing_id = serializers.UUIDField()
    title = serializers.CharField()
    totals = serializers.DictField()
    period_stats = serializers.DictField()
    daily_views = serializers.ListField()
    daily_clicks = serializers.ListField()


class RevenueAnalyticsSerializer(serializers.Serializer):
    """Serializer pour les analytics de revenus"""
    
    period = serializers.DictField()
    totals = serializers.DictField()
    daily_revenue = serializers.ListField()
    by_type = serializers.ListField()
    top_listings = serializers.ListField()


class TrendsSerializer(serializers.Serializer):
    """Serializer pour les tendances"""
    
    views = serializers.DictField()
    revenue = serializers.DictField()


class QuickListingSerializer(serializers.Serializer):
    """Serializer pour création rapide d'annonce"""
    
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    category_id = serializers.IntegerField()
    location = serializers.CharField(max_length=100, required=False, default="")
    listing_type = serializers.ChoiceField(choices=[('product', 'Produit'), ('service', 'Service'), ('rental', 'Location'), ('job', 'Prestation')], required=False, default='product')
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        max_length=5
    )
