"""Patients API URL version router."""

from __future__ import annotations

from django.urls import include, path

app_name = "patients_api"

urlpatterns = [
    path("", include("apps.patients.api.v1.urls")),
]
