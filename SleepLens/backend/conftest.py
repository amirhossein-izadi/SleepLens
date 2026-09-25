"""Root pytest fixtures shared by every app's tests."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.accounts.services.auth_service import UserService


@pytest.fixture
def user(db):
    """A regular user with a profile."""
    return UserService.create_user(
        email="test@example.com", password="testpass123", full_name="Test User"
    )


@pytest.fixture
def admin_user(db):
    """A superuser account."""
    return UserService.create_user(
        email="admin@example.com", password="adminpass123", full_name="Admin User"
    )


@pytest.fixture
def api_client() -> APIClient:
    """Unauthenticated DRF test client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client: APIClient, user) -> APIClient:
    """DRF test client authenticated as ``user``."""
    api_client.force_authenticate(user=user)
    return api_client
