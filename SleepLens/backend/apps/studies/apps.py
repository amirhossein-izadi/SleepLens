"""App configuration for studies."""

from __future__ import annotations

from django.apps import AppConfig


class StudiesConfig(AppConfig):
    name = "apps.studies"
    label = "studies"
    verbose_name = "Studies"
    default_auto_field = "django.db.models.BigAutoField"
