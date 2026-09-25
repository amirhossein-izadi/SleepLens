"""Admin for the Study model."""

from __future__ import annotations

from django.contrib import admin

from apps.studies.models import Study


@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "original_filename", "status", "n_epochs", "created_at")
    list_filter = ("status",)
    search_fields = ("original_filename", "user__email")
    readonly_fields = ("created_at", "updated_at", "started_at", "finished_at")
    ordering = ("-created_at",)
