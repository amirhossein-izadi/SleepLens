"""
SleepEpoch serializers for SleepLens API.
Supports hypnogram visualization and physician manual stage corrections.
"""

from rest_framework import serializers
from apps.hypnograms.models.epoch import SleepEpoch, SleepStage

class SleepEpochSerializer(serializers.ModelSerializer):
    stage_display = serializers.CharField(source="get_stage_display", read_only=True)
    ai_predicted_stage_display = serializers.CharField(source="get_ai_predicted_stage_display", read_only=True)

    class Meta:
        model = SleepEpoch
        fields = [
            "id",
            "epoch_index",
            "start_seconds",
            "stage",
            "stage_display",
            "ai_predicted_stage",
            "ai_predicted_stage_display",
            "confidence",
            "is_manually_corrected",
            "correction_reason",
            "is_lights_off",
            "metrics",
        ]
        read_only_fields = fields

class EpochOverrideSerializer(serializers.Serializer):
    """Payload for overriding a single epoch stage."""
    stage = serializers.ChoiceField(choices=SleepStage.choices, required=True)
    correction_reason = serializers.CharField(max_length=255, required=False, default="", allow_blank=True)

class EpochBulkOverrideSerializer(serializers.Serializer):
    """Payload for overriding a range of epochs."""
    start_epoch = serializers.IntegerField(min_value=0, required=True)
    end_epoch = serializers.IntegerField(min_value=0, required=True)
    stage = serializers.ChoiceField(choices=SleepStage.choices, required=True)
    correction_reason = serializers.CharField(max_length=255, required=False, default="", allow_blank=True)

    def validate(self, attrs):
        if attrs["start_epoch"] > attrs["end_epoch"]:
            raise serializers.ValidationError({"end_epoch": "end_epoch must be greater than or equal to start_epoch."})
        return attrs
