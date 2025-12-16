from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.db.models import Avg, Count, Q
from .models import Review, ReviewPhoto, ReviewReport, FavoriteSeller
from apps.listings.models import Favorite as ListingFavorite
from .serializers import (
    ReviewSerializer, ReviewCreateSerializer, ReviewReportSerializer,
    ReviewReportCreateSerializer, ListingFavoriteSerializer, FavoriteSellerSerializer,
    FavoriteListingCreateSerializer, FavoriteSellerCreateSerializer,
    SellerReputationSerializer
)


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet pour les avis"""
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = Review.objects.filter(is_approved=True).select_related('reviewer', 'seller')
        
        seller_id = self.request.query_params.get('seller_id')
        if seller_id:
            queryset = queryset.filter(seller_id=seller_id)
        
        listing_id = self.request.query_params.get('listing_id')
        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        if self.action == 'report_review':
            return ReviewReportCreateSerializer
        return ReviewSerializer
    
    def create(self, request, *args, **kwargs):
        """Créer un avis pour un vendeur"""
        if not request.user.is_authenticated:
            return Response({'error': 'Authentification requise'}, status=status.HTTP_401_UNAUTHORIZED)
        
        seller_id = request.data.get('seller_id')
        listing_id = request.data.get('listing_id')
        
        if not seller_id:
            return Response({'error': 'seller_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from apps.users.models import CustomUser
            seller = CustomUser.objects.get(id=seller_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Vendeur non trouvé'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user == seller:
            return Response({'error': 'Vous ne pouvez pas vous évaluer vous-même'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si un avis existe déjà
        existing_review = Review.objects.filter(
            reviewer=request.user,
            seller=seller,
            listing_id=listing_id
        ).first()
        
        if existing_review:
            return Response(
                {'error': 'Vous avez déjà laissé un avis pour ce vendeur/annonce'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Vérifier si l'acheteur a eu une interaction avec le vendeur
        is_verified = self._check_verified_buyer(request.user, seller, listing_id)
        
        listing = None
        if listing_id:
            from apps.listings.models import Listing
            try:
                listing = Listing.objects.get(id=listing_id)
            except Listing.DoesNotExist:
                pass
        
        review = Review.objects.create(
            reviewer=request.user,
            seller=seller,
            listing=listing,
            rating=serializer.validated_data['rating'],
            comment=serializer.validated_data.get('comment', ''),
            is_verified_buyer=is_verified
        )
        
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
    
    def _check_verified_buyer(self, buyer, seller, listing_id=None):
        """Vérifier si l'acheteur a eu une transaction avec le vendeur"""
        from apps.messaging.models import Conversation
        
        # Vérifier s'il y a eu une conversation
        has_conversation = Conversation.objects.filter(
            buyer=buyer, seller=seller
        ).exists()
        
        # Vérifier s'il y a eu un paiement (si le module payments existe)
        try:
            from apps.payments.models import Payment
            has_payment = Payment.objects.filter(
                user=buyer,
                listing__seller=seller,
                status='completed'
            ).exists()
        except:
            has_payment = False
        
        return has_conversation or has_payment
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_response(self, request, pk=None):
        """Réponse du vendeur à un avis"""
        review = self.get_object()
        
        if request.user != review.seller:
            return Response({'error': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        
        response_text = request.data.get('response', '').strip()
        if not response_text:
            return Response({'error': 'Texte de réponse requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        review.seller_response = response_text
        review.seller_response_date = timezone.now()
        review.save()
        
        return Response(ReviewSerializer(review).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def report_review(self, request, pk=None):
        """Signaler un avis inapproprié"""
        review = self.get_object()
        
        # Vérifier si l'utilisateur a déjà signalé cet avis
        existing_report = ReviewReport.objects.filter(
            review=review, reporter=request.user
        ).exists()
        
        if existing_report:
            return Response(
                {'error': 'Vous avez déjà signalé cet avis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReviewReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        report = ReviewReport.objects.create(
            review=review,
            reporter=request.user,
            reason=serializer.validated_data['reason'],
            description=serializer.validated_data.get('description', '')
        )
        
        # Si l'avis a plusieurs signalements, le marquer comme flagged
        if review.reports.count() >= 3:
            review.is_flagged = True
            review.save()
        
        return Response(ReviewReportSerializer(report).data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def seller_reviews(self, request):
        """Obtenir tous les avis d'un vendeur avec statistiques"""
        seller_id = request.query_params.get('seller_id')
        if not seller_id:
            return Response({'error': 'seller_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        reviews = Review.objects.filter(
            seller_id=seller_id, is_approved=True, is_flagged=False
        ).select_related('reviewer')
        
        # Calculer la distribution des notes
        distribution = reviews.values('rating').annotate(count=Count('rating'))
        rating_dist = {str(i): 0 for i in range(1, 6)}
        for item in distribution:
            rating_dist[str(item['rating'])] = item['count']
        
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        
        serializer = ReviewSerializer(reviews, many=True)
        
        return Response({
            'reviews': serializer.data,
            'count': reviews.count(),
            'average_rating': round(avg_rating, 2),
            'rating_distribution': rating_dist
        })
    
    @action(detail=False, methods=['get'])
    def seller_reputation(self, request):
        """Obtenir la réputation complète d'un vendeur avec badges"""
        seller_id = request.query_params.get('seller_id')
        if not seller_id:
            return Response({'error': 'seller_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from apps.users.models import CustomUser
            seller = CustomUser.objects.get(id=seller_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Vendeur non trouvé'}, status=status.HTTP_404_NOT_FOUND)
        
        reviews = Review.objects.filter(
            seller=seller, is_approved=True, is_flagged=False
        ).select_related('reviewer')
        
        # Distribution des notes
        distribution = reviews.values('rating').annotate(count=Count('rating'))
        rating_dist = {str(i): 0 for i in range(1, 6)}
        for item in distribution:
            rating_dist[str(item['rating'])] = item['count']
        
        # Calculer les badges
        badges = self._calculate_badges(seller, reviews)
        
        return Response({
            'seller_id': str(seller.id),
            'username': seller.username,
            'avg_rating': float(seller.avg_rating),
            'total_reviews': seller.total_reviews,
            'rating_distribution': rating_dist,
            'badges': badges,
            'recent_reviews': ReviewSerializer(reviews[:5], many=True).data
        })
    
    def _calculate_badges(self, seller, reviews):
        """Calculer les badges d'un vendeur"""
        badges = []
        
        total_reviews = reviews.count()
        avg_rating = seller.avg_rating
        
        # Badge: Nouveau vendeur
        if total_reviews == 0:
            badges.append('new_seller')
        
        # Badge: Vendeur vérifié (plus de 10 avis)
        if total_reviews >= 10:
            badges.append('verified_seller')
        
        # Badge: Top vendeur (plus de 50 avis avec note >= 4.5)
        if total_reviews >= 50 and avg_rating >= 4.5:
            badges.append('top_seller')
        
        # Badge: Excellente réputation (note >= 4.8)
        if total_reviews >= 5 and avg_rating >= 4.8:
            badges.append('excellent_reputation')
        
        # Badge: Super réactif (répond à plus de 80% des avis)
        responded = reviews.exclude(seller_response='').count()
        if total_reviews >= 5 and responded / total_reviews >= 0.8:
            badges.append('responsive_seller')
        
        return badges


class FavoriteListingViewSet(viewsets.ModelViewSet):
    """ViewSet pour les favoris d'annonces"""
    serializer_class = ListingFavoriteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ListingFavorite.objects.filter(user=self.request.user).select_related('listing')
    
    def create(self, request, *args, **kwargs):
        """Ajouter une annonce en favori"""
        listing_id = request.data.get('listing_id')
        
        if not listing_id:
            return Response({'error': 'listing_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        from apps.listings.models import Listing
        try:
            listing = Listing.objects.get(id=listing_id)
        except Listing.DoesNotExist:
            return Response({'error': 'Annonce non trouvée'}, status=status.HTTP_404_NOT_FOUND)
        
        # Vérifier si déjà en favori
        if ListingFavorite.objects.filter(user=request.user, listing=listing).exists():
            return Response({'error': 'Déjà en favoris'}, status=status.HTTP_400_BAD_REQUEST)
        
        favorite = ListingFavorite.objects.create(
            user=request.user,
            listing=listing
        )
        
        return Response(ListingFavoriteSerializer(favorite).data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """Toggle un favori d'annonce"""
        listing_id = request.data.get('listing_id')
        
        if not listing_id:
            return Response({'error': 'listing_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        favorite = ListingFavorite.objects.filter(
            user=request.user, listing_id=listing_id
        ).first()
        
        if favorite:
            favorite.delete()
            return Response({'status': 'removed', 'is_favorite': False})
        else:
            return self.create(request)
    
    @action(detail=False, methods=['get'])
    def check(self, request):
        """Vérifier si une annonce est en favori"""
        listing_id = request.query_params.get('id')
        
        if not listing_id:
            return Response({'error': 'id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        exists = ListingFavorite.objects.filter(
            user=request.user, listing_id=listing_id
        ).exists()
        
        return Response({'is_favorite': exists})


class FavoriteSellerViewSet(viewsets.ModelViewSet):
    """ViewSet pour les vendeurs favoris"""
    serializer_class = FavoriteSellerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FavoriteSeller.objects.filter(user=self.request.user).select_related('seller')
    
    def create(self, request, *args, **kwargs):
        """Ajouter un vendeur en favori"""
        seller_id = request.data.get('seller_id')
        
        if not seller_id:
            return Response({'error': 'seller_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        from apps.users.models import CustomUser
        try:
            seller = CustomUser.objects.get(id=seller_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Vendeur non trouvé'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user == seller:
            return Response({'error': 'Vous ne pouvez pas vous ajouter en favori'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si déjà en favori
        if FavoriteSeller.objects.filter(user=request.user, seller=seller).exists():
            return Response({'error': 'Déjà en favoris'}, status=status.HTTP_400_BAD_REQUEST)
        
        favorite = FavoriteSeller.objects.create(
            user=request.user,
            seller=seller
        )
        
        return Response(FavoriteSellerSerializer(favorite).data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """Toggle un favori de vendeur"""
        seller_id = request.data.get('seller_id')
        
        if not seller_id:
            return Response({'error': 'seller_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        favorite = FavoriteSeller.objects.filter(
            user=request.user, seller_id=seller_id
        ).first()
        
        if favorite:
            favorite.delete()
            return Response({'status': 'removed', 'is_favorite': False})
        else:
            return self.create(request)
    
    @action(detail=False, methods=['get'])
    def check(self, request):
        """Vérifier si un vendeur est en favori"""
        seller_id = request.query_params.get('id')
        
        if not seller_id:
            return Response({'error': 'id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        exists = FavoriteSeller.objects.filter(
            user=request.user, seller_id=seller_id
        ).exists()
        
        return Response({'is_favorite': exists})
