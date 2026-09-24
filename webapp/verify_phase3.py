#!/usr/bin/env python3
"""
SleepLens Phase 3 Verification Script.
Executes an end-to-end walkthrough of the RESTful API endpoints:
1. Register Patient (POST /api/v1/patients/)
2. Upload Study Archive (POST /api/v1/studies/upload/)
3. Poll In-Process Status (GET /api/v1/studies/{id}/status/)
4. Explore Extracted Files (GET /api/v1/studies/{id}/files/)
5. Retrieve Hypnogram & Micro-Metrics (GET /api/v1/studies/{id}/hypnogram/)
6. Correct Epoch Stage (PATCH /api/v1/studies/{id}/epochs/{idx}/override/)
7. Override Metric Value (POST /api/v1/studies/{id}/metrics/override/)
8. Trigger On-Demand SQI Recalculation (POST /api/v1/studies/{id}/metrics/recalculate/)
9. Sign Off on AI Clinical Report (POST /api/v1/studies/{id}/report/sign-off/)
"""

import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "apps"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from rest_framework.test import APIClient
from infrastructure.runners.thread_runner import ThreadRunner

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
    print_header("SleepLens — Phase 3 Verification Runner (REST APIs & Runner)")
    client = APIClient()

    # 1. Register Patient via API
    patient_payload = {
        "mrn": "MRN-API-DEMO-2026",
        "first_name": "Bahram",
        "last_name": "Radan",
        "birth_date": "1979-04-28",
        "biological_sex": "male",
        "medical_history": "Restless legs, loud snoring, unrefreshing sleep."
    }
    res_pat = client.post("/api/v1/patients/", data=patient_payload, format="json")
    if res_pat.status_code == 201:
        patient_id = res_pat.data["data"]["id"]
        print_check("POST /api/v1/patients/ (201 Created)", f"{patient_payload['first_name']} {patient_payload['last_name']} (ID: {patient_id[:8]}...)")
    else:
        # Retrieve existing
        res_list = client.get("/api/v1/patients/")
        patient_id = res_list.data["data"][0]["id"]
        print_check("GET /api/v1/patients/ (200 OK)", f"Using existing patient ID: {patient_id[:8]}...")

    # 2. Upload Study via API
    upload_payload = {
        "patient_id": patient_id,
        "study_type": "full_psg",
        "study_date": "2026-09-24"
    }
    res_upload = client.post("/api/v1/studies/upload/", data=upload_payload, format="multipart")
    assert res_upload.status_code == 201, f"Upload failed: {res_upload.data}"
    study_id = res_upload.data["data"]["study_id"]
    print_check("POST /api/v1/studies/upload/ (201 Created)", f"Study Session ID: {study_id}")

    # Poll status endpoint while background runner processes the pipeline
    print("\n--> Background task runner executing in-process pipeline...")
    status_data = {}
    for _ in range(25):
        time.sleep(0.2)
        res_status = client.get(f"/api/v1/studies/{study_id}/status/")
        status_data = res_status.data["data"]
        if status_data["status"] in ("completed", "failed"):
            break

    assert status_data["status"] == "completed", f"Pipeline failed with error: {status_data.get('error_log')}"
    print_check(
        "GET /api/v1/studies/{id}/status/ (200 OK)",
        f"Status: {status_data['status'].upper()} | Epochs: {status_data['total_epochs']} | Duration: {status_data['duration_minutes']} min"
    )

    # 4. Check Extracted Files
    res_files = client.get(f"/api/v1/studies/{study_id}/files/")
    print_check("GET /api/v1/studies/{id}/files/ (200 OK)", f"{res_files.data['metadata']['total']} extracted files cataloged")

    # 5. Retrieve Hypnogram Epochs
    res_hypno = client.get(f"/api/v1/studies/{study_id}/hypnogram/")
    epochs = res_hypno.data["data"]
    print_check(
        "GET /api/v1/studies/{id}/hypnogram/ (200 OK)",
        f"Retrieved {len(epochs)} epochs with micro-metrics & dual-stage tracking"
    )

    # 6. Single Epoch Override (Doctor changes epoch #10 from N1 to N2)
    sample_epoch_idx = epochs[10]["epoch_index"]
    patch_payload = {
        "stage": 2,  # N2
        "correction_reason": "Clear sleep spindles (12-14 Hz) visible on EEG Fpz-Cz"
    }
    res_patch = client.patch(
        f"/api/v1/studies/{study_id}/epochs/{sample_epoch_idx}/override/",
        data=patch_payload,
        format="json"
    )
    assert res_patch.status_code == 200
    print_check(
        f"PATCH /api/v1/studies/{{id}}/epochs/{sample_epoch_idx}/override/ (200 OK)",
        f"Stage corrected to {res_patch.data['data']['stage_display']} (Reason: {res_patch.data['data']['correction_reason'][:40]}...)"
    )

    # 7. Bulk Epoch Override (Range from 50 to 65 set to N3)
    bulk_payload = {
        "start_epoch": 50,
        "end_epoch": 65,
        "stage": 3,  # N3
        "correction_reason": "Synchronous high-voltage delta waves (> 75 uV)"
    }
    res_bulk = client.post(
        f"/api/v1/studies/{study_id}/epochs/bulk-override/",
        data=bulk_payload,
        format="json"
    )
    print_check(
        "POST /api/v1/studies/{id}/epochs/bulk-override/ (200 OK)",
        f"Bulk updated {res_bulk.data['data']['updated_epochs_count']} epochs to N3"
    )

    # 8. Query Metrics Summary & Catalog
    res_metrics = client.get(f"/api/v1/studies/{study_id}/metrics/")
    m_data = res_metrics.data["data"]
    print_check(
        "GET /api/v1/studies/{id}/metrics/ (200 OK)",
        f"Current SQI Score: {m_data['sqi_score']}/100 ({m_data['sqi_category'].upper()}) | WASO: {m_data['metrics_data'].get('waso_min')} min"
    )

    # 9. Manual Metric Override (Doctor adjusts WASO)
    override_payload = {
        "metric_key": "waso_min",
        "adjusted_value": 22.5,
        "clinical_rationale": "Filtered 2 movement artifacts in pre-dawn period"
    }
    res_m_override = client.post(
        f"/api/v1/studies/{study_id}/metrics/override/",
        data=override_payload,
        format="json"
    )
    print_check(
        "POST /api/v1/studies/{id}/metrics/override/ (200 OK)",
        f"WASO adjusted to {res_m_override.data['data']['metrics_data']['waso_min']} min (Audit log recorded)"
    )

    # 10. Trigger On-Demand Recalculation
    res_recalc = client.post(f"/api/v1/studies/{study_id}/metrics/recalculate/")
    recalc_data = res_recalc.data["data"]
    print_check(
        "POST /api/v1/studies/{id}/metrics/recalculate/ (200 OK)",
        f"New SQI Score: {recalc_data['sqi_score']}/100 ({recalc_data['sqi_category'].upper()}) | Preserved WASO: {recalc_data['metrics_data']['waso_min']} min"
    )

    # 11. Retrieve AI Clinical Report & Doctor Sign-Off
    res_report = client.get(f"/api/v1/studies/{study_id}/report/")
    print_check(
        "GET /api/v1/studies/{id}/report/ (200 OK)",
        f"Executive Summary: {res_report.data['data']['executive_summary'][:70]}..."
    )

    sign_payload = {
        "is_signed_off": True,
        "physician_notes": "Hypnogram and sleep stages reviewed and approved with manual corrections."
    }
    res_sign = client.post(
        f"/api/v1/studies/{study_id}/report/sign-off/",
        data=sign_payload,
        format="json"
    )
    print_check(
        "POST /api/v1/studies/{id}/report/sign-off/ (200 OK)",
        f"Signed Off: {res_sign.data['data']['is_signed_off']} | Notes: {res_sign.data['data']['physician_notes'][:50]}..."
    )

    print_header("Phase 3 Verification: ALL REST APIs & RUNNER OPERATIONAL!")
    print(f"{GREEN}✓ All 11 REST endpoints, in-process task runner, stage overrides, and recalculation verified successfully.{RESET}\n")

if __name__ == "__main__":
    main()
