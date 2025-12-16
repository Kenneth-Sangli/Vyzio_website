"""
URLs pour le module de paiements.
Phase 6 - Paiements : abonnements + pay-per-post
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # ViewSets
    PaymentViewSet, SubscriptionPlanViewSet, PostCreditPackViewSet,
    # Checkout Sessions
    CreateSubscriptionCheckoutView, CreatePostCreditCheckoutView,
    CreateSinglePostCheckoutView, CreatePurchaseCheckoutView,
    # Webhook
    StripeWebhookView,
    # Dev
    DevConfirmPaymentView,
    # User data
    MySubscriptionView, MyCreditsView, CreditTransactionsView,
    PaymentHistoryView, InvoiceListView,
    # Subscription Management
    CancelSubscriptionView, BillingPortalView,
    # Coupons
    ValidateCouponView,
)

app_name = 'payments'

router = DefaultRouter()
router.register(r'plans', SubscriptionPlanViewSet, basename='plans')
router.register(r'credit-packs', PostCreditPackViewSet, basename='credit-packs')
router.register(r'payments', PaymentViewSet, basename='payments')

urlpatterns = [
    # Router
    path('', include(router.urls)),
    
    # Checkout Sessions
    path('create-subscription-session/', CreateSubscriptionCheckoutView.as_view(), name='create-subscription-session'),
    path('create-post-session/', CreatePostCreditCheckoutView.as_view(), name='create-post-session'),
    path('create-single-post-session/', CreateSinglePostCheckoutView.as_view(), name='create-single-post-session'),
    path('create-purchase-session/', CreatePurchaseCheckoutView.as_view(), name='create-purchase-session'),
    
    # Webhook Stripe
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    
    # Dev: Simulate payment confirmation (DEBUG only)
    path('dev-confirm/', DevConfirmPaymentView.as_view(), name='dev-confirm-payment'),
    
    # User Subscription & Credits
    path('my-subscription/', MySubscriptionView.as_view(), name='my-subscription'),
    path('my-credits/', MyCreditsView.as_view(), name='my-credits'),
    path('credit-transactions/', CreditTransactionsView.as_view(), name='credit-transactions'),
    path('history/', PaymentHistoryView.as_view(), name='payment-history'),
    path('invoices/', InvoiceListView.as_view(), name='invoices'),
    
    # Subscription Management
    path('cancel-subscription/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('billing-portal/', BillingPortalView.as_view(), name='billing-portal'),
    
    # Coupons
    path('validate-coupon/', ValidateCouponView.as_view(), name='validate-coupon'),
]
