"""
Gestionnaire des webhooks Stripe.
Phase 6 - Paiements

SÉCURITÉ:
- Vérification de signature obligatoire
- Idempotence via WebhookEvent
- Ne pas logguer de données sensibles
"""
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class WebhookHandler:
    """
    Traite les événements Stripe reçus via webhook.
    
    Événements gérés:
    - checkout.session.completed: Paiement réussi
    - invoice.payment_succeeded: Renouvellement abonnement
    - invoice.payment_failed: Échec paiement
    - customer.subscription.updated: Mise à jour abonnement
    - customer.subscription.deleted: Annulation abonnement
    """
    
    def __init__(self):
        self.handlers = {
            'checkout.session.completed': self.handle_checkout_completed,
            'invoice.payment_succeeded': self.handle_invoice_succeeded,
            'invoice.payment_failed': self.handle_invoice_failed,
            'customer.subscription.updated': self.handle_subscription_updated,
            'customer.subscription.deleted': self.handle_subscription_deleted,
            'customer.subscription.created': self.handle_subscription_created,
        }
    
    def process_event(self, event: dict) -> bool:
        """
        Traite un événement Stripe.
        
        Args:
            event: Dictionnaire de l'événement Stripe
            
        Returns:
            True si traité avec succès
        """
        from apps.payments.models import WebhookEvent
        
        event_id = event.get('id')
        event_type = event.get('type')
        
        # Vérifier l'idempotence
        if WebhookEvent.objects.filter(stripe_event_id=event_id, processed=True).exists():
            logger.info(f"Webhook déjà traité: {event_id}")
            return True
        
        # Enregistrer l'événement
        webhook_event, created = WebhookEvent.objects.get_or_create(
            stripe_event_id=event_id,
            defaults={
                'event_type': event_type,
                'payload': event,
            }
        )
        
        # Obtenir le handler
        handler = self.handlers.get(event_type)
        
        if not handler:
            logger.info(f"Webhook non géré: {event_type}")
            webhook_event.mark_processed()
            return True
        
        try:
            handler(event['data']['object'], event)
            webhook_event.mark_processed()
            logger.info(f"Webhook traité: {event_type} ({event_id})")
            return True
            
        except Exception as e:
            logger.error(f"Erreur traitement webhook {event_type}: {e}")
            webhook_event.error_message = str(e)
            webhook_event.retry_count += 1
            webhook_event.save()
            return False
    
    # ==================== Handlers ====================
    
    def handle_checkout_completed(self, session: dict, event: dict):
        """
        Traite checkout.session.completed.
        
        - Abonnement: Activer l'abonnement
        - Pay-per-post: Créditer le compte
        - Single post: Activer l'annonce
        """
        from apps.payments.models import Payment, Subscription, PostCredit
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        session_id = session.get('id')
        metadata = session.get('metadata', {})
        payment_type = metadata.get('payment_type')
        
        # Trouver le Payment associé
        try:
            payment = Payment.objects.get(stripe_checkout_session_id=session_id)
        except Payment.DoesNotExist:
            logger.warning(f"Payment non trouvé pour session: {session_id}")
            return
        
        # Mettre à jour le Payment
        payment.status = 'completed'
        payment.completed_at = timezone.now()
        payment.stripe_payment_intent_id = session.get('payment_intent', '')
        payment.save()
        
        # Traiter selon le type
        if payment_type == 'subscription' or payment.payment_type == 'subscription':
            self._activate_subscription(payment, session)
            
        elif payment_type == 'post_credit' or payment.payment_type == 'post_credit':
            if metadata.get('listing_id'):
                # Paiement pour une annonce spécifique
                self._activate_listing(payment, metadata.get('listing_id'))
            else:
                # Pack de crédits
                self._credit_account(payment, metadata)
                
        logger.info(f"Checkout complété: {payment_type} pour {payment.user.email}")
    
    def handle_invoice_succeeded(self, invoice: dict, event: dict):
        """
        Traite invoice.payment_succeeded.
        
        Pour les renouvellements d'abonnement.
        Met à jour is_pro et les compteurs.
        """
        from apps.payments.models import Payment, Subscription
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        subscription_id = invoice.get('subscription')
        customer_id = invoice.get('customer')
        
        if not subscription_id:
            return
        
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
        except Subscription.DoesNotExist:
            logger.warning(f"Subscription non trouvée: {subscription_id}")
            return
        
        # Créer un Payment pour l'historique
        amount = invoice.get('amount_paid', 0) / 100  # Convertir depuis centimes
        Payment.objects.create(
            user=subscription.user,
            amount=amount,
            payment_type='subscription',
            status='completed',
            completed_at=timezone.now(),
            stripe_invoice_id=invoice.get('id'),
            stripe_customer_id=customer_id,
            subscription_plan=subscription.plan,
            description=f'Renouvellement {subscription.plan.name}',
        )
        
        # Mettre à jour l'abonnement
        subscription.status = 'active'
        subscription.current_period_start = timezone.now()
        
        if subscription.plan.billing_cycle == 'monthly':
            subscription.current_period_end = timezone.now() + timedelta(days=30)
        else:
            subscription.current_period_end = timezone.now() + timedelta(days=365)
        
        # Reset des compteurs mensuels
        subscription.listings_used = 0
        subscription.boosts_used = 0
        subscription.save()
        
        # Mettre à jour le profil vendeur
        self._update_seller_profile(subscription.user, is_pro=True)
        
        logger.info(f"Invoice succeeded: renouvellement pour {subscription.user.email}")
    
    def handle_invoice_failed(self, invoice: dict, event: dict):
        """
        Traite invoice.payment_failed.
        
        Désactive l'abonnement et alerte l'utilisateur.
        """
        from apps.payments.models import Payment, Subscription
        
        subscription_id = invoice.get('subscription')
        
        if not subscription_id:
            return
        
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
        except Subscription.DoesNotExist:
            return
        
        # Créer un Payment échoué
        amount = invoice.get('amount_due', 0) / 100
        Payment.objects.create(
            user=subscription.user,
            amount=amount,
            payment_type='subscription',
            status='failed',
            stripe_invoice_id=invoice.get('id'),
            subscription_plan=subscription.plan,
            error_message=invoice.get('last_payment_error', {}).get('message', 'Paiement échoué'),
        )
        
        # Mettre à jour le statut
        subscription.status = 'past_due'
        subscription.save()
        
        # Désactiver is_pro après un délai de grâce (géré ailleurs)
        # TODO: Envoyer un email d'alerte
        
        logger.warning(f"Invoice failed pour {subscription.user.email}")
    
    def handle_subscription_updated(self, sub_data: dict, event: dict):
        """
        Traite customer.subscription.updated.
        
        Synchronise les changements (upgrade, downgrade, annulation programmée).
        """
        from apps.payments.models import Subscription, SubscriptionPlan
        
        subscription_id = sub_data.get('id')
        
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
        except Subscription.DoesNotExist:
            return
        
        # Mettre à jour le statut
        status_map = {
            'active': 'active',
            'past_due': 'past_due',
            'canceled': 'cancelled',
            'unpaid': 'past_due',
            'trialing': 'trialing',
            'paused': 'paused',
        }
        subscription.status = status_map.get(sub_data.get('status'), 'active')
        
        # Mettre à jour les dates
        if sub_data.get('current_period_start'):
            subscription.current_period_start = timezone.datetime.fromtimestamp(
                sub_data['current_period_start'], 
                tz=timezone.utc
            )
        if sub_data.get('current_period_end'):
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                sub_data['current_period_end'], 
                tz=timezone.utc
            )
        
        subscription.cancel_at_period_end = sub_data.get('cancel_at_period_end', False)
        subscription.save()
        
        # Mettre à jour is_pro selon le statut
        is_pro = subscription.status in ('active', 'trialing')
        self._update_seller_profile(subscription.user, is_pro=is_pro)
        
        logger.info(f"Subscription updated: {subscription.user.email} -> {subscription.status}")
    
    def handle_subscription_deleted(self, sub_data: dict, event: dict):
        """
        Traite customer.subscription.deleted.
        
        Annule définitivement l'abonnement.
        """
        from apps.payments.models import Subscription
        
        subscription_id = sub_data.get('id')
        
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
        except Subscription.DoesNotExist:
            return
        
        subscription.status = 'cancelled'
        subscription.cancelled_at = timezone.now()
        subscription.ends_at = timezone.now()
        subscription.save()
        
        # Désactiver is_pro
        self._update_seller_profile(subscription.user, is_pro=False)
        
        logger.info(f"Subscription deleted: {subscription.user.email}")
    
    def handle_subscription_created(self, sub_data: dict, event: dict):
        """
        Traite customer.subscription.created.
        
        Crée ou met à jour l'abonnement local.
        """
        from apps.payments.models import Subscription, SubscriptionPlan
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Trouver l'utilisateur via le customer ID
        customer_id = sub_data.get('customer')
        
        # Chercher dans les payments existants
        from apps.payments.models import Payment
        payment = Payment.objects.filter(stripe_customer_id=customer_id).first()
        
        if not payment:
            logger.warning(f"User non trouvé pour customer: {customer_id}")
            return
        
        user = payment.user
        
        # Trouver le plan via le price_id
        price_id = sub_data.get('items', {}).get('data', [{}])[0].get('price', {}).get('id')
        
        try:
            plan = SubscriptionPlan.objects.get(stripe_price_id=price_id)
        except SubscriptionPlan.DoesNotExist:
            # Utiliser le plan du payment
            if payment.subscription_plan:
                plan = payment.subscription_plan
            else:
                logger.warning(f"Plan non trouvé pour price: {price_id}")
                return
        
        # Créer ou mettre à jour l'abonnement
        Subscription.objects.update_or_create(
            user=user,
            defaults={
                'plan': plan,
                'status': 'active',
                'stripe_subscription_id': sub_data.get('id'),
                'stripe_customer_id': customer_id,
                'current_period_start': timezone.datetime.fromtimestamp(
                    sub_data.get('current_period_start', timezone.now().timestamp()),
                    tz=timezone.utc
                ),
                'current_period_end': timezone.datetime.fromtimestamp(
                    sub_data.get('current_period_end', timezone.now().timestamp()),
                    tz=timezone.utc
                ),
            }
        )
        
        # Activer is_pro
        self._update_seller_profile(user, is_pro=True)
        
        logger.info(f"Subscription created: {user.email} -> {plan.name}")
    
    # ==================== Helpers ====================
    
    def _activate_subscription(self, payment, session: dict):
        """Active l'abonnement après checkout réussi."""
        from apps.payments.models import Subscription
        
        user = payment.user
        plan = payment.subscription_plan
        
        if not plan:
            return
        
        # Le subscription_id est dans la session
        subscription_id = session.get('subscription')
        
        # Calculer les dates
        if plan.billing_cycle == 'monthly':
            period_end = timezone.now() + timedelta(days=30)
        else:
            period_end = timezone.now() + timedelta(days=365)
        
        # Créer ou mettre à jour l'abonnement
        Subscription.objects.update_or_create(
            user=user,
            defaults={
                'plan': plan,
                'status': 'active',
                'stripe_subscription_id': subscription_id or '',
                'stripe_customer_id': payment.stripe_customer_id,
                'current_period_start': timezone.now(),
                'current_period_end': period_end,
                'listings_used': 0,
                'boosts_used': 0,
            }
        )
        
        # Mettre à jour le profil vendeur
        self._update_seller_profile(user, is_pro=True)
    
    def _credit_account(self, payment, metadata: dict):
        """Crédite le compte en crédits d'annonces."""
        from apps.payments.models import PostCredit, PostCreditPack
        
        user = payment.user
        credits = int(metadata.get('credits', 0))
        credit_pack_id = metadata.get('credit_pack_id')
        
        if not credits and credit_pack_id:
            try:
                pack = PostCreditPack.objects.get(id=credit_pack_id)
                credits = pack.total_credits
            except PostCreditPack.DoesNotExist:
                pass
        
        if not credits:
            # Essayer de récupérer depuis le payment metadata
            credits = payment.metadata.get('credits', 0)
        
        if credits:
            post_credit, _ = PostCredit.objects.get_or_create(user=user)
            post_credit.add_credits(credits, source=f'Achat pack - Payment {payment.id}')
            
            logger.info(f"Crédité {credits} crédits pour {user.email}")
    
    def _activate_listing(self, payment, listing_id: str):
        """Active une annonce après paiement."""
        from apps.listings.models import Listing
        
        try:
            listing = Listing.objects.get(id=listing_id)
            if listing.seller == payment.user:
                listing.status = 'active'
                listing.is_paid = True
                listing.save(update_fields=['status', 'is_paid', 'updated_at'])
                logger.info(f"Annonce activée: {listing.title}")
        except Listing.DoesNotExist:
            logger.warning(f"Listing non trouvé: {listing_id}")
    
    def _update_seller_profile(self, user, is_pro: bool):
        """Met à jour le statut is_pro du profil vendeur."""
        try:
            if hasattr(user, 'seller_profile'):
                user.seller_profile.is_pro = is_pro
                user.seller_profile.save(update_fields=['is_pro', 'updated_at'])
            
            # Mettre aussi à jour le user
            user.subscription_type = 'pro' if is_pro else 'free'
            user.save(update_fields=['subscription_type', 'updated_at'])
            
        except Exception as e:
            logger.error(f"Erreur mise à jour seller profile: {e}")
