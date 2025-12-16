from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Payment(models.Model):
    """
    Enregistrement des paiements (audit trail).
    Chaque transaction Stripe génère un Payment.
    """
    
    PAYMENT_TYPE_CHOICES = [
        ('subscription', 'Abonnement'),
        ('post_credit', 'Crédit annonce'),
        ('boost', 'Boost annonce'),
        ('commission', 'Commission'),
        ('purchase', 'Achat article'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
        ('cancelled', 'Annulé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Stripe details - JAMAIS stocker les numéros de carte
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, db_index=True)
    stripe_checkout_session_id = models.CharField(max_length=100, blank=True, db_index=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_invoice_id = models.CharField(max_length=100, blank=True)
    
    # Related objects
    subscription_plan = models.ForeignKey(
        'SubscriptionPlan', on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='payments'
    )
    listing = models.ForeignKey(
        'listings.Listing', on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='payments'
    )
    
    # Metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments_payment'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_type']),
        ]
    
    def __str__(self):
        return f"Payment {self.id} - {self.user.email} - {self.amount}€ ({self.status})"
    
    def mark_completed(self):
        """Marque le paiement comme complété."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])
    
    def mark_failed(self, error_message=''):
        """Marque le paiement comme échoué."""
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message', 'updated_at'])


class SubscriptionPlan(models.Model):
    """
    Plans d'abonnement disponibles (Option A).
    Configurés dans Stripe et synchronisés ici.
    """
    
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('business', 'Business'),
    ]
    
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Mensuel'),
        ('yearly', 'Annuel'),
    ]
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES)
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_price_id = models.CharField(max_length=100, blank=True, db_index=True)
    stripe_product_id = models.CharField(max_length=100, blank=True)
    
    # Features
    max_listings = models.IntegerField(default=5)
    max_images_per_listing = models.IntegerField(default=5)
    can_boost = models.BooleanField(default=False)
    boost_count_per_month = models.IntegerField(default=0)
    featured_badge = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    analytics_access = models.BooleanField(default=False)
    
    description = models.TextField(blank=True)
    features_list = models.JSONField(default=list, blank=True)  # Liste des features pour l'UI
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)  # Tag "Populaire"
    
    sort_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments_subscriptionplan'
        unique_together = ('plan_type', 'billing_cycle')
        ordering = ['sort_order', 'price']
    
    def __str__(self):
        return f"{self.name} - {self.get_billing_cycle_display()} ({self.price}€)"


class Subscription(models.Model):
    """
    Abonnement actif d'un utilisateur (Option A).
    Géré via webhooks Stripe pour la synchronisation.
    """
    
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('trialing', 'Période d\'essai'),
        ('past_due', 'Paiement en retard'),
        ('cancelled', 'Annulé'),
        ('expired', 'Expiré'),
        ('paused', 'En pause'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    stripe_subscription_id = models.CharField(max_length=100, blank=True, db_index=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    
    # Dates importantes
    started_at = models.DateTimeField(auto_now_add=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    
    # Compteurs du cycle courant
    listings_used = models.IntegerField(default=0)
    boosts_used = models.IntegerField(default=0)
    
    auto_renew = models.BooleanField(default=True)
    cancel_at_period_end = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments_subscription'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"
    
    @property
    def is_active(self):
        """Vérifie si l'abonnement est actif."""
        return self.status in ('active', 'trialing')
    
    @property
    def can_create_listing(self):
        """Vérifie si l'utilisateur peut créer une annonce."""
        if self.plan.max_listings == -1:  # Illimité
            return True
        return self.listings_used < self.plan.max_listings
    
    @property
    def remaining_listings(self):
        """Nombre d'annonces restantes."""
        if self.plan.max_listings == -1:
            return float('inf')
        return max(0, self.plan.max_listings - self.listings_used)
    
    def reset_monthly_counters(self):
        """Remet à zéro les compteurs mensuels."""
        self.listings_used = 0
        self.boosts_used = 0
        self.save(update_fields=['listings_used', 'boosts_used', 'updated_at'])


class Invoice(models.Model):
    """Invoices for payments"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invoices')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='invoices')
    
    invoice_number = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    issued_at = models.DateTimeField(auto_now_add=True)
    due_at = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)
    
    pdf_file = models.FileField(upload_to='invoices/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments_invoice'
        ordering = ['-issued_at']
    
    def __str__(self):
        return f"Invoice {self.invoice_number}"


class Coupon(models.Model):
    """Codes promo et réductions."""
    
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Pourcentage'),
        ('fixed', 'Montant fixe'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Applicable sur quoi
    applies_to_subscription = models.BooleanField(default=True)
    applies_to_post_credit = models.BooleanField(default=True)
    
    max_uses = models.IntegerField(null=True, blank=True)
    uses_count = models.IntegerField(default=0)
    max_uses_per_user = models.IntegerField(default=1)
    
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    is_active = models.BooleanField(default=True)
    stripe_coupon_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments_coupon'
    
    def __str__(self):
        return self.code
    
    def is_valid(self):
        """Vérifie si le coupon est utilisable."""
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.max_uses and self.uses_count >= self.max_uses:
            return False
        return True


class PostCreditPack(models.Model):
    """
    Packs de crédits pour pay-per-post (Option B).
    Acheter des crédits pour publier des annonces.
    """
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    credits = models.IntegerField()  # Nombre de crédits/annonces
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    stripe_price_id = models.CharField(max_length=100, blank=True, db_index=True)
    stripe_product_id = models.CharField(max_length=100, blank=True)
    
    # Bonus
    bonus_credits = models.IntegerField(default=0)  # Crédits bonus
    
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    
    sort_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments_postcreditpack'
        ordering = ['sort_order', 'price']
    
    def __str__(self):
        total = self.credits + self.bonus_credits
        return f"{self.name} - {total} crédits ({self.price}€)"
    
    @property
    def total_credits(self):
        return self.credits + self.bonus_credits
    
    @property
    def price_per_credit(self):
        return self.price / self.total_credits if self.total_credits > 0 else 0


class PostCredit(models.Model):
    """
    Crédits d'annonces d'un utilisateur (Option B - pay-per-post).
    Chaque crédit permet de publier une annonce.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='post_credits')
    
    # Balance
    balance = models.IntegerField(default=0)  # Crédits disponibles
    total_purchased = models.IntegerField(default=0)  # Total acheté
    total_used = models.IntegerField(default=0)  # Total utilisé
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments_postcredit'
    
    def __str__(self):
        return f"{self.user.email} - {self.balance} crédits"
    
    def add_credits(self, amount: int, source: str = ''):
        """Ajoute des crédits au compte."""
        self.balance += amount
        self.total_purchased += amount
        self.save(update_fields=['balance', 'total_purchased', 'updated_at'])
        
        # Log la transaction
        PostCreditTransaction.objects.create(
            post_credit=self,
            transaction_type='purchase',
            amount=amount,
            balance_after=self.balance,
            description=source,
        )
        return self.balance
    
    def use_credit(self, listing=None):
        """Utilise un crédit pour une annonce."""
        if self.balance <= 0:
            raise ValueError("Pas assez de crédits")
        
        self.balance -= 1
        self.total_used += 1
        self.save(update_fields=['balance', 'total_used', 'updated_at'])
        
        # Log la transaction
        PostCreditTransaction.objects.create(
            post_credit=self,
            transaction_type='use',
            amount=-1,
            balance_after=self.balance,
            listing=listing,
            description=f"Annonce: {listing.title}" if listing else '',
        )
        return self.balance
    
    def refund_credit(self, listing=None, reason: str = ''):
        """Rembourse un crédit (annonce supprimée/rejetée)."""
        self.balance += 1
        self.total_used -= 1
        self.save(update_fields=['balance', 'total_used', 'updated_at'])
        
        PostCreditTransaction.objects.create(
            post_credit=self,
            transaction_type='refund',
            amount=1,
            balance_after=self.balance,
            listing=listing,
            description=reason,
        )
        return self.balance


class PostCreditTransaction(models.Model):
    """
    Historique des transactions de crédits.
    Pour audit et traçabilité.
    """
    
    TRANSACTION_TYPE_CHOICES = [
        ('purchase', 'Achat'),
        ('use', 'Utilisation'),
        ('refund', 'Remboursement'),
        ('bonus', 'Bonus'),
        ('expiry', 'Expiration'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post_credit = models.ForeignKey(PostCredit, on_delete=models.CASCADE, related_name='transactions')
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.IntegerField()  # Positif = ajout, négatif = retrait
    balance_after = models.IntegerField()
    
    listing = models.ForeignKey(
        'listings.Listing', on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='credit_transactions'
    )
    payment = models.ForeignKey(
        Payment, on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='credit_transactions'
    )
    
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments_postcredittransaction'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.post_credit.user.email} - {self.transaction_type} - {self.amount}"


class WebhookEvent(models.Model):
    """
    Log des webhooks Stripe reçus.
    Pour débogage et idempotence.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stripe_event_id = models.CharField(max_length=100, unique=True, db_index=True)
    event_type = models.CharField(max_length=100, db_index=True)
    
    payload = models.JSONField()
    
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments_webhookevent'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.stripe_event_id}"
    
    def mark_processed(self):
        self.processed = True
        self.processed_at = timezone.now()
        self.save(update_fields=['processed', 'processed_at'])
