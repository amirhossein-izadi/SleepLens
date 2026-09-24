from django.contrib import admin
from apps.metrics.models.study_metric import StudyMetricsSummary
from apps.metrics.models.metric_definition import MetricDefinition
from apps.metrics.models.metric_override import MetricOverride

@admin.register(StudyMetricsSummary)
class StudyMetricsSummaryAdmin(admin.ModelAdmin):
    list_display = ("study", "sqi_score", "sqi_category", "is_manually_adjusted", "is_valid", "computed_at")
    list_filter = ("sqi_category", "is_manually_adjusted", "is_valid")
    search_fields = ("study__id", "study__patient__mrn")
    readonly_fields = ("id", "computed_at", "updated_at")

@admin.register(MetricDefinition)
class MetricDefinitionAdmin(admin.ModelAdmin):
    list_display = ("key", "display_name", "category", "unit", "normal_min", "normal_max", "is_active", "show_in_report")
    list_filter = ("category", "is_active", "show_in_report")
    search_fields = ("key", "display_name")

@admin.register(MetricOverride)
class MetricOverrideAdmin(admin.ModelAdmin):
    list_display = ("study", "metric_key", "original_value", "adjusted_value", "physician", "created_at")
    list_filter = ("metric_key", "created_at")
    search_fields = ("study__id", "metric_key", "clinical_rationale")
    readonly_fields = ("id", "created_at")
