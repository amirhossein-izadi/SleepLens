"""Admin for the User model."""

from __future__ import annotations

from django.contrib import admin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "is_active", "is_staff", "created_at")
    list_filter = ("is_active", "is_staff")
    search_fields = ("email",)
    readonly_fields = ("created_at", "updated_at", "last_login")
    ordering = ("-created_at",)
