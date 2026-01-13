"""
URLs pour l'app Orders.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BuyerOrderViewSet, SellerOrderViewSet, 
    WalletViewSet, WithdrawalViewSet,
    OrderSummaryView
)

router = DefaultRouter()

urlpatterns = [
    # Résumé global
    path('summary/', OrderSummaryView.as_view(), name='orders-summary'),
    
    # Achats (côté acheteur)
    path('my-purchases/', BuyerOrderViewSet.as_view({
        'get': 'list'
    }), name='buyer-orders-list'),
    path('my-purchases/<uuid:pk>/', BuyerOrderViewSet.as_view({
        'get': 'retrieve'
    }), name='buyer-order-detail'),
    path('my-purchases/<uuid:pk>/confirm-receipt/', BuyerOrderViewSet.as_view({
        'post': 'confirm_receipt'
    }), name='buyer-confirm-receipt'),
    
    # Ventes (côté vendeur)
    path('my-sales/', SellerOrderViewSet.as_view({
        'get': 'list'
    }), name='seller-orders-list'),
    path('my-sales/stats/', SellerOrderViewSet.as_view({
        'get': 'stats'
    }), name='seller-stats'),
    path('my-sales/<uuid:pk>/', SellerOrderViewSet.as_view({
        'get': 'retrieve'
    }), name='seller-order-detail'),
    path('my-sales/<uuid:pk>/ship/', SellerOrderViewSet.as_view({
        'post': 'ship'
    }), name='seller-ship-order'),
    path('my-sales/<uuid:pk>/mark-delivered/', SellerOrderViewSet.as_view({
        'post': 'mark_delivered'
    }), name='seller-mark-delivered'),
    
    # Wallet
    path('wallet/', WalletViewSet.as_view({
        'get': 'me'
    }), name='wallet-detail'),
    path('wallet/bank-details/', WalletViewSet.as_view({
        'patch': 'bank_details'
    }), name='wallet-bank-details'),
    path('wallet/transactions/', WalletViewSet.as_view({
        'get': 'transactions'
    }), name='wallet-transactions'),
    
    # Retraits
    path('withdrawals/', WithdrawalViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='withdrawals-list'),
    path('withdrawals/<uuid:pk>/', WithdrawalViewSet.as_view({
        'get': 'retrieve',
        'delete': 'destroy'
    }), name='withdrawal-detail'),
    
    # Router
    path('', include(router.urls)),
]
