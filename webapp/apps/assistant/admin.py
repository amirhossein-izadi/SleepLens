from django.contrib import admin
from apps.assistant.models.chat_session import ChatSession
from apps.assistant.models.chat_message import ChatMessage

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("title", "study", "physician", "opencode_session_id", "created_at")
    search_fields = ("title", "study__id", "opencode_session_id")
    readonly_fields = ("id", "created_at", "updated_at")

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("session", "sender", "created_at")
    list_filter = ("sender", "created_at")
    search_fields = ("content",)
    readonly_fields = ("id", "created_at")
