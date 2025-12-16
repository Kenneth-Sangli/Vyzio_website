from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserVerificationToken, SellerSubscription, SellerProfile, PasswordResetToken


class SellerProfileInline(admin.StackedInline):
    """Inline pour afficher le profil vendeur dans l'admin User"""
    model = SellerProfile
    can_delete = False
    verbose_name = 'Profil Vendeur'
    verbose_name_plural = 'Profil Vendeur'
    fk_name = 'user'
    
    fieldsets = (
        ('Boutique', {
            'fields': ('shop_name', 'shop_description', 'shop_logo', 'shop_banner')
        }),
        ('Informations professionnelles', {
            'fields': ('company_name', 'siret', 'vat_number', 'is_pro'),
            'classes': ('collapse',)
        }),
        ('Contact', {
            'fields': ('business_email', 'business_phone', 'website'),
            'classes': ('collapse',)
        }),
        ('Adresse', {
            'fields': ('address', 'city', 'postal_code', 'country'),
            'classes': ('collapse',)
        }),
        ('Statistiques', {
            'fields': ('total_sales', 'total_revenue', 'response_rate', 'response_time'),
            'classes': ('collapse',)
        }),
        ('Vérification', {
            'fields': ('is_verified', 'verification_date'),
        }),
    )


class SellerSubscriptionInline(admin.StackedInline):
    """Inline pour afficher l'abonnement vendeur"""
    model = SellerSubscription
    can_delete = False
    verbose_name = 'Abonnement Vendeur'
    verbose_name_plural = 'Abonnement Vendeur'
    fk_name = 'user'
    
    fieldsets = (
        ('Abonnement', {
            'fields': ('subscription_type', 'is_active', 'started_at', 'ends_at')
        }),
        ('Stripe', {
            'fields': ('stripe_customer_id', 'stripe_subscription_id'),
            'classes': ('collapse',)
        }),
        ('Limites', {
            'fields': ('listings_count', 'max_listings', 'can_boost', 'boost_count'),
        }),
    )


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin personnalisé pour les utilisateurs"""
    
    list_display = ('email', 'username', 'full_name', 'role', 'subscription_type', 
                    'is_verified', 'is_banned', 'is_active', 'created_at')
    list_filter = ('role', 'subscription_type', 'is_verified', 'is_banned', 
                   'is_active', 'is_staff', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'shop_name', 'phone')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'avg_rating', 'total_reviews', 'last_login')
    
    # Inlines pour les profils vendeurs
    inlines = [SellerProfileInline, SellerSubscriptionInline]
    
    fieldsets = (
        (None, {
            'fields': ('id', 'email', 'username', 'password')
        }),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'phone', 'avatar', 'bio', 'location')
        }),
        ('Rôle et abonnement', {
            'fields': ('role', 'subscription_type', 'subscription_start', 'subscription_end')
        }),
        ('Vendeur', {
            'fields': ('shop_name', 'company_name', 'is_professional', 'is_active_seller'),
            'classes': ('collapse',)
        }),
        ('Évaluations', {
            'fields': ('avg_rating', 'total_reviews'),
        }),
        ('Statut', {
            'fields': ('is_verified', 'is_banned', 'is_active', 'is_staff', 'is_superuser'),
        }),
        ('Permissions', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('last_login', 'created_at', 'updated_at'),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'role'),
        }),
    )
    
    def full_name(self, obj):
        return obj.get_full_name() or obj.username
    full_name.short_description = 'Nom complet'
    
    def get_inline_instances(self, request, obj=None):
        """N'afficher les inlines que pour les vendeurs"""
        if obj and obj.role in ['seller', 'professional']:
            return super().get_inline_instances(request, obj)
        return []
    

    actions = ['verify_users', 'ban_users', 'unban_users', 'upgrade_to_seller', 'suspend_users', 'reactivate_users']

    @admin.action(description='Suspendre les utilisateurs sélectionnés')
    def suspend_users(self, request, queryset):
        from apps.admin_panel.models import AdminAuditLog
        count = 0
        for user in queryset:
            user.is_active = False
            user.save()
            AdminAuditLog.objects.create(
                admin=request.user,
                action='suspend_user',
                target_user=user,
                details=f"Utilisateur suspendu via admin ({user.email})"
            )
            count += 1
        self.message_user(request, f'{count} utilisateur(s) suspendu(s).')

        @admin.action(description='Réactiver les utilisateurs sélectionnés')
        def reactivate_users(self, request, queryset):
            from apps.admin_panel.models import AdminAuditLog
            count = 0
            for user in queryset:
                user.is_active = True
                user.save()
                AdminAuditLog.objects.create(
                    admin=request.user,
                    action='reactivate_user',
                    target_user=user,
                    details=f"Utilisateur réactivé via admin ({user.email})"
                )
                count += 1
            self.message_user(request, f'{count} utilisateur(s) réactivé(s).')
    
    @admin.action(description='Vérifier les utilisateurs sélectionnés')
    def verify_users(self, request, queryset):
        count = queryset.update(is_verified=True)
        self.message_user(request, f'{count} utilisateur(s) vérifié(s).')
    
    @admin.action(description='Bannir les utilisateurs sélectionnés')
    def ban_users(self, request, queryset):
        count = queryset.update(is_banned=True)
        self.message_user(request, f'{count} utilisateur(s) banni(s).')
    
    @admin.action(description='Débannir les utilisateurs sélectionnés')
    def unban_users(self, request, queryset):
        count = queryset.update(is_banned=False)
        self.message_user(request, f'{count} utilisateur(s) débanni(s).')
    
    @admin.action(description='Passer en vendeur')
    def upgrade_to_seller(self, request, queryset):
        for user in queryset:
            user.role = 'seller'
            user.save()
            # Créer le profil vendeur si nécessaire
            SellerProfile.objects.get_or_create(user=user)
        self.message_user(request, f'{queryset.count()} utilisateur(s) passé(s) en vendeur.')


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    """Admin pour les profils vendeurs"""
    
    list_display = ('user', 'shop_name', 'company_name', 'is_pro', 'is_verified', 
                    'total_sales', 'response_rate', 'created_at')
    list_filter = ('is_pro', 'is_verified', 'country', 'created_at')
    search_fields = ('user__email', 'shop_name', 'company_name', 'siret')
    readonly_fields = ('created_at', 'updated_at', 'total_sales', 'total_revenue')
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Boutique', {
            'fields': ('shop_name', 'shop_description', 'shop_logo', 'shop_banner')
        }),
        ('Informations professionnelles', {
            'fields': ('company_name', 'siret', 'vat_number', 'is_pro')
        }),
        ('Contact', {
            'fields': ('business_email', 'business_phone', 'website')
        }),
        ('Adresse', {
            'fields': ('address', 'city', 'postal_code', 'country')
        }),
        ('Vérification', {
            'fields': ('is_verified', 'verification_date')
        }),
        ('Statistiques', {
            'fields': ('total_sales', 'total_revenue', 'response_rate', 'response_time')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['verify_profiles', 'mark_as_pro']
    
    @admin.action(description='Vérifier les profils sélectionnés')
    def verify_profiles(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(is_verified=True, verification_date=timezone.now())
        self.message_user(request, f'{count} profil(s) vérifié(s).')
    
    @admin.action(description='Marquer comme professionnel')
    def mark_as_pro(self, request, queryset):
        count = queryset.update(is_pro=True)
        # Mettre à jour aussi le user
        for profile in queryset:
            profile.user.is_professional = True
            profile.user.role = 'professional'
            profile.user.save()
        self.message_user(request, f'{count} profil(s) marqué(s) comme professionnel.')


@admin.register(UserVerificationToken)
class UserVerificationTokenAdmin(admin.ModelAdmin):
    """Admin pour les tokens de vérification email"""
    
    list_display = ('user', 'token_short', 'is_used', 'created_at', 'expires_at', 'is_expired')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('token', 'created_at')
    
    def token_short(self, obj):
        return f"{obj.token[:20]}..."
    token_short.short_description = 'Token'
    
    def is_expired(self, obj):
        from django.utils import timezone
        return obj.expires_at < timezone.now()
    is_expired.boolean = True
    is_expired.short_description = 'Expiré'


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin pour les tokens de réinitialisation mot de passe"""
    
    list_display = ('user', 'token_short', 'is_used', 'created_at', 'expires_at', 'is_expired')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('token', 'created_at')
    
    def token_short(self, obj):
        return f"{obj.token[:20]}..."
    token_short.short_description = 'Token'
    
    def is_expired(self, obj):
        from django.utils import timezone
        return obj.expires_at < timezone.now()
    is_expired.boolean = True
    is_expired.short_description = 'Expiré'


@admin.register(SellerSubscription)
class SellerSubscriptionAdmin(admin.ModelAdmin):
    """Admin pour les abonnements vendeurs"""
    
    list_display = ('user', 'subscription_type', 'is_active', 'listings_count', 
                    'max_listings', 'can_boost', 'started_at', 'ends_at')
    list_filter = ('subscription_type', 'is_active', 'can_boost')
    search_fields = ('user__email', 'stripe_customer_id')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Abonnement', {
            'fields': ('subscription_type', 'is_active', 'started_at', 'ends_at')
        }),
        ('Stripe', {
            'fields': ('stripe_customer_id', 'stripe_subscription_id'),
            'classes': ('collapse',)
        }),
        ('Limites', {
            'fields': ('listings_count', 'max_listings', 'can_boost', 'boost_count')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['activate_subscriptions', 'deactivate_subscriptions', 'reset_listings_count']
    
    @admin.action(description='Activer les abonnements')
    def activate_subscriptions(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} abonnement(s) activé(s).')
    
    @admin.action(description='Désactiver les abonnements')
    def deactivate_subscriptions(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} abonnement(s) désactivé(s).')
    
    @admin.action(description='Réinitialiser le compteur d\'annonces')
    def reset_listings_count(self, request, queryset):
        count = queryset.update(listings_count=0)
        self.message_user(request, f'{count} compteur(s) réinitialisé(s).')
