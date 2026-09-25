"""PSQI write serializer — the questionnaire is all-or-nothing."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.studies.models.psqi import COMPONENT_FIELDS


class PSQISerializer(serializers.Serializer):
    """Seven component scores (0-3 each); partial submissions are rejected."""

    subjective_quality = serializers.IntegerField(min_value=0, max_value=3)
    sleep_latency = serializers.IntegerField(min_value=0, max_value=3)
    sleep_duration = serializers.IntegerField(min_value=0, max_value=3)
    habitual_efficiency = serializers.IntegerField(min_value=0, max_value=3)
    disturbances = serializers.IntegerField(min_value=0, max_value=3)
    medication_use = serializers.IntegerField(min_value=0, max_value=3)
    daytime_dysfunction = serializers.IntegerField(min_value=0, max_value=3)

    @staticmethod
    def validate_psqi_dict(value: Any) -> dict[str, int]:
        """Validate a PSQI dict coming from a JSON form field."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("psqi must be a JSON object.")
        missing = [field for field in COMPONENT_FIELDS if field not in value]
        if missing:
            raise serializers.ValidationError(
                "PSQI must be answered completely or not at all; missing: "
                + ", ".join(missing)
            )
        extra = [key for key in value if key not in COMPONENT_FIELDS]
        if extra:
            raise serializers.ValidationError("Unknown PSQI fields: " + ", ".join(extra))
        normalized: dict[str, int] = {}
        for field in COMPONENT_FIELDS:
            try:
                score = int(value[field])
            except (TypeError, ValueError) as exc:
                raise serializers.ValidationError(f"{field} must be an integer 0-3.") from exc
            if isinstance(value[field], bool) or not 0 <= score <= 3:
                raise serializers.ValidationError(f"{field} must be between 0 and 3.")
            normalized[field] = score
        return normalized
