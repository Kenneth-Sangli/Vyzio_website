"""
Filtres avancés pour les annonces
"""
import django_filters
from django.db.models import Q
from .models import Listing


class ListingFilter(django_filters.FilterSet):
    """
    Filtres personnalisés pour les annonces
    """
    
    # Recherche full-text
    search = django_filters.CharFilter(
        method='filter_search',
        label='Recherche'
    )
    
    # Filtres prix
    price_min = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        label='Prix minimum'
    )
    
    price_max = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        label='Prix maximum'
    )
    
    # Filtres localisation (ville)
    city = django_filters.CharFilter(
        field_name='location',
        lookup_expr='icontains',
        label='Ville'
    )
    
    location = django_filters.CharFilter(
        field_name='location',
        lookup_expr='icontains',
        label='Localisation'
    )
    
    # Filtres catégorie (par slug ou id)
    category = django_filters.CharFilter(
        field_name='category__slug',
        lookup_expr='exact',
        label='Catégorie (slug)'
    )
    
    category_id = django_filters.NumberFilter(
        field_name='category__id',
        lookup_expr='exact',
        label='Catégorie (ID)'
    )
    
    # Filtres type d'annonce
    listing_type = django_filters.ChoiceFilter(
        field_name='listing_type',
        choices=Listing.TYPE_CHOICES,
        label='Type'
    )
    
    # Filtres statut
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=Listing.STATUS_CHOICES,
        label='Statut'
    )
    
    # Filtres vendeur
    seller = django_filters.CharFilter(
        field_name='seller__id',
        lookup_expr='exact',
        label='Vendeur (ID)'
    )
    
    seller_username = django_filters.CharFilter(
        field_name='seller__username',
        lookup_expr='exact',
        label='Vendeur (username)'
    )
    
    # Filtres boost
    is_boosted = django_filters.BooleanFilter(
        field_name='is_boosted',
        label='Avec boost'
    )
    
    # Filtres featured
    featured = django_filters.BooleanFilter(
        field_name='featured',
        label='En avant'
    )
    
    # Note: Le tri est géré par OrderingFilter de DRF dans la view
    # Pas besoin de le dupliquer ici
    
    class Meta:
        model = Listing
        fields = ['search', 'price_min', 'price_max', 'location', 'city', 'category', 
                  'category_id', 'listing_type', 'status', 'seller', 'is_boosted', 
                  'featured']
    
    def filter_search(self, queryset, name, value):
        """
        Recherche dans titre, description et localisation
        """
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(location__icontains=value) |
            Q(category__name__icontains=value)
        )


class ListingAdminFilter(django_filters.FilterSet):
    """
    Filtres pour l'admin (approbation, modération)
    """
    
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=Listing.STATUS_CHOICES,
        label='Statut'
    )
    
    seller = django_filters.CharFilter(
        field_name='seller__username',
        lookup_expr='icontains',
        label='Vendeur'
    )
    
    is_reported = django_filters.BooleanFilter(
        method='filter_reported',
        label='Signalée'
    )
    
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Créée après'
    )
    
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Créée avant'
    )
    
    class Meta:
        model = Listing
        fields = ['status', 'seller', 'is_reported', 'created_after', 'created_before']
    
    def filter_reported(self, queryset, name, value):
        """
        Filtre les annonces signalées
        """
        if value:
            return queryset.filter(report__isnull=False).distinct()
        return queryset
