"""
Phase 1 Automated Verification Suite.
Tests domain models, dynamic JSONB metrics, file indexing, and physician overrides.
"""

import pytest
import datetime
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.patients.models.patient import Patient, BiologicalSex
from apps.studies.models.study import SleepStudy, StudyStatus, StudyType
from apps.studies.models.study_file import StudyFile, StudyFileType
from apps.hypnograms.models.epoch import SleepEpoch, SleepStage
from apps.metrics.models.study_metric import StudyMetricsSummary, SQICategory
from apps.metrics.models.metric_definition import MetricDefinition, MetricCategory
from apps.metrics.models.metric_override import MetricOverride
from apps.reports.models.report import ClinicalReport
from apps.assistant.models.chat_session import ChatSession
from apps.assistant.models.chat_message import ChatMessage, ChatSender

User = get_user_model()

@pytest.fixture
def physician(db):
    return User.objects.create_user(
        username="dr_somnologist",
        email="dr.somno@hospital.org",
        password="secure_password_123",
        first_name="Alice",
        last_name="Somno"
    )

@pytest.fixture
def patient(db):
    return Patient.objects.create(
        mrn="MRN-2026-90412",
        first_name="Jane",
        last_name="Doe",
        birth_date=datetime.date(1985, 4, 12),
        biological_sex=BiologicalSex.FEMALE,
        medical_history="Complaints of excessive daytime sleepiness and unrestful sleep."
    )

@pytest.fixture
def study(db, patient, physician):
    return SleepStudy.objects.create(
        patient=patient,
        physician=physician,
        study_date=datetime.date(2026, 9, 24),
        study_type=StudyType.FULL_PSG,
        status=StudyStatus.UPLOADED,
        total_epochs=960,
        duration_minutes=480.0,
        metadata={"sampling_rate_hz": 100, "channels": ["EEG Fpz-Cz", "EOG", "EMG"]}
    )

