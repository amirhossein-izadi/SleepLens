"""PSQI — Pittsburgh Sleep Quality Index (optional, all-or-nothing)."""

from __future__ import annotations

from django.db import models

from common.models import BaseModel

COMPONENT_FIELDS: tuple[str, ...] = (
    "subjective_quality",
    "sleep_latency",
    "sleep_duration",
    "habitual_efficiency",
    "disturbances",
    "medication_use",
    "daytime_dysfunction",
)


class PSQI(BaseModel):
    """Seven component scores (0-3), global score 0-21. Higher = worse sleep."""

    study = models.OneToOneField(
        "studies.Study",
        on_delete=models.CASCADE,
        related_name="psqi",
    )
    subjective_quality = models.PositiveSmallIntegerField()
    sleep_latency = models.PositiveSmallIntegerField()
    sleep_duration = models.PositiveSmallIntegerField()
    habitual_efficiency = models.PositiveSmallIntegerField()
    disturbances = models.PositiveSmallIntegerField()
    medication_use = models.PositiveSmallIntegerField()
    daytime_dysfunction = models.PositiveSmallIntegerField()
    global_score = models.PositiveSmallIntegerField(editable=False)

    class Meta:
        db_table = "psqi"
        verbose_name = "PSQI"
        verbose_name_plural = "PSQI"

    def save(self, *args, **kwargs) -> None:  # type: ignore[override]
        self.global_score = sum(int(getattr(self, field)) for field in COMPONENT_FIELDS)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"PSQI[{self.study_id}] global={self.global_score}"
