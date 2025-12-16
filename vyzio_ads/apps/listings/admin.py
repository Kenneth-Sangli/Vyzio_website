from django.contrib import admin
from .models import Category, Listing, ListingImage, ListingVideo, Favorite

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'category', 'status', 'price', 'is_approved', 'created_at')
    list_filter = ('status', 'listing_type', 'category', 'is_approved', 'created_at')
    search_fields = ('title', 'seller__email', 'location')
    readonly_fields = ('slug', 'views_count', 'created_at', 'updated_at')
    actions = ['retirer_annonces', 'remettre_en_ligne']

    @admin.action(description='Retirer (archiver) les annonces sélectionnées')
    def retirer_annonces(self, request, queryset):
        from apps.admin_panel.models import AdminAuditLog
        count = 0
        for listing in queryset:
            listing.status = 'archived'
            listing.save()
            AdminAuditLog.objects.create(
                admin=request.user,
                action='retire_listing',
                target_listing_id=str(listing.id),
                details=f"Annonce retirée via admin ({listing.title})"
            )
            count += 1
        self.message_user(request, f"{count} annonce(s) retirée(s) (archivées).")

    @admin.action(description='Remettre en ligne les annonces sélectionnées')
    def remettre_en_ligne(self, request, queryset):
        from apps.admin_panel.models import AdminAuditLog
        count = 0
        for listing in queryset:
            listing.status = 'published'
            listing.save()
            AdminAuditLog.objects.create(
                admin=request.user,
                action='publish_listing',
                target_listing_id=str(listing.id),
                details=f"Annonce remise en ligne via admin ({listing.title})"
            )
            count += 1
        self.message_user(request, f"{count} annonce(s) remises en ligne.")

@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ('listing', 'is_primary', 'created_at')

@admin.register(ListingVideo)
class ListingVideoAdmin(admin.ModelAdmin):
    list_display = ('listing', 'platform')

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'listing', 'created_at')
    list_filter = ('created_at',)
