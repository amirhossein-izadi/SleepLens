"""
Report Generator Service for SleepLens.
Coordinates context construction, OpenCode LLM dispatch, and ClinicalReport persistence.
Adheres to backend_coding_guidelines/03_DJANGO_PATTERNS.md
"""

import logging
from apps.studies.models.study import SleepStudy
from apps.reports.models.report import ClinicalReport
from apps.reports.services.prompt_builder import PromptBuilder
from infrastructure.opencode.client import OpenCodeClient

logger = logging.getLogger("SleepLensReportGen")

class ReportGenerator:
    """Service for generating and regenerating clinical diagnostic reports."""

    @classmethod
    def generate_report_for_study(
        cls,
        study: SleepStudy,
        model_name: str = "opencode/default"
    ) -> ClinicalReport:
        context = PromptBuilder.build_clinical_context(study)
        opencode_client = OpenCodeClient()

        session_id = opencode_client.create_session(f"Clinical Report - {context.patient_name}")
        report_data = opencode_client.generate_clinical_report(session_id, context)

        report, created = ClinicalReport.objects.update_or_create(
            study=study,
            defaults={
                "llm_model_name": model_name,
                "executive_summary": report_data.get("executive_summary", ""),
                "architecture_findings": report_data.get("architecture_findings", ""),
                "respiratory_and_micro_notes": report_data.get("respiratory_and_micro_notes", ""),
                "differential_diagnoses": report_data.get("differential_diagnoses", []),
                "clinical_recommendations": report_data.get("clinical_recommendations", []),
                "raw_markdown": report_data.get("raw_text", ""),
                "is_signed_off": False,  # Reset sign-off on regeneration
            }
        )

        # Synchronize report artifacts to patient directory
        from infrastructure.storage.patient_storage_service import PatientStorageService
        PatientStorageService.export_study_artifacts(study)

        action = "Generated" if created else "Regenerated"
        logger.info(f"{action} clinical report for study {study.id}")
        return report
