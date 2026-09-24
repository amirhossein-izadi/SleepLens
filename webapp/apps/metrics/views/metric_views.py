"""
Metric views for SleepLens API.
Provides dynamic metrics summary, catalog metadata, manual overrides, and recalculation.
Adheres to backend_coding_guidelines/08_API_DESIGN.md
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.studies.models.study import SleepStudy
from apps.metrics.models.study_metric import StudyMetricsSummary
from apps.metrics.models.metric_definition import MetricDefinition
from apps.metrics.models.metric_override import MetricOverride
from apps.metrics.serializers.metric_serializer import (
    StudyMetricsSerializer,
    MetricDefinitionSerializer,
    MetricOverrideWriteSerializer,
)
from apps.studies.services.recalculation_service import RecalculationService
from common.responses import api_success, api_error

class MetricViewSet(viewsets.ViewSet):
    """Endpoints for study metrics, catalog metadata, physician overrides, and SQI recalculation."""

    @action(detail=False, methods=["GET"], url_path="catalog")
    def list_catalog(self, request: Request) -> Response:
        """
        Lists all active metric definitions and reference ranges.
        GET /api/v1/metrics/catalog/
        """
        definitions = MetricDefinition.objects.filter(is_active=True).order_by("category", "display_order")
        serializer = MetricDefinitionSerializer(definitions, many=True)
        return api_success(data=serializer.data, metadata={"total": definitions.count()})

    @action(detail=False, methods=["GET"], url_path=r"(?P<study_id>[^/.]+)/metrics")
    def get_study_metrics(self, request: Request, study_id=None) -> Response:
        """
        Retrieves the dynamic metrics summary and SQI score for a study.
        GET /api/v1/studies/{study_id}/metrics/
        """
        try:
            study = SleepStudy.objects.get(id=study_id)
        except SleepStudy.DoesNotExist:
            return api_error(code="NOT_FOUND", message=f"Study {study_id} not found", status_code=status.HTTP_404_NOT_FOUND)

        try:
            summary = StudyMetricsSummary.objects.get(study=study)
        except StudyMetricsSummary.DoesNotExist:
            return api_error(
                code="NOT_READY",
                message="Metrics have not yet been computed for this study. Check /status/.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        serializer = StudyMetricsSerializer(summary)
        return api_success(data=serializer.data)

    @action(detail=False, methods=["POST"], url_path=r"(?P<study_id>[^/.]+)/metrics/override")
    def override_metric(self, request: Request, study_id=None) -> Response:
        """
        Manually adjusts a specific metric with a clinical rationale.
        POST /api/v1/studies/{study_id}/metrics/override/
        """
        try:
            study = SleepStudy.objects.get(id=study_id)
        except SleepStudy.DoesNotExist:
            return api_error(code="NOT_FOUND", message=f"Study {study_id} not found", status_code=status.HTTP_404_NOT_FOUND)

        try:
            summary = StudyMetricsSummary.objects.get(study=study)
        except StudyMetricsSummary.DoesNotExist:
            return api_error(code="NOT_READY", message="No metrics summary found for this study.", status_code=status.HTTP_400_BAD_REQUEST)

        serializer = MetricOverrideWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(code="VALIDATION_ERROR", message="Invalid override data", details=[serializer.errors])

        metric_key = serializer.validated_data["metric_key"]
        adjusted_value = serializer.validated_data["adjusted_value"]
        rationale = serializer.validated_data["clinical_rationale"]

        original_value = summary.metrics_data.get(metric_key, 0.0)

        # 1. Update summary metrics_data and overrides log dict
        updated_metrics = summary.metrics_data.copy()
        updated_metrics[metric_key] = adjusted_value
        summary.metrics_data = updated_metrics
        summary.is_manually_adjusted = True

        overrides = summary.overrides.copy() if summary.overrides else {}
        overrides[metric_key] = {
            "original": original_value,
            "override": adjusted_value,
            "reason": rationale,
        }
        summary.overrides = overrides
        summary.save()

        # 2. Record permanent audit entry in MetricOverride
        if request.user and request.user.is_authenticated:
            physician = request.user
        else:
            from django.contrib.auth import get_user_model
            physician = get_user_model().objects.first()

        if physician:
            MetricOverride.objects.create(
                study=study,
                physician=physician,
                metric_key=metric_key,
                original_value=float(original_value),
                adjusted_value=float(adjusted_value),
                clinical_rationale=rationale
            )

        return api_success(
            data=StudyMetricsSerializer(summary).data,
            message=f"Metric '{metric_key}' adjusted from {original_value} to {adjusted_value}."
        )

    @action(detail=False, methods=["POST"], url_path=r"(?P<study_id>[^/.]+)/metrics/recalculate")
    def recalculate_metrics(self, request: Request, study_id=None) -> Response:
        """
        Recalculates dependent metrics and composite SQI score after epoch stage corrections.
        POST /api/v1/studies/{study_id}/metrics/recalculate/
        """
        try:
            study = SleepStudy.objects.get(id=study_id)
        except SleepStudy.DoesNotExist:
            return api_error(code="NOT_FOUND", message=f"Study {study_id} not found", status_code=status.HTTP_404_NOT_FOUND)

        try:
            summary = RecalculationService.recalculate_study_metrics(study)
        except Exception as e:
            return api_error(code="RECALCULATION_FAILED", message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

        return api_success(
            data=StudyMetricsSerializer(summary).data,
            message="Study metrics and SQI score recalculated successfully."
        )
