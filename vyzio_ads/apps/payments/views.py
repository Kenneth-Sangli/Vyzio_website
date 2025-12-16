"""
Vues pour le module de paiements.
Phase 6 - Paiements : abonnements + pay-per-post

Endpoints:
- POST /api/payments/create-subscription-session/
- POST /api/payments/create-post-session/
- POST /api/payments/webhook/
- GET /api/payments/plans/
- GET /api/payments/credit-packs/
- GET /api/payments/my-subscription/
- GET /api/payments/my-credits/
- GET /api/payments/history/
- POST /api/payments/cancel-subscription/
- POST /api/payments/billing-portal/
"""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.conf import settings
import logging

from .models import (
    Payment, SubscriptionPlan, Subscription, Invoice, Coupon,
    PostCreditPack, PostCredit, PostCreditTransaction
)
from .serializers import (
    PaymentSerializer, SubscriptionPlanSerializer, SubscriptionSerializer,
    InvoiceSerializer, CouponSerializer, CouponValidateSerializer,
    PostCreditPackSerializer, PostCreditSerializer, PostCreditTransactionSerializer,
    CreateSubscriptionCheckoutSerializer, CreatePostCreditCheckoutSerializer,
    CreateSinglePostCheckoutSerializer, CheckoutResponseSerializer, BillingPortalSerializer
)
from .services import StripeService, WebhookHandler

logger = logging.getLogger(__name__)


# ==================== Plans & Packs ====================

class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Liste des plans d'abonnement disponibles.
    
    GET /api/payments/plans/
    GET /api/payments/plans/{id}/
    """
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]  # Public pour afficher les prix


class PostCreditPackViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Liste des packs de crédits disponibles.
    
    GET /api/payments/credit-packs/
    GET /api/payments/credit-packs/{id}/
    """
    queryset = PostCreditPack.objects.filter(is_active=True)
    serializer_class = PostCreditPackSerializer
    permission_classes = [AllowAny]


# ==================== Checkout Sessions ====================

