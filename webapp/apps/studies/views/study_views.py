"""
Study views for SleepLens API.
Handles study uploads, background pipeline dispatch, status tracking, and file explorer.
Adheres to backend_coding_guidelines/08_API_DESIGN.md
"""

import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.studies.models.study import SleepStudy, StudyStatus, StudyType
from apps.studies.models.study_file import StudyFile
from apps.patients.models.patient import Patient
from apps.studies.serializers.study_serializer import (
    StudyListSerializer,
    StudyDetailSerializer,
    StudyUploadSerializer,
)
from apps.studies.serializers.study_file_serializer import StudyFileSerializer
from infrastructure.runners.thread_runner import ThreadRunner
from common.responses import api_success, api_error

class StudyViewSet(viewsets.ReadOnlyModelViewSet):
    """Endpoints for sleep studies, archive uploads, status polling, and file exploration."""
    queryset = SleepStudy.objects.all().select_related("patient", "metrics_summary").order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return StudyDetailSerializer
        return StudyListSerializer

    def list(self, request: Request, *args, **kwargs) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        serializer = StudyListSerializer(queryset, many=True)
        return api_success(
            data=serializer.data,
            metadata={"total": queryset.count()}
        )

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        serializer = StudyDetailSerializer(instance)
        return api_success(data=serializer.data)

    @action(detail=False, methods=["POST"], url_path="upload")
    def upload_study(self, request: Request) -> Response:
        """
        Uploads a patient study archive and dispatches in-process background processing.
        POST /api/v1/studies/upload/
        """
        serializer = StudyUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="VALIDATION_ERROR",
                message="Invalid upload parameters",
                details=[{"field": k, "message": str(v[0])} for k, v in serializer.errors.items()],
                status_code=status.HTTP_400_BAD_REQUEST
            )

        patient_id = serializer.validated_data["patient_id"]
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return api_error(
                code="NOT_FOUND",
                message=f"Patient with ID {patient_id} does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )

        study_date = serializer.validated_data.get("study_date") or datetime.date.today()
        study_type = serializer.validated_data.get("study_type", StudyType.FULL_PSG)
        raw_archive = serializer.validated_data.get("raw_archive")

        # Create the study with status UPLOADED
        study = SleepStudy.objects.create(
            patient=patient,
            physician=request.user if request.user and request.user.is_authenticated else None,
            study_date=study_date,
            study_type=study_type,
            status=StudyStatus.UPLOADED,
            raw_archive=raw_archive
        )

        # Dispatch background processing thread (non-blocking)
        ThreadRunner.dispatch_study_pipeline(str(study.id))

        return api_success(
            data={
                "study_id": str(study.id),
                "status": study.status,
                "created_at": study.created_at,
            },
            message="Study archive received; processing dispatched in background.",
            status_code=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["GET"], url_path="status")
    def study_status(self, request: Request, pk=None) -> Response:
        """
        Polls the real-time processing status of a study.
        GET /api/v1/studies/{id}/status/
        """
        study = self.get_object()
        return api_success(
            data={
                "study_id": str(study.id),
                "status": study.status,
                "status_display": study.get_status_display(),
                "total_epochs": study.total_epochs,
                "duration_minutes": study.duration_minutes,
                "error_log": study.error_log,
                "updated_at": study.updated_at,
            }
        )

    @action(detail=True, methods=["GET"], url_path="files")
    def study_files(self, request: Request, pk=None) -> Response:
        """
        Lists all files extracted from the patient's archive.
        GET /api/v1/studies/{id}/files/?file_type=epoch_report
        """
        study = self.get_object()
        files_qs = StudyFile.objects.filter(study=study)

        file_type = request.query_params.get("file_type")
        if file_type:
            files_qs = files_qs.filter(file_type=file_type)

        serializer = StudyFileSerializer(files_qs, many=True)
        return api_success(
            data=serializer.data,
            metadata={"total": files_qs.count()}
        )

    @action(detail=True, methods=["GET"], url_path=r"files/(?P<file_id>[^/.]+)")
    def file_detail(self, request: Request, pk=None, file_id=None) -> Response:
        """
        Retrieves metadata and signal preview for a specific extracted file.
        GET /api/v1/studies/{id}/files/{file_id}/
        """
        study = self.get_object()
        try:
            study_file = StudyFile.objects.get(study=study, id=file_id)
        except StudyFile.DoesNotExist:
            return api_error(
                code="NOT_FOUND",
                message=f"File with ID {file_id} not found for this study",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = StudyFileSerializer(study_file)
        return api_success(data=serializer.data)
