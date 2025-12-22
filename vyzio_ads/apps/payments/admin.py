from django.contrib import admin
from .models import (
    Payment, SubscriptionPlan, Subscription, Invoice, Coupon,
    PostCreditPack, PostCredit, PostCreditTransaction
)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_type', 'status', 'created_at')
    list_filter = ('payment_type', 'status', 'created_at')

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'billing_cycle', 'price', 'is_active')
    list_filter = ('plan_type', 'billing_cycle', 'is_active')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'started_at', 'ends_at')
    list_filter = ('status', 'plan__plan_type')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'user', 'amount', 'issued_at', 'paid_at')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'is_active')

@admin.register(PostCreditPack)
class PostCreditPackAdmin(admin.ModelAdmin):
    list_display = ('name', 'credits', 'bonus_credits', 'price', 'is_active', 'is_popular', 'sort_order')
    list_filter = ('is_active', 'is_popular')
    list_editable = ('sort_order', 'is_active', 'is_popular')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(PostCredit)
class PostCreditAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'total_purchased', 'total_used', 'updated_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('total_purchased', 'total_used')

@admin.register(PostCreditTransaction)
class PostCreditTransactionAdmin(admin.ModelAdmin):
    list_display = ('post_credit', 'transaction_type', 'amount', 'balance_after', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    readonly_fields = ('post_credit', 'transaction_type', 'amount', 'balance_after', 'description', 'created_at')
