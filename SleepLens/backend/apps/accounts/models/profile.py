"""User profile model — personal data kept out of the auth table."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from common.models import BaseModel


class UserProfile(BaseModel):
    """Profile fields for a user account."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    full_name = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "user_profiles"
        verbose_name = "User profile"
        verbose_name_plural = "User profiles"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.full_name or self.user.email
