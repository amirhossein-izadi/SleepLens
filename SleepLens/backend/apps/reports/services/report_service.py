"""ReportService — gather the study payload, call the LLM, persist the markdown."""

from __future__ import annotations

from typing import Any

import structlog

from apps.reports.models import ClinicalReport
from apps.reports.services.prompt import PROMPT_VERSION, REFERENCE_HINTS, build_messages
from apps.studies.services.results import (
    build_features_payload,
    build_night_payload,
    build_psqi_payload,
    build_ssc_payload,
)
from infrastructure.llm import chat, get_llm_config

logger = structlog.get_logger(__name__)


class ReportService:
    """Generation and retrieval of clinical reports."""

    @staticmethod
    def latest(study: Any) -> ClinicalReport | None:
        return study.clinical_reports.order_by("-created_at").first()

    @staticmethod
    def build_context(study: Any) -> dict[str, Any]:
        """Everything the LLM may use — and nothing else."""
        night = build_night_payload(study)
        ssc = build_features_payload(study)
        stage_summary = build_ssc_payload(study).get("stage_summary", {})
        patient = getattr(study, "patient", None)
        return {
            "patient": (
                {
                    "full_name": patient.full_name,
                    "birth_year": patient.birth_year,
                    "sex": patient.sex,
                }
                if patient is not None
                else None
            ),
            "night": night,
            "stage_summary": stage_summary,
            "psqi": build_psqi_payload(study),
            "ssc_features": ssc.get("values", {}).get("ssc", {}),
            "sqi_features": ssc.get("values", {}).get("sqi", {}),
            "not_assessable": ssc.get("not_assessable", []),
            "signal_quality": night.get("signal_quality", {}),
            "reference_hints": REFERENCE_HINTS,
        }

    @staticmethod
    def generate(*, study: Any, user: Any) -> ClinicalReport:
        """Generate a new report version for the study and persist it."""
        context = ReportService.build_context(study)
        messages = build_messages(context)
        markdown = chat(messages)

        config = get_llm_config()
        report = ClinicalReport.objects.create(
            study=study,
            user=user,
            markdown=markdown,
            model_name=config.model,
            prompt_version=PROMPT_VERSION,
        )
        logger.info(
            "report_generated",
            study_id=str(study.id),
            report_id=str(report.id),
            model=config.model,
            chars=len(markdown),
        )
        return report
