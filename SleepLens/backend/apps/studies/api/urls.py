"""Studies API URL version router."""

from __future__ import annotations

from django.urls import include, path

app_name = "studies_api"

urlpatterns = [
    path("", include("apps.studies.api.v1.urls")),
]
