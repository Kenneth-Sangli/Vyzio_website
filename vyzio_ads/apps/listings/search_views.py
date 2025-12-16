"""
Views pour la recherche avancée.
Endpoint GET /api/search/ avec logique de recherche spécialisée.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count

from .models import Listing, Category
from .serializers import ListingListSerializer, CategorySerializer
from .search import ListingSearchEngine, SearchQueryParams


class SearchPagination(PageNumberPagination):
    """Pagination pour les résultats de recherche"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class SearchView(APIView):
    """
    Endpoint de recherche avancée.
    
    GET /api/search/
    
    Fonctionnalités:
    - Recherche full-text (PostgreSQL) ou icontains (SQLite)
    - Filtres: catégorie, prix, localisation, type
    - Tri: recent, price_asc, price_desc, relevance, popular
    - Recherche géographique par rayon (si lat/lon fournis)
    - Pagination
    """
    permission_classes = [AllowAny]
    pagination_class = SearchPagination
    
    def get(self, request):
        """
        Recherche avancée d'annonces.
        """
        # Valider les paramètres
        params_serializer = SearchQueryParams(data=request.query_params)
        if not params_serializer.is_valid():
            return Response(
                {'error': 'Paramètres invalides', 'details': params_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        params = params_serializer.validated_data
        
        # Exécuter la recherche
        engine = ListingSearchEngine()
        queryset = engine.search(params)
        
        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = ListingListSerializer(page, many=True, context={'request': request})
            response = paginator.get_paginated_response(serializer.data)
            
            # Ajouter les métadonnées de recherche
            response.data['search_metadata'] = {
                'query': params.get('q', ''),
                'sort': params.get('sort', 'recent'),
                'filters': {
                    k: str(v) for k, v in params.items() 
                    if v is not None and k not in ['q', 'page', 'page_size', 'sort']
                },
                'backend': 'postgresql_fulltext' if engine.is_pg else 'sqlite_icontains'
            }
            
            return response
        
        serializer = ListingListSerializer(queryset, many=True, context={'request': request})
        return Response({
            'count': len(serializer.data),
            'results': serializer.data,
            'search_metadata': {
                'query': params.get('q', ''),
                'sort': params.get('sort', 'recent'),
                'backend': 'postgresql_fulltext' if engine.is_pg else 'sqlite_icontains'
            }
        })


class SearchSuggestView(APIView):
    """
    Suggestions de recherche (autocomplétion).
    
    GET /api/search/suggest/?q=iph
    
    Retourne des suggestions basées sur:
    - Titres d'annonces existantes
    - Catégories
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        q = request.query_params.get('q', '').strip()
        limit = int(request.query_params.get('limit', 10))
        
        if len(q) < 2:
            return Response({
                'suggestions': [],
                'categories': []
            })
        
        # Suggestions de titres (annonces publiées)
        title_suggestions = Listing.objects.filter(
            status='published',
            title__icontains=q
        ).values_list('title', flat=True).distinct()[:limit]
        
        # Suggestions de catégories
        category_suggestions = Category.objects.filter(
            is_active=True,
            name__icontains=q
        ).values('id', 'name', 'slug')[:5]
        
        return Response({
            'suggestions': list(title_suggestions),
            'categories': list(category_suggestions)
        })


class SearchStatsView(APIView):
    """
    Statistiques de recherche et facettes.
    
    GET /api/search/stats/
    
    Retourne les facettes (comptages) pour les filtres disponibles.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Base queryset
        qs = Listing.objects.filter(status='published')
        
        # Appliquer la recherche si présente
        q = request.query_params.get('q', '').strip()
        if q:
            engine = ListingSearchEngine(qs)
            qs = engine._sqlite_search(qs, q) if not engine.is_pg else engine._postgres_full_text_search(qs, q)
        
        # Catégorie filtre
        category_slug = request.query_params.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        
        # Facettes par catégorie
        category_facets = qs.values(
            'category__id', 'category__name', 'category__slug'
        ).annotate(count=Count('id')).order_by('-count')
        
        # Facettes par type
        type_facets = qs.values('listing_type').annotate(count=Count('id')).order_by('-count')
        
        # Plage de prix
        from django.db.models import Min, Max, Avg
        price_stats = qs.aggregate(
            min_price=Min('price'),
            max_price=Max('price'),
            avg_price=Avg('price')
        )
        
        # Facettes par ville (top 10)
        # Extraire les villes uniques des locations
        city_facets = qs.values('location').annotate(count=Count('id')).order_by('-count')[:10]
        
        return Response({
            'total_count': qs.count(),
            'facets': {
                'categories': [
                    {
                        'id': f['category__id'],
                        'name': f['category__name'],
                        'slug': f['category__slug'],
                        'count': f['count']
                    }
                    for f in category_facets if f['category__id']
                ],
                'listing_types': [
                    {'type': f['listing_type'], 'count': f['count']}
                    for f in type_facets
                ],
                'locations': [
                    {'location': f['location'], 'count': f['count']}
                    for f in city_facets
                ]
            },
            'price_range': {
                'min': float(price_stats['min_price']) if price_stats['min_price'] else 0,
                'max': float(price_stats['max_price']) if price_stats['max_price'] else 0,
                'avg': round(float(price_stats['avg_price']), 2) if price_stats['avg_price'] else 0
            }
        })
