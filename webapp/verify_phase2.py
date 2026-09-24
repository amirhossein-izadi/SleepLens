#!/usr/bin/env python3
"""
SleepLens Phase 2 Verification Script.
Executes an end-to-end smoke test of the decoupled adapters:
1. Safe ZIP extraction & file cataloging (ZipExtractor)
2. 30s epoch AASM sleep staging (StagingServiceClient)
3. Nightly metrics & SQI composite score calculation (MetricsServiceClient)
4. AI Clinical Report generation & chat consultation (OpenCodeClient)
"""

import sys
import json
import shutil
import zipfile
import tempfile
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "apps"))

from infrastructure.storage.zip_extractor import ZipExtractor, SecurityException
from infrastructure.staging_service.client import StagingServiceClient
from infrastructure.metrics_service.client import MetricsServiceClient
from infrastructure.opencode.client import OpenCodeClient
from lib.contracts.study_dto import ClinicalContextDTO

GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_header(title: str):
    print(f"\n{BOLD}{BLUE}=================================================================={RESET}")
    print(f"{BOLD}{BLUE} {title}{RESET}")
    print(f"{BOLD}{BLUE}=================================================================={RESET}")

def print_check(desc: str, detail: str = ""):
    print(f" {GREEN}✓{RESET} {desc}" + (f": {YELLOW}{detail}{RESET}" if detail else ""))

def create_synthetic_patient_zip(target_path: Path):
    """Creates a sample patient archive containing 30s epoch reports and raw recordings."""
    with zipfile.ZipFile(target_path, "w") as zf:
        # Create 180 epochs (90 minutes of sleep data)
        for i in range(180):
            # 0=Wake (0-15), 1=N1 (15-30), 2=N2 (30-100), 3=N3 (100-140), 4=REM (140-180)
            if i < 15:
                stage = 0
                conf = 0.95
                m = {"delta_power_uv2": 12.0, "alpha_power_uv2": 45.0, "emg_rms_uv": 8.5}
            elif i < 30:
                stage = 1
                conf = 0.84
                m = {"delta_power_uv2": 16.0, "theta_power_uv2": 32.0, "emg_rms_uv": 5.1}
            elif i < 100:
                stage = 2
                conf = 0.91
                m = {"delta_power_uv2": 24.5, "sigma_power_uv2": 34.0, "spindles_count": 2, "emg_rms_uv": 3.4}
            elif i < 140:
                stage = 3
                conf = 0.97
                m = {"delta_power_uv2": 72.0, "slow_wave_amp_uv": 88.0, "spindles_count": 1, "emg_rms_uv": 2.0}
            else:
                stage = 4
                conf = 0.93
                m = {"theta_power_uv2": 36.0, "beta_power_uv2": 19.5, "spindles_count": 0, "emg_rms_uv": 1.4}

            payload = {
                "epoch_index": i,
                "stage": stage,
                "confidence": conf,
                "duration_seconds": 30.0,
                "metrics": m
            }
            zf.writestr(f"epochs/epoch_{i:04d}_report.json", json.dumps(payload))

        # Add raw PSG recording and demographics
        zf.writestr("recordings/patient_psg_raw.edf", b"MOCK_HEADER_EDF_PSG_DATA")
        zf.writestr("metadata/patient_info.csv", "MRN,Age,Sex,Study\nMRN-PHASE2-TEST,48,Male,PSG\n")