class CreateSubscriptionCheckoutView(APIView):
    """
    Crée une session Stripe Checkout pour un abonnement.
    
    POST /api/payments/create-subscription-session/
    
    Body:
    {
        "plan_id": 1,
        "coupon_code": "PROMO20"  // optionnel
    }
    
    Response:
    {
        "checkout_url": "https://checkout.stripe.com/...",
        "session_id": "cs_..."
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CreateSubscriptionCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        plan_id = serializer.validated_data['plan_id']
        coupon_code = serializer.validated_data.get('coupon_code')
        success_url = serializer.validated_data.get('success_url')
        cancel_url = serializer.validated_data.get('cancel_url')
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {'error': 'Plan non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier si l'utilisateur a déjà un abonnement actif
        if hasattr(request.user, 'subscription') and request.user.subscription.is_active:
            return Response(
                {'error': 'Vous avez déjà un abonnement actif. Annulez-le d\'abord.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            stripe_service = StripeService()
            result = stripe_service.create_subscription_checkout_session(
                user=request.user,
                plan=plan,
                coupon_code=coupon_code,
                success_url=success_url,
                cancel_url=cancel_url,
            )
            
            response_serializer = CheckoutResponseSerializer(data=result)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur création checkout subscription: {e}")
            return Response(
                {'error': 'Erreur lors de la création de la session de paiement'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreatePostCreditCheckoutView(APIView):
    """
    Crée une session Stripe Checkout pour acheter des crédits.
    
    POST /api/payments/create-post-session/
    
    Body:
    {
        "pack_id": 1,
        "coupon_code": "PROMO10"  // optionnel
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CreatePostCreditCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        pack_id = serializer.validated_data['pack_id']
        coupon_code = serializer.validated_data.get('coupon_code')
        success_url = serializer.validated_data.get('success_url')
        cancel_url = serializer.validated_data.get('cancel_url')
        
        try:
            pack = PostCreditPack.objects.get(id=pack_id, is_active=True)
        except PostCreditPack.DoesNotExist:
            return Response(
                {'error': 'Pack non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            stripe_service = StripeService()
            result = stripe_service.create_post_credit_checkout_session(
                user=request.user,
                credit_pack=pack,
                coupon_code=coupon_code,
                success_url=success_url,
                cancel_url=cancel_url,
            )
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur création checkout crédits: {e}")
            return Response(
                {'error': 'Erreur lors de la création de la session de paiement'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreateSinglePostCheckoutView(APIView):
    """
    Crée une session pour payer une annonce unique.
    
    POST /api/payments/create-single-post-session/
    
    Body:
    {
        "listing_id": "uuid..."
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from apps.listings.models import Listing
        from decimal import Decimal
        
        serializer = CreateSinglePostCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        listing_id = serializer.validated_data['listing_id']
        
        try:
            listing = Listing.objects.get(id=listing_id, seller=request.user)
        except Listing.DoesNotExist:
            return Response(
                {'error': 'Annonce non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Prix par défaut pour une annonce
        price = Decimal('2.99')
        
        try:
            stripe_service = StripeService()
            result = stripe_service.create_single_post_checkout_session(
                user=request.user,
                listing=listing,
                price=price,
                success_url=serializer.validated_data.get('success_url'),
                cancel_url=serializer.validated_data.get('cancel_url'),
            )
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur création checkout single post: {e}")
            return Response(
                {'error': 'Erreur lors de la création de la session de paiement'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreatePurchaseCheckoutView(APIView):
    """
    Crée une session Stripe pour acheter un article.
    
    POST /api/payments/create-purchase-session/
    
    Body:
    {
        "listing_id": "uuid...",
        "success_url": "http://...",  // optionnel
        "cancel_url": "http://..."   // optionnel
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from apps.listings.models import Listing
        
        listing_id = request.data.get('listing_id')
        if not listing_id:
            return Response(
                {'error': 'listing_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            listing = Listing.objects.get(id=listing_id, status='published')
        except Listing.DoesNotExist:
            return Response(
                {'error': 'Annonce non trouvée ou non disponible'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier que l'acheteur n'est pas le vendeur
        if listing.seller == request.user:
            return Response(
                {'error': 'Vous ne pouvez pas acheter votre propre annonce'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            stripe_service = StripeService()
            result = stripe_service.create_purchase_checkout_session(
                buyer=request.user,
                listing=listing,
                success_url=request.data.get('success_url'),
                cancel_url=request.data.get('cancel_url'),
            )
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur création checkout achat: {e}")
            return Response(
                {'error': 'Erreur lors de la création de la session de paiement'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==================== Webhook ====================

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    Endpoint pour les webhooks Stripe.
    
    POST /api/payments/webhook/
    
    SÉCURITÉ:
    - Vérification de signature obligatoire
    - Pas d'authentification JWT (Stripe ne peut pas)
    - Idempotence via WebhookEvent
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Pas d'auth pour les webhooks
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        
        # Vérifier la signature
        stripe_service = StripeService()
        is_valid, event = stripe_service.verify_webhook_signature(payload, sig_header)
        
        if not is_valid:
            logger.warning("Webhook Stripe avec signature invalide")
            return HttpResponse(status=400)
        
        # Traiter l'événement
        webhook_handler = WebhookHandler()
        success = webhook_handler.process_event(event)
        
        if success:
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=500)


# ==================== Dev: Simulate Payment Confirmation ====================

class DevConfirmPaymentView(APIView):
    """
    [DEV ONLY] Simule la confirmation d'un paiement Stripe.
    Utilisé pour tester sans webhooks en local.
    
    POST /api/payments/dev-confirm/
    
    Body:
    {
        "session_id": "cs_test_..."
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Vérifier qu'on est en mode développement
        if not settings.DEBUG:
            return Response(
                {'error': 'Cette fonctionnalité n\'est disponible qu\'en développement'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        session_id = request.data.get('session_id')
        if not session_id:
            return Response(
                {'error': 'session_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Trouver le paiement
        try:
            payment = Payment.objects.get(
                stripe_checkout_session_id=session_id,
                user=request.user,
                status='pending'
            )
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Paiement non trouvé ou déjà traité'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from django.utils import timezone
        from datetime import timedelta
        
        # Marquer le paiement comme complété
        payment.status = 'completed'
        payment.completed_at = timezone.now()
        payment.save()
        
        result = {'payment_id': payment.id, 'status': 'completed'}
        
        # Traiter selon le type
        if payment.payment_type == 'post_credit':
            # Ajouter les crédits
            credits_to_add = payment.metadata.get('credits', 0)
            if credits_to_add:
                post_credit, created = PostCredit.objects.get_or_create(
                    user=request.user,
                    defaults={'balance': 0}
                )
                post_credit.balance += credits_to_add
                post_credit.save()
                
                # Créer la transaction
                PostCreditTransaction.objects.create(
                    post_credit=post_credit,
                    transaction_type='purchase',
                    amount=credits_to_add,
                    balance_after=post_credit.balance,
                    payment=payment,
                    description=f'Achat de {credits_to_add} crédits (dev)'
                )
                
                result['credits_added'] = credits_to_add
                result['new_balance'] = post_credit.balance
                logger.info(f"[DEV] Crédits ajoutés: {credits_to_add} pour {request.user.email}")
        
        elif payment.payment_type == 'subscription':
            # Activer l'abonnement
            # Le plan est stocké dans payment.subscription_plan
            plan = payment.subscription_plan
            if plan:
                try:
                    # Créer ou mettre à jour l'abonnement
                    subscription, created = Subscription.objects.update_or_create(
                        user=request.user,
                        defaults={
                            'plan': plan,
                            'status': 'active',
                            'current_period_start': timezone.now(),
                            'current_period_end': timezone.now() + timedelta(days=30 if plan.billing_cycle == 'monthly' else 365),
                            'stripe_subscription_id': f'sub_dev_{payment.id}',
                        }
                    )
                    
                    result['subscription_activated'] = True
                    result['plan'] = plan.name
                    logger.info(f"[DEV] Abonnement activé: {plan.name} pour {request.user.email}")
                    
                except Exception as e:
                    result['subscription_error'] = str(e)
            else:
                result['subscription_error'] = 'Plan non trouvé dans le paiement'
        
        elif payment.payment_type == 'purchase':
            # Achat d'un article
            listing_id = payment.metadata.get('listing_id')
            seller_id = payment.metadata.get('seller_id')
            listing_title = payment.metadata.get('listing_title', 'Article')
            
            result['purchase_confirmed'] = True
            result['listing_title'] = listing_title
            
            # Optionnel: marquer l'annonce comme vendue
            if listing_id:
                try:
                    from apps.listings.models import Listing
                    listing = Listing.objects.get(id=listing_id)
                    listing.status = 'sold'
                    listing.save(update_fields=['status'])
                    result['listing_status'] = 'sold'
                    logger.info(f"[DEV] Achat confirmé: {listing_title} par {request.user.email}")
                    
                    # Créer les notifications pour l'acheteur et le vendeur
                    try:
                        from apps.messaging.models import Notification
                        
                        # Notification pour l'acheteur
                        Notification.create_purchase_notification_for_buyer(
                            buyer=request.user,
                            listing=listing,
                            seller=listing.seller
                        )
                        
                        # Notification pour le vendeur
                        Notification.create_sale_notification_for_seller(
                            seller=listing.seller,
                            listing=listing,
                            buyer=request.user
                        )
                        
                        logger.info(f"[DEV] Notifications créées pour achat {listing.title}")
                    except Exception as e:
                        logger.error(f"[DEV] Erreur création notifications: {e}")
                    
                except Exception as e:
                    logger.error(f"[DEV] Erreur mise à jour annonce: {e}")
            
            # Optionnel: créer une conversation automatique entre acheteur et vendeur
            if seller_id:
                try:
                    from apps.messaging.models import Conversation
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    
                    seller = User.objects.get(id=seller_id)
                    
                    # Créer ou récupérer la conversation
                    conversation, created = Conversation.objects.get_or_create(
                        buyer=request.user,
                        seller=seller,
                        listing_id=listing_id,
                        defaults={'is_active': True}
                    )
                    result['conversation_id'] = str(conversation.id)
                except Exception as e:
                    logger.error(f"[DEV] Erreur création conversation: {e}")
        
        return Response(result, status=status.HTTP_200_OK)


# ==================== User Subscription & Credits ====================

class MySubscriptionView(APIView):
    """
    Récupère l'abonnement de l'utilisateur connecté.
    
    GET /api/payments/my-subscription/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            subscription = request.user.subscription
            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data)
        except Subscription.DoesNotExist:
            return Response(
                {'detail': 'Aucun abonnement actif'},
                status=status.HTTP_404_NOT_FOUND
            )


class MyCreditsView(APIView):
    """
    Récupère le solde de crédits de l'utilisateur.
    
    GET /api/payments/my-credits/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        post_credit, created = PostCredit.objects.get_or_create(user=request.user)
        serializer = PostCreditSerializer(post_credit)
        return Response(serializer.data)


class CreditTransactionsView(generics.ListAPIView):
    """
    Historique des transactions de crédits.
    
    GET /api/payments/credit-transactions/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PostCreditTransactionSerializer
    
    def get_queryset(self):
        try:
            return PostCreditTransaction.objects.filter(
                post_credit__user=self.request.user
            )
        except PostCredit.DoesNotExist:
            return PostCreditTransaction.objects.none()


class PaymentHistoryView(generics.ListAPIView):
    """
    Historique des paiements de l'utilisateur.
    
    GET /api/payments/history/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


class InvoiceListView(generics.ListAPIView):
    """
    Liste des factures de l'utilisateur.
    
    GET /api/payments/invoices/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer
    
    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user)


# ==================== Subscription Management ====================

class CancelSubscriptionView(APIView):
    """
    Annule l'abonnement de l'utilisateur.
    
    POST /api/payments/cancel-subscription/
    
    Body:
    {
        "immediate": false  // true pour annuler immédiatement
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        immediate = request.data.get('immediate', False)
        
        try:
            subscription = request.user.subscription
        except Subscription.DoesNotExist:
            return Response(
                {'error': 'Aucun abonnement à annuler'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if subscription.status == 'cancelled':
            return Response(
                {'error': 'Abonnement déjà annulé'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        stripe_service = StripeService()
        success = stripe_service.cancel_subscription(request.user, immediate=immediate)
        
        if success:
            # Rafraîchir l'abonnement
            subscription.refresh_from_db()
            serializer = SubscriptionSerializer(subscription)
            return Response({
                'message': 'Abonnement annulé' if immediate else 'Abonnement annulé à la fin de la période',
                'subscription': serializer.data
            })
        else:
            return Response(
                {'error': 'Erreur lors de l\'annulation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BillingPortalView(APIView):
    """
    Redirige vers le portail de facturation Stripe.
    
    POST /api/payments/billing-portal/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            stripe_service = StripeService()
            result = stripe_service.create_billing_portal_session(request.user)
            return Response(result)
        except Exception as e:
            logger.error(f"Erreur création portal session: {e}")
            return Response(
                {'error': 'Erreur lors de la création de la session'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==================== Coupon Validation ====================

class ValidateCouponView(APIView):
    """
    Valide un code promo.
    
    POST /api/payments/validate-coupon/
    
    Body:
    {
        "code": "PROMO20",
        "payment_type": "subscription"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CouponValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        payment_type = serializer.validated_data['payment_type']
        
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response(
                {'valid': False, 'error': 'Code promo invalide'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier la validité
        if not coupon.is_valid():
            return Response(
                {'valid': False, 'error': 'Code promo expiré ou épuisé'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier l'applicabilité
        if payment_type == 'subscription' and not coupon.applies_to_subscription:
            return Response(
                {'valid': False, 'error': 'Ce code ne s\'applique pas aux abonnements'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if payment_type == 'post_credit' and not coupon.applies_to_post_credit:
            return Response(
                {'valid': False, 'error': 'Ce code ne s\'applique pas aux crédits'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Coupon valide
        coupon_serializer = CouponSerializer(coupon)
        return Response({
            'valid': True,
            'coupon': coupon_serializer.data
        })


# ==================== Legacy ViewSet (backward compatibility) ====================

class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet legacy pour compatibilité.
    Utilisez les nouvelles vues spécifiques.
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def create_checkout_session(self, request):
        """Deprecated: utiliser /create-subscription-session/"""
        plan_id = request.data.get('plan_id')
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
        
        stripe_service = StripeService()
        result = stripe_service.create_subscription_checkout_session(
            user=request.user,
            plan=plan,
            coupon_code=request.data.get('coupon_code'),
        )
        
        return Response(result)
