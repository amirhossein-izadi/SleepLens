"""Admin for chat messages."""

from __future__ import annotations

from django.contrib import admin

from apps.assistant.models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "sender", "created_at")
    list_filter = ("sender",)
    search_fields = ("content", "session__study__original_filename")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
