"""
Patient serializers for SleepLens API.
Separates read and write operations per backend_coding_guidelines/03_DJANGO_PATTERNS.md
"""

from rest_framework import serializers
from apps.patients.models.patient import Patient, BiologicalSex

class PatientReadSerializer(serializers.ModelSerializer):
    """Read serializer with all demographic details."""
    biological_sex_display = serializers.CharField(source="get_biological_sex_display", read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id",
            "mrn",
            "first_name",
            "last_name",
            "birth_date",
            "biological_sex",
            "biological_sex_display",
            "medical_history",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

class PatientWriteSerializer(serializers.ModelSerializer):
    """Write serializer for creating or updating patients."""
    biological_sex = serializers.CharField(required=False, default="other")

    class Meta:
        model = Patient
        fields = [
            "mrn",
            "first_name",
            "last_name",
            "birth_date",
            "biological_sex",
            "medical_history",
        ]

    def validate_mrn(self, value: str) -> str:
        return value.strip().upper()

    def validate_biological_sex(self, value: str) -> str:
        val = str(value).lower().strip()
        if val in ["m", "male", "مرد"]:
            return "male"
        if val in ["f", "female", "زن"]:
            return "female"
        return "other"
