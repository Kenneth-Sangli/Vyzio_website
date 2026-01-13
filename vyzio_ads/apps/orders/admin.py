"""
Configuration admin pour l'app Orders.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Order, SellerWallet, WalletTransaction, WithdrawalRequest


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'listing_title', 'buyer_email', 'seller_email',
        'item_price', 'seller_amount', 'status_badge', 'created_at'
    ]
    list_filter = ['status', 'delivery_type', 'created_at', 'funds_released']
    search_fields = ['order_number', 'listing_title', 'buyer__email', 'seller__email']
    readonly_fields = [
        'id', 'order_number', 'buyer', 'seller', 'listing', 
        'payment', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'order_number', 'status', 'delivery_type')
        }),
        ('Parties', {
            'fields': ('buyer', 'seller', 'listing')
        }),
        ('Article', {
            'fields': ('listing_title', 'listing_snapshot')
        }),
        ('Montants', {
            'fields': ('item_price', 'platform_fee', 'platform_fee_percent', 'seller_amount')
        }),
        ('Livraison', {
            'fields': ('shipping_address', 'tracking_number', 'carrier', 'tracking_url')
        }),
        ('Notes', {
            'fields': ('seller_notes', 'buyer_notes', 'internal_notes')
        }),
        ('Dates', {
            'fields': (
                'created_at', 'confirmed_at', 'shipped_at', 
                'delivered_at', 'completed_at', 'cancelled_at'
            )
        }),
        ('Flags', {
            'fields': ('seller_notified', 'buyer_confirmed_receipt', 'funds_released')
        }),
    )
    
    def buyer_email(self, obj):
        return obj.buyer.email
    buyer_email.short_description = 'Acheteur'
    
    def seller_email(self, obj):
        return obj.seller.email
    seller_email.short_description = 'Vendeur'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'confirmed': '#17a2b8',
            'processing': '#17a2b8',
            'shipped': '#6f42c1',
            'delivered': '#20c997',
            'completed': '#28a745',
            'cancelled': '#dc3545',
            'refunded': '#fd7e14',
            'disputed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'


@admin.register(SellerWallet)
class SellerWalletAdmin(admin.ModelAdmin):
    list_display = [
        'user_email', 'balance', 'pending_balance', 
        'total_earned', 'total_withdrawn', 'has_bank_info'
    ]
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['id', 'balance', 'pending_balance', 'total_earned', 'total_withdrawn']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('id', 'user')
        }),
        ('Soldes', {
            'fields': ('balance', 'pending_balance', 'total_earned', 'total_withdrawn')
        }),
        ('Informations bancaires', {
            'fields': ('bank_name', 'account_holder', 'iban', 'bic')
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Utilisateur'
    
    def has_bank_info(self, obj):
        return bool(obj.iban)
    has_bank_info.boolean = True
    has_bank_info.short_description = 'IBAN renseigné'


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'user_email', 'transaction_type', 'amount', 
        'balance_after', 'description', 'created_at'
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['wallet__user__email', 'description']
    readonly_fields = [
        'id', 'wallet', 'transaction_type', 'amount', 
        'balance_after', 'order', 'withdrawal', 'created_at'
    ]
    ordering = ['-created_at']
    
    def user_email(self, obj):
        return obj.wallet.user.email
    user_email.short_description = 'Utilisateur'


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = [
        'user_email', 'amount', 'status_badge', 
        'created_at', 'processed_at', 'processed_by'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['wallet__user__email']
    readonly_fields = ['id', 'wallet', 'created_at', 'updated_at']
    ordering = ['-created_at']
    actions = ['approve_withdrawals', 'reject_withdrawals']
    
    fieldsets = (
        ('Demande', {
            'fields': ('id', 'wallet', 'amount', 'status')
        }),
        ('Informations bancaires', {
            'fields': ('bank_details',)
        }),
        ('Notes', {
            'fields': ('user_notes', 'admin_notes', 'rejection_reason')
        }),
        ('Traitement', {
            'fields': ('transfer_reference', 'processed_by', 'processed_at', 'completed_at')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def user_email(self, obj):
        return obj.wallet.user.email
    user_email.short_description = 'Utilisateur'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'processing': '#17a2b8',
            'completed': '#28a745',
            'rejected': '#dc3545',
            'cancelled': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def approve_withdrawals(self, request, queryset):
        """Action pour approuver les demandes sélectionnées."""
        approved = 0
        for withdrawal in queryset.filter(status='pending'):
            try:
                withdrawal.approve(admin_user=request.user)
                approved += 1
            except Exception as e:
                self.message_user(request, f"Erreur pour {withdrawal}: {e}", level='error')
        
        self.message_user(request, f"{approved} demande(s) approuvée(s)")
    approve_withdrawals.short_description = "Approuver les demandes sélectionnées"
    
    def reject_withdrawals(self, request, queryset):
        """Action pour rejeter les demandes sélectionnées."""
        rejected = 0
        for withdrawal in queryset.filter(status='pending'):
            try:
                withdrawal.reject(admin_user=request.user, reason="Rejeté par l'administrateur")
                rejected += 1
            except Exception as e:
                self.message_user(request, f"Erreur pour {withdrawal}: {e}", level='error')
        
        self.message_user(request, f"{rejected} demande(s) rejetée(s)")
    reject_withdrawals.short_description = "Rejeter les demandes sélectionnées"
