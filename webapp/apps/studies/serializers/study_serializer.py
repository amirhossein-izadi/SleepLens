"""
SleepStudy serializers for SleepLens API.
Separates read, list, and upload operations per backend_coding_guidelines.
"""

from rest_framework import serializers
from apps.studies.models.study import SleepStudy, StudyStatus, StudyType
from apps.patients.serializers.patient_serializer import PatientReadSerializer

class StudyListSerializer(serializers.ModelSerializer):
    """Compact serializer for dashboard study tables."""
    patient = PatientReadSerializer(read_only=True)
    sqi_score = serializers.SerializerMethodField()
    sqi_category = serializers.SerializerMethodField()

    class Meta:
        model = SleepStudy
        fields = [
            "id",
            "patient",
            "study_date",
            "study_type",
            "status",
            "total_epochs",
            "duration_minutes",
            "sqi_score",
            "sqi_category",
            "created_at",
        ]
        read_only_fields = fields

    def get_sqi_score(self, obj: SleepStudy) -> float | None:
        if hasattr(obj, "metrics_summary") and obj.metrics_summary:
            return obj.metrics_summary.sqi_score
        return None

    def get_sqi_category(self, obj: SleepStudy) -> str | None:
        if hasattr(obj, "metrics_summary") and obj.metrics_summary:
            return obj.metrics_summary.sqi_category
        return None

class StudyDetailSerializer(serializers.ModelSerializer):
    """Comprehensive detail serializer for clinical workstation."""
    patient = PatientReadSerializer(read_only=True)
    sqi_score = serializers.SerializerMethodField()
    sqi_category = serializers.SerializerMethodField()

    class Meta:
        model = SleepStudy
        fields = [
            "id",
            "patient",
            "study_date",
            "study_type",
            "status",
            "raw_archive",
            "extracted_path",
            "total_epochs",
            "duration_minutes",
            "sqi_score",
            "sqi_category",
            "metadata",
            "error_log",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_sqi_score(self, obj: SleepStudy) -> float | None:
        if hasattr(obj, "metrics_summary") and obj.metrics_summary:
            return obj.metrics_summary.sqi_score
        return None

    def get_sqi_category(self, obj: SleepStudy) -> str | None:
        if hasattr(obj, "metrics_summary") and obj.metrics_summary:
            return obj.metrics_summary.sqi_category
        return None

class StudyUploadSerializer(serializers.Serializer):
    """Write serializer for uploading a patient study archive."""
    patient_id = serializers.UUIDField(required=True)
    study_date = serializers.DateField(required=False, allow_null=True)
    study_type = serializers.ChoiceField(choices=StudyType.choices, default=StudyType.FULL_PSG)
    raw_archive = serializers.FileField(required=False, allow_null=True)
