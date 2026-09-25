"""Development settings."""

from __future__ import annotations

from .base import *  # noqa: F403
from .base import env

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Security relaxations that are safe only in dev.
AUTH_PASSWORD_VALIDATORS: list = []

# Verbose console logging in dev.
LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["django"]["level"] = "INFO"  # noqa: F405

if env("DB_ENGINE") == "sqlite":
    CACHES = {  # noqa: F405
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }
