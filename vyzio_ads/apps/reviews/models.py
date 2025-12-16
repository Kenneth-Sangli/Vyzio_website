from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
import uuid

User = get_user_model()


class Review(models.Model):
    """Reviews/Ratings for sellers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_made')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    listing = models.ForeignKey('listings.Listing', on_delete=models.SET_NULL, null=True, blank=True)
    
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    
    is_verified_buyer = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    
    seller_response = models.TextField(blank=True)
    seller_response_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews_review'
        ordering = ['-created_at']
        unique_together = ('reviewer', 'seller', 'listing')
        indexes = [
            models.Index(fields=['seller', 'rating']),
        ]
    
    def __str__(self):
        return f"Review by {self.reviewer.email} for {self.seller.email} - {self.rating}★"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update seller's average rating
        self.update_seller_rating()
    
    def delete(self, *args, **kwargs):
        seller = self.seller
        super().delete(*args, **kwargs)
        # Update seller's average rating after deletion
        self._update_seller_rating_static(seller)
    
    def update_seller_rating(self):
        """Update seller's average rating"""
        self._update_seller_rating_static(self.seller)
    
    @staticmethod
    def _update_seller_rating_static(seller):
        """Static method to update seller rating"""
        reviews = Review.objects.filter(seller=seller, is_approved=True, is_flagged=False)
        if reviews.exists():
            avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
            seller.avg_rating = round(avg_rating, 2) if avg_rating else 0
            seller.total_reviews = reviews.count()
        else:
            seller.avg_rating = 0
            seller.total_reviews = 0
        seller.save(update_fields=['avg_rating', 'total_reviews'])


class ReviewPhoto(models.Model):
    """Photos attached to reviews"""
    
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='review_photos/')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reviews_reviewphoto'
    
    def __str__(self):
        return f"Photo for {self.review}"


class ReviewReport(models.Model):
    """Reports/Flags for inappropriate reviews"""
    
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('inappropriate', 'Contenu inapproprié'),
        ('fake', 'Avis frauduleux'),
        ('harassment', 'Harcèlement'),
        ('other', 'Autre'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_reports_made')
    
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True)
    
    is_resolved = models.BooleanField(default=False)
    resolution_note = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='review_reports_resolved'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reviews_reviewreport'
        ordering = ['-created_at']
        unique_together = ('review', 'reporter')
    
    def __str__(self):
        return f"Report on review {self.review.id} by {self.reporter.email}"


class FavoriteSeller(models.Model):
    """User favorite sellers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_sellers')
    seller = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='favorited_by_users'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reviews_favorite_seller'
        ordering = ['-created_at']
        unique_together = ('user', 'seller')
    
    def __str__(self):
        return f"{self.user.email} favorited seller: {self.seller.email}"
