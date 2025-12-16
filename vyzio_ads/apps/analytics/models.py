"""
Modèles pour le tracking d'événements et analytics
Phase 9 - Dashboard seller & analytics
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class Event(models.Model):
    """
    Modèle pour tracker les événements (vues, clics, etc.)
    Similaire à Mixpanel/Amplitude mais simplifié
    """
    
    EVENT_TYPES = [
        ('listing_view', 'Vue d\'annonce'),
        ('listing_click', 'Clic sur annonce'),
        ('listing_contact', 'Contact vendeur'),
        ('listing_favorite', 'Ajout favori'),
        ('listing_share', 'Partage annonce'),
        ('message_sent', 'Message envoyé'),
        ('message_received', 'Message reçu'),
        ('payment_initiated', 'Paiement initié'),
        ('payment_completed', 'Paiement complété'),
        ('review_received', 'Avis reçu'),
        ('profile_view', 'Vue profil vendeur'),
        ('search', 'Recherche'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, db_index=True)
    
    # Utilisateur qui a effectué l'action (peut être null pour visiteurs anonymes)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='events_performed'
    )
    
    # Utilisateur cible de l'action (ex: vendeur dont l'annonce est vue)
    target_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='events_received'
    )
    
    # Annonce concernée (si applicable)
    listing = models.ForeignKey(
        'listings.Listing', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='events'
    )
    
    # Métadonnées additionnelles (JSON)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Informations de tracking
    session_id = models.CharField(max_length=100, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(max_length=500, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'analytics_event'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['target_user', 'event_type', 'created_at']),
            models.Index(fields=['listing', 'event_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class DailyStats(models.Model):
    """
    Statistiques agrégées par jour pour performance
    Dénormalisation pour éviter les requêtes coûteuses
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_stats')
    date = models.DateField(db_index=True)
    
    # Métriques d'engagement
    listing_views = models.IntegerField(default=0)
    listing_clicks = models.IntegerField(default=0)
    profile_views = models.IntegerField(default=0)
    
    # Métriques de conversion
    messages_received = models.IntegerField(default=0)
    messages_sent = models.IntegerField(default=0)
    favorites_received = models.IntegerField(default=0)
    
    # Métriques financières
    payments_received = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Métriques de réputation
    reviews_received = models.IntegerField(default=0)
    avg_rating_day = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_dailystats'
        unique_together = ('user', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
    
    def __str__(self):
        return f"Stats {self.user.email} - {self.date}"


class ListingStats(models.Model):
    """
    Statistiques par annonce
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    listing = models.OneToOneField(
        'listings.Listing', on_delete=models.CASCADE, related_name='stats'
    )
    
    # Compteurs totaux
    total_views = models.IntegerField(default=0)
    total_clicks = models.IntegerField(default=0)
    total_favorites = models.IntegerField(default=0)
    total_shares = models.IntegerField(default=0)
    total_contacts = models.IntegerField(default=0)
    
    # Compteurs uniques (par utilisateur distinct)
    unique_views = models.IntegerField(default=0)
    unique_clicks = models.IntegerField(default=0)
    
    # Taux de conversion
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_listingstats'
    
    def __str__(self):
        return f"Stats for {self.listing.title}"
    
    def calculate_conversion_rate(self):
        """Calculer le taux de conversion (contacts / vues)"""
        if self.total_views > 0:
            self.conversion_rate = (self.total_contacts / self.total_views) * 100
        else:
            self.conversion_rate = 0
        return self.conversion_rate
