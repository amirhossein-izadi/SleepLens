"""Assistant consultation endpoints (opencode-backed).

One session per study, auto-created on first message. GET never creates the
session (it may not exist yet); availability is binary — a dead opencode
server returns 503 OPENCODE_UNAVAILABLE, never a fake reply.
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assistant.api.v1.serializers.chat import (
    ChatMessageCreateSerializer,
    ChatMessageSerializer,
    ChatSessionSerializer,
)
from apps.assistant.services.chat_service import ChatService, OpenCodeUnavailable
from apps.studies.services.study_service import StudyService


def _opencode_unavailable(exc: OpenCodeUnavailable) -> Response:
    return Response(
        {
            "success": False,
            "data": None,
            "error": {
                "code": "OPENCODE_UNAVAILABLE",
                "message": str(exc),
                "details": [],
            },
        },
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


def _session_payload(study) -> dict:
    """Shared shape for GET/POST of the consultation thread."""
    session = ChatService.get_session(study)
    if session is None:
        return {"study_id": str(study.id), "available": False, "session": None, "messages": []}
    messages = session.messages.all()
    return {
        "study_id": str(study.id),
        "available": True,
        "session": ChatSessionSerializer(session).data,
        "messages": ChatMessageSerializer(messages, many=True).data,
    }


class ChatView(APIView):
    """Consultation thread: read (GET), create (POST), reset (DELETE)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id="studies_chat_retrieve", summary="Consultation thread", tags=["Assistant"])
    def get(self, request: Request, study_id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=study_id)
        return Response(_session_payload(study))

    @extend_schema(operation_id="studies_chat_create", summary="Create (or re-fetch) the session", tags=["Assistant"])
    def post(self, request: Request, study_id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=study_id)
        if ChatService.get_session(study) is None:
            try:
                ChatService.get_or_create_session(study=study, user=request.user)
            except OpenCodeUnavailable as exc:
                return _opencode_unavailable(exc)
        return Response(_session_payload(study), status=status.HTTP_201_CREATED)

    @extend_schema(operation_id="studies_chat_reset", summary="Reset the consultation", tags=["Assistant"])
    def delete(self, request: Request, study_id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=study_id)
        ChatService.reset(study=study)
        return Response(_session_payload(study))


class ChatMessageView(APIView):
    """Send an expert question; auto-creates the session when missing."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="studies_chat_message",
        summary="Send a message and get the assistant reply",
        tags=["Assistant"],
        request=ChatMessageCreateSerializer,
    )
    def post(self, request: Request, study_id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=study_id)
        serializer = ChatMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = ChatService.get_session(study)
        if session is None:
            try:
                session = ChatService.get_or_create_session(study=study, user=request.user)
            except OpenCodeUnavailable as exc:
                return _opencode_unavailable(exc)

        try:
            reply = ChatService.send_message(session=session, content=serializer.validated_data["content"])
        except OpenCodeUnavailable as exc:
            return _opencode_unavailable(exc)
        return Response({"reply": ChatMessageSerializer(reply).data}, status=status.HTTP_201_CREATED)


class SuggestedPromptsView(APIView):
    """Data-driven question chips for this night."""

    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id="studies_chat_prompts", summary="Suggested questions", tags=["Assistant"])
    def get(self, request: Request, study_id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=study_id)
        return Response({"prompts": ChatService.suggested_prompts(study)})
