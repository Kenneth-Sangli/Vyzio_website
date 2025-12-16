from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Listing, Category, ListingImage, Favorite
from .serializers import (ListingListSerializer, ListingDetailSerializer, 
                         ListingCreateUpdateSerializer, CategorySerializer, 
                         ListingImageSerializer, FavoriteSerializer)
from .filters import ListingFilter
from apps.users.permissions import IsOwnListingOrReadOnly, IsSellerOrReadOnly


class ListingPagination(PageNumberPagination):
    """Pagination personnalisée pour les annonces"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Pas de pagination pour les catégories


class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnListingOrReadOnly]
    pagination_class = ListingPagination
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ListingFilter
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['created_at', 'price', 'views_count', 'favorites_count']
    ordering = ['-created_at']
    lookup_field = 'pk'
    
    def get_queryset(self):
        """
        Retourne les annonces publiées pour les utilisateurs non authentifiés
        ou toutes les annonces pour les propriétaires
        """
        user = self.request.user
        
        # Pour my_listings, retourner toutes les annonces du user
        if self.action == 'my_listings':
            return Listing.objects.filter(seller=user).select_related('seller', 'category').prefetch_related('images')
        
        # Pour les actions qui ciblent une annonce spécifique (retrieve, update, delete, actions custom)
        # permettre l'accès à toutes les annonces (les permissions gèrent l'autorisation)
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy', 
                           'upload_images', 'delete_image', 'set_primary_image', 
                           'publish', 'boost', 'toggle_favorite']:
            return Listing.objects.select_related('seller', 'category').prefetch_related('images')
        
        # Pour list (public), seulement les publiées
        queryset = Listing.objects.filter(status='published')
        
        return queryset.select_related('seller', 'category').prefetch_related('images')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ListingDetailSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ListingCreateUpdateSerializer
        return ListingListSerializer
    
    def get_permissions(self):
        """
        Permissions personnalisées par action
        """
        if self.action in ['create']:
            # Seuls les sellers peuvent créer des annonces
            return [IsAuthenticated(), IsSellerOrReadOnly()]
        if self.action in ['update', 'partial_update', 'destroy']:
            # Seul le propriétaire peut modifier/supprimer
            return [IsAuthenticated(), IsOwnListingOrReadOnly()]
        if self.action in ['my_listings', 'toggle_favorite', 'boost', 'upload_images']:
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def perform_create(self, serializer):
        """Crée l'annonce avec le vendeur actuel après vérification des droits"""
        user = self.request.user
        
        # Vérifier si le vendeur peut publier
        can_publish, reason = self._check_can_publish(user)
        if not can_publish:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(detail=reason)
        
        # Utiliser le status envoyé ou 'draft' par défaut (publication après paiement si nécessaire)
        status_value = self.request.data.get('status', 'draft')
        
        # Si pas d'abonnement actif et pas de crédits, forcer en draft
        if not self._has_active_subscription(user) and not self._has_credits(user):
            status_value = 'pending_payment'
        
        listing = serializer.save(seller=user, status=status_value)
        
        # Déduire un crédit si pay-per-post
        if status_value == 'published' and not self._has_active_subscription(user):
            self._use_credit(user)
        
        # Incrémenter le compteur d'annonces de l'abonnement
        if self._has_active_subscription(user):
            try:
                user.subscription.listings_used += 1
                user.subscription.save(update_fields=['listings_used'])
            except Exception:
                pass
        
        # Handle images if provided
        images = self.request.FILES.getlist('images')
        for index, image in enumerate(images):
            ListingImage.objects.create(
                listing=listing,
                image=image,
                is_primary=(index == 0),
                order=index
            )
        return listing
    
    def _check_can_publish(self, user):
        """Vérifie si l'utilisateur peut publier une annonce"""
        # Vérifier le rôle
        if user.role not in ['seller', 'professional'] and not user.is_superuser:
            return False, "Seuls les vendeurs peuvent publier des annonces"
        
        # Vérifier abonnement actif
        if self._has_active_subscription(user):
            subscription = user.subscription
            if subscription.can_create_listing:
                return True, None
            else:
                return False, "Vous avez atteint la limite d'annonces de votre abonnement"
        
        # Vérifier crédits pay-per-post
        if self._has_credits(user):
            return True, None
        
        # Aucun moyen de paiement
        return False, "Vous devez avoir un abonnement actif ou des crédits pour publier. Rendez-vous sur la page Abonnements."
    
    def _has_active_subscription(self, user):
        """Vérifie si l'utilisateur a un abonnement actif"""
        try:
            return hasattr(user, 'subscription') and user.subscription and user.subscription.is_active
        except Exception:
            return False
    
    def _has_credits(self, user):
        """Vérifie si l'utilisateur a des crédits disponibles"""
        try:
            return hasattr(user, 'post_credits') and user.post_credits and user.post_credits.balance > 0
        except Exception:
            return False
    
    def _use_credit(self, user):
        """Utilise un crédit pour publier une annonce"""
        try:
            if hasattr(user, 'post_credits') and user.post_credits:
                user.post_credits.use_credit()
                return True
        except Exception:
            pass
        return False
    
    def create(self, request, *args, **kwargs):
        """Override pour retourner le détail complet après création"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        listing = self.perform_create(serializer)
        
        # Retourner le détail complet
        detail_serializer = ListingDetailSerializer(listing, context={'request': request})
        headers = self.get_success_headers(serializer.data)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def retrieve(self, request, *args, **kwargs):
        """Increment view count"""
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        
        from apps.listings.models import ViewHistory
        ViewHistory.objects.create(
            user=request.user if request.user.is_authenticated else None,
            listing=instance,
            ip_address=self.get_client_ip(request)
        )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='by-slug/(?P<slug>[^/.]+)')
    def retrieve_by_slug(self, request, slug=None):
        """
        Récupère une annonce par son slug.
        GET /api/listings/by-slug/{slug}/
        """
        try:
            instance = Listing.objects.select_related('seller', 'category').prefetch_related('images').get(slug=slug)
            
            # Vérifier que l'annonce est publiée ou appartient à l'utilisateur
            if instance.status != 'published':
                if not request.user.is_authenticated or instance.seller != request.user:
                    return Response(
                        {'error': 'Annonce non trouvée'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # Incrémenter le compteur de vues
            instance.views_count += 1
            instance.save(update_fields=['views_count'])
            
            from apps.listings.models import ViewHistory
            ViewHistory.objects.create(
                user=request.user if request.user.is_authenticated else None,
                listing=instance,
                ip_address=self.get_client_ip(request)
            )
            
            serializer = ListingDetailSerializer(instance, context={'request': request})
            return Response(serializer.data)
            
        except Listing.DoesNotExist:
            return Response(
                {'error': 'Annonce non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_listings(self, request):
        """Get user's listings"""
        listings = Listing.objects.filter(seller=request.user).prefetch_related('images')
        page = self.paginate_queryset(listings)
        if page is not None:
            serializer = ListingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ListingListSerializer(listings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def can_publish(self, request):
        """Vérifie si l'utilisateur peut publier une annonce"""
        user = request.user
        
        # Vérifier le rôle
        if user.role not in ['seller', 'professional'] and not user.is_superuser:
            return Response({
                'can_publish': False,
                'reason': 'role',
                'message': 'Seuls les vendeurs peuvent publier des annonces',
                'has_subscription': False,
                'has_credits': False,
                'credits_balance': 0,
                'subscription_remaining': 0,
            })
        
        has_sub = self._has_active_subscription(user)
        has_credits = self._has_credits(user)
        
        subscription_info = {}
        if has_sub:
            sub = user.subscription
            subscription_info = {
                'plan_name': sub.plan.name,
                'remaining_listings': sub.remaining_listings,
                'can_create': sub.can_create_listing,
            }
        
        credits_balance = 0
        if hasattr(user, 'post_credits') and user.post_credits:
            credits_balance = user.post_credits.balance
        
        # Vérifier si peut publier: abonnement actif avec quota OU crédits disponibles
        can_publish_with_sub = has_sub and hasattr(user, 'subscription') and user.subscription.can_create_listing
        can_publish = can_publish_with_sub or has_credits
        
        return Response({
            'can_publish': can_publish,
            'reason': None if can_publish else 'no_payment',
            'message': None if can_publish else 'Vous devez avoir un abonnement actif ou acheter des crédits',
            'has_subscription': has_sub,
            'has_credits': has_credits,
            'credits_balance': credits_balance,
            'subscription_info': subscription_info,
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def favorites(self, request):
        """Get user's favorite listings"""
        favorite_listings = Listing.objects.filter(
            favorites__user=request.user
        ).prefetch_related('images').select_related('seller', 'category')
        page = self.paginate_queryset(favorite_listings)
        if page is not None:
            serializer = ListingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ListingListSerializer(favorite_listings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated],
            parser_classes=[MultiPartParser, FormParser])
    def upload_images(self, request, pk=None):
        """
        Upload d'images pour une annonce
        POST /api/listings/{id}/upload_images/
        """
        listing = self.get_object()
        
        # Vérifier que l'utilisateur est le propriétaire
        if listing.seller != request.user:
            return Response(
                {'error': 'Vous ne pouvez pas modifier cette annonce.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        images = request.FILES.getlist('images')
        if not images:
            return Response(
                {'error': 'Aucune image fournie.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Limiter le nombre d'images
        existing_count = listing.images.count()
        max_images = 10
        
        if existing_count + len(images) > max_images:
            return Response(
                {'error': f'Maximum {max_images} images par annonce. Vous en avez déjà {existing_count}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_images = []
        for index, image in enumerate(images):
            # Vérifier le type de fichier
            if not image.content_type.startswith('image/'):
                continue
            
            img = ListingImage.objects.create(
                listing=listing,
                image=image,
                is_primary=(existing_count == 0 and index == 0),
                order=existing_count + index
            )
            created_images.append(img)
        
        serializer = ListingImageSerializer(created_images, many=True)
        return Response({
            'message': f'{len(created_images)} image(s) uploadée(s).',
            'images': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated],
            url_path='images/(?P<image_id>[0-9]+)')
    def delete_image(self, request, pk=None, image_id=None):
        """
        Supprimer une image d'une annonce
        DELETE /api/listings/{id}/images/{image_id}/
        """
        listing = self.get_object()
        
        if listing.seller != request.user:
            return Response(
                {'error': 'Vous ne pouvez pas modifier cette annonce.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            image = listing.images.get(id=image_id)
            was_primary = image.is_primary
            image.delete()
            
            # Si c'était l'image principale, assigner la première image restante
            if was_primary:
                first_image = listing.images.first()
                if first_image:
                    first_image.is_primary = True
                    first_image.save()
            
            return Response({'message': 'Image supprimée.'}, status=status.HTTP_204_NO_CONTENT)
        except ListingImage.DoesNotExist:
            return Response({'error': 'Image non trouvée.'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated],
            url_path='images/(?P<image_id>[0-9]+)/set-primary')
    def set_primary_image(self, request, pk=None, image_id=None):
        """
        Définir une image comme principale
        POST /api/listings/{id}/images/{image_id}/set-primary/
        """
        listing = self.get_object()
        
        if listing.seller != request.user:
            return Response(
                {'error': 'Vous ne pouvez pas modifier cette annonce.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Retirer le flag primary de toutes les images
            listing.images.update(is_primary=False)
            
            # Définir la nouvelle image principale
            image = listing.images.get(id=image_id)
            image.is_primary = True
            image.save()
            
            return Response({'message': 'Image principale définie.'})
        except ListingImage.DoesNotExist:
            return Response({'error': 'Image non trouvée.'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def publish(self, request, pk=None):
        """
        Publier une annonce (passer de draft à published)
        POST /api/listings/{id}/publish/
        """
        listing = self.get_object()
        
        if listing.seller != request.user:
            return Response(
                {'error': 'Vous ne pouvez pas modifier cette annonce.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if listing.status != 'draft':
            return Response(
                {'error': f'Impossible de publier une annonce avec le statut "{listing.status}".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier qu'il y a au moins une image
        if not listing.images.exists():
            return Response(
                {'error': 'Ajoutez au moins une image avant de publier.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        listing.status = 'published'
        listing.save()
        
        serializer = ListingDetailSerializer(listing, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_favorite(self, request, pk=None):
        """Add/remove listing from favorites"""
        listing = self.get_object()
        favorite, created = Favorite.objects.get_or_create(user=request.user, listing=listing)
        
        if not created:
            favorite.delete()
            return Response({'status': 'removed'})
        
        return Response(FavoriteSerializer(favorite).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def boost(self, request, pk=None):
        """Boost a listing (premium feature)"""
        listing = self.get_object()
        
        if listing.seller != request.user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        if not hasattr(request.user, 'seller_subscription'):
            return Response({'error': 'No subscription'}, status=status.HTTP_400_BAD_REQUEST)
        
        subscription = request.user.seller_subscription
        if not subscription.can_boost or subscription.boost_count <= 0:
            return Response({'error': 'No boosts available'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Boost for 7 days
        from datetime import timedelta
        listing.is_boosted = True
        listing.boost_end_date = timezone.now() + timedelta(days=7)
        listing.save()
        
        subscription.boost_count -= 1
        subscription.save()
        
        return Response({'status': 'boosted'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending listings"""
        trending = Listing.objects.filter(
            status='published',
            is_approved=True
        ).order_by('-views_count')[:10]
        
        serializer = ListingListSerializer(trending, many=True)
        return Response(serializer.data)
    
    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
