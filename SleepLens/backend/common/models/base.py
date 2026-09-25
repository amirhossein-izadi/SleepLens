"""Abstract base model shared by every SleepLens model.

Primary keys are UUIDs so database internals are never exposed through the API.
``uuid.uuid7`` (sortable) requires Python 3.14; this project targets 3.10, so
``uuid4`` is used.
"""

from __future__ import annotations

import uuid

from django.db import models


class BaseModel(models.Model):
    """UUID-keyed model with creation/update timestamps."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ("-created_at",)
