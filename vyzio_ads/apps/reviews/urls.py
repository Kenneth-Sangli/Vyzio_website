from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReviewViewSet, FavoriteListingViewSet, FavoriteSellerViewSet

app_name = 'reviews'

router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='reviews')
router.register(r'favorites/listings', FavoriteListingViewSet, basename='favorite-listings')
router.register(r'favorites/sellers', FavoriteSellerViewSet, basename='favorite-sellers')

urlpatterns = [
    path('', include(router.urls)),
]
