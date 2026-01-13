"""
Modèles pour la gestion des commandes et du wallet vendeur.

Order: Représente une transaction d'achat entre un acheteur et un vendeur
SellerWallet: Solde disponible pour chaque vendeur
WalletTransaction: Historique des mouvements du wallet
WithdrawalRequest: Demandes de retrait des vendeurs
"""
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


class Order(models.Model):
    """
    Commande représentant un achat.
    Créée automatiquement après paiement réussi.
    """
    
    STATUS_CHOICES = [
        ('pending', 'En attente de confirmation'),
        ('confirmed', 'Confirmée'),
        ('processing', 'En préparation'),
        ('shipped', 'Expédiée'),
        ('delivered', 'Livrée'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
        ('refunded', 'Remboursée'),
        ('disputed', 'Litige en cours'),
    ]
    
    DELIVERY_TYPE_CHOICES = [
        ('shipping', 'Livraison'),
        ('pickup', 'Retrait en main propre'),
        ('digital', 'Livraison numérique'),
        ('service', 'Service'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    
    # Parties
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders_as_buyer'
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders_as_seller'
    )
    
    # Article acheté
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders'
    )
    listing_title = models.CharField(max_length=200)  # Snapshot du titre
    listing_snapshot = models.JSONField(default=dict)  # Snapshot des détails
    
    # Paiement
    payment = models.OneToOneField(
        'payments.Payment',
        on_delete=models.SET_NULL,
        null=True,
        related_name='order'
    )
    
    # Montants
    item_price = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    seller_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Ce que reçoit le vendeur
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_TYPE_CHOICES, default='shipping')
    
    # Livraison
    shipping_address = models.TextField(blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    tracking_url = models.URLField(blank=True)
    carrier = models.CharField(max_length=50, blank=True)  # Transporteur
    
    # Notes et communication
    seller_notes = models.TextField(blank=True, help_text="Notes du vendeur pour l'acheteur")
    buyer_notes = models.TextField(blank=True, help_text="Notes de l'acheteur")
    internal_notes = models.TextField(blank=True, help_text="Notes internes (admin)")
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Flags
    seller_notified = models.BooleanField(default=False)
    buyer_confirmed_receipt = models.BooleanField(default=False)
    review_requested = models.BooleanField(default=False)
    funds_released = models.BooleanField(default=False)  # Argent libéré au vendeur
    
    class Meta:
        db_table = 'orders_order'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} - {self.listing_title}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        if not self.seller_amount:
            self.calculate_amounts()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_order_number():
        """Génère un numéro de commande unique."""
        import random
        import string
        prefix = timezone.now().strftime('%y%m')
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"VYZ-{prefix}-{suffix}"
    
    def calculate_amounts(self):
        """Calcule la commission et le montant vendeur."""
        if self.item_price:
            self.platform_fee = self.item_price * (self.platform_fee_percent / 100)
            self.seller_amount = self.item_price - self.platform_fee
    
    def confirm(self):
        """Confirme la commande après paiement."""
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        self.save(update_fields=['status', 'confirmed_at', 'updated_at'])
    
    def mark_shipped(self, tracking_number='', carrier='', tracking_url=''):
        """Marque la commande comme expédiée."""
        self.status = 'shipped'
        self.shipped_at = timezone.now()
        self.tracking_number = tracking_number
        self.carrier = carrier
        self.tracking_url = tracking_url
        self.save(update_fields=[
            'status', 'shipped_at', 'tracking_number', 
            'carrier', 'tracking_url', 'updated_at'
        ])
    
    def mark_delivered(self):
        """Marque la commande comme livrée."""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at', 'updated_at'])
    
    def confirm_receipt(self):
        """L'acheteur confirme la réception."""
        self.buyer_confirmed_receipt = True
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=[
            'buyer_confirmed_receipt', 'status', 
            'completed_at', 'updated_at'
        ])
        # Libérer les fonds au vendeur
        self.release_funds()
    
    def release_funds(self):
        """Libère les fonds au vendeur (ajoute au wallet)."""
        if self.funds_released:
            return False
        
        wallet, created = SellerWallet.objects.get_or_create(
            user=self.seller,
            defaults={'balance': Decimal('0.00')}
        )
        wallet.credit(
            amount=self.seller_amount,
            description=f"Vente: {self.listing_title}",
            order=self
        )
        self.funds_released = True
        self.save(update_fields=['funds_released', 'updated_at'])
        return True
    
    def cancel(self, reason=''):
        """Annule la commande."""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        if reason:
            self.internal_notes = f"{self.internal_notes}\nAnnulation: {reason}".strip()
        self.save(update_fields=['status', 'cancelled_at', 'internal_notes', 'updated_at'])


