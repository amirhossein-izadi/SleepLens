"""App configuration for assistant."""

from __future__ import annotations

from django.apps import AppConfig


class AssistantConfig(AppConfig):
    name = "apps.assistant"
    label = "assistant"
    verbose_name = "Assistant"
    default_auto_field = "django.db.models.BigAutoField"
