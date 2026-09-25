"""Patient model — demographics used to interpret sleep quality norms."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from common.models import BaseModel


class BiologicalSex(models.TextChoices):
    """Sex used for age/sex-dependent sleep reference ranges."""

    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"
    UNKNOWN = "unknown", "Unknown"


class Patient(BaseModel):
    """A person whose studies are analyzed; owned by the uploading user."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patients",
    )
    full_name = models.CharField(max_length=255)
    birth_year = models.PositiveSmallIntegerField(null=True, blank=True)
    sex = models.CharField(
        max_length=10,
        choices=BiologicalSex.choices,
        default=BiologicalSex.UNKNOWN,
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "patients"
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
        ordering = ["full_name", "-created_at"]
        indexes = [models.Index(fields=["owner", "full_name"])]

    def __str__(self) -> str:
        return self.full_name
