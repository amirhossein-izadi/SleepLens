"""
ClinicalReport views for SleepLens API.
Provides clinical report retrieval and physician sign-off.
Adheres to backend_coding_guidelines/08_API_DESIGN.md
"""

import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.studies.models.study import SleepStudy
from apps.reports.models.report import ClinicalReport
from apps.reports.serializers.report_serializer import (
    ClinicalReportSerializer,
    ReportSignOffSerializer,
)
from common.responses import api_success, api_error

class ReportViewSet(viewsets.ViewSet):
    """Endpoints for clinical reports and physician approval."""

    @action(detail=False, methods=["GET"], url_path=r"(?P<study_id>[^/.]+)/report")
    def get_report(self, request: Request, study_id=None) -> Response:
        """
        Retrieves the narrative clinical diagnostic report for a study.
        GET /api/v1/studies/{study_id}/report/
        """
        try:
            study = SleepStudy.objects.get(id=study_id)
        except SleepStudy.DoesNotExist:
            return api_error(code="NOT_FOUND", message=f"Study {study_id} not found", status_code=status.HTTP_404_NOT_FOUND)

        try:
            report = ClinicalReport.objects.get(study=study)
        except ClinicalReport.DoesNotExist:
            return api_error(
                code="NOT_READY",
                message="Clinical report is still generating or not available. Check /status/.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        serializer = ClinicalReportSerializer(report)
        return api_success(data=serializer.data)

    @action(detail=False, methods=["POST"], url_path=r"(?P<study_id>[^/.]+)/report/sign-off")
    def sign_off_report(self, request: Request, study_id=None) -> Response:
        """
        Allows supervising physician to approve, annotate, and finalize the report.
        POST /api/v1/studies/{study_id}/report/sign-off/
        """
        try:
            study = SleepStudy.objects.get(id=study_id)
        except SleepStudy.DoesNotExist:
            return api_error(code="NOT_FOUND", message=f"Study {study_id} not found", status_code=status.HTTP_404_NOT_FOUND)

        try:
            report = ClinicalReport.objects.get(study=study)
        except ClinicalReport.DoesNotExist:
            return api_error(code="NOT_READY", message="Report not found for this study.", status_code=status.HTTP_400_BAD_REQUEST)

        serializer = ReportSignOffSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(code="VALIDATION_ERROR", message="Invalid sign-off data", details=[serializer.errors])

        report.is_signed_off = serializer.validated_data["is_signed_off"]
        if "physician_notes" in serializer.validated_data:
            report.physician_notes = serializer.validated_data["physician_notes"]

        if report.is_signed_off:
            report.signed_off_at = datetime.datetime.now(datetime.timezone.utc)
        else:
            report.signed_off_at = None

        report.save()

        return api_success(
            data=ClinicalReportSerializer(report).data,
            message="Report sign-off status updated successfully."
        )
