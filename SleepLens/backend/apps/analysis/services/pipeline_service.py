"""Bridge between the pure pipeline and the database.

Runs the night pipeline for a study and persists epochs, night features and
summary state. Failures mark the study as failed with a readable message —
they are never retried automatically (bad input stays bad).
"""

from __future__ import annotations

from typing import Any

import structlog
from django.db import transaction
from django.utils import timezone

from apps.analysis.pipeline.weights import MissingWeightsError
from apps.studies.models import NightFeatures, Study, StudyEpoch
from apps.studies.utils.choices import StudyStatus

logger = structlog.get_logger(__name__)


class PipelineService:
    """Study processing entry point used by the Celery task."""

    @staticmethod
    def process(study_id: str) -> None:
        """Run the full analysis for ``study_id`` and persist the result."""
        study = Study.objects.filter(id=study_id).first()
        if study is None:
            logger.warning("study_not_found", study_id=study_id)
            return

        study.status = StudyStatus.PROCESSING
        study.status_message = "Running sleep staging and sleep depth analysis."
        study.started_at = timezone.now()
        study.save(update_fields=["status", "status_message", "started_at", "updated_at"])
        logger.info("study_processing_started", study_id=study_id)

        try:
            # Lazy import: keeps the heavyweight ML stack (torch/pandas) out of
            # the web tier; only the Celery worker imports the pipeline.
            from apps.analysis.pipeline import run_night_pipeline

            recording_path = study.source_path or study.file.path
            result = run_night_pipeline(recording_path)
        except MissingWeightsError as exc:
            PipelineService._mark_failed(study, f"Model weights unavailable: {exc}")
            return
        except Exception as exc:  # noqa: BLE001 - any pipeline failure fails the study
            logger.exception("study_processing_failed", study_id=study_id, error=str(exc))
            PipelineService._mark_failed(study, str(exc))
            return

        PipelineService._persist(study, result)
        logger.info(
            "study_processing_finished",
            study_id=study_id,
            n_epochs=result.summary.get("sleep_pct"),
            review_pct=result.summary.get("needs_review_pct"),
        )

    @staticmethod
    def _persist(study: Study, result: Any) -> None:
        with transaction.atomic():
            study.epochs.all().delete()
            StudyEpoch.objects.bulk_create(
                [
                    StudyEpoch(
                        study=study,
                        epoch_index=epoch.epoch_index,
                        start_sec=epoch.start_sec,
                        stage=epoch.stage,
                        probabilities=epoch.probabilities,
                        confidence=epoch.confidence,
                        confidence_band=epoch.confidence_band,
                        needs_review=epoch.needs_review,
                        sdi=epoch.sdi,
                        rem_pred=epoch.rem_pred,
                    )
                    for epoch in result.epochs
                ],
                batch_size=1000,
            )
            NightFeatures.objects.update_or_create(
                study=study,
                defaults={
                    "values": result.features,
                    "not_assessable": result.not_assessable,
                },
            )
            study.status = StudyStatus.COMPLETED
            study.status_message = "Analysis complete."
            study.error_message = ""
            study.n_epochs = len(result.epochs)
            study.duration_minutes = result.duration_minutes
            study.summary = result.summary
            study.signal_quality = result.signal_quality
            study.finished_at = timezone.now()
            study.save(
                update_fields=[
                    "status",
                    "status_message",
                    "error_message",
                    "n_epochs",
                    "duration_minutes",
                    "summary",
                    "signal_quality",
                    "finished_at",
                    "updated_at",
                ]
            )

    @staticmethod
    def _mark_failed(study: Study, message: str) -> None:
        study.status = StudyStatus.FAILED
        study.status_message = "Analysis failed."
        study.error_message = message[:2000]
        study.finished_at = timezone.now()
        study.save(
            update_fields=[
                "status",
                "status_message",
                "error_message",
                "finished_at",
                "updated_at",
            ]
        )
        logger.error("study_marked_failed", study_id=str(study.id), error=message[:300])
