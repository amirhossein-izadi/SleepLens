"""Study viewset — upload, filtered list, split result streams, signals, PSQI, reports."""

from __future__ import annotations

from django.http import FileResponse
from django.utils.dateparse import parse_date
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from apps.assistant.api.v1.serializers.chat import (
    ChatMessageCreateSerializer,
    ChatMessageSerializer,
    ChatSessionSerializer,
)
from apps.assistant.services.chat_service import ChatService, OpenCodeUnavailable
from apps.reports.services.report_service import ReportService
from apps.studies.api.v1.serializers.psqi import PSQISerializer
from apps.studies.api.v1.serializers.study import StudySerializer
from apps.studies.api.v1.serializers.study_create import StudyCreateSerializer
from apps.studies.models import Study
from apps.studies.services.results import (
    build_features_payload,
    build_night_payload,
    build_psqi_payload,
    build_sdi_payload,
    build_ssc_features_payload,
    build_ssc_payload,
    build_sqi_features_payload,
)
from apps.studies.services.signals import epoch_snippet, preview, recording_path
from apps.studies.services.study_service import StudyService
from infrastructure.llm import LLMError


def _float_param(request: Request, name: str, default: float | None) -> float | None:
    raw = request.query_params.get(name)
    if raw in (None, ""):
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValidationError({name: "Must be a number."}) from exc


def _int_param(request: Request, name: str, default: int) -> int:
    raw = request.query_params.get(name)
    if raw in (None, ""):
        return default
    try:
        return int(float(raw))
    except ValueError as exc:
        raise ValidationError({name: "Must be an integer."}) from exc


def _channels_param(request: Request) -> list[str] | None:
    values = request.query_params.getlist("channels")
    if not values:
        single = request.query_params.get("channels")
        values = [single] if single else []
    channels: list[str] = []
    for value in values:
        channels.extend(part.strip() for part in str(value).split(",") if part.strip())
    return channels or None

LIST_FILTERS = [
    OpenApiParameter(
        name="search", type=OpenApiTypes.STR, description="Filter by filename (contains)"
    ),
    OpenApiParameter(
        name="status",
        type=OpenApiTypes.STR,
        description="uploaded | processing | completed | failed",
    ),
    OpenApiParameter(name="date_from", type=OpenApiTypes.DATE, description="created_at >= date"),
    OpenApiParameter(name="date_to", type=OpenApiTypes.DATE, description="created_at <= date"),
    OpenApiParameter(
        name="ordering",
        type=OpenApiTypes.STR,
        description="created_at, -created_at (default), original_filename, status",
    ),
]


