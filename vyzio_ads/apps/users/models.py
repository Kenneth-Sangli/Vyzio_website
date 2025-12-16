from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class CustomUser(AbstractUser):
    """Custom User model with extended fields"""
    
    ROLE_CHOICES = [
        ('buyer', 'Acheteur'),
        ('seller', 'Vendeur'),
        ('professional', 'Vendeur Professionnel'),
    ]
    
    SUBSCRIPTION_CHOICES = [
        ('free', 'Gratuit'),
        ('basic', 'Basic'),
        ('pro', 'Pro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='buyer')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    
    # Subscription info
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_CHOICES, default='free')
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)
    
    # Seller info
    shop_name = models.CharField(max_length=100, blank=True)
    company_name = models.CharField(max_length=100, blank=True)
    is_professional = models.BooleanField(default=False)
    
    # Ratings
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, 
                                     validators=[MinValueValidator(0), MaxValueValidator(5)])
    total_reviews = models.IntegerField(default=0)
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_active_seller = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_customuser'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
    
    def is_seller(self):
        return self.role in ['seller', 'professional']


class UserVerificationToken(models.Model):
    """Email verification tokens"""
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='verification_token')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'users_verificationtoken'
    
    def __str__(self):
        return f"Token for {self.user.email}"


class SellerProfile(models.Model):
    """
    Profil vendeur détaillé - séparé du User pour plus de flexibilité
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='seller_profile')
    
    # Informations boutique
    shop_name = models.CharField(max_length=100, blank=True)
    shop_description = models.TextField(max_length=1000, blank=True)
    shop_logo = models.ImageField(upload_to='shop_logos/', blank=True, null=True)
    shop_banner = models.ImageField(upload_to='shop_banners/', blank=True, null=True)
    
    # Informations professionnelles
    company_name = models.CharField(max_length=100, blank=True)
    siret = models.CharField(max_length=14, blank=True)  # Numéro SIRET pour les pros
    vat_number = models.CharField(max_length=20, blank=True)  # TVA intracommunautaire
    
    # Contact professionnel
    business_email = models.EmailField(blank=True)
    business_phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    
    # Adresse
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=50, default='France')
    
    # Statut
    is_pro = models.BooleanField(default=False)  # Vendeur professionnel
    is_verified = models.BooleanField(default=False)  # Profil vérifié par admin
    verification_date = models.DateTimeField(null=True, blank=True)
    
    # Statistiques
    total_sales = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    response_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # En %
    response_time = models.IntegerField(default=0)  # En minutes
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_sellerprofile'
        verbose_name = 'Profil Vendeur'
        verbose_name_plural = 'Profils Vendeurs'
    
    def __str__(self):
        return f"Profil vendeur: {self.user.email}"


class SellerSubscription(models.Model):
    """Seller subscription management"""
    
    SUBSCRIPTION_TYPES = [
        ('basic', 'Basic - 5 annonces/mois'),
        ('pro', 'Pro - Annonces illimitées'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='seller_subscription')
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPES, default='basic')
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    
    is_active = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    
    listings_count = models.IntegerField(default=0)
    max_listings = models.IntegerField(default=5)  # 5 for basic, unlimited for pro
    
    can_boost = models.BooleanField(default=False)
    boost_count = models.IntegerField(default=0)  # Available boosts for this month
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_sellersubscription'
    
    def __str__(self):
        return f"{self.user.email} - {self.subscription_type}"


class PasswordResetToken(models.Model):
    """Token pour réinitialisation du mot de passe"""
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'users_passwordresettoken'
    
    def __str__(self):
        return f"Password reset for {self.user.email}"
