"""
SleepLens Phase 8 End-to-End Test Suite.
Exercises full clinical lifecycle: PSG ingestion, staging, SQI metrics,
physician hypnogram override, recalculation, report sign-off, and OpenCode chat.
Adheres to backend_coding_guidelines/06_TESTING_GUIDELINES.md.
"""

import pytest
import datetime
from pathlib import Path
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.patients.models.patient import Patient, BiologicalSex
from apps.studies.models.study import SleepStudy, StudyStatus, StudyType
from apps.hypnograms.models.epoch import SleepEpoch
from apps.metrics.models.study_metric import StudyMetricsSummary
from apps.reports.models.report import ClinicalReport
from infrastructure.runners.thread_runner import ThreadRunner
from tests.fixtures.psg_sample_generator import create_realistic_psg_zip

@pytest.mark.django_db
class TestPhase8EndToEndPipeline:
    """Comprehensive End-to-End Integration Tests for SleepLens."""

    @pytest.fixture(autouse=True)
    def setup_client(self, tmp_path):
        self.client = APIClient()
        self.tmp_path = tmp_path

        # 1. Register test patient
        self.patient = Patient.objects.create(
            mrn="MRN-E2E-PSG-2026",
            first_name="Siavash",
            last_name="Ghomayshi",
            birth_date=datetime.date(1975, 6, 21),
            biological_sex=BiologicalSex.MALE,
            medical_history="Chronic unrefreshing sleep, loud snoring, suspected OSA."
        )

        # 2. Generate realistic PSG ZIP archive
        self.zip_path = tmp_path / "siavash_psg_study.zip"
        create_realistic_psg_zip(self.zip_path, num_epochs=120)

    def test_01_end_to_end_psg_ingestion_and_processing(self):
        """Tests complete study upload, extraction, staging, SQI metrics, and report."""
        with open(self.zip_path, "rb") as zf:
            uploaded = SimpleUploadedFile(
                name="siavash_psg_study.zip",
                content=zf.read(),
                content_type="application/zip"
            )
            # Patch dispatch to avoid background thread database lock on SQLite test db
            with patch.object(ThreadRunner, "dispatch_study_pipeline"):
                response = self.client.post(
                    "/api/v1/studies/upload/",
                    data={
                        "patient_id": str(self.patient.id),
                        "study_type": StudyType.FULL_PSG,
                        "raw_archive": uploaded
                    },
                    format="multipart"
                )

        assert response.status_code == 201
        study_id = response.data["data"]["study_id"]

        # Run in-process pipeline synchronously for the test
        ThreadRunner._execute_study_pipeline(study_id)

        # Assert Study Status
        study = SleepStudy.objects.get(id=study_id)
        assert study.status == StudyStatus.COMPLETED
        assert study.total_epochs == 120
        assert study.duration_minutes == 60.0

        # Assert File Cataloging (120 epochs + demographics + montage + annotations + referral)
        files_res = self.client.get(f"/api/v1/studies/{study_id}/files/")
        assert files_res.status_code == 200
        assert len(files_res.data["data"]) >= 120

        # Assert Hypnogram Staging
        hypno_res = self.client.get(f"/api/v1/studies/{study_id}/hypnogram/")
        assert hypno_res.status_code == 200
        epochs = hypno_res.data["data"]
        assert len(epochs) == 120
        # Check distribution
        stages = [e["stage"] for e in epochs]
        assert 0 in stages  # Wake
        assert 1 in stages  # N1
        assert 2 in stages  # N2
        assert 3 in stages  # N3
        assert 4 in stages  # REM

        # Assert SQI Metrics Calculation
        metrics_res = self.client.get(f"/api/v1/studies/{study_id}/metrics/")
        assert metrics_res.status_code == 200
        summary = metrics_res.data["data"]
        assert 0.0 <= summary["sqi_score"] <= 100.0
        assert summary["sqi_category"].lower() in ["optimal", "good", "fair", "poor"]
        assert "se_pct" in summary["metrics_data"]
        assert "tst_min" in summary["metrics_data"]
        assert "waso_min" in summary["metrics_data"]

        # Assert Clinical Report Generation
        report = ClinicalReport.objects.get(study=study)
        assert len(report.executive_summary) > 20
        assert len(report.architecture_findings) > 20
        assert report.is_signed_off is False

    def test_02_physician_epoch_override_and_sqi_recalculation(self):
        """Tests physician correcting an epoch and triggering on-demand SQI recalculation."""
        study = SleepStudy.objects.create(
            patient=self.patient,
            study_type=StudyType.FULL_PSG,
            study_date=datetime.date(2026, 9, 24),
            status=StudyStatus.COMPLETED,
            total_epochs=60,
            duration_minutes=30.0
        )
        # Create epochs: 50 N2, 10 Wake
        for i in range(60):
            stage = 2 if i < 50 else 0
            SleepEpoch.objects.create(
                study=study,
                epoch_index=i,
                start_seconds=i * 30.0,
                stage=stage,
                ai_predicted_stage=stage,
                confidence=0.92
            )

        # Compute initial metrics
        from apps.studies.services.recalculation_service import RecalculationService
        RecalculationService.recalculate_study_metrics(study)

        # Physician overrides epoch 0 from N2 to Wake (patient was clearly awake)
        override_res = self.client.patch(
            f"/api/v1/studies/{study.id}/epochs/0/override/",
            data={
                "stage": 0,
                "correction_reason": "Clear alpha rhythm visible on EEG Fpz-Cz"
            },
            format="json"
        )
        assert override_res.status_code == 200
        assert override_res.data["data"]["stage"] == 0
        assert override_res.data["data"]["is_manually_corrected"] is True

        # Trigger on-demand recalculation
        recalc_res = self.client.post(f"/api/v1/studies/{study.id}/metrics/recalculate/")
        assert recalc_res.status_code == 200
        new_metrics = recalc_res.data["data"]
        assert new_metrics["metrics_data"]["se_pct"] < 83.33

    def test_03_physician_metric_override_and_audit(self):
        """Tests manual adjustment of a clinical metric with audit recording."""
        study = SleepStudy.objects.create(
            patient=self.patient,
            study_type=StudyType.FULL_PSG,
            study_date=datetime.date(2026, 9, 24),
            status=StudyStatus.COMPLETED,
            total_epochs=120,
            duration_minutes=60.0
        )
        # Create epoch and compute initial metrics
        SleepEpoch.objects.create(study=study, epoch_index=0, start_seconds=0, stage=2, ai_predicted_stage=2)
        from apps.studies.services.recalculation_service import RecalculationService
        RecalculationService.recalculate_study_metrics(study)
        # Override apnea_index from baseline to 14.5
        override_res = self.client.post(
            f"/api/v1/studies/{study.id}/metrics/override/",
            data={
                "metric_key": "apnea_index",
                "adjusted_value": 14.5,
                "clinical_rationale": "Manual counting of hypopneas from nasal cannula channel."
            },
            format="json"
        )
        assert override_res.status_code == 200
        summary = StudyMetricsSummary.objects.get(study=study)
        assert summary.metrics_data["apnea_index"] == 14.5
        assert summary.is_manually_adjusted is True

    def test_04_physician_report_sign_off(self):
        """Tests physician clinical notes addition and final report sign-off."""
        study = SleepStudy.objects.create(
            patient=self.patient,
            study_type=StudyType.FULL_PSG,
            study_date=datetime.date(2026, 9, 24),
            status=StudyStatus.COMPLETED
        )
        report = ClinicalReport.objects.create(
            study=study,
            executive_summary="گزارش اولیه وضعیت خواب بیمار...",
            architecture_findings="معماری مراحل خواب...",
            is_signed_off=False
        )

        sign_off_res = self.client.post(
            f"/api/v1/studies/{study.id}/report/sign-off/",
            data={
                "is_signed_off": True,
                "physician_notes": "یافته‌ها بررسی و تایید شدند. شروع CBT-I توصیه می‌گردد."
            },
            format="json"
        )
        assert sign_off_res.status_code == 200
        report.refresh_from_db()
        assert report.is_signed_off is True
        assert report.signed_off_at is not None
        assert "CBT-I" in report.physician_notes

    def test_05_interactive_consultation_chat_lifecycle(self):
        """Tests physician consultation chat session, prompt suggestions, and turns."""
        study = SleepStudy.objects.create(
            patient=self.patient,
            study_type=StudyType.FULL_PSG,
            study_date=datetime.date(2026, 9, 24),
            status=StudyStatus.COMPLETED
        )

        # 1. Create Consultation Session
        session_res = self.client.post(
            f"/api/v1/studies/{study.id}/chat/",
            data={"title": "E2E Somnology Review"},
            format="json"
        )
        assert session_res.status_code == 200
        session_id = session_res.data["data"]["id"]

        # 2. Suggested Prompts
        prompts_res = self.client.get(f"/api/v1/studies/{study.id}/chat/{session_id}/suggested-prompts/")
        assert prompts_res.status_code == 200
        assert len(prompts_res.data["data"]) >= 2

        # 3. Send Doctor Question Turn
        msg_res = self.client.post(
            f"/api/v1/studies/{study.id}/chat/{session_id}/message/",
            data={"content": "Does the patient show signs of severe REM-related hypoxemia?"},
            format="json"
        )
        assert msg_res.status_code == 200
        assert "content" in msg_res.data["data"]
        assert len(msg_res.data["data"]["content"]) > 10