def _opencode_unavailable(message: str) -> Response:
    return Response(
        {
            "success": False,
            "data": None,
            "error": {"code": "OPENCODE_UNAVAILABLE", "message": message, "details": []},
        },
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


class StudyUploadThrottle(UserRateThrottle):
    scope = "study_upload"


class ReportGenerationThrottle(UserRateThrottle):
    scope = "report_generation"


class StudyViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Endpoints for a user's studies."""

    serializer_class = StudySerializer
    lookup_field = "id"

    def get_queryset(self):
        queryset = Study.objects.filter(user=self.request.user).select_related("patient")
        params = self.request.query_params

        search = params.get("search", "").strip()
        if search:
            queryset = queryset.filter(original_filename__icontains=search)

        status_value = params.get("status", "").strip()
        if status_value:
            queryset = queryset.filter(status=status_value)

        date_from = params.get("date_from", "").strip()
        if date_from:
            parsed = parse_date(date_from)
            if parsed is None:
                raise ValidationError({"date_from": "Use ISO format YYYY-MM-DD."})
            queryset = queryset.filter(created_at__date__gte=parsed)

        date_to = params.get("date_to", "").strip()
        if date_to:
            parsed = parse_date(date_to)
            if parsed is None:
                raise ValidationError({"date_to": "Use ISO format YYYY-MM-DD."})
            queryset = queryset.filter(created_at__date__lte=parsed)

        ordering = params.get("ordering", "-created_at").strip()
        allowed = {
            "created_at",
            "-created_at",
            "original_filename",
            "-original_filename",
            "status",
            "-status",
        }
        return queryset.order_by(ordering if ordering in allowed else "-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return StudyCreateSerializer
        return StudySerializer

    def get_throttles(self):
        if self.action == "create":
            return [StudyUploadThrottle()]
        if self.action == "report_generate":
            return [ReportGenerationThrottle()]
        return super().get_throttles()

    # ── upload / list ────────────────────────────────────────────────────────

    @extend_schema(
        operation_id="studies_list",
        summary="List studies (filter by filename, status, date; paginated)",
        tags=["Studies"],
        parameters=LIST_FILTERS,
        responses={200: StudySerializer(many=True)},
    )
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(
        operation_id="studies_create",
        summary="Upload a new study (optional patient link and full PSQI)",
        tags=["Studies"],
        request=StudyCreateSerializer,
        responses={201: StudySerializer},
    )
    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        study = serializer.save()
        return Response(StudySerializer(study).data, status=status.HTTP_201_CREATED)

    # ── night summary ────────────────────────────────────────────────────────

    @extend_schema(
        operation_id="studies_night",
        summary="Night summary item (stage table, review load, SDI metrics, window)",
        tags=["Analysis"],
    )
    @action(detail=True, methods=["get"])
    def night(self, request: Request, id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=id)
        return Response(build_night_payload(study))

    # ── per-frame streams (charts) ───────────────────────────────────────────

    @extend_schema(
        operation_id="studies_ssc",
        summary="Sleep stage classification per frame (stage, probabilities, confidence, review)",
        tags=["Analysis"],
    )
    @action(detail=True, methods=["get"])
    def ssc(self, request: Request, id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=id)
        return Response(build_ssc_payload(study))

    @extend_schema(
        operation_id="studies_sdi",
        summary="Sleep depth index per frame (sdi 0-1, REM flag)",
        tags=["Analysis"],
    )
    @action(detail=True, methods=["get"])
    def sdi(self, request: Request, id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=id)
        return Response(build_sdi_payload(study))

    # ── night-level feature groups ───────────────────────────────────────────

    @extend_schema(
        operation_id="studies_features_ssc",
        summary="Features derived from the staging stream (continuity, architecture, ...)",
        tags=["Analysis"],
    )
    @action(detail=True, methods=["get"], url_path="features/ssc")
    def features_ssc(self, request: Request, id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=id)
        return Response(build_ssc_features_payload(study))

    @extend_schema(
        operation_id="studies_features_sqi",
        summary="Features derived from the sleep-depth model (RB/AP/CV/SK/MDR/PR/APEn/DFA)",
        tags=["Analysis"],
    )
    @action(detail=True, methods=["get"], url_path="features/sqi")
    def features_sqi(self, request: Request, id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=id)
        return Response(build_sqi_features_payload(study))

    @extend_schema(
        operation_id="studies_features",
        summary="Both feature groups in one payload (report generator input)",
        tags=["Analysis"],
    )
    @action(detail=True, methods=["get"])
    def features(self, request: Request, id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=id)
        return Response(build_features_payload(study))

    # ── PSQI (optional questionnaire) ────────────────────────────────────────

    @extend_schema(
        operation_id="studies_psqi",
        summary="Get, set or remove the PSQI questionnaire (all-or-nothing)",
        tags=["Analysis"],
        request=PSQISerializer,
    )
    @action(detail=True, methods=["get", "put", "delete"])
    def psqi(self, request: Request, id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=id)
        if request.method.lower() == "get":
            return Response(build_psqi_payload(study))
        if request.method.lower() == "delete":
            if hasattr(study, "psqi"):
                study.psqi.delete()
            return Response(build_psqi_payload(study))

        serializer = PSQISerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        StudyService.set_psqi(user=request.user, study_id=id, components=serializer.validated_data)
        return Response(build_psqi_payload(study))

    # ── LLM report ───────────────────────────────────────────────────────────

    @extend_schema(
        operation_id="studies_report",
        summary="Latest generated markdown report (available=false when none)",
        tags=["Reports"],
    )
    @action(detail=True, methods=["get"])
    def report(self, request: Request, id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=id)
        latest = ReportService.latest(study)
        if latest is None:
            return Response({"study_id": str(study.id), "available": False, "markdown": None})
        return Response(
            {
                "study_id": str(study.id),
                "available": True,
                "markdown": latest.markdown,
                "model_name": latest.model_name,
                "prompt_version": latest.prompt_version,
                "generated_at": latest.created_at,
            }
        )

    @extend_schema(
        operation_id="studies_report_generate",
        summary="Generate a new LLM markdown report (features + PSQI + night summary)",
        tags=["Reports"],
        request=None,
    )
    @action(detail=True, methods=["post"], url_path="report/generate")
    def report_generate(self, request: Request, id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=id)
        try:
            report = ReportService.generate(study=study, user=request.user)
        except LLMError as exc:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "LLM_UNAVAILABLE",
                        "message": str(exc),
                        "details": [],
                    },
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {
                "study_id": str(study.id),
                "available": True,
                "markdown": report.markdown,
                "model_name": report.model_name,
                "prompt_version": report.prompt_version,
                "generated_at": report.created_at,
            },
            status=status.HTTP_201_CREATED,
        )

    # ── raw signals (frontend preview of the actual test) ────────────────────

    @extend_schema(
        operation_id="studies_signals",
        summary="Channel list + decimated preview of the actual recording",
        tags=["Signals"],
        parameters=[
            OpenApiParameter(name="channels", type=OpenApiTypes.STR, description="Comma-separated labels (default: first 8)"),
            OpenApiParameter(name="start_sec", type=OpenApiTypes.FLOAT),
            OpenApiParameter(name="duration_sec", type=OpenApiTypes.FLOAT, description="Default: to end (max 3600 s)"),
            OpenApiParameter(name="max_points", type=OpenApiTypes.INT, description="Default 1200 (min/max envelope when decimating)"),
        ],
    )
    @action(detail=True, methods=["get"])
    def signals(self, request: Request, id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=id)
        return Response(
            preview(
                study,
                channels=_channels_param(request),
                start_sec=_float_param(request, "start_sec", 0.0) or 0.0,
                duration_sec=_float_param(request, "duration_sec", None),
                max_points=_int_param(request, "max_points", 1200),
            )
        )

    @extend_schema(
        operation_id="studies_signal_epoch",
        summary="One 30-second epoch waveform for zoomed inspection",
        tags=["Signals"],
        parameters=[
            OpenApiParameter(name="channels", type=OpenApiTypes.STR),
            OpenApiParameter(name="points", type=OpenApiTypes.INT, description="Default 750 (stride-averaged)"),
        ],
    )
    @action(detail=True, methods=["get"], url_path=r"signals/(?P<epoch_index>\d+)")
    def signal_epoch(self, request: Request, id: str | None = None, epoch_index: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=id)
        return Response(
            epoch_snippet(
                study,
                epoch_index=int(epoch_index or 0),
                channels=_channels_param(request),
                points=_int_param(request, "points", 750),
            )
        )

    @extend_schema(
        operation_id="studies_download",
        summary="Download the uploaded recording file",
        tags=["Studies"],
    )
    @action(detail=True, methods=["get"])
    def download(self, request: Request, id: str | None = None) -> FileResponse:
        study = StudyService.get_user_study(user=request.user, study_id=id)
        path = recording_path(study)
        return FileResponse(
            open(path, "rb"),
            as_attachment=True,
            filename=study.original_filename,
        )

    # ── assistant (opencode-backed consultation) ─────────────────────────────

    @extend_schema(
        operation_id="studies_chat",
        summary="Consultation chat: GET session+history · POST create/get · DELETE reset",
        tags=["Assistant"],
    )
    @action(detail=True, methods=["get", "post", "delete"], url_path="chat")
    def chat(self, request: Request, id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=id)
        if request.method.lower() == "delete":
            ChatService.reset(study=study)
            return Response(
                {"study_id": str(study.id), "available": False, "session": None, "messages": []}
            )
        try:
            session = ChatService.get_or_create_session(study=study, user=request.user)
        except OpenCodeUnavailable as exc:
            return _opencode_unavailable(str(exc))
        messages = session.messages.all().order_by("created_at")
        return Response(
            {
                "study_id": str(study.id),
                "available": True,
                "session": ChatSessionSerializer(session).data,
                "messages": ChatMessageSerializer(messages, many=True).data,
            }
        )

    @extend_schema(
        operation_id="studies_chat_send",
        summary="Send an expert question; returns the assistant reply",
        tags=["Assistant"],
        request=ChatMessageCreateSerializer,
    )
    @action(detail=True, methods=["post"], url_path="chat/messages")
    def chat_messages(self, request: Request, id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=id)
        serializer = ChatMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            session = ChatService.get_or_create_session(study=study, user=request.user)
            message = ChatService.send_message(
                session=session, content=serializer.validated_data["content"]
            )
        except OpenCodeUnavailable as exc:
            return _opencode_unavailable(str(exc))
        return Response(ChatMessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        operation_id="studies_chat_suggestions",
        summary="Suggested question chips grounded in this study's data",
        tags=["Assistant"],
    )
    @action(detail=True, methods=["get"], url_path="chat/suggested-prompts")
    def chat_suggestions(self, request: Request, id: str | None = None) -> Response:
        study = StudyService.get_user_study(user=request.user, study_id=id)
        return Response(
            {"study_id": str(study.id), "prompts": ChatService.suggested_prompts(study)}
        )

    # ── reprocess ────────────────────────────────────────────────────────────

    @extend_schema(
        operation_id="studies_reprocess",
        summary="Re-run the analysis pipeline for a study",
        tags=["Studies"],
        request=None,
        responses={200: StudySerializer},
    )
    @action(detail=True, methods=["post"])
    def reprocess(self, request: Request, id: str | None = None) -> Response:
        study = StudyService.reprocess(user=request.user, study_id=id)
        return Response(StudySerializer(study).data)
