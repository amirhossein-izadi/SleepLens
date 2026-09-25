"""Accounts API URL version router."""

from __future__ import annotations

from django.urls import include, path

app_name = "accounts_api"

urlpatterns = [
    path("", include("apps.accounts.api.v1.urls")),
]
