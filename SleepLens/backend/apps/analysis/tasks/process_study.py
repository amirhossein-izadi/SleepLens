"""Celery task: process one uploaded study end to end."""

from __future__ import annotations

import structlog
from celery import shared_task

from apps.analysis.services.pipeline_service import PipelineService

logger = structlog.get_logger(__name__)


@shared_task(name="analysis.process_study")
def process_study(study_id: str) -> dict:
    """Run staging + SDI + night features for one study.

    ``PipelineService.process`` records success/failure on the study row, so
    the task itself never raises (and therefore is not retried blindly).
    """
    logger.info("task_process_study_received", study_id=study_id)
    PipelineService.process(study_id)
    return {"study_id": study_id, "status": "handled"}
