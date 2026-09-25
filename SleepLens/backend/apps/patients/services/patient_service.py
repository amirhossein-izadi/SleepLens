"""Explicit patient operations used by the API layer."""

from __future__ import annotations

from typing import Any

from rest_framework.exceptions import NotFound

from apps.patients.models import Patient


class PatientService:
    """Patient lifecycle operations."""

    @staticmethod
    def create_patient(*, owner: Any, **fields: Any) -> Patient:
        return Patient.objects.create(owner=owner, **fields)

    @staticmethod
    def get_owned_patient(*, owner: Any, patient_id: Any) -> Patient:
        """Return the user's patient or raise ``NotFound``."""
        patient = Patient.objects.filter(id=patient_id, owner=owner).first()
        if patient is None:
            raise NotFound("Patient not found.")
        return patient