@pytest.mark.django_db
class TestPhase1DomainModels:

    def test_patient_creation_and_uuid7(self, patient):
        """Verify Patient model creation and UUID format."""
        assert patient.id is not None
        assert str(patient) == "Jane Doe (MRN: MRN-2026-90412)"
        assert patient.biological_sex == BiologicalSex.FEMALE
        
        # Test unique MRN constraint
        with pytest.raises(IntegrityError):
            Patient.objects.create(
                mrn="MRN-2026-90412",
                first_name="Duplicate",
                last_name="Test"
            )

    def test_study_and_study_file_indexing(self, study):
        """Verify SleepStudy state and StudyFile registration for epoch transparency."""
        assert study.status == StudyStatus.UPLOADED
        assert study.total_epochs == 960

        # Register extracted 30s epoch report files
        file1 = StudyFile.objects.create(
            study=study,
            file_name="epoch_0001_report.json",
            relative_path="epochs/epoch_0001_report.json",
            file_type=StudyFileType.EPOCH_REPORT,
            epoch_index=1,
            file_size_bytes=2048,
            preview_data={"dominant_freq": "alpha", "amplitude_uv": 45.2}
        )
        assert file1.id is not None
        assert file1.study == study
        assert study.files.count() == 1

    def test_sleep_epoch_staging_and_physician_override(self, study, physician):
        """
        Verify SleepEpoch creation with dual-state tracking
        (immutable AI prediction vs. physician manual correction).
        """
        epoch = SleepEpoch.objects.create(
            study=study,
            epoch_index=42,
            start_seconds=1260.0,
            stage=SleepStage.N1,
            ai_predicted_stage=SleepStage.WAKE,  # AI predicted Wake
            confidence=0.88,
            is_lights_off=True,
            metrics={
                "delta_power": 18.4,
                "alpha_power": 4.2,
                "spindles_count": 2,
                "emg_rms_uv": 3.8
            }
        )
        assert epoch.ai_predicted_stage == SleepStage.WAKE
        assert epoch.stage == SleepStage.N1
        assert epoch.is_manually_corrected is False
        assert epoch.metrics["spindles_count"] == 2
        assert epoch.metrics["delta_power"] == 18.4

        # Doctor reviews epoch #42 and manually corrects it to N2
        epoch.stage = SleepStage.N2
        epoch.is_manually_corrected = True
        epoch.corrected_by = physician
        epoch.corrected_at = datetime.datetime.now(datetime.timezone.utc)
        epoch.correction_reason = "Vertex sharp waves and sleep spindles observed"
        epoch.save()

        # Reload from database to verify persistence
        reloaded = SleepEpoch.objects.get(id=epoch.id)
        assert reloaded.stage == SleepStage.N2
        assert reloaded.ai_predicted_stage == SleepStage.WAKE  # Original AI baseline remains intact
        assert reloaded.is_manually_corrected is True
        assert reloaded.corrected_by == physician
        assert "Vertex sharp waves" in reloaded.correction_reason

    def test_dynamic_metrics_and_physician_override(self, study, physician):
        """
        Verify dynamic metrics JSONB storage (zero migrations for any number of metrics)
        and manual physician metric adjustments with audit trail.
        """
        # 1. Store initial AI-generated metrics with 10+ arbitrary parameters
        initial_metrics = {
            "tib_min": 480.0,
            "tst_min": 412.5,
            "se_pct": 85.9,
            "waso_min": 45.0,
            "sol_min": 18.5,
            "sfi": 12.4,
            "n3_pct_tst": 18.2,
            "swa_sum": 1950.4,
            "apnea_index": 4.2,
            "custom_experimental_score": 92.1  # Arbitrary metric
        }

        summary = StudyMetricsSummary.objects.create(
            study=study,
            sqi_score=82.5,
            sqi_category=SQICategory.GOOD,
            metrics_data=initial_metrics,
            ai_raw_metrics=initial_metrics.copy(),
            category_summaries={
                "continuity": {"score": 85, "status": "NORMAL"},
                "fragmentation": {"score": 80, "status": "NORMAL"},
                "architecture": {"score": 83, "status": "NORMAL"},
            },
            clinical_alerts=["Borderline WASO"]
        )

        assert summary.sqi_score == 82.5
        assert summary.metrics_data["custom_experimental_score"] == 92.1
        assert summary.is_manually_adjusted is False

        # 2. Doctor detects artifact in WASO and manually adjusts waso_min from 45.0 to 30.0
        new_metrics = summary.metrics_data.copy()
        new_metrics["waso_min"] = 30.0
        summary.metrics_data = new_metrics
        summary.is_manually_adjusted = True
        summary.overrides = {
            "waso_min": {
                "original": 45.0,
                "override": 30.0,
                "reason": "Exclusion of movement artifact during pre-dawn awakening.",
                "updated_by": str(physician.id)
            }
        }
        summary.save()

        # Log permanent audit entry in MetricOverride
        override_log = MetricOverride.objects.create(
            study=study,
            physician=physician,
            metric_key="waso_min",
            original_value=45.0,
            adjusted_value=30.0,
            clinical_rationale="Exclusion of movement artifact during pre-dawn awakening."
        )

        # Verify audit integrity
        assert summary.metrics_data["waso_min"] == 30.0
        assert summary.ai_raw_metrics["waso_min"] == 45.0  # Baseline preserved
        assert override_log.adjusted_value == 30.0
        assert study.metric_overrides.count() == 1

    def test_metric_definition_catalog(self, db):
        """Verify MetricDefinition catalog entries and queries."""
        MetricDefinition.objects.create(
            key="waso_min",
            display_name="Wake After Sleep Onset",
            category=MetricCategory.CONTINUITY,
            unit="min",
            normal_min=0.0,
            normal_max=30.0,
            description="Total wake time occurring post-onset."
        )

        entry = MetricDefinition.objects.get(key="waso_min")
        assert entry.display_name == "Wake After Sleep Onset"
        assert entry.category == MetricCategory.CONTINUITY
        assert entry.normal_max == 30.0

    def test_clinical_report_and_sign_off(self, study, physician):
        """Verify ClinicalReport creation, recommendations, and doctor sign-off."""
        report = ClinicalReport.objects.create(
            study=study,
            llm_model_name="opencode/claude-3.7-sonnet",
            executive_summary="The patient demonstrates preserved sleep architecture with mild sleep fragmentation.",
            architecture_findings="Normal REM latency with adequate slow wave sleep.",
            differential_diagnoses=["Mild Primary Insomnia", "Upper Airway Resistance Syndrome"],
            clinical_recommendations=["Cognitive Behavioral Therapy for Insomnia (CBT-I)", "Sleep hygiene protocol"]
        )

        assert report.is_signed_off is False
        assert len(report.clinical_recommendations) == 2

        # Doctor signs off on the report
        report.physician_notes = "Approved with agreement on CBT-I recommendation."
        report.is_signed_off = True
        report.signed_off_at = datetime.datetime.now(datetime.timezone.utc)
        report.save()

        reloaded_report = ClinicalReport.objects.get(id=report.id)
        assert reloaded_report.is_signed_off is True
        assert "Approved" in reloaded_report.physician_notes

    def test_assistant_chat_session_and_messages(self, study, physician):
        """Verify OpenCode interactive consultation chat session and message flow."""
        session = ChatSession.objects.create(
            study=study,
            physician=physician,
            opencode_session_id="opencode_sess_90412_abc",
            title="Analysis of Elevated WASO in Patient Jane Doe"
        )

        # Physician sends question
        msg1 = ChatMessage.objects.create(
            session=session,
            sender=ChatSender.PHYSICIAN,
            content="Could the elevated WASO be attributed to medication side effects?"
        )

        # AI Assistant answers
        msg2 = ChatMessage.objects.create(
            session=session,
            sender=ChatSender.ASSISTANT,
            content="Based on the patient's records, beta-blocker therapy can indeed contribute to sleep maintenance insomnia.",
            prompt_tokens=450,
            completion_tokens=65
        )

        assert session.messages.count() == 2
        assert msg1.sender == ChatSender.PHYSICIAN
        assert msg2.sender == ChatSender.ASSISTANT
