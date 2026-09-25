"""Study — one uploaded sleep test (PSG recording) and its analysis state."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.studies.utils.choices import StudyStatus
from common.models import BaseModel


class Study(BaseModel):
    """An uploaded PSG file plus processing state and night summary."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="studies",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="studies",
    )
    file = models.FileField(upload_to="studies/%Y/%m/", blank=True)
    source_path = models.CharField(
        max_length=1000,
        blank=True,
        help_text="Absolute path to a recording that stays in place (dataset ingest).",
    )
    ground_truth_labels = models.JSONField(
        null=True,
        blank=True,
        help_text="Expert hypnogram per 30-s epoch (0-4, -1 unscored); ingest only.",
    )
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=StudyStatus.choices,
        default=StudyStatus.UPLOADED,
    )
    status_message = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)

    # Filled by the analysis pipeline
    duration_minutes = models.FloatField(null=True, blank=True)
    n_epochs = models.IntegerField(null=True, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    signal_quality = models.JSONField(default=dict, blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "studies"
        verbose_name = "Study"
        verbose_name_plural = "Studies"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.original_filename} ({self.status})"
