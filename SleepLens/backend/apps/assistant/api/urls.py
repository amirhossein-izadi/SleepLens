"""Assistant API URL version router."""

from __future__ import annotations

from django.urls import include, path

app_name = "assistant_api"

urlpatterns = [
    path("", include("apps.assistant.api.v1.urls")),
]
