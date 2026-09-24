"""
Recalculation Service for SleepLens.
Re-computes dependent sleep metrics and SQI score after physician manual stage or metric edits.
Adheres to backend_coding_guidelines/03_DJANGO_PATTERNS.md
"""

import logging
from typing import Optional

from apps.studies.models.study import SleepStudy
from apps.hypnograms.models.epoch import SleepEpoch
from apps.metrics.models.study_metric import StudyMetricsSummary
from infrastructure.metrics_service.client import MetricsServiceClient
from lib.contracts.study_dto import EpochPredictionDTO

logger = logging.getLogger("SleepLensRecalculate")

class RecalculationService:
    """Handles on-demand recalculation of metrics and SQI score."""

    @classmethod
    def recalculate_study_metrics(cls, study: SleepStudy) -> StudyMetricsSummary:
        """
        Recalculates all study metrics and SQI score using current active epoch stages.
        Preserves original AI baseline while honoring active physician overrides.
        """
        epochs = SleepEpoch.objects.filter(study=study).order_by("epoch_index")
        if not epochs.exists():
            raise ValueError(f"No epochs found for study {study.id} to recalculate.")

        # Convert active database epochs to EpochPredictionDTOs
        prediction_dtos = [
            EpochPredictionDTO(
                epoch_index=e.epoch_index,
                start_seconds=e.start_seconds,
                stage=e.stage,  # Incorporates any physician manual stage correction
                confidence=e.confidence,
                metrics=e.metrics,
                is_lights_off=e.is_lights_off
            )
            for e in epochs
        ]

        # Calculate updated metrics using the metrics adapter
        metrics_client = MetricsServiceClient()
        calculated_dto = metrics_client.calculate_metrics(prediction_dtos)

        # Retrieve or create the StudyMetricsSummary
        summary, _ = StudyMetricsSummary.objects.get_or_create(
            study=study,
            defaults={
                "sqi_score": calculated_dto.sqi_score,
                "sqi_category": calculated_dto.sqi_category,
                "metrics_data": calculated_dto.metrics_data,
                "ai_raw_metrics": calculated_dto.metrics_data.copy(),
                "category_summaries": calculated_dto.category_summaries,
                "clinical_alerts": calculated_dto.clinical_alerts,
                "is_valid": True,
            }
        )

        # Update metrics_data with new calculations
        updated_metrics = calculated_dto.metrics_data.copy()

        # Re-apply any active physician metric overrides
        if summary.overrides:
            for key, override_info in summary.overrides.items():
                if isinstance(override_info, dict) and "override" in override_info:
                    updated_metrics[key] = float(override_info["override"])
                elif isinstance(override_info, (int, float)):
                    updated_metrics[key] = float(override_info)

        summary.metrics_data = updated_metrics
        summary.sqi_score = calculated_dto.sqi_score
        summary.sqi_category = calculated_dto.sqi_category
        summary.category_summaries = calculated_dto.category_summaries
        summary.clinical_alerts = calculated_dto.clinical_alerts
        summary.save()

        logger.info(f"Recalculated SQI for study {study.id}: {summary.sqi_score} ({summary.sqi_category})")
        return summary
