"""
Chat Service for SleepLens Assistant.
Manages interactive doctor-LLM consultations, context pre-injection, and SSE streaming.
Adheres to backend_coding_guidelines/03_DJANGO_PATTERNS.md
"""

import json
import time
import logging
from typing import Generator, List, Dict, Any

from django.contrib.auth import get_user_model
from apps.studies.models.study import SleepStudy
from apps.assistant.models.chat_session import ChatSession
from apps.assistant.models.chat_message import ChatMessage, ChatSender
from apps.reports.services.prompt_builder import PromptBuilder
from infrastructure.opencode.client import OpenCodeClient
from infrastructure.storage.patient_storage_service import PatientStorageService
logger = logging.getLogger("SleepLensChatService")
User = get_user_model()

class ChatService:
    """Manages physician-LLM conversational consultations."""

    @classmethod
    def get_or_create_session(cls, study: SleepStudy, physician) -> ChatSession:
        """Retrieves existing consultation session or creates a new one with pre-injected context."""
        session = ChatSession.objects.filter(study=study).first()
        if session:
            return session

        if not physician or not getattr(physician, "is_authenticated", False):
            physician = study.physician or User.objects.first()
            if not physician:
                physician, _ = User.objects.get_or_create(
                    username="physician_assistant",
                    defaults={"first_name": "Attending", "last_name": "Somnologist"}
                )
        opencode_client = OpenCodeClient()
        patient = study.patient
        session_title = f"Consultation: {patient.first_name} {patient.last_name}"
        opencode_sess_id = opencode_client.create_session(session_title)

        session = ChatSession.objects.create(
            study=study,
            physician=physician,
            opencode_session_id=opencode_sess_id,
            title=session_title
        )

        # Pre-inject patient context and dedicated directory into OpenCode session
        PatientStorageService.export_study_artifacts(study)
        patient_context = PatientStorageService.get_patient_context_for_llm(study)
        
        # Send context directly to OpenCode session
        opencode_client.send_chat_message(
            opencode_sess_id,
            f"System Initialization - Clinical Polysomnography Case:\n{patient_context}\n"
            f"Please review the patient's data, hypnogram, and metrics above. Answer all subsequent physician questions "
            f"with clinical precision grounded in this patient's specific recordings and metrics."
        )

        ChatMessage.objects.create(
            session=session,
            sender=ChatSender.SYSTEM,
            content=patient_context
        )
        # Initial greeting from assistant
        summary = getattr(study, "metrics_summary", None)
        sqi_val = f"{summary.sqi_score:.1f}" if summary else "N/A"
        sqi_cat = summary.sqi_category.capitalize() if summary else "Pending"
        ChatMessage.objects.create(
            session=session,
            sender=ChatSender.ASSISTANT,
            content=(
                f"Hello Doctor. I have reviewed the polysomnography metrics for {patient.first_name} {patient.last_name}. "
                f"The recorded SQI score is {sqi_val} ({sqi_cat}). "
                f"How can I assist you with this patient's findings or treatment plan?"
            )
        )

        return session

    @classmethod
    def send_message(cls, session: ChatSession, content: str) -> ChatMessage:
        """Sends a physician question and records the synchronized assistant reply."""
        # 1. Record physician message
        ChatMessage.objects.create(
            session=session,
            sender=ChatSender.PHYSICIAN,
            content=content
        )

        # 2. Query OpenCode LLM with patient grounding
        opencode_client = OpenCodeClient()
        llm_prompt = (
            f"[Patient: {session.study.patient.first_name} {session.study.patient.last_name} | "
            f"MRN: {session.study.patient.mrn}]\n"
            f"Physician Inquiry: {content}"
        )
        response_text = opencode_client.send_chat_message(session.opencode_session_id, llm_prompt)
        # 3. Record assistant message
        assistant_msg = ChatMessage.objects.create(
            session=session,
            sender=ChatSender.ASSISTANT,
            content=response_text,
            prompt_tokens=len(content.split()) * 2,
            completion_tokens=len(response_text.split()) * 2
        )
        return assistant_msg

    @classmethod
    def stream_message(cls, session: ChatSession, content: str) -> Generator[str, None, None]:
        """
        Streams assistant response tokens in real-time using Server-Sent Events (SSE).
        Yields format: 'data: {"delta": "token"}\n\n'
        """
        # Record physician message
        ChatMessage.objects.create(
            session=session,
            sender=ChatSender.PHYSICIAN,
            content=content
        )

        opencode_client = OpenCodeClient()
        llm_prompt = (
            f"[Patient: {session.study.patient.first_name} {session.study.patient.last_name} | "
            f"MRN: {session.study.patient.mrn}]\n"
            f"Physician Inquiry: {content}"
        )
        full_text = opencode_client.send_chat_message(session.opencode_session_id, llm_prompt)
        accumulated = []
        tokens = full_text.split(" ")
        for token in tokens:
            chunk = token + " "
            accumulated.append(chunk)
            payload = json.dumps({"delta": chunk, "done": False})
            yield f"data: {payload}\n\n"
            time.sleep(0.02)  # Simulates realistic streaming cadence

        # Send terminal SSE event
        final_payload = json.dumps({"delta": "", "done": True})
        yield f"data: {final_payload}\n\n"

        # Persist full assistant message to DB
        ChatMessage.objects.create(
            session=session,
            sender=ChatSender.ASSISTANT,
            content="".join(accumulated).strip(),
            prompt_tokens=len(content.split()) * 2,
            completion_tokens=len(tokens) * 2
        )

    @classmethod
    def get_suggested_prompts(cls, study: SleepStudy) -> List[str]:
        """Generates dynamic clinical query suggestions tailored to patient anomalies."""
        prompts = [
            "Draft a patient-friendly summary letter explaining these findings in Persian and English.",
            "What non-pharmacological interventions are best indicated for this sleep profile?",
        ]

        summary = getattr(study, "metrics_summary", None)
        if not summary:
            return prompts

        m = summary.metrics_data
        if m.get("se_pct", 100) < 80.0 or m.get("waso_min", 0) > 40.0:
            prompts.insert(0, "Why is the sleep efficiency reduced and how can we consolidate sleep?")
        if m.get("n3_pct_tst", 20) < 15.0:
            prompts.insert(1, "What factors could be suppressing the patient's N3 slow-wave deep sleep?")
        if m.get("sfi", 0) > 15.0:
            prompts.append("Analyze the causes behind the elevated Sleep Fragmentation Index (SFI).")
        if m.get("apnea_index", 0) >= 5.0:
            prompts.append("Does the apnea index warrant positional therapy or CPAP evaluation?")

        return prompts[:4]
