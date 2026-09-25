"""Accounts API v1 URL configuration."""

from __future__ import annotations

from django.urls import path

from apps.accounts.api.v1.views.auth import LoginView, RegisterView
from apps.accounts.api.v1.views.logout import LogoutView
from apps.accounts.api.v1.views.me import MeView
from apps.accounts.api.v1.views.token_refresh import TokenRefreshView

app_name = "v1"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
]
