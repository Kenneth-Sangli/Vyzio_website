from django.contrib import admin
from .models import Payment, SubscriptionPlan, Subscription, Invoice, Coupon

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
