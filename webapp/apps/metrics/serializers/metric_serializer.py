"""
Metric serializers for SleepLens API.
Handles dynamic JSONB metric payload, catalog definitions, and manual overrides.
"""

from rest_framework import serializers
from apps.metrics.models.study_metric import StudyMetricsSummary
from apps.metrics.models.metric_definition import MetricDefinition
from apps.metrics.models.metric_override import MetricOverride

class MetricDefinitionSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = MetricDefinition
        fields = [
            "key",
            "display_name",
            "category",
            "category_display",
            "unit",
            "normal_min",
            "normal_max",
            "description",
            "is_editable",
            "show_in_report",
            "display_order",
        ]
        read_only_fields = fields

class StudyMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyMetricsSummary
        fields = [
            "id",
            "study_id",
            "sqi_score",
            "sqi_category",
            "metrics_data",
            "ai_raw_metrics",
            "category_summaries",
            "overrides",
            "is_manually_adjusted",
            "clinical_alerts",
            "is_valid",
            "computed_at",
            "updated_at",
        ]
        read_only_fields = fields

class MetricOverrideWriteSerializer(serializers.Serializer):
    """Payload for physician manual override of a metric."""
    metric_key = serializers.CharField(max_length=64, required=True)
    adjusted_value = serializers.FloatField(required=True)
    clinical_rationale = serializers.CharField(required=True, min_length=5)
