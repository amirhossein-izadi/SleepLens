"""Upload serializer for studies — optional patient link and PSQI."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.patients.services.patient_service import PatientService
from apps.studies.api.v1.serializers.psqi import PSQISerializer
from apps.studies.services.study_service import StudyService
from apps.studies.services.upload_validation import validate_study_upload


class StudyCreateSerializer(serializers.Serializer):
    """Write serializer for a new study upload.

    ``patient`` and ``psqi`` are optional. PSQI is all-or-nothing: send all
    seven 0-3 component scores or omit the field entirely (partial answers are
    rejected).
    """

    file = serializers.FileField()
    patient = serializers.UUIDField(required=False, allow_null=True)
    psqi = serializers.JSONField(required=False)

    def validate_file(self, value: Any) -> Any:
        validate_study_upload(value)
        return value

    def validate_patient(self, value: Any) -> Any:
        if value is None:
            return None
        request = self.context["request"]
        # Raises NotFound (404) when the patient belongs to someone else.
        self._patient = PatientService.get_owned_patient(owner=request.user, patient_id=value)
        return value

    def validate_psqi(self, value: Any) -> dict[str, int]:
        return PSQISerializer.validate_psqi_dict(value)

    def create(self, validated_data: dict[str, Any]) -> Any:
        request = self.context["request"]
        return StudyService.create_study(
            user=request.user,
            uploaded_file=validated_data["file"],
            patient=getattr(self, "_patient", None),
            psqi=validated_data.get("psqi"),
        )
