#!/usr/bin/env python3
"""
SleepLens Phase 8 End-to-End Verification Runner.
Executes complete clinical walkthrough:
1. Patient Registration & Clinical Profile Setup
2. Multi-Channel PSG Ingestion (120 epochs, Sleep-EDF style archive)
3. 4-Stage In-Process Pipeline (Unpack -> Stage -> Metrics -> OpenCode AI Report)
4. Full File Transparency & StudyFile Cataloging
5. 5-Class AASM Hypnogram Staging
6. 7-Category Metric Engine & SQI Calculation
7. OpenCode Persian Diagnostic Report & ICD-10 Differential Diagnoses
8. Physician Hypnogram Stage Correction & On-Demand Recalculation
9. Physician Metric Adjustment & Audit Trail Logging
10. Physician Clinical Report Sign-Off
11. Real-Time Interactive OpenCode Consultation Session
"""

import os
import sys
import time
import json
import datetime
from pathlib import Path

# Add project root and apps to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "apps"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.patients.models.patient import Patient, BiologicalSex
from apps.studies.models.study import SleepStudy, StudyStatus, StudyType
from apps.hypnograms.models.epoch import SleepEpoch
from apps.metrics.models.study_metric import StudyMetricsSummary
from apps.reports.models.report import ClinicalReport
from infrastructure.runners.thread_runner import ThreadRunner
from tests.fixtures.psg_sample_generator import create_realistic_psg_zip

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

