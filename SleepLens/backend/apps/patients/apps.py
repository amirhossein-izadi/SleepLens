"""App configuration for patients."""

from __future__ import annotations

from django.apps import AppConfig


class PatientsConfig(AppConfig):
    name = "apps.patients"
    label = "patients"
    verbose_name = "Patients"
    default_auto_field = "django.db.models.BigAutoField"
