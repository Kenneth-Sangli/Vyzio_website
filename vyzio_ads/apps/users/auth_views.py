"""
Auth Views - Endpoints d'authentification dédiés
POST /api/auth/register/
POST /api/auth/login/
GET/PUT /api/auth/me/
POST /api/auth/password-reset/
POST /api/auth/password-reset/confirm/
POST /api/auth/verify-email/
POST /api/auth/resend-verification/
POST /api/auth/refresh/
POST /api/auth/logout/
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import secrets

from .models import CustomUser, UserVerificationToken, SellerProfile, PasswordResetToken
from .serializers import (
    UserRegistrationSerializer, 
    UserDetailSerializer, 
    UserProfileUpdateSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    LoginSerializer,
    EmailVerificationSerializer
)


# ==================== REGISTRATION ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    POST /api/auth/register/
    Inscription d'un nouvel utilisateur
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Créer le token de vérification email
        token = secrets.token_urlsafe(32)
        UserVerificationToken.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(days=1)
        )
        
        # Créer SellerProfile si vendeur
        if user.role in ['seller', 'professional']:
            SellerProfile.objects.create(user=user)
        
        # Envoyer l'email de vérification
        send_verification_email(user, token)
        
        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Inscription réussie. Veuillez vérifier votre email.',
            'user': UserDetailSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================== LOGIN ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    POST /api/auth/login/
    Connexion et retourne JWT tokens
    """
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    
    # Authentifier avec email comme username
    user = authenticate(username=email, password=password)
    
    if user is None:
        # Essayer de trouver l'utilisateur par email
        try:
            user_obj = CustomUser.objects.get(email=email)
            user = authenticate(username=user_obj.username, password=password)
        except CustomUser.DoesNotExist:
            pass
    
    if user is None:
        return Response({
            'error': 'Identifiants invalides'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if user.is_banned:
        return Response({
            'error': 'Votre compte a été suspendu'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Mettre à jour last_login
    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])
    
    # Générer les tokens
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'message': 'Connexion réussie',
        'user': UserDetailSerializer(user).data,
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        },
        'email_verified': user.is_verified
    })


# ==================== ME (Current User) ====================

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def me(request):
    """
    GET /api/auth/me/ - Récupérer le profil
    PUT/PATCH /api/auth/me/ - Mettre à jour le profil
    """
    user = request.user
    
    if request.method == 'GET':
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)
    
    # PUT ou PATCH
    serializer = UserProfileUpdateSerializer(
        user, 
        data=request.data, 
        partial=(request.method == 'PATCH')
    )
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Profil mis à jour',
            'user': UserDetailSerializer(user).data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================== PASSWORD RESET ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    POST /api/auth/password-reset/
    Demande de réinitialisation du mot de passe
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    
    try:
        user = CustomUser.objects.get(email=email)
        
        # Supprimer les anciens tokens
        PasswordResetToken.objects.filter(user=user).delete()
        
        # Créer un nouveau token
        token = secrets.token_urlsafe(32)
        PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        # Envoyer l'email
        send_password_reset_email(user, token)
        
    except CustomUser.DoesNotExist:
        # Ne pas révéler si l'email existe ou non
        pass
    
    return Response({
        'message': 'Si un compte existe avec cet email, un lien de réinitialisation a été envoyé.'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """
    POST /api/auth/password-reset/confirm/
    Confirmer la réinitialisation avec le token
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    token = serializer.validated_data['token']
    new_password = serializer.validated_data['new_password']
    
    try:
        reset_token = PasswordResetToken.objects.get(
            token=token,
            is_used=False,
            expires_at__gt=timezone.now()
        )
        
        # Mettre à jour le mot de passe
        user = reset_token.user
        user.set_password(new_password)
        user.save()
        
        # Marquer le token comme utilisé
        reset_token.is_used = True
        reset_token.save()
        
        return Response({
            'message': 'Mot de passe réinitialisé avec succès'
        })
        
    except PasswordResetToken.DoesNotExist:
        return Response({
            'error': 'Token invalide ou expiré'
        }, status=status.HTTP_400_BAD_REQUEST)


# ==================== EMAIL VERIFICATION ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    POST /api/auth/verify-email/
    Vérifier l'email avec le token
    """
    serializer = EmailVerificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    token = serializer.validated_data['token']
    
    try:
        verification = UserVerificationToken.objects.get(
            token=token,
            is_used=False,
            expires_at__gt=timezone.now()
        )
        
        # Marquer l'utilisateur comme vérifié
        user = verification.user
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        
        # Marquer le token comme utilisé
        verification.is_used = True
        verification.save()
        
        return Response({
            'message': 'Email vérifié avec succès',
            'user': UserDetailSerializer(user).data
        })
        
    except UserVerificationToken.DoesNotExist:
        return Response({
            'error': 'Token de vérification invalide ou expiré'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resend_verification(request):
    """
    POST /api/auth/resend-verification/
    Renvoyer l'email de vérification
    """
    user = request.user
    
    if user.is_verified:
        return Response({
            'message': 'Votre email est déjà vérifié'
        })
    
    # Supprimer les anciens tokens
    UserVerificationToken.objects.filter(user=user).delete()
    
    # Créer un nouveau token
    token = secrets.token_urlsafe(32)
    UserVerificationToken.objects.create(
        user=user,
        token=token,
        expires_at=timezone.now() + timedelta(days=1)
    )
    
    # Envoyer l'email
    send_verification_email(user, token)
    
    return Response({
        'message': 'Email de vérification envoyé'
    })


# ==================== TOKEN REFRESH & LOGOUT ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def token_refresh(request):
    """
    POST /api/auth/refresh/
    Rafraîchir le token d'accès
    """
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response({
            'error': 'Refresh token requis'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        refresh = RefreshToken(refresh_token)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        })
    except TokenError:
        return Response({
            'error': 'Token invalide ou expiré'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    POST /api/auth/logout/
    Invalider le refresh token
    """
    refresh_token = request.data.get('refresh')
    
    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass  # Token déjà invalide
    
    return Response({
        'message': 'Déconnexion réussie'
    })


# ==================== HELPER FUNCTIONS ====================

def send_verification_email(user, token):
    """
    Envoyer l'email de vérification
    """
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    
    subject = 'Vyzio Ads - Vérifiez votre email'
    message = f"""
Bonjour {user.first_name or user.username},

Merci de vous être inscrit sur Vyzio Ads !

Pour activer votre compte, veuillez cliquer sur le lien suivant :
{verification_url}

Ce lien expire dans 24 heures.

Si vous n'avez pas créé de compte, ignorez cet email.

L'équipe Vyzio Ads
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True  # En dev, ne pas bloquer si email échoue
        )
    except Exception as e:
        # Log l'erreur mais ne pas bloquer
        print(f"Erreur envoi email: {e}")


def send_password_reset_email(user, token):
    """
    Envoyer l'email de réinitialisation du mot de passe
    """
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    subject = 'Vyzio Ads - Réinitialisation du mot de passe'
    message = f"""
Bonjour {user.first_name or user.username},

Vous avez demandé la réinitialisation de votre mot de passe.

Cliquez sur le lien suivant pour définir un nouveau mot de passe :
{reset_url}

Ce lien expire dans 1 heure.

Si vous n'avez pas fait cette demande, ignorez cet email.

L'équipe Vyzio Ads
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True
        )
    except Exception as e:
        print(f"Erreur envoi email: {e}")
