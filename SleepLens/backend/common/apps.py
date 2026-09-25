"""App configuration for the shared ``common`` package."""

from __future__ import annotations

from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = "common"
    verbose_name = "Common"
    default_auto_field = "django.db.models.BigAutoField"
