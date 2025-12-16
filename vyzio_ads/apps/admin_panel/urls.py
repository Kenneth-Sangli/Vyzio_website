from django.urls import path
from .views import AdminDashboardViewSet

urlpatterns = [
    path('dashboard-stats/', AdminDashboardViewSet.as_view({'get': 'dashboard_stats'}), name='dashboard-stats'),
    path('users/', AdminDashboardViewSet.as_view({'get': 'users'}), name='admin-users'),
    path('ban-user/', AdminDashboardViewSet.as_view({'post': 'ban_user'}), name='ban-user'),
    path('unban-user/', AdminDashboardViewSet.as_view({'post': 'unban_user'}), name='unban-user'),
    path('pending-listings/', AdminDashboardViewSet.as_view({'get': 'pending_listings'}), name='pending-listings'),
    path('approve-listing/', AdminDashboardViewSet.as_view({'post': 'approve_listing'}), name='approve-listing'),
    path('reject-listing/', AdminDashboardViewSet.as_view({'post': 'reject_listing'}), name='reject-listing'),
    path('reports/', AdminDashboardViewSet.as_view({'get': 'reports'}), name='admin-reports'),
    path('resolve-report/', AdminDashboardViewSet.as_view({'post': 'resolve_report'}), name='resolve-report'),
    path('audit-logs/', AdminDashboardViewSet.as_view({'get': 'audit_logs'}), name='audit-logs'),
]
