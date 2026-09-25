"""StudyEpoch — per-30-second staging + sleep depth result for one epoch.

This is the row the charts are built from: label, full probability vector,
confidence and band (review flag), plus the sleep depth index and its REM head.
"""

from __future__ import annotations

from django.db import models

from apps.studies.utils.choices import ConfidenceBand
from common.models import BaseModel


class StudyEpoch(BaseModel):
    """One 30-second epoch of a study's analysis output."""

    study = models.ForeignKey(
        "studies.Study",
        on_delete=models.CASCADE,
        related_name="epochs",
    )
    epoch_index = models.IntegerField()
    start_sec = models.IntegerField()

    stage = models.CharField(max_length=4)
    probabilities = models.JSONField(default=dict)
    confidence = models.FloatField()
    confidence_band = models.CharField(max_length=6, choices=ConfidenceBand.choices)
    needs_review = models.BooleanField(default=False)

    sdi = models.FloatField(null=True, blank=True)
    rem_pred = models.BooleanField(null=True, blank=True)

    class Meta:
        db_table = "study_epochs"
        verbose_name = "Study epoch"
        verbose_name_plural = "Study epochs"
        ordering = ["epoch_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["study", "epoch_index"], name="unique_epoch_per_study"
            )
        ]
        indexes = [
            models.Index(fields=["study", "epoch_index"]),
            models.Index(fields=["study", "needs_review"]),
        ]

    def __str__(self) -> str:
        return f"{self.study_id} #{self.epoch_index} {self.stage}"
