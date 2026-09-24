"""
Interactive Test Ingestion Management Command.
Allows the user to test the entire Phase 2 pipeline hands-on:
1. Unpacks any provided or synthesized patient ZIP archive.
2. Saves all files into the database (StudyFile).
3. Predicts sleep stages and saves them into the database (SleepEpoch).
4. Calculates SQI metrics and saves them into the database (StudyMetricsSummary).
5. Generates an AI report and saves it into the database (ClinicalReport).
6. Displays the direct web browser link to view everything in Django Admin.

Usage:
  python manage.py test_ingestion
  python manage.py test_ingestion --zip /path/to/patient_data.zip
"""

import os
import json
import zipfile
import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

from apps.patients.models.patient import Patient, BiologicalSex
from apps.studies.models.study import SleepStudy, StudyStatus, StudyType
from apps.studies.models.study_file import StudyFile
from apps.hypnograms.models.epoch import SleepEpoch, SleepStage
from apps.metrics.models.study_metric import StudyMetricsSummary
from apps.reports.models.report import ClinicalReport
from infrastructure.storage.zip_extractor import ZipExtractor
from infrastructure.staging_service.client import StagingServiceClient
from infrastructure.metrics_service.client import MetricsServiceClient
from infrastructure.opencode.client import OpenCodeClient
from lib.contracts.study_dto import ClinicalContextDTO

User = get_user_model()

