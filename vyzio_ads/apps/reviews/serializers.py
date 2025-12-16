from rest_framework import serializers
from .models import Review, ReviewPhoto, ReviewReport, FavoriteSeller
from apps.users.serializers import UserProfileSerializer
from apps.listings.models import Favorite as ListingFavorite


class ReviewPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewPhoto
        fields = ('id', 'image')


class ReviewSerializer(serializers.ModelSerializer):
    reviewer = UserProfileSerializer(read_only=True)
    photos = ReviewPhotoSerializer(many=True, read_only=True)
    reports_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = ('id', 'reviewer', 'rating', 'comment', 'photos', 'seller_response',
                  'seller_response_date', 'is_verified_buyer', 'is_flagged', 
                  'reports_count', 'created_at')
        read_only_fields = ('id', 'reviewer', 'created_at', 'seller_response', 
                           'seller_response_date', 'is_verified_buyer', 'is_flagged')
    
    def get_reports_count(self, obj):
        return obj.reports.count()


class ReviewCreateSerializer(serializers.ModelSerializer):
    listing_id = serializers.UUIDField(required=False, allow_null=True)
    
    class Meta:
        model = Review
        fields = ('rating', 'comment', 'listing_id')
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("La note doit être entre 1 et 5")
        return value


class ReviewReportSerializer(serializers.ModelSerializer):
    reporter = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = ReviewReport
        fields = ('id', 'review', 'reporter', 'reason', 'description', 
                  'is_resolved', 'created_at')
        read_only_fields = ('id', 'reporter', 'is_resolved', 'created_at')


class ReviewReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewReport
        fields = ('reason', 'description')
    
    def validate_reason(self, value):
        valid_reasons = ['spam', 'inappropriate', 'fake', 'harassment', 'other']
        if value not in valid_reasons:
            raise serializers.ValidationError(f"Raison invalide. Choisir parmi: {', '.join(valid_reasons)}")
        return value


class ListingFavoriteSerializer(serializers.ModelSerializer):
    """Serializer pour les favoris d'annonces (depuis listings app)"""
    listing_details = serializers.SerializerMethodField()
    
    class Meta:
        model = ListingFavorite
        fields = ('id', 'listing', 'listing_details', 'created_at')
        read_only_fields = ('id', 'created_at')
    
    def get_listing_details(self, obj):
        if obj.listing:
            return {
                'id': str(obj.listing.id),
                'title': obj.listing.title,
                'price': str(obj.listing.price),
                'status': obj.listing.status,
            }
        return None


class FavoriteSellerSerializer(serializers.ModelSerializer):
    """Serializer pour les vendeurs favoris"""
    seller_details = serializers.SerializerMethodField()
    
    class Meta:
        model = FavoriteSeller
        fields = ('id', 'seller', 'seller_details', 'created_at')
        read_only_fields = ('id', 'created_at')
    
    def get_seller_details(self, obj):
        if obj.seller:
            return {
                'id': str(obj.seller.id),
                'username': obj.seller.username,
                'avg_rating': float(obj.seller.avg_rating),
                'total_reviews': obj.seller.total_reviews,
            }
        return None


class FavoriteListingCreateSerializer(serializers.Serializer):
    """Serializer pour créer un favori d'annonce"""
    listing_id = serializers.UUIDField()


class FavoriteSellerCreateSerializer(serializers.Serializer):
    """Serializer pour créer un favori de vendeur"""
    seller_id = serializers.UUIDField()


class SellerReputationSerializer(serializers.Serializer):
    """Serializer for seller reputation/stats"""
    seller_id = serializers.UUIDField()
    username = serializers.CharField()
    avg_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    total_reviews = serializers.IntegerField()
    rating_distribution = serializers.DictField()
    badges = serializers.ListField(child=serializers.CharField())
    recent_reviews = ReviewSerializer(many=True)
