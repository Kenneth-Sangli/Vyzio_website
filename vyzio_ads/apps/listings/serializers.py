from rest_framework import serializers
from .models import Listing, ListingImage, ListingVideo, Category, Favorite
from apps.users.serializers import UserProfileSerializer


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'icon')


class ListingImageSerializer(serializers.ModelSerializer):
    """Serializer basique pour les images"""
    class Meta:
        model = ListingImage
        fields = ('id', 'image', 'is_primary', 'order')


class ListingImageWithVariantsSerializer(serializers.ModelSerializer):
    """Serializer avec toutes les variantes d'images (thumbnails, etc.)"""
    thumbnail = serializers.SerializerMethodField()
    card = serializers.SerializerMethodField()
    detail = serializers.SerializerMethodField()
    full = serializers.SerializerMethodField()
    
    class Meta:
        model = ListingImage
        fields = ('id', 'image', 'is_primary', 'order', 'thumbnail', 'card', 'detail', 'full')
    
    def _get_cloudinary_url(self, obj, transformation: dict) -> str:
        """Génère une URL Cloudinary avec transformation."""
        if not obj.image:
            return None
        
        # Si c'est une URL Cloudinary
        image_url = str(obj.image.url) if obj.image else ''
        if 'cloudinary' in image_url or 'res.cloudinary.com' in image_url:
            try:
                import cloudinary
                # Extraire le public_id de l'URL
                # Format: https://res.cloudinary.com/cloud_name/image/upload/v123/folder/image.jpg
                parts = image_url.split('/upload/')
                if len(parts) == 2:
                    public_id = parts[1].rsplit('.', 1)[0]  # Enlever l'extension
                    if public_id.startswith('v'):
                        # Enlever le version number
                        public_id = '/'.join(public_id.split('/')[1:])
                    return cloudinary.CloudinaryImage(public_id).build_url(**transformation)
            except Exception:
                pass
        
        # Fallback: retourner l'URL originale
        return image_url
    
    def get_thumbnail(self, obj):
        return self._get_cloudinary_url(obj, {
            'width': 150, 'height': 150, 'crop': 'fill',
            'gravity': 'auto', 'quality': 'auto:low', 'fetch_format': 'auto'
        })
    
    def get_card(self, obj):
        return self._get_cloudinary_url(obj, {
            'width': 400, 'height': 300, 'crop': 'fill',
            'gravity': 'auto', 'quality': 'auto:good', 'fetch_format': 'auto'
        })
    
    def get_detail(self, obj):
        return self._get_cloudinary_url(obj, {
            'width': 800, 'height': 600, 'crop': 'limit',
            'quality': 'auto:best', 'fetch_format': 'auto'
        })
    
    def get_full(self, obj):
        return self._get_cloudinary_url(obj, {
            'width': 1200, 'crop': 'limit',
            'quality': 'auto:best', 'fetch_format': 'auto'
        })


class ListingVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingVideo
        fields = ('id', 'video_url', 'platform')


class ListingListSerializer(serializers.ModelSerializer):
    seller = UserProfileSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Listing
        fields = ('id', 'title', 'slug', 'price', 'location', 'listing_type', 'condition', 'status',
                  'seller', 'category', 'primary_image', 'views_count', 'is_boosted', 
                  'created_at', 'favorites_count')
        read_only_fields = ('id', 'views_count', 'created_at')
    
    def get_primary_image(self, obj):
        """Retourne l'image principale avec variantes (thumbnail, card)"""
        image = obj.images.filter(is_primary=True).first()
        if not image:
            image = obj.images.first()
        if image:
            return ListingImageWithVariantsSerializer(image).data
        return None


class ListingDetailSerializer(serializers.ModelSerializer):
    seller = UserProfileSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    images = ListingImageWithVariantsSerializer(many=True, read_only=True)
    video = ListingVideoSerializer(read_only=True)
    is_favorite = serializers.SerializerMethodField()
    
    class Meta:
        model = Listing
        fields = ('id', 'title', 'slug', 'description', 'price', 'price_negotiable',
                  'location', 'latitude', 'longitude', 'listing_type', 'condition', 'status',
                  'seller', 'category', 'images', 'video', 'stock', 'available',
                  'views_count', 'is_boosted', 'boost_end_date', 'is_favorite',
                  'created_at', 'updated_at', 'favorites_count')
        read_only_fields = ('id', 'views_count', 'created_at', 'updated_at')
    
    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, listing=obj).exists()
        return False


class ListingCreateUpdateSerializer(serializers.ModelSerializer):
    images = ListingImageSerializer(many=True, read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Listing
        fields = ('id', 'title', 'description', 'price', 'price_negotiable',
                  'location', 'latitude', 'longitude', 'listing_type', 'condition', 'category',
                  'category_id', 'stock', 'available', 'images', 'status')
        read_only_fields = ('id',)
    
    def create(self, validated_data):
        # Gérer category_id
        category_id = validated_data.pop('category_id', None)
        if category_id:
            validated_data['category_id'] = category_id
        
        # Définir le statut par défaut à 'published' pour publication directe
        if 'status' not in validated_data:
            validated_data['status'] = 'published'
        
        return super().create(validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    listing = ListingListSerializer(read_only=True)
    
    class Meta:
        model = Favorite
        fields = ('id', 'listing', 'created_at')
        read_only_fields = ('id', 'created_at')