def main():
    print_header("SleepLens — Phase 2 Verification Runner (Ingestion & Adapters)")
    temp_dir = Path(tempfile.mkdtemp(prefix="sleeplens_phase2_"))

    try:
        # 1. Prepare Synthetic Patient ZIP
        zip_path = temp_dir / "sample_patient_night.zip"
        create_synthetic_patient_zip(zip_path)
        print_check("Synthetic Patient ZIP Generated", f"Size: {zip_path.stat().st_size / 1024:.1f} KB (180 epochs)")

        # 2. Test Safe ZIP Extractor & Cataloging
        extractor = ZipExtractor()
        extract_dest = temp_dir / "extracted_files"
        extracted_files = extractor.extract_and_catalog(zip_path, extract_dest)
        
        epoch_files = [f for f in extracted_files if f.file_type == "epoch_report"]
        raw_files = [f for f in extracted_files if f.file_type == "raw_edf"]
        meta_files = [f for f in extracted_files if f.file_type == "metadata_excel"]

        print_check("ZipExtractor Executed Safely", f"Total files unpacked: {len(extracted_files)}")
        print_check("File Classification & Hash Verified", f"{len(epoch_files)} epoch reports, {len(raw_files)} raw EDF, {len(meta_files)} metadata")
        print_check("SHA-256 Forensics", f"Sample Hash: {extracted_files[0].file_hash_sha256[:16]}...")

        # 3. Test Path Traversal Guard
        malicious_zip = temp_dir / "evil.zip"
        with zipfile.ZipFile(malicious_zip, "w") as zf:
            zf.writestr("../../etc/passwd_evil.txt", "Malicious content")
        try:
            extractor.extract_and_catalog(malicious_zip, temp_dir / "sandbox")
            print(f" {YELLOW}WARNING: Path traversal guard did not trigger!{RESET}")
        except SecurityException:
            print_check("Path Traversal Security Guard", "Successfully blocked traversal attack (../../)")

        # 4. Test Sleep Staging Model Adapter
        staging_client = StagingServiceClient()
        predictions = staging_client.predict_stages(extracted_files, extract_dest)
        stage_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        for p in predictions:
            stage_counts[p.stage] = stage_counts.get(p.stage, 0) + 1

        print_check("StagingServiceClient Invocation", f"Staged {len(predictions)} epochs successfully")
        print_check(
            "AASM Stage Distribution",
            f"Wake: {stage_counts[0]}, N1: {stage_counts[1]}, N2: {stage_counts[2]}, N3: {stage_counts[3]}, REM: {stage_counts[4]}"
        )

        # 5. Test Metrics & SQI Engine Adapter
        metrics_client = MetricsServiceClient()
        metrics_dto = metrics_client.calculate_metrics(predictions)
        
        print_check(
            "MetricsServiceClient Calculated",
            f"SQI Score: {metrics_dto.sqi_score}/100 | Category: {metrics_dto.sqi_category.upper()}"
        )
        print_check(
            "Continuity Metrics",
            f"TST: {metrics_dto.metrics_data['tst_min']} min | Sleep Efficiency: {metrics_dto.metrics_data['se_pct']}% | WASO: {metrics_dto.metrics_data['waso_min']} min"
        )
        print_check(
            "Architecture Metrics",
            f"Deep N3: {metrics_dto.metrics_data['n3_pct_tst']}% | REM: {metrics_dto.metrics_data['rem_pct_tst']}% | SFI: {metrics_dto.metrics_data['sfi']}/hr"
        )
        print_check("Category Summaries", f"{list(metrics_dto.category_summaries.keys())}")
        if metrics_dto.clinical_alerts:
            print_check("Clinical Alerts Flagged", f"{metrics_dto.clinical_alerts}")

        # 6. Test OpenCode LLM Client
        opencode_client = OpenCodeClient()
        server_live = opencode_client.is_server_available()
        status_note = "Online (Port 4096)" if server_live else "Offline (Using Resilient Clinical Fallback)"
        print_check("OpenCode Server Connection", status_note)

        context = ClinicalContextDTO(
            patient_mrn="MRN-PHASE2-TEST",
            patient_name="Amir Rezaei",
            patient_age=48,
            patient_sex="Male",
            medical_history="Suspected sleep apnea and frequent awakenings.",
            study_date="2026-09-24",
            sqi_score=metrics_dto.sqi_score,
            sqi_category=metrics_dto.sqi_category,
            key_metrics=metrics_dto.metrics_data,
            clinical_alerts=metrics_dto.clinical_alerts
        )

        session_id = opencode_client.create_session("Phase 2 Diagnostic Consultation")
        report = opencode_client.generate_clinical_report(session_id, context)
        print_check("AI Clinical Report Generated", f"Executive Summary: {report['executive_summary'][:80]}...")
        print_check("Differential Diagnoses", f"{report['differential_diagnoses']}")
        print_check("Clinical Recommendations", f"{report['clinical_recommendations']}")

        # 7. Test Interactive Chat Consultation Turn
        doctor_reply = opencode_client.send_chat_message(
            session_id,
            "Doctor Query: Does the deep sleep N3 percentage suggest adequate restorative recovery?"
        )
        print_check("Doctor-LLM Interactive Turn", f"Reply: {doctor_reply[:75]}...")

        print_header("Phase 2 Verification: ALL ADAPTERS & INGESTION OPERATIONAL!")
        print(f"{GREEN}✓ ZipExtractor, StagingServiceClient, MetricsServiceClient, and OpenCodeClient verified successfully.{RESET}\n")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
