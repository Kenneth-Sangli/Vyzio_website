from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
import uuid

User = get_user_model()

class Category(models.Model):
    """Listing categories"""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='category_icons/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'listings_category'
        ordering = ['name']
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Listing(models.Model):
    FORBIDDEN_WORDS = ['arnaque', 'escroquerie', 'interdit', 'fake']
    """Product/Service listing model"""
    
    TYPE_CHOICES = [
        ('product', 'Produit'),
        ('service', 'Service'),
        ('rental', 'Location'),
        ('job', 'Prestation'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
        ('sold', 'Vendu'),
        ('archived', 'Archivé'),
        ('pending', 'En attente'),
    ]
    
    CONDITION_CHOICES = [
        ('new', 'Neuf'),
        ('like_new', 'Comme neuf'),
        ('good', 'Bon état'),
        ('fair', 'État correct'),
        ('poor', 'Usé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    
    listing_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='product')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_negotiable = models.BooleanField(default=True)
    
    location = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Availability
    stock = models.IntegerField(default=1)
    available = models.BooleanField(default=True)
    
    # Visibility & Stats
    views_count = models.IntegerField(default=0)
    favorites_count = models.IntegerField(default=0)
    
    # Premium features
    is_boosted = models.BooleanField(default=False)
    boost_end_date = models.DateTimeField(null=True, blank=True)
    featured = models.BooleanField(default=False)
    
    # Moderation
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'listings_listing'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller', '-created_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.seller.email}"
    
    def save(self, *args, **kwargs):
        # Automatisation : rejet si mot interdit dans le titre
        for word in self.FORBIDDEN_WORDS:
            if word.lower() in self.title.lower():
                raise ValueError(f"Le titre contient un mot interdit : '{word}'")
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Listing.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class ListingImage(models.Model):
    """Multiple images for listings"""
    
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listings/')
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'listings_image'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Image for {self.listing.title}"


class ListingVideo(models.Model):
    """Video for listings"""
    
    listing = models.OneToOneField(Listing, on_delete=models.CASCADE, related_name='video')
    video_url = models.URLField()
    platform = models.CharField(max_length=20, choices=[('youtube', 'YouTube'), ('vimeo', 'Vimeo')])
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'listings_video'
    
    def __str__(self):
        return f"Video for {self.listing.title}"


class Favorite(models.Model):
    """User favorites"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='favorited_by')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'listings_favorite'
        unique_together = ('user', 'listing')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.listing.title}"


class ViewHistory(models.Model):
    """Track listing views"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='view_history', null=True, blank=True)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='view_history')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'listings_viewhistory'
        indexes = [
            models.Index(fields=['listing', 'created_at']),
        ]
    
    def __str__(self):
        return f"View of {self.listing.title}"
