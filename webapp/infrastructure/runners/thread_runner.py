"""
In-Process Asynchronous Pipeline Runner for SleepLens.
Replaces Celery/Redis complexity with standard Python ThreadPoolExecutor.
Executes study ingestion, staging, SQI metrics extraction, and AI report generation.
"""

import os
import sys
import logging
import traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from django.db import connections
from django.conf import settings

logger = logging.getLogger("SleepLensRunner")

# Global in-process executor with 2 workers to keep concurrency bounded
_EXECUTOR: Optional[ThreadPoolExecutor] = None

def get_executor() -> ThreadPoolExecutor:
    global _EXECUTOR
    if _EXECUTOR is None:
        _EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="sleeplens_worker_")
    return _EXECUTOR

class ThreadRunner:
    """Manages background study processing pipelines."""

    @classmethod
    def dispatch_study_pipeline(cls, study_id: str):
        """Dispatches study processing to background thread pool."""
        executor = get_executor()
        executor.submit(cls._run_pipeline_safe, str(study_id))
        logger.info(f"Dispatched pipeline execution for study {study_id}")

    @classmethod
    def _run_pipeline_safe(cls, study_id: str):
        """Wrapper ensuring database connections are properly managed per thread."""
        try:
            cls._execute_study_pipeline(study_id)
        except Exception as e:
            logger.error(f"Fatal error processing study {study_id}: {e}\n{traceback.format_exc()}")
        finally:
            connections.close_all()

    @classmethod
    def _execute_study_pipeline(cls, study_id: str):
        from apps.studies.models.study import SleepStudy, StudyStatus
        from apps.studies.models.study_file import StudyFile
        from apps.hypnograms.models.epoch import SleepEpoch
        from apps.metrics.models.study_metric import StudyMetricsSummary
        from apps.reports.models.report import ClinicalReport
        from infrastructure.storage.zip_extractor import ZipExtractor
        from infrastructure.staging_service.client import StagingServiceClient
        from infrastructure.metrics_service.client import MetricsServiceClient
        from infrastructure.opencode.client import OpenCodeClient
        from lib.contracts.study_dto import ClinicalContextDTO

        try:
            study = SleepStudy.objects.get(id=study_id)
        except SleepStudy.DoesNotExist:
            logger.error(f"Study {study_id} does not exist.")
            return

        try:
            work_dir = Path(settings.MEDIA_ROOT) / "studies_work" / str(study.id)
            work_dir.mkdir(parents=True, exist_ok=True)
            extracted_dir = work_dir / "extracted"

            # ---------------------------------------------------------
            # Step 1: Extract Archive & Catalog Files
            # ---------------------------------------------------------
            study.status = StudyStatus.EXTRACTING
            study.save(update_fields=["status", "updated_at"])

            extractor = ZipExtractor()
            extracted_dtos = []

            # If raw_archive file exists on disk
            if study.raw_archive and os.path.exists(study.raw_archive.path):
                zip_path = Path(study.raw_archive.path)
                extracted_dtos = extractor.extract_and_catalog(zip_path, extracted_dir)
            else:
                # If no file uploaded, check if extracted_path already set or create empty dir
                extracted_dir.mkdir(parents=True, exist_ok=True)

            study.extracted_path = str(extracted_dir)
            study.save(update_fields=["extracted_path", "updated_at"])

            # Bulk create StudyFile records
            file_records = []
            for dto in extracted_dtos:
                file_records.append(
                    StudyFile(
                        study=study,
                        file_name=dto.file_name,
                        relative_path=dto.relative_path,
                        file_type=dto.file_type,
                        file_size_bytes=dto.file_size_bytes,
                        file_hash_sha256=dto.file_hash_sha256,
                        epoch_index=dto.epoch_index,
                        preview_data=dto.preview_data
                    )
                )
            if file_records:
                StudyFile.objects.bulk_create(file_records)

            # ---------------------------------------------------------
            # Step 2: Predict Sleep Stages (AASM 5-Class)
            # ---------------------------------------------------------
            study.status = StudyStatus.STAGING
            study.save(update_fields=["status", "updated_at"])

            staging_client = StagingServiceClient()
            predictions = staging_client.predict_stages(
                extracted_dtos,
                extracted_dir,
                total_epochs=study.total_epochs or (180 if not extracted_dtos else None)
            )

            # Map files to epoch indices
            epoch_to_file = {
                f.epoch_index: f for f in StudyFile.objects.filter(study=study) if f.epoch_index is not None
            }

            epoch_objects = []
            for p in predictions:
                epoch_objects.append(
                    SleepEpoch(
                        study=study,
                        file=epoch_to_file.get(p.epoch_index),
                        epoch_index=p.epoch_index,
                        start_seconds=p.start_seconds,
                        stage=p.stage,
                        ai_predicted_stage=p.stage,
                        confidence=p.confidence,
                        metrics=p.metrics,
                        is_lights_off=p.is_lights_off
                    )
                )
            # Delete any existing epochs and bulk create
            SleepEpoch.objects.filter(study=study).delete()
            SleepEpoch.objects.bulk_create(epoch_objects)

            study.total_epochs = len(epoch_objects)
            study.duration_minutes = round(study.total_epochs * 0.5, 1)
            study.save(update_fields=["total_epochs", "duration_minutes", "updated_at"])

            # ---------------------------------------------------------
            # Step 3: Compute SQI Metrics
            # ---------------------------------------------------------
            study.status = StudyStatus.COMPUTING_METRICS
            study.save(update_fields=["status", "updated_at"])

            metrics_client = MetricsServiceClient()
            metrics_dto = metrics_client.calculate_metrics(predictions)

            summary, _ = StudyMetricsSummary.objects.update_or_create(
                study=study,
                defaults={
                    "sqi_score": metrics_dto.sqi_score,
                    "sqi_category": metrics_dto.sqi_category,
                    "metrics_data": metrics_dto.metrics_data,
                    "ai_raw_metrics": metrics_dto.metrics_data.copy(),
                    "category_summaries": metrics_dto.category_summaries,
                    "clinical_alerts": metrics_dto.clinical_alerts,
                    "is_valid": True,
                }
            )

            # ---------------------------------------------------------
            # Step 4: Generate AI Clinical Report via OpenCode
            # ---------------------------------------------------------
            study.status = StudyStatus.GENERATING_REPORT
            study.save(update_fields=["status", "updated_at"])

            opencode_client = OpenCodeClient()
            session_id = opencode_client.create_session(f"Report for Study {study.id}")

            patient = study.patient
            context = ClinicalContextDTO(
                patient_mrn=patient.mrn,
                patient_name=f"{patient.first_name} {patient.last_name}",
                patient_age=45,
                patient_sex=patient.get_biological_sex_display(),
                medical_history=patient.medical_history,
                study_date=str(study.study_date),
                sqi_score=summary.sqi_score,
                sqi_category=summary.sqi_category,
                key_metrics=summary.metrics_data,
                clinical_alerts=summary.clinical_alerts
            )

            report_dict = opencode_client.generate_clinical_report(session_id, context)

            ClinicalReport.objects.update_or_create(
                study=study,
                defaults={
                    "llm_model_name": "opencode/default",
                    "executive_summary": report_dict.get("executive_summary", ""),
                    "architecture_findings": report_dict.get("architecture_findings", ""),
                    "respiratory_and_micro_notes": report_dict.get("respiratory_and_micro_notes", ""),
                    "differential_diagnoses": report_dict.get("differential_diagnoses", []),
                    "clinical_recommendations": report_dict.get("clinical_recommendations", [])
                }
            )

            # Pipeline Success!
            study.status = StudyStatus.COMPLETED
            study.error_log = ""
            study.save(update_fields=["status", "error_log", "updated_at"])
            logger.info(f"Pipeline completed successfully for study {study.id}")

        except Exception as exc:
            study.status = StudyStatus.FAILED
            study.error_log = f"{exc}\n{traceback.format_exc()}"
            study.save(update_fields=["status", "error_log", "updated_at"])
            logger.error(f"Pipeline failed for study {study.id}: {exc}")
