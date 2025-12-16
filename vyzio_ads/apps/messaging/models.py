from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Conversation(models.Model):
    """Messaging between users"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_conversations')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_conversations')
    listing = models.ForeignKey('listings.Listing', on_delete=models.SET_NULL, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'messaging_conversation'
        ordering = ['-last_message_date']
        indexes = [
            models.Index(fields=['buyer', 'seller']),
        ]
        unique_together = ('buyer', 'seller', 'listing')
    
    def __str__(self):
        return f"{self.buyer.email} - {self.seller.email}"


class Message(models.Model):
    """Individual messages"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'messaging_message'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.email}"


class BlockedUser(models.Model):
    """Users blocking feature"""
    
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_users')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'messaging_blockeduser'
        unique_together = ('blocker', 'blocked')
    
    def __str__(self):
        return f"{self.blocker.email} blocked {self.blocked.email}"


class Report(models.Model):
    """Report spam/inappropriate behavior"""
    
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('inappropriate', 'Contenu inapproprié'),
        ('scam', 'Arnaque'),
        ('offensive', 'Offensant'),
        ('other', 'Autre'),
    ]
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True)
    
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField()
    is_resolved = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'messaging_report'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report: {self.reason} by {self.reporter.email}"


class Notification(models.Model):
    """Notifications utilisateur"""
    
    TYPE_CHOICES = [
        ('message', 'Nouveau message'),
        ('purchase', 'Achat effectué'),
        ('sale', 'Vente effectuée'),
        ('favorite', 'Favori ajouté'),
        ('review', 'Nouvel avis'),
        ('subscription', 'Abonnement'),
        ('system', 'Système'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Données supplémentaires (ex: listing_id, seller_id, etc.)
    data = models.JSONField(default=dict, blank=True)
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'messaging_notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"Notification: {self.title} for {self.user.email}"
    
    def mark_as_read(self):
        """Marque la notification comme lue"""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])
    
    @classmethod
    def create_purchase_notification_for_buyer(cls, buyer, listing, seller):
        """Crée une notification pour l'acheteur après achat"""
        return cls.objects.create(
            user=buyer,
            type='purchase',
            title='Achat confirmé ! 🎉',
            message=f'Merci pour votre achat de "{listing.title}". Contactez {seller.username} pour organiser la remise.',
            data={
                'listing_id': str(listing.id),
                'listing_title': listing.title,
                'listing_slug': listing.slug,
                'seller_id': str(seller.id),
                'seller_username': seller.username,
            }
        )
    
    @classmethod
    def create_sale_notification_for_seller(cls, seller, listing, buyer):
        """Crée une notification pour le vendeur après vente"""
        return cls.objects.create(
            user=seller,
            type='sale',
            title='Nouvelle vente ! 💰',
            message=f'Félicitations ! {buyer.username} a acheté "{listing.title}". Contactez l\'acheteur pour organiser la remise.',
            data={
                'listing_id': str(listing.id),
                'listing_title': listing.title,
                'listing_slug': listing.slug,
                'buyer_id': str(buyer.id),
                'buyer_username': buyer.username,
            }
        )
