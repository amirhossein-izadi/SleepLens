"""Read serializer for studies."""

from __future__ import annotations

from django.urls import reverse
from rest_framework import serializers

from apps.studies.models import Study


class StudySerializer(serializers.ModelSerializer):
    """Study representation shown in list/detail endpoints."""

    patient = serializers.SerializerMethodField()
    psqi_taken = serializers.SerializerMethodField()
    psqi_global_score = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Study
        fields = [
            "id",
            "original_filename",
            "file_size",
            "download_url",
            "status",
            "status_message",
            "error_message",
            "patient",
            "duration_minutes",
            "n_epochs",
            "summary",
            "signal_quality",
            "psqi_taken",
            "psqi_global_score",
            "created_at",
            "started_at",
            "finished_at",
        ]
        read_only_fields = fields

    def get_download_url(self, study: Study) -> str:
        return reverse("studies_api:v1:studies-download", args=[study.id])

    def get_patient(self, study: Study) -> dict | None:
        patient = study.patient
        if patient is None:
            return None
        return {
            "id": str(patient.id),
            "full_name": patient.full_name,
            "sex": patient.sex,
            "birth_year": patient.birth_year,
        }

    def get_psqi_taken(self, study: Study) -> bool:
        return hasattr(study, "psqi")

    def get_psqi_global_score(self, study: Study) -> int | None:
        psqi = getattr(study, "psqi", None)
        return psqi.global_score if psqi is not None else None
