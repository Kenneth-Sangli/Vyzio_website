from rest_framework import serializers
from .models import CustomUser, SellerSubscription, SellerProfile, PasswordResetToken
from django.contrib.auth.password_validation import validate_password


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name', 'password', 'password2', 'role', 'phone')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un compte avec cet email existe déjà.")
        return value.lower()
    
    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer pour la connexion"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour afficher un profil public"""
    avg_rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'phone', 'avatar', 
                  'bio', 'location', 'role', 'shop_name', 'is_verified', 'avg_rating', 
                  'total_reviews', 'created_at')
        read_only_fields = ('id', 'created_at', 'email', 'avg_rating', 'total_reviews')


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mise à jour du profil"""
    
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'phone', 'avatar', 'bio', 'location', 
                  'shop_name', 'company_name')
    
    def validate_phone(self, value):
        # Nettoyer le numéro de téléphone
        if value:
            value = ''.join(filter(str.isdigit, value))
            if len(value) < 10:
                raise serializers.ValidationError("Numéro de téléphone invalide.")
        return value


class SellerProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil vendeur"""
    
    class Meta:
        model = SellerProfile
        fields = ('shop_name', 'shop_description', 'shop_logo', 'shop_banner',
                  'company_name', 'siret', 'vat_number', 'business_email', 
                  'business_phone', 'website', 'address', 'city', 'postal_code',
                  'country', 'is_pro', 'is_verified', 'total_sales', 'response_rate',
                  'response_time', 'created_at')
        read_only_fields = ('is_verified', 'total_sales', 'response_rate', 'response_time', 'created_at')


class SellerSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer pour l'abonnement vendeur"""
    
    class Meta:
        model = SellerSubscription
        fields = ('id', 'subscription_type', 'is_active', 'started_at', 'ends_at', 
                  'listings_count', 'max_listings', 'can_boost', 'boost_count')
        read_only_fields = fields


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer complet pour l'utilisateur connecté"""
    seller_subscription = serializers.SerializerMethodField()
    seller_profile = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'phone', 'avatar', 
                  'bio', 'location', 'role', 'shop_name', 'company_name', 'is_professional',
                  'is_verified', 'is_active_seller', 'avg_rating', 'total_reviews', 
                  'subscription_type', 'created_at', 'seller_subscription', 'seller_profile',
                  'is_superuser')
        read_only_fields = fields
    
    def get_seller_subscription(self, obj):
        if hasattr(obj, 'seller_subscription'):
            return SellerSubscriptionSerializer(obj.seller_subscription).data
        return None
    
    def get_seller_profile(self, obj):
        if hasattr(obj, 'seller_profile'):
            return SellerProfileSerializer(obj.seller_profile).data
        return None


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer pour demande de reset mot de passe"""
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer pour confirmation reset mot de passe"""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs.pop('new_password2'):
            raise serializers.ValidationError({"new_password": "Les mots de passe ne correspondent pas."})
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer pour vérification email"""
    token = serializers.CharField(required=True)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour changement de mot de passe (utilisateur connecté)"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs.pop('new_password2'):
            raise serializers.ValidationError({"new_password": "Les mots de passe ne correspondent pas."})
        return attrs
