from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ListingViewSet, CategoryViewSet
from .search_views import SearchView, SearchSuggestView, SearchStatsView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='categories')

urlpatterns = [
    # Endpoints de recherche avancée
    path('search/', SearchView.as_view(), name='search'),
    path('search/suggest/', SearchSuggestView.as_view(), name='search-suggest'),
    path('search/stats/', SearchStatsView.as_view(), name='search-stats'),
    
    # Listings directement sous /api/listings/
    path('', ListingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='listing-list'),
    
    # Route par slug (doit être AVANT la route par UUID pour éviter les conflits)
    path('by-slug/<slug:slug>/', ListingViewSet.as_view({
        'get': 'retrieve_by_slug'
    }), name='listing-by-slug'),
    
    path('<uuid:pk>/', ListingViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='listing-detail'),
    path('my-listings/', ListingViewSet.as_view({'get': 'my_listings'}), name='my-listings'),
    path('can-publish/', ListingViewSet.as_view({'get': 'can_publish'}), name='can-publish'),
    path('favorites/', ListingViewSet.as_view({'get': 'favorites'}), name='listing-favorites'),
    path('<uuid:pk>/upload_images/', ListingViewSet.as_view({'post': 'upload_images'}), name='listing-upload-images'),
    path('<uuid:pk>/favorite/', ListingViewSet.as_view({'post': 'toggle_favorite'}), name='listing-toggle-favorite'),
    path('<uuid:pk>/boost/', ListingViewSet.as_view({'post': 'boost'}), name='listing-boost'),
    
    # Router pour categories
    path('', include(router.urls)),
]
