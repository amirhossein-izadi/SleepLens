"""
Chat views for SleepLens Assistant.
Provides endpoints for doctor-LLM consultation sessions, message dispatch, and SSE streaming.
Adheres to backend_coding_guidelines/08_API_DESIGN.md
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from django.http import StreamingHttpResponse

from apps.studies.models.study import SleepStudy
from apps.assistant.models.chat_session import ChatSession
from apps.assistant.models.chat_message import ChatMessage
from apps.assistant.serializers.chat_serializer import (
    ChatSessionSerializer,
    ChatMessageSerializer,
    ChatMessageCreateSerializer,
)
from apps.assistant.services.chat_service import ChatService
from common.responses import api_success, api_error

class ChatViewSet(viewsets.ViewSet):
    """Endpoints for interactive consultations with OpenCode LLM."""

    @action(detail=False, methods=["POST"], url_path=r"(?P<study_id>[^/.]+)/chat")
    def get_or_create_session(self, request: Request, study_id=None) -> Response:
        """
        Creates or retrieves the consultation chat session for a study.
        POST /api/v1/studies/{study_id}/chat/
        """
        try:
            study = SleepStudy.objects.get(id=study_id)
        except SleepStudy.DoesNotExist:
            return api_error(code="NOT_FOUND", message=f"Study {study_id} not found", status_code=status.HTTP_404_NOT_FOUND)

        session = ChatService.get_or_create_session(study, request.user)
        serializer = ChatSessionSerializer(session)
        return api_success(
            data=serializer.data,
            message="Consultation session active with patient context pre-loaded.",
            status_code=status.HTTP_200_OK
        )

    @action(detail=False, methods=["GET"], url_path=r"(?P<study_id>[^/.]+)/chat/(?P<session_id>[^/.]+)/messages")
    def list_messages(self, request: Request, study_id=None, session_id=None) -> Response:
        """
        Retrieves dialogue history for a session.
        GET /api/v1/studies/{study_id}/chat/{session_id}/messages/
        """
        try:
            session = ChatSession.objects.get(id=session_id, study_id=study_id)
        except ChatSession.DoesNotExist:
            return api_error(code="NOT_FOUND", message="Session not found for this study", status_code=status.HTTP_404_NOT_FOUND)

        messages = session.messages.all().order_by("created_at")
        serializer = ChatMessageSerializer(messages, many=True)
        return api_success(data=serializer.data, metadata={"total": messages.count()})

    @action(detail=False, methods=["POST"], url_path=r"(?P<study_id>[^/.]+)/chat/(?P<session_id>[^/.]+)/message")
    def send_message(self, request: Request, study_id=None, session_id=None) -> Response:
        """
        Sends physician prompt and returns synchronized LLM response.
        POST /api/v1/studies/{study_id}/chat/{session_id}/message/
        """
        try:
            session = ChatSession.objects.get(id=session_id, study_id=study_id)
        except ChatSession.DoesNotExist:
            return api_error(code="NOT_FOUND", message="Session not found for this study", status_code=status.HTTP_404_NOT_FOUND)

        serializer = ChatMessageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(code="VALIDATION_ERROR", message="Invalid message content", details=[serializer.errors])

        content = serializer.validated_data["content"]
        assistant_msg = ChatService.send_message(session, content)
        return api_success(
            data=ChatMessageSerializer(assistant_msg).data,
            message="Assistant response generated successfully."
        )

    @action(detail=False, methods=["GET"], url_path=r"(?P<study_id>[^/.]+)/chat/(?P<session_id>[^/.]+)/stream")
    def stream_message(self, request: Request, study_id=None, session_id=None) -> Response:
        """
        Real-time Server-Sent Events (SSE) token stream for instantaneous response typing.
        GET /api/v1/studies/{study_id}/chat/{session_id}/stream/?prompt=...
        """
        try:
            session = ChatSession.objects.get(id=session_id, study_id=study_id)
        except ChatSession.DoesNotExist:
            return api_error(code="NOT_FOUND", message="Session not found for this study", status_code=status.HTTP_404_NOT_FOUND)

        prompt = request.query_params.get("prompt", "").strip()
        if not prompt:
            return api_error(code="VALIDATION_ERROR", message="Missing 'prompt' query parameter for stream.")

        stream_generator = ChatService.stream_message(session, prompt)
        response = StreamingHttpResponse(stream_generator, content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    @action(detail=False, methods=["GET"], url_path=r"(?P<study_id>[^/.]+)/chat/(?P<session_id>[^/.]+)/suggested-prompts")
    def suggested_prompts(self, request: Request, study_id=None, session_id=None) -> Response:
        """
        Returns dynamic clinical prompt chips tailored to this patient's anomalies.
        GET /api/v1/studies/{study_id}/chat/{session_id}/suggested-prompts/
        """
        try:
            session = ChatSession.objects.get(id=session_id, study_id=study_id)
        except ChatSession.DoesNotExist:
            return api_error(code="NOT_FOUND", message="Session not found for this study", status_code=status.HTTP_404_NOT_FOUND)

        suggestions = ChatService.get_suggested_prompts(session.study)
        return api_success(data=suggestions)