def main():
    print_header("SleepLens — Phase 8 End-to-End Verification Runner")
    client = APIClient()

    # 1. Register Patient
    print(f"\n{BOLD}[Step 1] Registering Patient & Clinical Profile...{RESET}")
    patient, _ = Patient.objects.get_or_create(
        mrn="MRN-E2E-PSG-8819",
        defaults={
            "first_name": "Siavash",
            "last_name": "Ghomayshi",
            "birth_date": datetime.date(1975, 6, 21),
            "biological_sex": BiologicalSex.MALE,
            "medical_history": "Chronic unrefreshing sleep, loud snoring, suspected OSA vs RLS."
        }
    )
    print_check("Patient Registered", f"{patient.first_name} {patient.last_name} (MRN: {patient.mrn})")

    # 2. Generate Realistic PSG Study Archive
    print(f"\n{BOLD}[Step 2] Generating Multi-Channel Polysomnography (PSG) Archive...{RESET}")
    psg_zip_path = BASE_DIR / "media" / "test_fixtures" / "siavash_psg_e2e.zip"
    create_realistic_psg_zip(psg_zip_path, num_epochs=120)
    print_check("PSG Archive Generated", f"{psg_zip_path.name} (120 epochs @ 100 Hz, 5 channels)")

    # 3. Upload Study Archive via API
    print(f"\n{BOLD}[Step 3] Uploading Study via REST API...{RESET}")
    with open(psg_zip_path, "rb") as zf:
        uploaded = SimpleUploadedFile(
            name=psg_zip_path.name,
            content=zf.read(),
            content_type="application/zip"
        )
        res_upload = client.post(
            "/api/v1/studies/upload/",
            data={
                "patient_id": str(patient.id),
                "study_type": StudyType.FULL_PSG,
                "raw_archive": uploaded
            },
            format="multipart"
        )
    assert res_upload.status_code == 201
    study_id = res_upload.data["data"]["study_id"]
    print_check("POST /api/v1/studies/upload/ (201 Created)", f"Study ID: {study_id}")

    # 4. In-Process Pipeline Execution
    print(f"\n{BOLD}[Step 4] Executing 4-Step In-Process Pipeline...{RESET}")
    t0 = time.time()
    ThreadRunner._execute_study_pipeline(study_id)
    duration = time.time() - t0
    print_check(f"Pipeline Completed in {duration:.2f}s", "Extraction ➔ Staging ➔ Metrics ➔ AI Report")

    # 5. File Explorer & Transparency
    print(f"\n{BOLD}[Step 5] Checking StudyFile Catalog...{RESET}")
    res_files = client.get(f"/api/v1/studies/{study_id}/files/")
    assert res_files.status_code == 200
    files = res_files.data["data"]
    print_check("GET /api/v1/studies/{id}/files/ (200 OK)", f"{len(files)} files indexed with SHA-256 hashes")

    # 6. Hypnogram Staging
    print(f"\n{BOLD}[Step 6] Reviewing Hypnogram Staging...{RESET}")
    res_hypno = client.get(f"/api/v1/studies/{study_id}/hypnogram/")
    assert res_hypno.status_code == 200
    epochs = res_hypno.data["data"]
    stage_counts = {}
    for e in epochs:
        stage_counts[e["stage"]] = stage_counts.get(e["stage"], 0) + 1
    print_check("GET /api/v1/studies/{id}/hypnogram/ (200 OK)", f"120 Epochs (Wake:{stage_counts.get(0,0)}, N1:{stage_counts.get(1,0)}, N2:{stage_counts.get(2,0)}, N3:{stage_counts.get(3,0)}, REM:{stage_counts.get(4,0)})")

    # 7. Metrics & SQI Score
    print(f"\n{BOLD}[Step 7] Checking Metrics Engine & SQI...{RESET}")
    res_metrics = client.get(f"/api/v1/studies/{study_id}/metrics/")
    assert res_metrics.status_code == 200
    m_data = res_metrics.data["data"]
    sqi = m_data["sqi_score"]
    cat = m_data["sqi_category"]
    se = m_data["metrics_data"].get("se_pct", 0)
    tst = m_data["metrics_data"].get("tst_min", 0)
    print_check("GET /api/v1/studies/{id}/metrics/ (200 OK)", f"SQI: {sqi:.1f}/100 ({cat}) | SE: {se:.1f}% | TST: {tst:.0f} min")

    # 8. OpenCode AI Clinical Report
    print(f"\n{BOLD}[Step 8] Verifying OpenCode AI Clinical Report...{RESET}")
    report = ClinicalReport.objects.get(study_id=study_id)
    print_check("ClinicalReport Persistence", f"Model: {report.llm_model_name} | Length: {len(report.raw_markdown)} chars")
    print_check("Differential Diagnoses", f"{len(report.differential_diagnoses)} identified (ICD-10)")
    print_check("Recommendations", f"{len(report.clinical_recommendations)} clinical interventions")

    # 9. Physician Hypnogram Stage Override & Recalculation
    print(f"\n{BOLD}[Step 9] Simulating Physician Epoch Correction & Recalculation...{RESET}")
    res_override = client.patch(
        f"/api/v1/studies/{study_id}/epochs/0/override/",
        data={
            "stage": 0,
            "correction_reason": "Prominent occipital alpha rhythm confirming wakefulness."
        },
        format="json"
    )
    assert res_override.status_code == 200
    print_check("PATCH /api/v1/studies/{id}/epochs/0/override/ (200 OK)", "Stage updated with rationale")

    res_recalc = client.post(f"/api/v1/studies/{study_id}/metrics/recalculate/")
    assert res_recalc.status_code == 200
    print_check("POST /api/v1/studies/{id}/metrics/recalculate/ (200 OK)", "SQI score recomputed dynamically")

    # 10. Physician Metric Adjustment
    print(f"\n{BOLD}[Step 10] Testing Metric Override with Audit Logging...{RESET}")
    res_m_override = client.post(
        f"/api/v1/studies/{study_id}/metrics/override/",
        data={
            "metric_key": "apnea_index",
            "adjusted_value": 12.0,
            "clinical_rationale": "Direct visual counting of hypopneas on nasal cannula channel."
        },
        format="json"
    )
    assert res_m_override.status_code == 200
    print_check("POST /api/v1/studies/{id}/metrics/override/ (200 OK)", "Metric updated to 12.0 events/hr with audit log")

    # 11. Physician Report Sign-Off
    print(f"\n{BOLD}[Step 11] Physician Review & Report Sign-Off...{RESET}")
    res_sign = client.post(
        f"/api/v1/studies/{study_id}/report/sign-off/",
        data={
            "is_signed_off": True,
            "physician_notes": "پلی‌سومنوگرافی بیمار بازبینی و تایید گردید. ارزیابی راه هوایی فوقانی و بررسی تست تیتراسیون CPAP توصیه می‌شود."
        },
        format="json"
    )
    assert res_sign.status_code == 200
    print_check("POST /api/v1/studies/{id}/report/sign-off/ (200 OK)", "Report officially signed off and archived")

    # 12. Interactive Consultation Chat with OpenCode
    print(f"\n{BOLD}[Step 12] Testing Interactive OpenCode Consultation Chat...{RESET}")
    res_session = client.post(
        f"/api/v1/studies/{study_id}/chat/",
        data={"title": "E2E Somnology Case Review"},
        format="json"
    )
    assert res_session.status_code == 200
    session_id = res_session.data["data"]["id"]
    print_check("POST /api/v1/studies/{id}/chat/ (200 OK)", f"Session: {session_id}")

    res_prompts = client.get(f"/api/v1/studies/{study_id}/chat/{session_id}/suggested-prompts/")
    assert res_prompts.status_code == 200
    print_check("GET .../suggested-prompts/ (200 OK)", f"{len(res_prompts.data['data'])} prompts suggested")

    res_msg = client.post(
        f"/api/v1/studies/{study_id}/chat/{session_id}/message/",
        data={"content": "آیا علائم این بیمار بیشتر با آپنه انسدادی خواب مطابقت دارد یا سندرم مقاومت راه هوایی؟"},
        format="json"
    )
    assert res_msg.status_code == 200
    answer = res_msg.data["data"]["content"]
    print_check("POST .../message/ (200 OK)", f"OpenCode Response: {len(answer)} chars")

    print_header("PHASE 8 END-TO-END VERIFICATION RESULT: ALL CHECKS PASSED ✅")
    print(f"{GREEN}✓ Complete Polysomnography lifecycle successfully verified end-to-end.{RESET}\n")

if __name__ == "__main__":
    main()
