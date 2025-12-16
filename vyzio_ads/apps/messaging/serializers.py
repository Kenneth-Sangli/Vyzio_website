from rest_framework import serializers
from .models import Conversation, Message, BlockedUser, Report, Notification
from apps.users.serializers import UserProfileSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ('id', 'sender', 'content', 'is_read', 'created_at')
        read_only_fields = ('id', 'sender', 'created_at')


class ConversationSerializer(serializers.ModelSerializer):
    buyer = UserProfileSerializer(read_only=True)
    seller = UserProfileSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    listing_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ('id', 'buyer', 'seller', 'listing', 'listing_info', 'is_active', 'last_message', 'unread_count', 'last_message_date', 'created_at')
    
    def get_listing_info(self, obj):
        if obj.listing:
            return {
                'id': str(obj.listing.id),
                'title': obj.listing.title,
                'slug': obj.listing.slug,
            }
        return None
    
    def get_last_message(self, obj):
        message = obj.messages.last()
        if message:
            return MessageSerializer(message).data
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request:
            if request.user == obj.seller:
                return obj.messages.filter(sender=obj.buyer, is_read=False).count()
            else:
                return obj.messages.filter(sender=obj.seller, is_read=False).count()
        return 0


class ConversationDetailSerializer(serializers.ModelSerializer):
    buyer = UserProfileSerializer(read_only=True)
    seller = UserProfileSerializer(read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Conversation
        fields = ('id', 'buyer', 'seller', 'is_active', 'messages', 'created_at')


class ReportSerializer(serializers.ModelSerializer):
    reporter = UserProfileSerializer(read_only=True)
    reported_user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Report
        fields = ('id', 'reporter', 'reported_user', 'reason', 'description', 'is_resolved', 'created_at')
        read_only_fields = ('id', 'reporter', 'created_at')


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer pour les notifications"""
    
    class Meta:
        model = Notification
        fields = ('id', 'type', 'title', 'message', 'data', 'is_read', 'read_at', 'created_at')
        read_only_fields = ('id', 'type', 'title', 'message', 'data', 'created_at')
