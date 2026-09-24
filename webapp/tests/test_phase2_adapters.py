"""
Phase 2 Automated Verification Suite.
Tests decoupled infrastructure adapters:
- ZipExtractor (Safe extraction, security guards, file cataloging)
- StagingServiceClient (30s epoch staging, AASM stages)
- MetricsServiceClient (SQI_METRICS.md calculations, SQI composite score)
- OpenCodeClient (Clinical prompt building, report parsing, session management)
"""

import io
import json
import zipfile
import pytest
from pathlib import Path

from infrastructure.storage.zip_extractor import ZipExtractor, SecurityException
from infrastructure.staging_service.client import StagingServiceClient
from infrastructure.metrics_service.client import MetricsServiceClient
from infrastructure.opencode.client import OpenCodeClient
from lib.contracts.study_dto import EpochPredictionDTO, ClinicalContextDTO

@pytest.fixture
def sample_zip(tmp_path) -> Path:
    """Generates a synthetic patient study ZIP with discrete epoch reports and raw files."""
    zip_file_path = tmp_path / "patient_study_sample.zip"
    
    with zipfile.ZipFile(zip_file_path, "w") as zf:
        # 1. Epoch 1 report
        ep1_data = {
            "epoch": 1,
            "stage": 0,
            "confidence": 0.94,
            "metrics": {"delta_power_uv2": 12.5, "alpha_power_uv2": 45.2, "emg_rms_uv": 8.1}
        }
        zf.writestr("epochs/epoch_0001.json", json.dumps(ep1_data))

        # 2. Epoch 2 report
        ep2_data = {
            "epoch": 2,
            "stage": 1,
            "confidence": 0.88,
            "metrics": {"delta_power_uv2": 18.2, "theta_power_uv2": 26.4, "emg_rms_uv": 5.4}
        }
        zf.writestr("epochs/epoch_0002.json", json.dumps(ep2_data))

        # 3. Epoch 3 report (N2 sleep with spindles)
        ep3_data = {
            "epoch": 3,
            "stage": 2,
            "confidence": 0.91,
            "metrics": {"delta_power_uv2": 24.0, "spindles_count": 2, "emg_rms_uv": 3.2}
        }
        zf.writestr("epochs/epoch_0003.json", json.dumps(ep3_data))

        # 4. Raw recording file
        zf.writestr("recordings/raw_psg.edf", b"MOCK_EDF_HEADER_DATA_12345")

        # 5. Demographics metadata
        zf.writestr("metadata/demographics.csv", "Subject,Age,Sex\n101,45,M\n")

    return zip_file_path


