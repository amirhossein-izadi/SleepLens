"""Test settings — fast hashing, in-memory database, eager Celery."""

from __future__ import annotations

from .base import *  # noqa: F403

DEBUG = False

DATABASES: dict = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CACHES: dict = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}

PASSWORD_HASHERS: list[str] = ["django.contrib.auth.hashers.MD5PasswordHasher"]

CELERY_TASK_ALWAYS_EAGER = True

# Keep tests hermetic: analysis pipeline runs synchronously and writes to a
# temporary media root.
import tempfile  # noqa: E402

MEDIA_ROOT = tempfile.mkdtemp(prefix="sleeplens-test-media-")  # noqa: F405

AUTH_PASSWORD_VALIDATORS: list = []
