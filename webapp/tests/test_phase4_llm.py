"""
Phase 4 Automated Verification Suite for OpenCode LLM Integration & Interactive Chat.
Tests:
- PromptBuilder context and clinical prompt generation
- ReportGenerator and report regeneration endpoint
- Chat session lifecycle & system context pre-injection
- Physician-LLM message exchange
- Server-Sent Events (SSE) token streaming
- Dynamic clinical prompt suggestions
"""

import pytest
import datetime
from rest_framework.test import APIClient
from rest_framework import status

from apps.patients.models.patient import Patient, BiologicalSex
from apps.studies.models.study import SleepStudy, StudyStatus, StudyType
from apps.metrics.models.study_metric import StudyMetricsSummary, SQICategory
from apps.reports.models.report import ClinicalReport
from apps.reports.services.prompt_builder import PromptBuilder
from apps.reports.services.report_generator import ReportGenerator

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def study_with_metrics(db):
    patient = Patient.objects.create(
        mrn="MRN-PHASE4-TEST-01",
        first_name="Maryam",
        last_name="Mirzakhani",
        birth_date=datetime.date(1986, 5, 12),
        biological_sex=BiologicalSex.FEMALE,
        medical_history="Fatigue, restless sleep, waking with dry mouth."
    )
    study = SleepStudy.objects.create(
        patient=patient,
        study_date=datetime.date(2026, 9, 24),
        study_type=StudyType.FULL_PSG,
        status=StudyStatus.COMPLETED,
        total_epochs=960,
        duration_minutes=480.0
    )
    StudyMetricsSummary.objects.create(
        study=study,
        sqi_score=72.4,
        sqi_category=SQICategory.FAIR,
        metrics_data={
            "tst_min": 380.0,
            "se_pct": 79.2,
            "waso_min": 58.0,
            "n3_pct_tst": 11.5,
            "rem_pct_tst": 21.0,
            "sfi": 19.4,
            "apnea_index": 7.2,
            "rem_atonia_ratio": 1.65,
        },
        category_summaries={
            "continuity": {"score": 79, "status": "BORDERLINE"},
            "fragmentation": {"score": 62, "status": "ABNORMAL"},
        },
        clinical_alerts=[
            "Suboptimal Sleep Efficiency (79.2% < 85%)",
            "Elevated WASO (58 min > 30 min)",
            "Deficit in Slow-Wave Deep Sleep (11.5% < 15%)"
        ]
    )
    return study

@pytest.mark.django_db
class TestPhase4LLMAndChat:

    def test_prompt_builder(self, study_with_metrics):
        """Test PromptBuilder generates formatted clinical context and prompt."""
        context = PromptBuilder.build_clinical_context(study_with_metrics)
        assert context.patient_name == "Maryam Mirzakhani"
        assert context.sqi_score == 72.4
        assert len(context.clinical_alerts) == 3

        prompt = PromptBuilder.build_report_prompt(context)
        assert "Maryam Mirzakhani" in prompt
        assert "72.4" in prompt
        assert "Suboptimal Sleep Efficiency" in prompt
        assert "INSTRUCTIONS:" in prompt

    def test_report_generator_and_api_regenerate(self, api_client, study_with_metrics):
        """Test clinical report generation and on-demand regeneration endpoint."""
        # 1. Generate report directly via service
        report = ReportGenerator.generate_report_for_study(study_with_metrics)
        assert report is not None
        assert report.study == study_with_metrics
        assert len(report.executive_summary) > 20
        assert len(report.differential_diagnoses) >= 1

        # 2. Test API Regeneration Endpoint (POST /api/v1/studies/{id}/report/regenerate/)
        res = api_client.post(f"/api/v1/studies/{study_with_metrics.id}/report/regenerate/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["success"] is True
        assert "executive_summary" in res.data["data"]

    def test_assistant_chat_session_creation(self, api_client, study_with_metrics):
        """Test initializing a doctor-LLM consultation chat session."""
        res = api_client.post(f"/api/v1/studies/{study_with_metrics.id}/chat/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["success"] is True
        session_data = res.data["data"]
        session_id = session_data["id"]
        assert session_id is not None

        # Verify initial context messages (system context + greeting)
        msg_res = api_client.get(f"/api/v1/studies/{study_with_metrics.id}/chat/{session_id}/messages/")
        assert msg_res.status_code == status.HTTP_200_OK
        messages = msg_res.data["data"]
        assert len(messages) >= 2
        assert any(m["sender"] == "system" for m in messages)
        assert any(m["sender"] == "assistant" for m in messages)

    def test_assistant_chat_message_turn(self, api_client, study_with_metrics):
        """Test sending a physician query and receiving a synchronized assistant answer."""
        # 1. Create session
        res = api_client.post(f"/api/v1/studies/{study_with_metrics.id}/chat/")
        session_id = res.data["data"]["id"]

        # 2. Send physician query
        query = {"content": "Could the deficit in N3 sleep explain her morning fatigue?"}
        msg_res = api_client.post(
            f"/api/v1/studies/{study_with_metrics.id}/chat/{session_id}/message/",
            data=query,
            format="json"
        )
        assert msg_res.status_code == status.HTTP_200_OK
        assert msg_res.data["success"] is True
        reply = msg_res.data["data"]
        assert reply["sender"] == "assistant"
        assert len(reply["content"]) > 10

    def test_assistant_sse_token_streaming(self, api_client, study_with_metrics):
        """Test real-time Server-Sent Events (SSE) streaming endpoint."""
        res = api_client.post(f"/api/v1/studies/{study_with_metrics.id}/chat/")
        session_id = res.data["data"]["id"]

        stream_url = f"/api/v1/studies/{study_with_metrics.id}/chat/{session_id}/stream/?prompt=Explain+the+WASO+metric"
        stream_res = api_client.get(stream_url)
        assert stream_res.status_code == status.HTTP_200_OK
        assert stream_res["Content-Type"] == "text/event-stream"

        # Read streaming generator content
        content = b"".join(stream_res.streaming_content).decode("utf-8")
        assert "data: " in content
        assert '"done": true' in content or '"done": True' in content

    def test_suggested_prompts_endpoint(self, api_client, study_with_metrics):
        """Test dynamic clinical prompt suggestions tailored to patient anomalies."""
        res = api_client.post(f"/api/v1/studies/{study_with_metrics.id}/chat/")
        session_id = res.data["data"]["id"]

        sugg_res = api_client.get(f"/api/v1/studies/{study_with_metrics.id}/chat/{session_id}/suggested-prompts/")
        assert sugg_res.status_code == status.HTTP_200_OK
        suggestions = sugg_res.data["data"]
        assert len(suggestions) > 0
        # Given low N3 and high WASO, should suggest targeted inquiries
        assert any("N3" in s or "efficiency" in s or "letter" in s for s in suggestions)
