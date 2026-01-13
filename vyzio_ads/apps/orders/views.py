"""
Views pour l'app Orders.
API pour gérer les commandes, wallet et retraits.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Sum, Count, Q
from django.shortcuts import get_object_or_404
from decimal import Decimal
import logging

from .models import Order, SellerWallet, WalletTransaction, WithdrawalRequest
from .serializers import (
    OrderListSerializer, OrderDetailSerializer, OrderShipSerializer,
    SellerWalletSerializer, WalletBankDetailsSerializer,
    WalletTransactionSerializer, WithdrawalRequestSerializer,
    CreateWithdrawalSerializer, OrderStatsSerializer
)

logger = logging.getLogger(__name__)


class BuyerOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API pour les commandes côté acheteur.
    
    GET /api/orders/my-purchases/ - Liste des achats
    GET /api/orders/my-purchases/{id}/ - Détail d'un achat
    POST /api/orders/my-purchases/{id}/confirm_receipt/ - Confirmer réception
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderListSerializer
    
    def get_queryset(self):
        return Order.objects.filter(
            buyer=self.request.user
        ).select_related('buyer', 'seller', 'listing')
    
    @action(detail=True, methods=['post'])
    def confirm_receipt(self, request, pk=None):
        """L'acheteur confirme avoir reçu la commande."""
        order = self.get_object()
        
        if order.status not in ['shipped', 'delivered']:
            return Response(
                {'error': "La commande doit être expédiée ou livrée pour confirmer la réception"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if order.buyer_confirmed_receipt:
            return Response(
                {'error': "Réception déjà confirmée"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.confirm_receipt()
        
        # Créer notification pour le vendeur
        try:
            from apps.messaging.models import Notification
            Notification.objects.create(
                user=order.seller,
                type='sale',
                title='Réception confirmée ! 💰',
                message=f'{order.buyer.username} a confirmé la réception de "{order.listing_title}". Les fonds ont été ajoutés à votre portefeuille.',
                data={
                    'order_id': str(order.id),
                    'order_number': order.order_number,
                    'amount': str(order.seller_amount),
                }
            )
        except Exception as e:
            logger.error(f"Erreur création notification: {e}")
        
        return Response({
            'message': 'Réception confirmée avec succès',
            'order': OrderDetailSerializer(order).data
        })
    
    @action(detail=True, methods=['post'])
    def add_review(self, request, pk=None):
        """Ajoute un avis après achat."""
        order = self.get_object()
        
        if order.status != 'completed':
            return Response(
                {'error': "La commande doit être terminée pour laisser un avis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Déléguer à l'API reviews
        return Response({
            'redirect': f'/api/reviews/create/',
            'data': {
                'listing_id': str(order.listing.id) if order.listing else None,
                'seller_id': str(order.seller.id),
            }
        })


class SellerOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API pour les commandes côté vendeur.
    
    GET /api/orders/my-sales/ - Liste des ventes
    GET /api/orders/my-sales/{id}/ - Détail d'une vente
    POST /api/orders/my-sales/{id}/ship/ - Marquer comme expédié
    POST /api/orders/my-sales/{id}/mark_delivered/ - Marquer comme livré
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderListSerializer
    
    def get_queryset(self):
        return Order.objects.filter(
            seller=self.request.user
        ).select_related('buyer', 'seller', 'listing')
    
    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        """Marque la commande comme expédiée."""
        order = self.get_object()
        
        if order.status not in ['pending', 'confirmed', 'processing']:
            return Response(
                {'error': f"Impossible d'expédier une commande au statut '{order.get_status_display()}'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = OrderShipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Mettre à jour les notes vendeur si fournies
        if serializer.validated_data.get('seller_notes'):
            order.seller_notes = serializer.validated_data['seller_notes']
        
        order.mark_shipped(
            tracking_number=serializer.validated_data.get('tracking_number', ''),
            carrier=serializer.validated_data.get('carrier', ''),
            tracking_url=serializer.validated_data.get('tracking_url', ''),
        )
        
        # Notifier l'acheteur
        try:
            from apps.messaging.models import Notification
            message = f'Votre commande "{order.listing_title}" a été expédiée !'
            if order.tracking_number:
                message += f' Numéro de suivi: {order.tracking_number}'
            
            Notification.objects.create(
                user=order.buyer,
                type='purchase',
                title='Commande expédiée ! 📦',
                message=message,
                data={
                    'order_id': str(order.id),
                    'order_number': order.order_number,
                    'tracking_number': order.tracking_number,
                    'carrier': order.carrier,
                }
            )
        except Exception as e:
            logger.error(f"Erreur création notification: {e}")
        
        return Response({
            'message': 'Commande marquée comme expédiée',
            'order': OrderDetailSerializer(order).data
        })
    
    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        """Marque la commande comme livrée."""
        order = self.get_object()
        
        if order.status != 'shipped':
            return Response(
                {'error': "La commande doit être expédiée pour être marquée comme livrée"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.mark_delivered()
        
        # Notifier l'acheteur
        try:
            from apps.messaging.models import Notification
            Notification.objects.create(
                user=order.buyer,
                type='purchase',
                title='Commande livrée ! 🎉',
                message=f'Votre commande "{order.listing_title}" a été livrée. Confirmez la réception pour finaliser la transaction.',
                data={
                    'order_id': str(order.id),
                    'order_number': order.order_number,
                }
            )
        except Exception as e:
            logger.error(f"Erreur création notification: {e}")
        
        return Response({
            'message': 'Commande marquée comme livrée',
            'order': OrderDetailSerializer(order).data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques de vente."""
        orders = self.get_queryset()
        
        # Calculer les stats
        total_sales = orders.filter(status='completed').count()
        total_revenue = orders.filter(status='completed').aggregate(
            total=Sum('seller_amount')
        )['total'] or Decimal('0.00')
        
        pending_orders = orders.filter(
            status__in=['pending', 'confirmed', 'processing', 'shipped']
        ).count()
        
        completed_orders = orders.filter(status='completed').count()
        
        # Wallet
        wallet_balance = Decimal('0.00')
        pending_balance = Decimal('0.00')
        try:
            wallet = request.user.wallet
            wallet_balance = wallet.balance
            pending_balance = wallet.pending_balance
        except SellerWallet.DoesNotExist:
            pass
        
        data = {
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'wallet_balance': wallet_balance,
            'pending_balance': pending_balance,
        }
        
        return Response(OrderStatsSerializer(data).data)


class WalletViewSet(viewsets.GenericViewSet):
    """
    API pour le portefeuille vendeur.
    
    GET /api/orders/wallet/ - Détails du wallet
    PATCH /api/orders/wallet/bank_details/ - Mettre à jour infos bancaires
    GET /api/orders/wallet/transactions/ - Historique des transactions
    """
    permission_classes = [IsAuthenticated]
    
    def get_wallet(self):
        wallet, created = SellerWallet.objects.get_or_create(
            user=self.request.user,
            defaults={'balance': Decimal('0.00')}
        )
        return wallet
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Récupère le wallet de l'utilisateur."""
        wallet = self.get_wallet()
        return Response(SellerWalletSerializer(wallet).data)
    
    @action(detail=False, methods=['patch'], url_path='bank-details')
    def bank_details(self, request):
        """Met à jour les coordonnées bancaires."""
        wallet = self.get_wallet()
        serializer = WalletBankDetailsSerializer(wallet, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'Coordonnées bancaires mises à jour',
            'wallet': SellerWalletSerializer(wallet).data
        })
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Historique des transactions."""
        wallet = self.get_wallet()
        transactions = wallet.transactions.all()[:50]
        return Response(WalletTransactionSerializer(transactions, many=True).data)


class WithdrawalViewSet(viewsets.ModelViewSet):
    """
    API pour les demandes de retrait.
    
    GET /api/orders/withdrawals/ - Liste des demandes
    POST /api/orders/withdrawals/ - Créer une demande
    DELETE /api/orders/withdrawals/{id}/ - Annuler une demande en attente
    """
    permission_classes = [IsAuthenticated]
    serializer_class = WithdrawalRequestSerializer
    
    def get_queryset(self):
        try:
            wallet = self.request.user.wallet
            return WithdrawalRequest.objects.filter(wallet=wallet)
        except SellerWallet.DoesNotExist:
            return WithdrawalRequest.objects.none()
    
    def create(self, request):
        """Crée une nouvelle demande de retrait."""
        serializer = CreateWithdrawalSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        wallet = request.user.wallet
        withdrawal = WithdrawalRequest.create_request(
            wallet=wallet,
            amount=serializer.validated_data['amount'],
            notes=serializer.validated_data.get('notes', '')
        )
        
        # Notifier les admins (optionnel - par email)
        logger.info(f"Nouvelle demande de retrait: {withdrawal.amount}€ de {wallet.user.email}")
        
        return Response(
            WithdrawalRequestSerializer(withdrawal).data,
            status=status.HTTP_201_CREATED
        )
    
    def destroy(self, request, pk=None):
        """Annule une demande en attente."""
        withdrawal = self.get_object()
        
        if withdrawal.status != 'pending':
            return Response(
                {'error': "Seules les demandes en attente peuvent être annulées"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        withdrawal.status = 'cancelled'
        withdrawal.save(update_fields=['status', 'updated_at'])
        
        return Response({'message': 'Demande annulée'})


class OrderSummaryView(APIView):
    """
    Vue pour obtenir un résumé global des commandes.
    
    GET /api/orders/summary/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Achats
        purchases = Order.objects.filter(buyer=user)
        purchases_summary = {
            'total': purchases.count(),
            'pending': purchases.filter(status__in=['pending', 'confirmed', 'processing']).count(),
            'shipped': purchases.filter(status='shipped').count(),
            'delivered': purchases.filter(status='delivered').count(),
            'completed': purchases.filter(status='completed').count(),
        }
        
        # Ventes
        sales = Order.objects.filter(seller=user)
        sales_summary = {
            'total': sales.count(),
            'pending': sales.filter(status__in=['pending', 'confirmed']).count(),
            'to_ship': sales.filter(status='confirmed').count(),
            'shipped': sales.filter(status='shipped').count(),
            'completed': sales.filter(status='completed').count(),
            'revenue': sales.filter(status='completed').aggregate(
                total=Sum('seller_amount')
            )['total'] or Decimal('0.00'),
        }
        
        # Wallet
        wallet_data = None
        try:
            wallet = user.wallet
            wallet_data = {
                'balance': wallet.balance,
                'pending_balance': wallet.pending_balance,
                'total_earned': wallet.total_earned,
            }
        except SellerWallet.DoesNotExist:
            pass
        
        return Response({
            'purchases': purchases_summary,
            'sales': sales_summary,
            'wallet': wallet_data,
        })
