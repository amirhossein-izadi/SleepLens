"""Admin for generated clinical reports."""

from __future__ import annotations

from django.contrib import admin

from apps.reports.models import ClinicalReport


@admin.register(ClinicalReport)
class ClinicalReportAdmin(admin.ModelAdmin):
    list_display = ("id", "study", "user", "model_name", "prompt_version", "created_at")
    search_fields = ("study__original_filename", "user__email")
    readonly_fields = ("created_at", "updated_at", "markdown")
    ordering = ("-created_at",)
