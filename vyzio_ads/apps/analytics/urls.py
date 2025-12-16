"""
URLs pour analytics
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardViewSet, EventTrackingView, ExportView, KPIView

app_name = 'analytics'

router = DefaultRouter()
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
    path('track/', EventTrackingView.as_view(), name='track'),
    path('export/<str:export_type>/', ExportView.as_view(), name='export'),
    path('kpis/', KPIView.as_view(), name='kpis'),
]
