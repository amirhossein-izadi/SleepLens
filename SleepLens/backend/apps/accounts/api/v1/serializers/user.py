"""Read serializer for the authenticated user."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Public representation of a user account."""

    full_name = serializers.CharField(source="profile.full_name", default="", read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "is_active", "created_at"]
        read_only_fields = fields
