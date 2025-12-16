from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConversationViewSet, NotificationViewSet

app_name = 'messaging'

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversations')
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('', include(router.urls)),
]
