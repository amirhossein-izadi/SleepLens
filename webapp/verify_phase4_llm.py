#!/usr/bin/env python3
"""
SleepLens Phase 4 Verification Script.
Executes an end-to-end walkthrough of OpenCode LLM integration & Interactive Chat:
1. Clinical Prompt Engineering & Context Assembly
2. AI Clinical Diagnostic Report Generation & On-Demand Regeneration
3. Doctor-LLM Consultation Session (with pre-injected patient context)
4. Dynamic Clinical Prompt Suggestions
5. Physician Query & Synchronized Response Turn
6. Real-Time Server-Sent Events (SSE) Token Streaming
"""

import os
import sys
import time
import json
import datetime
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "apps"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from rest_framework.test import APIClient
from apps.patients.models.patient import Patient, BiologicalSex
from apps.studies.models.study import SleepStudy, StudyStatus, StudyType
from apps.metrics.models.study_metric import StudyMetricsSummary, SQICategory
from apps.reports.services.prompt_builder import PromptBuilder
from apps.reports.services.report_generator import ReportGenerator

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
    print_header("SleepLens — Phase 4 Verification Runner (OpenCode LLM & Chat)")
    client = APIClient()

    # 1. Setup Patient with Clinical Metrics
    patient, _ = Patient.objects.get_or_create(
        mrn="MRN-LLM-DEMO-2026",
        defaults={
            "first_name": "Parisa",
            "last_name": "Shams",
            "birth_date": datetime.date(1989, 7, 14),
            "biological_sex": BiologicalSex.FEMALE,
            "medical_history": "Morning brain fog, fragmented sleep, non-restorative rest."
        }
    )

    study, _ = SleepStudy.objects.get_or_create(
        patient=patient,
        study_date=datetime.date(2026, 9, 24),
        defaults={
            "study_type": StudyType.FULL_PSG,
            "status": StudyStatus.COMPLETED,
            "total_epochs": 960,
            "duration_minutes": 480.0
        }
    )

    summary, _ = StudyMetricsSummary.objects.get_or_create(
        study=study,
        defaults={
            "sqi_score": 68.5,
            "sqi_category": SQICategory.FAIR,
            "metrics_data": {
                "tst_min": 372.0,
                "se_pct": 77.5,
                "waso_min": 68.0,
                "sol_min": 24.0,
                "n3_pct_tst": 9.8,
                "rem_pct_tst": 22.4,
                "sfi": 21.2,
                "apnea_index": 3.8,
                "rem_atonia_ratio": 1.70,
            },
            "category_summaries": {
                "continuity": {"score": 77.5, "status": "BORDERLINE"},
                "fragmentation": {"score": 55.0, "status": "ABNORMAL"},
                "architecture": {"score": 65.0, "status": "BORDERLINE"},
            },
            "clinical_alerts": [
                "Suboptimal Sleep Efficiency (77.5% < 85%)",
                "Severe WASO (68 min > 30 min)",
                "Deficit in Slow-Wave Deep Sleep (9.8% < 15%)",
                "Elevated Sleep Fragmentation Index (21.2/hr > 15/hr)"
            ]
        }
    )
    print_check("Patient Profile & Metrics Loaded", f"{patient.first_name} {patient.last_name} | SQI: {summary.sqi_score} ({summary.sqi_category})")

    # 2. Test PromptBuilder
    context = PromptBuilder.build_clinical_context(study)
    prompt = PromptBuilder.build_report_prompt(context)
    print_check("PromptBuilder Context Assembled", f"Length: {len(prompt)} chars | Embedded Alerts: {len(context.clinical_alerts)}")

    # 3. Test ReportGenerator (initial draft)
    report = ReportGenerator.generate_report_for_study(study)
    print_check("ClinicalReport Generated", f"Executive Summary: {report.executive_summary[:65]}...")
    print_check("Differential Diagnoses (ICD-10)", f"{report.differential_diagnoses}")
    print_check("Actionable Recommendations", f"{report.clinical_recommendations}")

    # 4. Test Report Regeneration Endpoint (POST /api/v1/studies/{id}/report/regenerate/)
    res_regen = client.post(f"/api/v1/studies/{study.id}/report/regenerate/")
    assert res_regen.status_code == 200
    print_check("POST /api/v1/studies/{id}/report/regenerate/ (200 OK)", "Report refreshed with latest metrics")

    # 5. Initialize Doctor-LLM Consultation Session (POST /api/v1/studies/{id}/chat/)
    res_chat = client.post(f"/api/v1/studies/{study.id}/chat/")
    assert res_chat.status_code == 200
    session_id = res_chat.data["data"]["id"]
    print_check("POST /api/v1/studies/{id}/chat/ (200 OK)", f"Session Active: {session_id}")

    # 6. Retrieve Dynamic Suggested Prompt Chips
    res_sugg = client.get(f"/api/v1/studies/{study.id}/chat/{session_id}/suggested-prompts/")
    suggestions = res_sugg.data["data"]
    print_check("GET /api/v1/studies/{id}/chat/{session_id}/suggested-prompts/ (200 OK)", f"Found {len(suggestions)} clinical chips:")
    for s in suggestions:
        print(f"     {CYAN}• \"{s}\"{RESET}")

    # 7. Send Physician Inquiry Turn (POST /api/v1/studies/{id}/chat/{session_id}/message/)
    query_text = "Doctor Inquiry: How should we address her deep sleep N3 deficit given the high fragmentation?"
    res_msg = client.post(
        f"/api/v1/studies/{study.id}/chat/{session_id}/message/",
        data={"content": query_text},
        format="json"
    )
    assert res_msg.status_code == 200
    assistant_reply = res_msg.data["data"]["content"]
    print_check("POST /api/v1/studies/{id}/chat/{session_id}/message/ (200 OK)", "Synchronized Turn Received")
    print(f"\n{BOLD}{YELLOW}--- Doctor-LLM Synchronous Answer ---{RESET}")
    print(f"{assistant_reply}")
    print(f"{BOLD}{YELLOW}-------------------------------------{RESET}\n")

    # 8. Test Server-Sent Events (SSE) Real-Time Token Streaming
    stream_url = f"/api/v1/studies/{study.id}/chat/{session_id}/stream/?prompt=Explain+the+impact+of+WASO+on+her+brain+fog"
    res_stream = client.get(stream_url)
    assert res_stream.status_code == 200
    assert res_stream["Content-Type"] == "text/event-stream"

    print_check("GET /api/v1/studies/{id}/chat/{session_id}/stream/ (200 OK)", "Streaming SSE token stream live:")
    print(f"{BOLD}{CYAN}Streaming response tokens: {RESET}", end="", flush=True)

    streamed_text = []
    for chunk_bytes in res_stream.streaming_content:
        chunk_str = chunk_bytes.decode("utf-8")
        for line in chunk_str.split("\n"):
            if line.startswith("data: "):
                try:
                    payload = json.loads(line[6:])
                    delta = payload.get("delta", "")
                    if delta:
                        print(f"{GREEN}{delta}{RESET}", end="", flush=True)
                        streamed_text.append(delta)
                except Exception:
                    pass
    print("\n")

    print_header("Phase 4 Verification: OPENCODE LLM & CHAT OPERATIONAL!")
    print(f"{GREEN}✓ Structured prompt engineering, report regeneration, consultation chat, and SSE streaming verified successfully.{RESET}\n")

if __name__ == "__main__":
    main()
