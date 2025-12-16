from django.contrib import admin

from .models import Review, ReviewPhoto, ReviewReport

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'seller', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('reviewer__email', 'seller__email')

@admin.register(ReviewPhoto)
class ReviewPhotoAdmin(admin.ModelAdmin):
    list_display = ('review', 'image')


@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
    list_display = ('review', 'reporter', 'reason', 'is_resolved', 'resolved_by', 'resolved_at', 'created_at')
    list_filter = ('is_resolved', 'reason', 'created_at')
    search_fields = ('review__id', 'reporter__email', 'review__seller__email')
    actions = ['mark_resolved', 'mark_unresolved']

    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(is_resolved=True, resolved_at=timezone.now(), resolved_by=request.user)
        self.message_user(request, f"{count} signalement(s) marqué(s) comme résolu(s).")
    mark_resolved.short_description = "Marquer comme résolu"

    def mark_unresolved(self, request, queryset):
        count = queryset.update(is_resolved=False, resolved_at=None, resolved_by=None)
        self.message_user(request, f"{count} signalement(s) remis à non résolu.")
    mark_unresolved.short_description = "Remettre à non résolu"
