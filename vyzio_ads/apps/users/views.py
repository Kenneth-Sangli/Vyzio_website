from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import CustomUser, SellerSubscription
from .serializers import UserRegistrationSerializer, UserProfileSerializer, UserDetailSerializer, SellerSubscriptionSerializer
from django.contrib.auth import authenticate
from django_ratelimit.decorators import ratelimit
from django.db import models

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        if self.action == 'retrieve':
            return UserDetailSerializer
        return UserProfileSerializer
    
    def get_permissions(self):
        # Permettre l'accès public à la création (register) et à la visualisation de profil
        if self.action in ['create', 'retrieve']:
            return [AllowAny()]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user profile"""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    @ratelimit(key='ip', rate='5/m', block=True)
    def login(self, request):
        """Login endpoint"""
        email = request.data.get('email')
        password = request.data.get('password')
        
        user = authenticate(username=email, password=password)
        if user is not None:
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserDetailSerializer(user).data
            })
        return Response({'error': 'Identifiants invalides'}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    @ratelimit(key='ip', rate='3/m', block=True)
    def register(self, request):
        """Registration endpoint (rate-limited)"""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserDetailSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    @ratelimit(key='user', rate='10/m', block=True)
    def update_profile(self, request):
        """Update user profile"""
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Change password for authenticated user"""
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response({'error': 'Ancien et nouveau mot de passe requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.check_password(old_password):
            return Response({'error': 'Mot de passe actuel incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(new_password) < 8:
            return Response({'error': 'Le nouveau mot de passe doit faire au moins 8 caractères'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Mot de passe modifié avec succès'})
    
    @action(detail=False, methods=['get'])
    def seller_stats(self, request):
        """Get seller statistics"""
        if not request.user.is_seller():
            return Response({'error': 'Vous n\'êtes pas un vendeur'}, status=status.HTTP_403_FORBIDDEN)
        
        from apps.listings.models import Listing
        from apps.reviews.models import Review
        
        listings_count = Listing.objects.filter(seller=request.user).count()
        reviews = Review.objects.filter(seller=request.user)
        avg_rating = reviews.aggregate(avg=models.Avg('rating'))['avg'] or 0
        
        return Response({
            'listings_count': listings_count,
            'avg_rating': avg_rating,
            'total_reviews': reviews.count(),
            'subscription': SellerSubscriptionSerializer(request.user.seller_subscription).data if hasattr(request.user, 'seller_subscription') else None
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def export_data(self, request):
        """Export des données personnelles de l'utilisateur connecté (RGPD)"""
        user = request.user
        # Récupérer les données principales
        user_data = UserDetailSerializer(user).data
        # Ajouter les données associées si besoin (ex: seller_profile, seller_subscription)
        # Ajoutez ici d'autres données liées si nécessaire
        return Response(user_data)

    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated])
    def delete_account(self, request):
        """Suppression définitive du compte utilisateur (RGPD)"""
        user = request.user
        # Anonymisation/suppression des données associées
        # Supprimer les profils liés
        if hasattr(user, 'seller_profile'):
            user.seller_profile.delete()
        if hasattr(user, 'seller_subscription'):
            user.seller_subscription.delete()
        # Supprimer les tokens de reset et de vérification
        if hasattr(user, 'verification_token'):
            user.verification_token.delete()
        if hasattr(user, 'password_reset_tokens'):
            user.password_reset_tokens.all().delete()
        # Anonymiser l'utilisateur avant suppression (optionnel)
        user.email = f'deleted_{user.id}@example.com'
        user.username = f'deleted_{user.id}'
        user.first_name = ''
        user.last_name = ''
        user.phone = ''
        user.avatar = None
        user.bio = ''
        user.location = ''
        user.shop_name = ''
        user.company_name = ''
        user.is_active = False
        user.is_verified = False
        user.save()
        # Supprimer le compte
        user.delete()
        return Response({'detail': 'Votre compte et vos données personnelles ont été supprimés.'}, status=status.HTTP_204_NO_CONTENT)
