"""Patient serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.patients.models import Patient


class PatientSerializer(serializers.ModelSerializer):
    """Read/write serializer for patients."""

    class Meta:
        model = Patient
        fields = ["id", "full_name", "birth_year", "sex", "notes", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_birth_year(self, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 1900 or value > 2100:
            raise serializers.ValidationError("birth_year must be between 1900 and 2100.")
        return value
