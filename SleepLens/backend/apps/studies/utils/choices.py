"""Shared choices for the studies domain."""

from __future__ import annotations

from django.db import models


class StudyStatus(models.TextChoices):
    """Lifecycle of an uploaded study."""

    UPLOADED = "uploaded", "Uploaded"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class Stage(models.TextChoices):
    """Five AASM sleep stages (as produced by the staging model)."""

    WAKE = "Wake", "Wake"
    N1 = "N1", "N1"
    N2 = "N2", "N2"
    N3 = "N3", "N3"
    REM = "REM", "REM"


class ConfidenceBand(models.TextChoices):
    """How much a per-epoch prediction should be trusted."""

    HIGH = "high", "High — confident, label accepted as-is"
    MEDIUM = "medium", "Medium — review recommended"
    LOW = "low", "Low — suspicious, needs expert review"
