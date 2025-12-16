from django.contrib import admin
from .models import Conversation, Message, BlockedUser, Report

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'seller', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'conversation', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')

@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ('blocker', 'blocked', 'created_at')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'reported_user', 'reason', 'is_resolved')
    list_filter = ('reason', 'is_resolved')
