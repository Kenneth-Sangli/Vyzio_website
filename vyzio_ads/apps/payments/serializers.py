from rest_framework import serializers
from .models import (
    Payment, SubscriptionPlan, Subscription, Invoice, Coupon,
    PostCreditPack, PostCredit, PostCreditTransaction
)


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer pour les plans d'abonnement."""
    
    class Meta:
        model = SubscriptionPlan
        fields = (
            'id', 'name', 'slug', 'plan_type', 'billing_cycle', 'price',
            'max_listings', 'max_images_per_listing', 'can_boost', 
            'boost_count_per_month', 'featured_badge', 'priority_support',
            'analytics_access', 'description', 'features_list', 'is_popular'
        )
        read_only_fields = ('id',)


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer pour les abonnements utilisateurs."""
    
    plan = SubscriptionPlanSerializer(read_only=True)
    is_active = serializers.ReadOnlyField()
    can_create_listing = serializers.ReadOnlyField()
    remaining_listings = serializers.ReadOnlyField()
    
    class Meta:
        model = Subscription
        fields = (
            'id', 'plan', 'status', 'is_active', 
            'started_at', 'current_period_start', 'current_period_end',
            'ends_at', 'cancelled_at', 'trial_ends_at',
            'listings_used', 'boosts_used', 'can_create_listing', 'remaining_listings',
            'auto_renew', 'cancel_at_period_end'
        )
        read_only_fields = fields


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer pour l'historique des paiements."""
    
    subscription_plan = SubscriptionPlanSerializer(read_only=True)
    
    class Meta:
        model = Payment
        fields = (
            'id', 'amount', 'currency', 'payment_type', 'status',
            'subscription_plan', 'description', 
            'created_at', 'completed_at'
        )
        read_only_fields = fields


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer pour les factures."""
    
    class Meta:
        model = Invoice
        fields = (
            'id', 'invoice_number', 'amount', 'tax_amount', 
            'issued_at', 'due_at', 'paid_at', 'pdf_file'
        )
        read_only_fields = fields


class CouponSerializer(serializers.ModelSerializer):
    """Serializer pour les coupons."""
    
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = Coupon
        fields = (
            'code', 'discount_type', 'discount_value',
            'applies_to_subscription', 'applies_to_post_credit',
            'valid_from', 'valid_until', 'is_valid'
        )
        read_only_fields = fields
    
    def get_is_valid(self, obj):
        return obj.is_valid()


class CouponValidateSerializer(serializers.Serializer):
    """Serializer pour valider un code promo."""
    
    code = serializers.CharField(max_length=50)
    payment_type = serializers.ChoiceField(
        choices=['subscription', 'post_credit'],
        default='subscription'
    )


# ==================== Post Credit (Pay-per-post) ====================

class PostCreditPackSerializer(serializers.ModelSerializer):
    """Serializer pour les packs de crédits."""
    
    total_credits = serializers.ReadOnlyField()
    price_per_credit = serializers.ReadOnlyField()
    
    class Meta:
        model = PostCreditPack
        fields = (
            'id', 'name', 'slug', 'credits', 'bonus_credits', 'total_credits',
            'price', 'price_per_credit', 'description', 'is_popular'
        )
        read_only_fields = fields


class PostCreditSerializer(serializers.ModelSerializer):
    """Serializer pour le solde de crédits d'un utilisateur."""
    
    class Meta:
        model = PostCredit
        fields = ('balance', 'total_purchased', 'total_used')
        read_only_fields = fields


class PostCreditTransactionSerializer(serializers.ModelSerializer):
    """Serializer pour l'historique des transactions de crédits."""
    
    listing_title = serializers.SerializerMethodField()
    
    class Meta:
        model = PostCreditTransaction
        fields = (
            'id', 'transaction_type', 'amount', 'balance_after',
            'listing_title', 'description', 'created_at'
        )
        read_only_fields = fields
    
    def get_listing_title(self, obj):
        return obj.listing.title if obj.listing else None


# ==================== Checkout Session Serializers ====================

class CreateSubscriptionCheckoutSerializer(serializers.Serializer):
    """Serializer pour créer une session checkout abonnement."""
    
    plan_id = serializers.IntegerField()
    coupon_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    success_url = serializers.URLField(required=False)
    cancel_url = serializers.URLField(required=False)
    
    def validate_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Plan invalide ou inactif")
        return value


class CreatePostCreditCheckoutSerializer(serializers.Serializer):
    """Serializer pour créer une session checkout crédits."""
    
    pack_id = serializers.IntegerField()
    coupon_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    success_url = serializers.URLField(required=False)
    cancel_url = serializers.URLField(required=False)
    
    def validate_pack_id(self, value):
        try:
            pack = PostCreditPack.objects.get(id=value, is_active=True)
        except PostCreditPack.DoesNotExist:
            raise serializers.ValidationError("Pack invalide ou inactif")
        return value


class CreateSinglePostCheckoutSerializer(serializers.Serializer):
    """Serializer pour payer une annonce unique."""
    
    listing_id = serializers.UUIDField()
    success_url = serializers.URLField(required=False)
    cancel_url = serializers.URLField(required=False)


class CheckoutResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse checkout."""
    
    checkout_url = serializers.URLField()
    session_id = serializers.CharField()
    is_test = serializers.BooleanField(default=False)


class BillingPortalSerializer(serializers.Serializer):
    """Serializer pour la réponse du portail de facturation."""
    
    url = serializers.URLField()
