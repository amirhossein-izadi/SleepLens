"""Admin for the Patient model."""

from __future__ import annotations

from django.contrib import admin

from apps.patients.models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "owner", "sex", "birth_year", "created_at")
    list_filter = ("sex",)
    search_fields = ("full_name", "owner__email")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("full_name",)
