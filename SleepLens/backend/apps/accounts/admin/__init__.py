"""Accounts admin registrations."""

from __future__ import annotations

from .profile import UserProfileAdmin
from .user import UserAdmin

__all__ = ["UserAdmin", "UserProfileAdmin"]
