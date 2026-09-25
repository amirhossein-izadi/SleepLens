"""ChatService — sessions grounded in study data and backed by opencode."""

from __future__ import annotations

from typing import Any

import structlog

from apps.assistant.models import ChatMessage, ChatSender, ChatSession
from apps.assistant.services.context import build_case_context
from apps.studies.services.results import build_features_payload
from infrastructure.opencode import OpenCodeClient, OpenCodeError

logger = structlog.get_logger(__name__)


class OpenCodeUnavailable(RuntimeError):
    """Raised when the local opencode server cannot be reached."""


class ChatService:
    """One consultation session per study; explicit, no signals, no fake fallbacks."""

    @staticmethod
    def _client() -> OpenCodeClient:
        return OpenCodeClient()

    @staticmethod
    def get_session(study: Any) -> ChatSession | None:
        return ChatSession.objects.filter(study=study).first()

    @staticmethod
    def get_or_create_session(*, study: Any, user: Any) -> ChatSession:
        """Return the study's consultation session, creating + grounding it once."""
        existing = ChatService.get_session(study)
        if existing is not None:
            return existing

        client = ChatService._client()
        if not client.is_available():
            raise OpenCodeUnavailable(
                "opencode server is not running (start it with: opencode serve --port 4096)."
            )

        title = f"SleepLens consultation — {study.original_filename}"
        try:
            opencode_id = client.create_session(title)
        except OpenCodeError as exc:
            raise OpenCodeUnavailable(str(exc)) from exc

        session = ChatSession.objects.create(
            study=study,
            user=user,
            opencode_session_id=opencode_id,
            title=title,
        )
        context = build_case_context(study)
        try:
            client.send_message(opencode_id, context)
            session.context_injected = True
            session.save(update_fields=["context_injected", "updated_at"])
        except OpenCodeError as exc:
            logger.warning("assistant_context_injection_failed", study_id=str(study.id), error=str(exc))
        ChatMessage.objects.create(session=session, sender=ChatSender.SYSTEM, content=context)
        logger.info("assistant_session_created", study_id=str(study.id), session=str(session.id))
        return session

    @staticmethod
    def send_message(*, session: ChatSession, content: str) -> ChatMessage:
        """Store the expert's question, ask opencode, store the reply."""
        ChatMessage.objects.create(session=session, sender=ChatSender.USER, content=content)
        client = ChatService._client()
        try:
            reply = client.send_message(
                session.opencode_session_id,
                f"[Study: {session.study.original_filename}]\nExpert question: {content}",
            )
        except OpenCodeError as exc:
            raise OpenCodeUnavailable(str(exc)) from exc
        message = ChatMessage.objects.create(
            session=session, sender=ChatSender.ASSISTANT, content=reply
        )
        logger.info("assistant_reply", study_id=str(session.study_id), chars=len(reply))
        return message

    @staticmethod
    def reset(*, study: Any) -> None:
        """Delete the local session and best-effort remove the opencode one."""
        session = ChatService.get_session(study)
        if session is None:
            return
        ChatService._client().delete_session(session.opencode_session_id)
        session.delete()

    @staticmethod
    def suggested_prompts(study: Any) -> list[str]:
        """Data-driven question chips (only for assessable signals)."""
        features = build_features_payload(study).get("values", {})
        ssc = features.get("ssc", {})
        sqi = features.get("sqi", {})
        summary = study.summary or {}

        prompts: list[str] = []
        se = ssc.get("se_pct")
        if isinstance(se, (int, float)) and se < 85:
            prompts.append("Why is sleep efficiency reduced, and how can sleep be consolidated?")
        n3 = ssc.get("n3_pct_tst")
        if isinstance(n3, (int, float)) and n3 < 15:
            prompts.append("What could be suppressing deep (N3) slow-wave sleep?")
        sfi = ssc.get("sfi")
        if isinstance(sfi, (int, float)) and sfi > 15:
            prompts.append("What drives the elevated fragmentation index in this night?")
        rb = sqi.get("sdi_rb")
        if isinstance(rb, (int, float)) and rb > 0.3:
            prompts.append("The depth model reports a high share of shallow sleep — how reliable is this?")
        review = summary.get("needs_review_pct")
        if isinstance(review, (int, float)) and review > 10:
            prompts.append("Which epochs need expert review, and what should I check in the signals?")
        prompts.append("Draft a patient-friendly summary of this night's findings.")
        return prompts[:4]
