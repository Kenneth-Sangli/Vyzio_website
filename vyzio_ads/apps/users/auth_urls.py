"""
Auth URLs - Routes d'authentification
Préfixe: /api/auth/
"""
from django.urls import path
from . import auth_views

urlpatterns = [
    # Inscription et connexion
    path('register/', auth_views.register, name='auth_register'),
    path('login/', auth_views.login, name='auth_login'),
    path('logout/', auth_views.logout, name='auth_logout'),
    
    # Profil utilisateur
    path('me/', auth_views.me, name='auth_me'),
    
    # Réinitialisation mot de passe
    path('password-reset/', auth_views.password_reset_request, name='auth_password_reset'),
    path('password-reset/confirm/', auth_views.password_reset_confirm, name='auth_password_reset_confirm'),
    
    # Vérification email
    path('verify-email/', auth_views.verify_email, name='auth_verify_email'),
    path('resend-verification/', auth_views.resend_verification, name='auth_resend_verification'),
    
    # Token refresh
    path('refresh/', auth_views.token_refresh, name='auth_token_refresh'),
]
