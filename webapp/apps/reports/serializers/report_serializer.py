"""
ClinicalReport serializers for SleepLens API.
"""

from rest_framework import serializers
from apps.reports.models.report import ClinicalReport

class ClinicalReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalReport
        fields = [
            "id",
            "study_id",
            "llm_model_name",
            "executive_summary",
            "architecture_findings",
            "respiratory_and_micro_notes",
            "differential_diagnoses",
            "clinical_recommendations",
            "physician_notes",
            "is_signed_off",
            "signed_off_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "study_id", "llm_model_name", "created_at", "updated_at"]

class ReportSignOffSerializer(serializers.Serializer):
    physician_notes = serializers.CharField(required=False, default="", allow_blank=True)
    is_signed_off = serializers.BooleanField(required=True)
