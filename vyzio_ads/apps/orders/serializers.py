"""
Serializers pour l'app Orders.
"""
from rest_framework import serializers
from .models import Order, SellerWallet, WalletTransaction, WithdrawalRequest


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des commandes."""
    
    buyer_username = serializers.CharField(source='buyer.username', read_only=True)
    buyer_email = serializers.CharField(source='buyer.email', read_only=True)
    seller_username = serializers.CharField(source='seller.username', read_only=True)
    seller_email = serializers.CharField(source='seller.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    delivery_type_display = serializers.CharField(source='get_delivery_type_display', read_only=True)
    listing_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'listing_title', 'listing_image',
            'buyer_username', 'buyer_email',
            'seller_username', 'seller_email',
            'item_price', 'platform_fee', 'seller_amount',
            'status', 'status_display',
            'delivery_type', 'delivery_type_display',
            'tracking_number', 'carrier',
            'created_at', 'shipped_at', 'delivered_at', 'completed_at',
        ]
    
    def get_listing_image(self, obj):
        if obj.listing and obj.listing.images.exists():
            first_image = obj.listing.images.first()
            if first_image and first_image.image:
                return first_image.image.url
        # Essayer de récupérer depuis le snapshot
        if obj.listing_snapshot and obj.listing_snapshot.get('image'):
            return obj.listing_snapshot['image']
        return None


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une commande."""
    
    buyer = serializers.SerializerMethodField()
    seller = serializers.SerializerMethodField()
    listing = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    delivery_type_display = serializers.CharField(source='get_delivery_type_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number',
            'buyer', 'seller', 'listing',
            'listing_title', 'listing_snapshot',
            'item_price', 'platform_fee', 'platform_fee_percent', 'seller_amount',
            'status', 'status_display',
            'delivery_type', 'delivery_type_display',
            'shipping_address', 'tracking_number', 'tracking_url', 'carrier',
            'seller_notes', 'buyer_notes',
            'buyer_confirmed_receipt', 'funds_released',
            'created_at', 'updated_at', 'confirmed_at',
            'shipped_at', 'delivered_at', 'completed_at', 'cancelled_at',
        ]
    
    def get_buyer(self, obj):
        return {
            'id': str(obj.buyer.id),
            'username': obj.buyer.username,
            'email': obj.buyer.email,
            'avatar': obj.buyer.avatar.url if obj.buyer.avatar else None,
        }
    
    def get_seller(self, obj):
        return {
            'id': str(obj.seller.id),
            'username': obj.seller.username,
            'email': obj.seller.email,
            'avatar': obj.seller.avatar.url if obj.seller.avatar else None,
        }
    
    def get_listing(self, obj):
        if obj.listing:
            return {
                'id': str(obj.listing.id),
                'slug': obj.listing.slug,
                'title': obj.listing.title,
                'image': obj.listing.images.first().image.url if obj.listing.images.exists() else None,
            }
        return obj.listing_snapshot


class OrderShipSerializer(serializers.Serializer):
    """Serializer pour marquer une commande comme expédiée."""
    
    tracking_number = serializers.CharField(required=False, allow_blank=True, max_length=100)
    carrier = serializers.CharField(required=False, allow_blank=True, max_length=50)
    tracking_url = serializers.URLField(required=False, allow_blank=True)
    seller_notes = serializers.CharField(required=False, allow_blank=True, max_length=500)


class SellerWalletSerializer(serializers.ModelSerializer):
    """Serializer pour le wallet vendeur."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    pending_orders_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SellerWallet
        fields = [
            'id', 'user_email', 'user_username',
            'balance', 'pending_balance', 'total_earned', 'total_withdrawn',
            'bank_name', 'iban', 'bic', 'account_holder',
            'pending_orders_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'balance', 'pending_balance', 'total_earned', 'total_withdrawn']
    
    def get_pending_orders_count(self, obj):
        return Order.objects.filter(
            seller=obj.user,
            status__in=['pending', 'confirmed', 'processing', 'shipped']
        ).count()


class WalletBankDetailsSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour les infos bancaires."""
    
    class Meta:
        model = SellerWallet
        fields = ['bank_name', 'iban', 'bic', 'account_holder']


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer pour les transactions wallet."""
    
    type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'transaction_type', 'type_display',
            'amount', 'balance_after', 'description',
            'order_number', 'created_at',
        ]


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    """Serializer pour les demandes de retrait."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_email = serializers.CharField(source='wallet.user.email', read_only=True)
    
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'user_email', 'amount',
            'status', 'status_display',
            'bank_details', 'user_notes', 'rejection_reason',
            'transfer_reference',
            'created_at', 'processed_at', 'completed_at',
        ]
        read_only_fields = [
            'id', 'status', 'bank_details', 'rejection_reason',
            'transfer_reference', 'processed_at', 'completed_at'
        ]


class CreateWithdrawalSerializer(serializers.Serializer):
    """Serializer pour créer une demande de retrait."""
    
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=10)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate_amount(self, value):
        user = self.context['request'].user
        try:
            wallet = user.wallet
        except SellerWallet.DoesNotExist:
            raise serializers.ValidationError("Vous n'avez pas de portefeuille")
        
        if value > wallet.balance:
            raise serializers.ValidationError(
                f"Solde insuffisant. Disponible: {wallet.balance}€"
            )
        return value
    
    def validate(self, data):
        user = self.context['request'].user
        
        # Vérifier les infos bancaires
        try:
            wallet = user.wallet
            if not wallet.iban:
                raise serializers.ValidationError({
                    'bank': "Veuillez d'abord ajouter vos coordonnées bancaires"
                })
        except SellerWallet.DoesNotExist:
            raise serializers.ValidationError("Portefeuille non trouvé")
        
        # Vérifier pas de demande en attente
        if WithdrawalRequest.objects.filter(wallet=wallet, status='pending').exists():
            raise serializers.ValidationError(
                "Vous avez déjà une demande de retrait en attente"
            )
        
        return data


class OrderStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques vendeur."""
    
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    wallet_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
