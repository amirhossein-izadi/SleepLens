"""Admin for the UserProfile model."""

from __future__ import annotations

from django.contrib import admin

from apps.accounts.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "full_name", "created_at")
    search_fields = ("user__email", "full_name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
