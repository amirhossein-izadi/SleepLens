"""App configuration for analysis."""

from __future__ import annotations

from django.apps import AppConfig


class AnalysisConfig(AppConfig):
    name = "apps.analysis"
    label = "analysis"
    verbose_name = "Analysis"
    default_auto_field = "django.db.models.BigAutoField"