class SellerWallet(models.Model):
    """
    Portefeuille vendeur.
    Contient le solde disponible pour retrait.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    
    # Soldes
    balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Solde disponible pour retrait"
    )
    pending_balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Solde en attente (commandes non terminées)"
    )
    total_earned = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Total gagné depuis le début"
    )
    total_withdrawn = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Total retiré"
    )
    
    # Infos bancaires (pour les retraits)
    bank_name = models.CharField(max_length=100, blank=True)
    iban = models.CharField(max_length=34, blank=True)
    bic = models.CharField(max_length=11, blank=True)
    account_holder = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'orders_seller_wallet'
        verbose_name = 'Portefeuille vendeur'
        verbose_name_plural = 'Portefeuilles vendeurs'
    
    def __str__(self):
        return f"Wallet {self.user.email}: {self.balance}€"
    
    def credit(self, amount, description='', order=None):
        """Crédite le wallet."""
        amount = Decimal(str(amount))
        self.balance += amount
        self.total_earned += amount
        self.save(update_fields=['balance', 'total_earned', 'updated_at'])
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='credit',
            amount=amount,
            balance_after=self.balance,
            description=description,
            order=order
        )
        return True
    
    def debit(self, amount, description='', withdrawal=None):
        """Débite le wallet (pour retrait)."""
        amount = Decimal(str(amount))
        if amount > self.balance:
            raise ValueError("Solde insuffisant")
        
        self.balance -= amount
        self.total_withdrawn += amount
        self.save(update_fields=['balance', 'total_withdrawn', 'updated_at'])
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='withdrawal',
            amount=amount,
            balance_after=self.balance,
            description=description,
            withdrawal=withdrawal
        )
        return True
    
    def add_pending(self, amount):
        """Ajoute au solde en attente."""
        amount = Decimal(str(amount))
        self.pending_balance += amount
        self.save(update_fields=['pending_balance', 'updated_at'])
    
    def release_pending(self, amount):
        """Libère du solde en attente vers le solde disponible."""
        amount = Decimal(str(amount))
        if amount > self.pending_balance:
            amount = self.pending_balance
        self.pending_balance -= amount
        self.balance += amount
        self.total_earned += amount
        self.save(update_fields=['pending_balance', 'balance', 'total_earned', 'updated_at'])


class WalletTransaction(models.Model):
    """
    Historique des transactions du wallet.
    """
    
    TRANSACTION_TYPES = [
        ('credit', 'Crédit (vente)'),
        ('withdrawal', 'Retrait'),
        ('refund', 'Remboursement'),
        ('adjustment', 'Ajustement'),
        ('fee', 'Frais'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        SellerWallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    
    # Références optionnelles
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_transactions'
    )
    withdrawal = models.ForeignKey(
        'WithdrawalRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'orders_wallet_transaction'
        ordering = ['-created_at']
        verbose_name = 'Transaction wallet'
        verbose_name_plural = 'Transactions wallet'
    
    def __str__(self):
        return f"{self.transaction_type}: {self.amount}€ - {self.wallet.user.email}"


class WithdrawalRequest(models.Model):
    """
    Demande de retrait d'un vendeur.
    L'admin valide et effectue le virement.
    """
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours de traitement'),
        ('completed', 'Effectué'),
        ('rejected', 'Rejeté'),
        ('cancelled', 'Annulé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        SellerWallet,
        on_delete=models.CASCADE,
        related_name='withdrawal_requests'
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Infos bancaires au moment de la demande (snapshot)
    bank_details = models.JSONField(default=dict)
    
    # Notes
    user_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Référence du virement
    transfer_reference = models.CharField(max_length=100, blank=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Admin qui a traité
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_withdrawals'
    )
    
    class Meta:
        db_table = 'orders_withdrawal_request'
        ordering = ['-created_at']
        verbose_name = 'Demande de retrait'
        verbose_name_plural = 'Demandes de retrait'
    
    def __str__(self):
        return f"Retrait {self.amount}€ - {self.wallet.user.email} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Snapshot des infos bancaires
        if not self.bank_details and self.wallet:
            self.bank_details = {
                'bank_name': self.wallet.bank_name,
                'iban': self.wallet.iban,
                'bic': self.wallet.bic,
                'account_holder': self.wallet.account_holder,
            }
        super().save(*args, **kwargs)
    
    def approve(self, admin_user, transfer_reference=''):
        """Approuve et marque comme effectué."""
        if self.status != 'pending':
            raise ValueError("Seules les demandes en attente peuvent être approuvées")
        
        # Débiter le wallet
        self.wallet.debit(
            amount=self.amount,
            description=f"Retrait #{str(self.id)[:8]}",
            withdrawal=self
        )
        
        self.status = 'completed'
        self.transfer_reference = transfer_reference
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.completed_at = timezone.now()
        self.save()
        return True
    
    def reject(self, admin_user, reason=''):
        """Rejette la demande."""
        if self.status != 'pending':
            raise ValueError("Seules les demandes en attente peuvent être rejetées")
        
        self.status = 'rejected'
        self.rejection_reason = reason
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.save()
        return True
    
    @classmethod
    def create_request(cls, wallet, amount, notes=''):
        """Crée une nouvelle demande de retrait."""
        amount = Decimal(str(amount))
        
        if amount <= 0:
            raise ValueError("Le montant doit être positif")
        if amount > wallet.balance:
            raise ValueError("Solde insuffisant")
        if amount < Decimal('10.00'):
            raise ValueError("Montant minimum de retrait: 10€")
        
        # Vérifier qu'il n'y a pas de demande en attente
        if cls.objects.filter(wallet=wallet, status='pending').exists():
            raise ValueError("Vous avez déjà une demande de retrait en attente")
        
        return cls.objects.create(
            wallet=wallet,
            amount=amount,
            user_notes=notes
        )