class Command(BaseCommand):
    help = "Hands-on test for Phase 2: Ingestion, Staging, SQI Metrics, and Report Generation."

    def add_arguments(self, parser):
        parser.add_argument(
            "--zip",
            type=str,
            help="Path to an existing patient ZIP archive. If omitted, a sample 180-epoch archive is synthesized.",
            default=None
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== SleepLens Hands-on Ingestion & Adapter Test ==="))

        # 1. Ensure a physician user exists
        physician, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@sleeplens.org", "first_name": "Admin", "last_name": "Doctor"}
        )

        # 2. Ensure a patient exists
        patient, _ = Patient.objects.get_or_create(
            mrn="MRN-TEST-USER-001",
            defaults={
                "first_name": "Hassan",
                "last_name": "Hosseini",
                "birth_date": datetime.date(1978, 11, 20),
                "biological_sex": BiologicalSex.MALE,
                "medical_history": "Complaints of unrefreshing sleep, partner reports intermittent snoring."
            }
        )
        self.stdout.write(f"✓ Patient: {patient.first_name} {patient.last_name} (MRN: {patient.mrn})")

        # 3. Create a SleepStudy session
        study = SleepStudy.objects.create(
            patient=patient,
            physician=physician,
            study_date=datetime.date.today(),
            study_type=StudyType.FULL_PSG,
            status=StudyStatus.UPLOADED
        )
        self.stdout.write(f"✓ Created SleepStudy Session (ID: {study.id})")

        # 4. Prepare ZIP archive
        zip_arg = options.get("zip")
        work_dir = Path(settings.MEDIA_ROOT) / "studies_work" / str(study.id)
        work_dir.mkdir(parents=True, exist_ok=True)
        zip_path = work_dir / "patient_archive.zip"

        if zip_arg and Path(zip_arg).exists():
            import shutil
            shutil.copyfile(zip_arg, zip_path)
            self.stdout.write(f"✓ Using user-provided ZIP archive: {zip_arg}")
        else:
            self._create_synthetic_zip(zip_path)
            self.stdout.write(f"✓ Synthesized test patient archive: {zip_path.name} (180 epochs / 90 mins)")

        # 5. Extract and Index Files
        self.stdout.write("\n--> Extracting archive & cataloging files...")
        extractor = ZipExtractor()
        extracted_dir = work_dir / "extracted"
        extracted_dtos = extractor.extract_and_catalog(zip_path, extracted_dir)
        study.extracted_path = str(extracted_dir)
        study.status = StudyStatus.EXTRACTING
        study.save()

        # Save StudyFile records
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
        StudyFile.objects.bulk_create(file_records)
        self.stdout.write(f"✓ Saved {len(file_records)} files into database table 'studies_studyfile'")

        # 6. Run Staging Adapter
        self.stdout.write("\n--> Running Staging Adapter (predicting sleep stages)...")
        study.status = StudyStatus.STAGING
        study.save()
        staging_client = StagingServiceClient()
        predictions = staging_client.predict_stages(extracted_dtos, extracted_dir)

        # Create mapping of epoch_index to StudyFile
        epoch_to_file = {f.epoch_index: f for f in StudyFile.objects.filter(study=study) if f.epoch_index is not None}

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
        SleepEpoch.objects.bulk_create(epoch_objects)
        study.total_epochs = len(epoch_objects)
        study.duration_minutes = study.total_epochs * 0.5
        study.save()
        self.stdout.write(f"✓ Saved {len(epoch_objects)} epoch predictions into database table 'hypnograms_sleepepoch'")

        # 7. Run Metrics & SQI Engine Adapter
        self.stdout.write("\n--> Calculating 7-category sleep metrics & SQI score...")
        study.status = StudyStatus.COMPUTING_METRICS
        study.save()
        metrics_client = MetricsServiceClient()
        metrics_dto = metrics_client.calculate_metrics(predictions)

        summary = StudyMetricsSummary.objects.create(
            study=study,
            sqi_score=metrics_dto.sqi_score,
            sqi_category=metrics_dto.sqi_category,
            metrics_data=metrics_dto.metrics_data,
            ai_raw_metrics=metrics_dto.metrics_data.copy(),
            category_summaries=metrics_dto.category_summaries,
            clinical_alerts=metrics_dto.clinical_alerts
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ SQI Score: {summary.sqi_score}/100 ({summary.sqi_category.upper()}) | "
                f"Sleep Efficiency: {summary.metrics_data.get('se_pct')}% | TST: {summary.metrics_data.get('tst_min')} min"
            )
        )

        # 8. Run OpenCode LLM Adapter to Generate Clinical Report
        self.stdout.write("\n--> Contacting OpenCode LLM for narrative clinical report...")
        study.status = StudyStatus.GENERATING_REPORT
        study.save()
        opencode_client = OpenCodeClient()
        session_id = opencode_client.create_session(f"Clinical Report - {patient.first_name} {patient.last_name}")

        context = ClinicalContextDTO(
            patient_mrn=patient.mrn,
            patient_name=f"{patient.first_name} {patient.last_name}",
            patient_age=47,
            patient_sex=patient.get_biological_sex_display(),
            medical_history=patient.medical_history,
            study_date=str(study.study_date),
            sqi_score=summary.sqi_score,
            sqi_category=summary.sqi_category,
            key_metrics=summary.metrics_data,
            clinical_alerts=summary.clinical_alerts
        )

        report_dict = opencode_client.generate_clinical_report(session_id, context)

        report = ClinicalReport.objects.create(
            study=study,
            llm_model_name="opencode/default",
            executive_summary=report_dict.get("executive_summary", ""),
            architecture_findings=report_dict.get("architecture_findings", ""),
            respiratory_and_micro_notes=report_dict.get("respiratory_and_micro_notes", ""),
            differential_diagnoses=report_dict.get("differential_diagnoses", []),
            clinical_recommendations=report_dict.get("clinical_recommendations", [])
        )
        study.status = StudyStatus.COMPLETED
        study.save()

        self.stdout.write(self.style.SUCCESS(f"✓ AI Clinical Report Generated and saved to database"))

        # 9. Provide direct instructions to inspect visually in web browser!
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== INGESTION & PIPELINE COMPLETE! ==="))
        self.stdout.write("You can now open your browser and visually inspect everything in Django Admin:")
        self.stdout.write(self.style.NOTICE("1. Run the server:  .venv/bin/python manage.py runserver"))
        self.stdout.write(self.style.NOTICE("2. Open in browser: http://127.0.0.1:8000/admin/"))
        self.stdout.write(f"3. Direct Links:")
        self.stdout.write(f"   • View Study Files ({len(file_records)} files):    http://127.0.0.1:8000/admin/studies/studyfile/?study__id__exact={study.id}")
        self.stdout.write(f"   • View Sleep Epochs ({len(epoch_objects)} epochs):  http://127.0.0.1:8000/admin/hypnograms/sleepepoch/?study__id__exact={study.id}")
        self.stdout.write(f"   • View SQI Metrics & Score:       http://127.0.0.1:8000/admin/metrics/studymetricssummary/{summary.id}/change/")
        self.stdout.write(f"   • View AI Clinical Report:        http://127.0.0.1:8000/admin/reports/clinicalreport/{report.id}/change/\n")

    def _create_synthetic_zip(self, zip_path: Path):
        with zipfile.ZipFile(zip_path, "w") as zf:
            for i in range(180):
                if i < 15:
                    stage = 0
                    m = {"delta_power_uv2": 10.5, "alpha_power_uv2": 44.0, "emg_rms_uv": 8.0}
                elif i < 30:
                    stage = 1
                    m = {"delta_power_uv2": 15.0, "theta_power_uv2": 30.0, "emg_rms_uv": 5.0}
                elif i < 100:
                    stage = 2
                    m = {"delta_power_uv2": 23.0, "sigma_power_uv2": 32.0, "spindles_count": 2, "emg_rms_uv": 3.2}
                elif i < 140:
                    stage = 3
                    m = {"delta_power_uv2": 70.0, "slow_wave_amp_uv": 85.0, "spindles_count": 1, "emg_rms_uv": 2.0}
                else:
                    stage = 4
                    m = {"theta_power_uv2": 34.0, "beta_power_uv2": 18.0, "spindles_count": 0, "emg_rms_uv": 1.3}

                data = {
                    "epoch_index": i,
                    "stage": stage,
                    "confidence": 0.92,
                    "metrics": m
                }
                zf.writestr(f"epochs/epoch_{i:04d}_report.json", json.dumps(data))
            zf.writestr("signals/raw_psg_fpz_cz.edf", b"RAW_PSG_CHANNEL_SIGNAL_BYTES")
            zf.writestr("metadata/demographics.csv", "Subject,Age,Sex\n101,47,Male\n")