class TestPhase2Adapters:

    def test_zip_extractor_safe_extraction_and_catalog(self, sample_zip, tmp_path):
        """Verify ZipExtractor unpacks, hashes, and catalogs study files cleanly."""
        extractor = ZipExtractor()
        dest_dir = tmp_path / "extracted_study"
        
        extracted_dtos = extractor.extract_and_catalog(sample_zip, dest_dir)
        
        assert len(extracted_dtos) == 5
        
        # Check epoch report classification
        epoch_files = [f for f in extracted_dtos if f.file_type == "epoch_report"]
        assert len(epoch_files) == 3
        assert {f.epoch_index for f in epoch_files} == {1, 2, 3}

        # Check raw edf classification
        edf_files = [f for f in extracted_dtos if f.file_type == "raw_edf"]
        assert len(edf_files) == 1
        assert edf_files[0].file_name == "raw_psg.edf"

        # Verify SHA-256 hashes generated
        for f in extracted_dtos:
            assert len(f.file_hash_sha256) == 64
            assert (dest_dir / f.relative_path).exists()

    def test_zip_extractor_path_traversal_guard(self, tmp_path):
        """Verify security guard prevents path traversal attacks."""
        malicious_zip = tmp_path / "evil.zip"
        dest_dir = tmp_path / "sandbox"

        # Construct ZIP with ../ entry
        with zipfile.ZipFile(malicious_zip, "w") as zf:
            zf.writestr("../../evil_payload.txt", "Malicious Content")

        extractor = ZipExtractor()
        with pytest.raises(SecurityException, match="Path traversal detected"):
            extractor.extract_and_catalog(malicious_zip, dest_dir)

    def test_zip_extractor_file_count_guard(self, tmp_path):
        """Verify safety limit on excessive file count."""
        zip_path = tmp_path / "too_many_files.zip"
        dest_dir = tmp_path / "sandbox"

        with zipfile.ZipFile(zip_path, "w") as zf:
            for i in range(15):
                zf.writestr(f"file_{i}.txt", f"content {i}")

        extractor = ZipExtractor(max_files=10)  # Threshold set to 10
        with pytest.raises(SecurityException, match="safety threshold"):
            extractor.extract_and_catalog(zip_path, dest_dir)

    def test_staging_service_from_epoch_files(self, sample_zip, tmp_path):
        """Verify StagingServiceClient parses stages and micro-metrics from epoch files."""
        extractor = ZipExtractor()
        dest_dir = tmp_path / "study_staging"
        files = extractor.extract_and_catalog(sample_zip, dest_dir)

        staging_client = StagingServiceClient()
        predictions = staging_client.predict_stages(files, dest_dir)

        assert len(predictions) == 3
        assert predictions[0].stage == 0  # Wake
        assert predictions[1].stage == 1  # N1
        assert predictions[2].stage == 2  # N2
        assert predictions[2].metrics.get("spindles_count") == 2

    def test_staging_service_calibrated_hypnogram(self):
        """Verify StagingServiceClient generates 960 epochs of realistic AASM staging."""
        staging_client = StagingServiceClient()
        predictions = staging_client.predict_stages([], Path("/tmp"), total_epochs=960)

        assert len(predictions) == 960
        stages = {p.stage for p in predictions}
        # Must contain all 5 AASM sleep stages: 0=Wake, 1=N1, 2=N2, 3=N3, 4=REM
        assert stages == {0, 1, 2, 3, 4}

        # Check micro-metrics attached
        assert "delta_power_uv2" in predictions[0].metrics
        assert all(0.0 <= p.confidence <= 1.0 for p in predictions)

    def test_metrics_service_sqi_calculation(self):
        """Verify MetricsServiceClient calculates 7 categories and composite SQI score."""
        # Create a synthetic night: 10 Wake epochs, 20 N1, 80 N2, 40 N3, 30 REM = 180 epochs (90 min)
        epochs = []
        for i in range(10):
            epochs.append(EpochPredictionDTO(i, i * 30.0, 0, 0.95))
        for i in range(10, 30):
            epochs.append(EpochPredictionDTO(i, i * 30.0, 1, 0.90))
        for i in range(30, 110):
            epochs.append(EpochPredictionDTO(i, i * 30.0, 2, 0.92, {"spindles_count": 1, "delta_power_uv2": 22.0}))
        for i in range(110, 150):
            epochs.append(EpochPredictionDTO(i, i * 30.0, 3, 0.96, {"delta_power_uv2": 75.0}))
        for i in range(150, 180):
            epochs.append(EpochPredictionDTO(i, i * 30.0, 4, 0.91))

        client = MetricsServiceClient()
        dto = client.calculate_metrics(epochs)

        assert dto.sqi_score > 0.0
        assert dto.sqi_category in ("optimal", "good", "fair", "poor")
        
        # Verify continuity metrics
        assert dto.metrics_data["tib_min"] == 90.0
        assert dto.metrics_data["tst_min"] == 85.0
        assert dto.metrics_data["se_pct"] == round((170 / 180) * 100.0, 1)
        assert dto.metrics_data["sol_min"] == 5.0  # 10th epoch = 5 min

        # Verify architecture percentages
        assert dto.metrics_data["n3_pct_tst"] > 0
        assert dto.metrics_data["rem_pct_tst"] > 0
        assert "continuity" in dto.category_summaries
        assert "fragmentation" in dto.category_summaries

    def test_opencode_client_prompt_and_report_generation(self):
        """Verify OpenCodeClient session handling, prompt formatting, and clinical report output."""
        client = OpenCodeClient(base_url="http://127.0.0.1:4096")
        
        # 1. Test Session Creation (mock fallback if offline)
        session_id = client.create_session("Study Consultation Test")
        assert session_id is not None
        assert len(session_id) > 0

        # 2. Test Report Generation from Context
        context = ClinicalContextDTO(
            patient_mrn="MRN-TEST-101",
            patient_name="John Doe",
            patient_age=52,
            patient_sex="Male",
            medical_history="Snoring and daytime fatigue.",
            study_date="2026-09-24",
            sqi_score=78.5,
            sqi_category="good",
            key_metrics={"tst_min": 412.0, "se_pct": 82.5, "waso_min": 48.0, "n3_pct_tst": 16.5, "apnea_index": 6.2},
            clinical_alerts=["Elevated WASO (> 45 min)", "Mild Apnea Index"]
        )

        report_dict = client.generate_clinical_report(session_id, context)
        assert "executive_summary" in report_dict
        assert "architecture_findings" in report_dict
        assert "differential_diagnoses" in report_dict
        assert "clinical_recommendations" in report_dict
        assert len(report_dict["clinical_recommendations"]) > 0

        # 3. Test Interactive Chat Inquiry
        reply = client.send_chat_message(session_id, "What caused the elevated WASO?")
        assert len(reply) > 20
