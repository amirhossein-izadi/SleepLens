"""API tests for register / login / me / logout."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

pytestmark = pytest.mark.django_db

User = get_user_model()


class TestRegister:
    def test_register_succeeds(self, api_client):
        url = reverse("accounts_api:v1:register")
        response = api_client.post(
            url,
            {
                "email": "new@example.com",
                "password": "strongpass123",
                "full_name": "New User",
            },
            format="json",
        )
        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["data"]["user"]["email"] == "new@example.com"
        assert "access" in body["data"]["tokens"]
        assert "access_token" in response.cookies
        assert User.objects.filter(email="new@example.com").exists()

    def test_register_duplicate_email_fails(self, api_client, user):
        url = reverse("accounts_api:v1:register")
        response = api_client.post(
            url,
            {"email": user.email, "password": "strongpass123", "full_name": "Dup"},
            format="json",
        )
        assert response.status_code == 400
        assert response.json()["success"] is False
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"


class TestLogin:
    def test_login_succeeds(self, api_client, user):
        url = reverse("accounts_api:v1:login")
        response = api_client.post(
            url, {"email": user.email, "password": "testpass123"}, format="json"
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["user"]["full_name"] == "Test User"
        assert body["data"]["tokens"]["access"]

    def test_login_wrong_password_fails(self, api_client, user):
        url = reverse("accounts_api:v1:login")
        response = api_client.post(
            url, {"email": user.email, "password": "wrong-password"}, format="json"
        )
        assert response.status_code == 400
        assert response.json()["success"] is False


class TestMe:
    def test_me_requires_auth(self, api_client):
        url = reverse("accounts_api:v1:me")
        response = api_client.get(url)
        assert response.status_code == 401

    def test_me_returns_current_user(self, authenticated_client, user):
        url = reverse("accounts_api:v1:me")
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response.json()["data"]["email"] == user.email


class TestLogout:
    def test_logout_clears_cookies(self, authenticated_client):
        url = reverse("accounts_api:v1:logout")
        response = authenticated_client.post(url, {}, format="json")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.cookies["access_token"].value == ""
