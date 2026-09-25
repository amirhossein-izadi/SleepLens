"""Admin for consultation sessions."""

from __future__ import annotations

from django.contrib import admin

from apps.assistant.models import ChatSession


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "study", "user", "context_injected", "created_at")
    search_fields = ("study__original_filename", "user__email")
    readonly_fields = ("created_at", "updated_at", "opencode_session_id")
    ordering = ("-created_at",)
