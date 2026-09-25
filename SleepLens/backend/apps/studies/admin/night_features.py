"""Admin for night-level features."""

from __future__ import annotations

from django.contrib import admin

from apps.studies.models import NightFeatures


@admin.register(NightFeatures)
class NightFeaturesAdmin(admin.ModelAdmin):
    list_display = ("id", "study", "created_at")
    search_fields = ("study__original_filename", "study__user__email")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
