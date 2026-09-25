"""ClinicalReport — one generated markdown night-quality report (versioned)."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from common.models import BaseModel


class ClinicalReport(BaseModel):
    """An LLM-generated markdown report for a study.

    Rows are immutable versions: generating again appends a new report and the
    latest one wins. ``model_name`` and ``prompt_version`` record exactly what
    produced the text.
    """

    study = models.ForeignKey(
        "studies.Study",
        on_delete=models.CASCADE,
        related_name="clinical_reports",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clinical_reports",
    )
    markdown = models.TextField()
    model_name = models.CharField(max_length=120)
    prompt_version = models.CharField(max_length=20, default="v1")

    class Meta:
        db_table = "clinical_reports"
        verbose_name = "Clinical report"
        verbose_name_plural = "Clinical reports"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["study", "-created_at"])]

    def __str__(self) -> str:
        return f"report[{self.study_id}] {self.created_at:%Y-%m-%d %H:%M}"
