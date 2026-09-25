"""Login serializer."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.accounts.services.auth_service import UserService


class LoginSerializer(serializers.Serializer):
    """Validate credentials and expose the authenticated user."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        try:
            user = UserService.authenticate_user(
                email=attrs["email"].lower().strip(),
                password=attrs["password"],
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        attrs["user"] = user
        return attrs
