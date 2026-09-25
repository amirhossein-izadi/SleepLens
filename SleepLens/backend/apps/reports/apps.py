"""App configuration for reports."""

from __future__ import annotations

from django.apps import AppConfig


class ReportsConfig(AppConfig):
    name = "apps.reports"
    label = "reports"
    verbose_name = "Reports"
    default_auto_field = "django.db.models.BigAutoField"
