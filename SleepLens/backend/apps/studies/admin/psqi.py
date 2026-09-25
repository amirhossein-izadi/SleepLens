"""Admin for PSQI questionnaires."""

from __future__ import annotations

from django.contrib import admin

from apps.studies.models import PSQI


@admin.register(PSQI)
class PSQIAdmin(admin.ModelAdmin):
    list_display = ("id", "study", "global_score", "created_at")
    search_fields = ("study__original_filename",)
    readonly_fields = ("created_at", "updated_at", "global_score")
    ordering = ("-created_at",)
