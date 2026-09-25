"""NightFeatures — the ~96 night-level sleep-quality parameters for a study."""

from __future__ import annotations

from django.db import models

from common.models import BaseModel


class NightFeatures(BaseModel):
    """Night-level feature table plus explicit not-assessable marks.

    ``values`` holds every computed parameter; ``not_assessable`` lists
    ``{"key": ..., "reason": ...}`` entries for parameters that cannot be
    computed for this recording (missing channel, coarse signal, ...). Those
    keys are absent from ``values`` so a consumer can never read a missing
    sensor as a good score.
    """

    study = models.OneToOneField(
        "studies.Study",
        on_delete=models.CASCADE,
        related_name="features",
    )
    values = models.JSONField(default=dict)
    not_assessable = models.JSONField(default=list)

    class Meta:
        db_table = "night_features"
        verbose_name = "Night features"
        verbose_name_plural = "Night features"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"features[{self.study_id}]"
