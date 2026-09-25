"""Authentication and user lifecycle services (explicit calls, no signals)."""

from __future__ import annotations

from django.contrib.auth import authenticate
from django.db import transaction

from apps.accounts.models import User, UserProfile


class UserService:
    """Explicit user lifecycle operations."""

    @staticmethod
    def create_user(*, email: str, password: str, full_name: str) -> User:
        """Create a user together with their profile."""
        with transaction.atomic():
            user = User.objects.create_user(email=email, password=password)
            UserProfile.objects.create(user=user, full_name=full_name)
            return user

    @staticmethod
    def authenticate_user(*, email: str, password: str) -> User:
        """Return the user for valid credentials or raise ``ValueError``."""
        user = authenticate(email=email, password=password)
        if not user:
            raise ValueError("Invalid email or password.")
        if not user.is_active:
            raise ValueError("User account is disabled.")
        return user

    @staticmethod
    def ensure_profile(*, user: User, full_name: str | None = None) -> UserProfile:
        """Return the user's profile, creating it when missing."""
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={"full_name": full_name or user.email.split("@")[0]},
        )
        if full_name and profile.full_name != full_name:
            profile.full_name = full_name
            profile.save(update_fields=["full_name", "updated_at"])
        return profile
