"""
Service Stripe pour la gestion des paiements.
Phase 6 - Paiements : abonnements + pay-per-post

SÉCURITÉ:
- Ne JAMAIS logguer les numéros de carte
- Toujours vérifier les signatures des webhooks
- Utiliser les métadonnées pour le tracking
"""
import stripe
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from typing import Optional, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


def get_stripe():
    """Configure et retourne le module Stripe."""
    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
    return stripe


def is_stripe_configured() -> bool:
    """Vérifie si Stripe est configuré."""
    return bool(getattr(settings, 'STRIPE_SECRET_KEY', ''))


class StripeService:
    """
    Service de gestion des paiements Stripe.
    Gère les abonnements (Option A) et pay-per-post (Option B).
    """
    
    def __init__(self):
        self.stripe = get_stripe()
        self.frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        self.webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
    
    # ==================== Customer Management ====================
    
    def get_or_create_customer(self, user) -> str:
        """
        Récupère ou crée un customer Stripe pour un utilisateur.
        
        Args:
            user: Instance CustomUser
            
        Returns:
            stripe_customer_id
        """
        if not is_stripe_configured():
            return f"cus_test_{user.id}"
        
        # Vérifier si l'utilisateur a déjà un customer ID
        from apps.payments.models import Payment
        existing_customer_id = None
        
        existing = Payment.objects.filter(
            user=user,
            stripe_customer_id__startswith='cus_'
        ).first()
        
        if existing and existing.stripe_customer_id:
            existing_customer_id = existing.stripe_customer_id
        
        # Vérifier dans l'abonnement
        if not existing_customer_id and hasattr(user, 'subscription') and user.subscription.stripe_customer_id:
            existing_customer_id = user.subscription.stripe_customer_id
        
        # Si on a un customer ID existant, vérifier qu'il existe vraiment dans Stripe
        if existing_customer_id:
            try:
                self.stripe.Customer.retrieve(existing_customer_id)
                return existing_customer_id
            except stripe.error.InvalidRequestError:
                # Customer n'existe pas (probablement créé en mode test)
                logger.warning(f"Customer {existing_customer_id} non trouvé dans Stripe, création d'un nouveau")
                existing_customer_id = None
        
        # Créer un nouveau customer
        try:
            customer = self.stripe.Customer.create(
                email=user.email,
                name=user.get_full_name() or user.username,
                metadata={
                    'user_id': str(user.id),
                    'username': user.username,
                }
            )
            logger.info(f"Customer Stripe créé: {customer.id} pour {user.email}")
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Erreur création customer Stripe: {e}")
            raise
    
    # ==================== Subscription (Option A) ====================
    
    def create_subscription_checkout_session(
        self,
        user,
        plan,
        coupon_code: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> Dict:
        """
        Crée une session de checkout pour un abonnement.
        
        Args:
            user: Instance CustomUser
            plan: Instance SubscriptionPlan
            coupon_code: Code promo optionnel
            success_url: URL de redirection après succès
            cancel_url: URL de redirection après annulation
            
        Returns:
            Dict avec checkout_url, session_id
        """
        from apps.payments.models import Payment, Coupon
        
        if not is_stripe_configured():
            # Mode test sans Stripe
            return {
                'checkout_url': f'{self.frontend_url}/payment-mock',
                'session_id': f'cs_test_{user.id}_{plan.id}',
                'is_test': True,
            }
        
        customer_id = self.get_or_create_customer(user)
        
        # Préparer les paramètres
        checkout_params = {
            'customer': customer_id,
            'mode': 'subscription',
            'success_url': success_url or f'{self.frontend_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}',
            'cancel_url': cancel_url or f'{self.frontend_url}/payment-cancel',
            'metadata': {
                'user_id': str(user.id),
                'plan_id': str(plan.id),
                'plan_type': plan.plan_type,
                'payment_type': 'subscription',
            },
            'subscription_data': {
                'metadata': {
                    'user_id': str(user.id),
                    'plan_id': str(plan.id),
                }
            },
            'allow_promotion_codes': True,
        }
        
        # Utiliser le price_id Stripe si disponible
        if plan.stripe_price_id:
            checkout_params['line_items'] = [{
                'price': plan.stripe_price_id,
                'quantity': 1,
            }]
        else:
            # Créer le prix dynamiquement
            checkout_params['line_items'] = [{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': plan.name,
                        'description': plan.description or f'Abonnement {plan.get_plan_type_display()}',
                    },
                    'unit_amount': int(plan.price * 100),
                    'recurring': {
                        'interval': 'month' if plan.billing_cycle == 'monthly' else 'year',
                    },
                },
                'quantity': 1,
            }]
        
        # Appliquer le coupon si fourni
        if coupon_code:
            try:
                coupon = Coupon.objects.get(
                    code=coupon_code,
                    is_active=True,
                    applies_to_subscription=True
                )
                if coupon.is_valid() and coupon.stripe_coupon_id:
                    checkout_params['discounts'] = [{'coupon': coupon.stripe_coupon_id}]
            except Coupon.DoesNotExist:
                pass
        
        try:
            session = self.stripe.checkout.Session.create(**checkout_params)
            
            # Créer le Payment en attente
            Payment.objects.create(
                user=user,
                amount=plan.price,
                payment_type='subscription',
                status='pending',
                stripe_checkout_session_id=session.id,
                stripe_customer_id=customer_id,
                subscription_plan=plan,
                description=f'Abonnement {plan.name}',
                metadata={'coupon_code': coupon_code} if coupon_code else {},
            )
            
            logger.info(f"Session checkout subscription créée: {session.id}")
            
            return {
                'checkout_url': session.url,
                'session_id': session.id,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur création session checkout: {e}")
            raise
    
    def cancel_subscription(self, user, immediate: bool = False) -> bool:
        """
        Annule l'abonnement d'un utilisateur.
        
        Args:
            user: Instance CustomUser
            immediate: Si True, annule immédiatement. Sinon, à la fin de la période.
            
        Returns:
            True si succès
        """
        from apps.payments.models import Subscription
        
        try:
            subscription = user.subscription
        except Subscription.DoesNotExist:
            return False
        
        if not subscription.stripe_subscription_id:
            # Pas de subscription Stripe, juste mettre à jour localement
            subscription.status = 'cancelled'
            subscription.cancelled_at = timezone.now()
            subscription.save()
            return True
        
        if not is_stripe_configured():
            subscription.status = 'cancelled'
            subscription.cancelled_at = timezone.now()
            subscription.save()
            return True
        
        try:
            if immediate:
                self.stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = 'cancelled'
                subscription.cancelled_at = timezone.now()
                subscription.ends_at = timezone.now()
            else:
                self.stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                subscription.cancel_at_period_end = True
                subscription.cancelled_at = timezone.now()
            
            subscription.save()
            logger.info(f"Abonnement annulé pour {user.email}")
            return True
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur annulation abonnement: {e}")
            return False
    
    # ==================== Pay-per-post (Option B) ====================
    
    def create_post_credit_checkout_session(
        self,
        user,
        credit_pack,
        coupon_code: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> Dict:
        """
        Crée une session de checkout pour acheter des crédits d'annonces.
        
        Args:
            user: Instance CustomUser
            credit_pack: Instance PostCreditPack
            coupon_code: Code promo optionnel
            success_url: URL de redirection après succès
            cancel_url: URL de redirection après annulation
            
        Returns:
            Dict avec checkout_url, session_id
        """
        from apps.payments.models import Payment, Coupon
        
        if not is_stripe_configured():
            return {
                'checkout_url': f'{self.frontend_url}/payment-mock',
                'session_id': f'cs_test_{user.id}_credits_{credit_pack.id}',
                'is_test': True,
            }
        
        customer_id = self.get_or_create_customer(user)
        
        checkout_params = {
            'customer': customer_id,
            'mode': 'payment',  # Paiement unique, pas récurrent
            'success_url': success_url or f'{self.frontend_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}',
            'cancel_url': cancel_url or f'{self.frontend_url}/payment-cancel',
            'metadata': {
                'user_id': str(user.id),
                'credit_pack_id': str(credit_pack.id),
                'credits': str(credit_pack.total_credits),
                'payment_type': 'post_credit',
            },
            'allow_promotion_codes': True,
        }
        
        # Utiliser le price_id si disponible
        if credit_pack.stripe_price_id:
            checkout_params['line_items'] = [{
                'price': credit_pack.stripe_price_id,
                'quantity': 1,
            }]
        else:
            checkout_params['line_items'] = [{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': credit_pack.name,
                        'description': f'{credit_pack.total_credits} crédits pour publier des annonces',
                    },
                    'unit_amount': int(credit_pack.price * 100),
                },
                'quantity': 1,
            }]
        
        # Appliquer le coupon
        if coupon_code:
            try:
                coupon = Coupon.objects.get(
                    code=coupon_code,
                    is_active=True,
                    applies_to_post_credit=True
                )
                if coupon.is_valid() and coupon.stripe_coupon_id:
                    checkout_params['discounts'] = [{'coupon': coupon.stripe_coupon_id}]
            except Coupon.DoesNotExist:
                pass
        
        try:
            session = self.stripe.checkout.Session.create(**checkout_params)
            
            # Créer le Payment en attente
            Payment.objects.create(
                user=user,
                amount=credit_pack.price,
                payment_type='post_credit',
                status='pending',
                stripe_checkout_session_id=session.id,
                stripe_customer_id=customer_id,
                description=f'{credit_pack.total_credits} crédits',
                metadata={
                    'credit_pack_id': str(credit_pack.id),
                    'credits': credit_pack.total_credits,
                    'coupon_code': coupon_code,
                },
            )
            
            logger.info(f"Session checkout crédits créée: {session.id}")
            
            return {
                'checkout_url': session.url,
                'session_id': session.id,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur création session checkout crédits: {e}")
            raise
    
    def create_single_post_checkout_session(
        self,
        user,
        listing,
        price: Decimal,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> Dict:
        """
        Crée une session pour payer une seule annonce.
        Alternative à l'achat de packs de crédits.
        
        Args:
            user: Instance CustomUser
            listing: Instance Listing (en draft)
            price: Prix de l'annonce
            
        Returns:
            Dict avec checkout_url, session_id
        """
        from apps.payments.models import Payment
        
        if not is_stripe_configured():
            return {
                'checkout_url': f'{self.frontend_url}/payment-mock',
                'session_id': f'cs_test_{user.id}_listing_{listing.id}',
                'is_test': True,
            }
        
        customer_id = self.get_or_create_customer(user)
        
        try:
            session = self.stripe.checkout.Session.create(
                customer=customer_id,
                mode='payment',
                success_url=success_url or f'{self.frontend_url}/listing/{listing.slug}/success?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=cancel_url or f'{self.frontend_url}/listing/{listing.slug}/edit',
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': f'Publication: {listing.title[:50]}',
                            'description': 'Frais de publication d\'annonce',
                        },
                        'unit_amount': int(price * 100),
                    },
                    'quantity': 1,
                }],
                metadata={
                    'user_id': str(user.id),
                    'listing_id': str(listing.id),
                    'payment_type': 'single_post',
                },
            )
            
            Payment.objects.create(
                user=user,
                amount=price,
                payment_type='post_credit',
                status='pending',
                stripe_checkout_session_id=session.id,
                stripe_customer_id=customer_id,
                listing=listing,
                description=f'Publication annonce: {listing.title}',
            )
            
            return {
                'checkout_url': session.url,
                'session_id': session.id,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur création session checkout annonce: {e}")
            raise
    
    def create_purchase_checkout_session(
        self,
        buyer,
        listing,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> Dict:
        """
        Crée une session Stripe pour qu'un acheteur achète un article.
        
        Args:
            buyer: Instance CustomUser (l'acheteur)
            listing: Instance Listing (l'article à acheter)
            success_url: URL de redirection après succès
            cancel_url: URL de redirection après annulation
            
        Returns:
            Dict avec checkout_url, session_id
        """
        from apps.payments.models import Payment
        
        if not is_stripe_configured():
            return {
                'checkout_url': f'{self.frontend_url}/payment-mock',
                'session_id': f'cs_test_{buyer.id}_purchase_{listing.id}',
                'is_test': True,
            }
        
        customer_id = self.get_or_create_customer(buyer)
        
        # Frais de plateforme (ex: 5%)
        platform_fee_percent = 5
        platform_fee = int(listing.price * platform_fee_percent)  # En centimes
        
        try:
            # Construire l'URL absolue de l'image si disponible
            image_urls = []
            if listing.images.exists():
                first_image = listing.images.first()
                if first_image and first_image.image:
                    # Stripe nécessite une URL absolue
                    image_url = first_image.image.url
                    if image_url.startswith('/'):
                        # URL relative, la convertir en absolue
                        image_url = f'{self.frontend_url.replace(":3000", ":8000")}{image_url}'
                    image_urls = [image_url]
            
            session = self.stripe.checkout.Session.create(
                customer=customer_id,
                mode='payment',
                success_url=success_url or f'{self.frontend_url}/achat-succes?session_id={{CHECKOUT_SESSION_ID}}&listing={listing.slug}',
                cancel_url=cancel_url or f'{self.frontend_url}/annonces/{listing.slug}',
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': listing.title[:100],
                            'description': f'Achat sur Vyzio - Vendeur: {listing.seller.username}',
                            'images': image_urls,
                        },
                        'unit_amount': int(listing.price * 100),  # Prix en centimes
                    },
                    'quantity': 1,
                }],
                metadata={
                    'buyer_id': str(buyer.id),
                    'seller_id': str(listing.seller.id),
                    'listing_id': str(listing.id),
                    'listing_slug': listing.slug,
                    'payment_type': 'purchase',
                },
            )
            
            # Créer le Payment en attente
            Payment.objects.create(
                user=buyer,
                amount=listing.price,
                payment_type='purchase',
                status='pending',
                stripe_checkout_session_id=session.id,
                stripe_customer_id=customer_id,
                description=f'Achat: {listing.title}',
                metadata={
                    'listing_id': str(listing.id),
                    'seller_id': str(listing.seller.id),
                    'listing_title': listing.title,
                },
            )
            
            logger.info(f"Session d'achat créée: {session.id} pour {listing.title}")
            
            return {
                'checkout_url': session.url,
                'session_id': session.id,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur création session achat: {e}")
            raise
    
    # ==================== Portal & Utils ====================
    
    def create_billing_portal_session(self, user) -> Dict:
        """
        Crée une session vers le portail de facturation Stripe.
        Permet à l'utilisateur de gérer ses moyens de paiement.
        """
        if not is_stripe_configured():
            return {'url': f'{self.frontend_url}/account/billing'}
        
        customer_id = self.get_or_create_customer(user)
        
        try:
            session = self.stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=f'{self.frontend_url}/account/billing',
            )
            return {'url': session.url}
        except stripe.error.StripeError as e:
            logger.error(f"Erreur création portal session: {e}")
            raise
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> Tuple[bool, Optional[Dict]]:
        """
        Vérifie la signature d'un webhook Stripe.
        
        SÉCURITÉ: Toujours vérifier la signature pour éviter les attaques.
        
        Args:
            payload: Corps de la requête (bytes)
            signature: Header Stripe-Signature
            
        Returns:
            Tuple (is_valid, event_data)
        """
        if not self.webhook_secret:
            logger.warning("STRIPE_WEBHOOK_SECRET non configuré!")
            return False, None
        
        try:
            event = self.stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret
            )
            return True, event
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Signature webhook invalide: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Erreur vérification webhook: {e}")
            return False, None
    
    def get_subscription_info(self, subscription_id: str) -> Optional[Dict]:
        """Récupère les infos d'un abonnement Stripe."""
        if not is_stripe_configured() or not subscription_id:
            return None
        
        try:
            sub = self.stripe.Subscription.retrieve(subscription_id)
            return {
                'id': sub.id,
                'status': sub.status,
                'current_period_start': timezone.datetime.fromtimestamp(sub.current_period_start, tz=timezone.utc),
                'current_period_end': timezone.datetime.fromtimestamp(sub.current_period_end, tz=timezone.utc),
                'cancel_at_period_end': sub.cancel_at_period_end,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Erreur récupération subscription: {e}")
            return None
