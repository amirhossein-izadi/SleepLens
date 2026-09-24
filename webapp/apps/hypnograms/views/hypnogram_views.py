"""
Hypnogram views for SleepLens API.
Provides interactive epoch data, stage editing, and bulk corrections.
Adheres to backend_coding_guidelines/08_API_DESIGN.md
"""

import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.studies.models.study import SleepStudy
from apps.hypnograms.models.epoch import SleepEpoch
from apps.hypnograms.serializers.epoch_serializer import (
    SleepEpochSerializer,
    EpochOverrideSerializer,
    EpochBulkOverrideSerializer,
)
from common.responses import api_success, api_error

class HypnogramViewSet(viewsets.ViewSet):
    """Endpoints for retrieving hypnogram epochs and performing physician stage corrections."""

    @action(detail=False, methods=["GET"], url_path=r"(?P<study_id>[^/.]+)/hypnogram")
    def list_epochs(self, request: Request, study_id=None) -> Response:
        """
        Retrieves all 30-second epochs for a study to plot the interactive hypnogram.
        GET /api/v1/studies/{study_id}/hypnogram/
        """
        try:
            study = SleepStudy.objects.get(id=study_id)
        except SleepStudy.DoesNotExist:
            return api_error(code="NOT_FOUND", message=f"Study {study_id} not found", status_code=status.HTTP_404_NOT_FOUND)

        epochs = SleepEpoch.objects.filter(study=study).order_by("epoch_index")
        serializer = SleepEpochSerializer(epochs, many=True)
        return api_success(
            data=serializer.data,
            metadata={"total_epochs": epochs.count()}
        )

    @action(detail=False, methods=["PATCH"], url_path=r"(?P<study_id>[^/.]+)/epochs/(?P<epoch_index>\d+)/override")
    def override_single_epoch(self, request: Request, study_id=None, epoch_index=None) -> Response:
        """
        Corrects the sleep stage of a single epoch.
        PATCH /api/v1/studies/{study_id}/epochs/{epoch_index}/override/
        """
        try:
            study = SleepStudy.objects.get(id=study_id)
        except SleepStudy.DoesNotExist:
            return api_error(code="NOT_FOUND", message=f"Study {study_id} not found", status_code=status.HTTP_404_NOT_FOUND)

        try:
            epoch = SleepEpoch.objects.get(study=study, epoch_index=int(epoch_index))
        except SleepEpoch.DoesNotExist:
            return api_error(code="NOT_FOUND", message=f"Epoch {epoch_index} not found for study {study_id}", status_code=status.HTTP_404_NOT_FOUND)

        serializer = EpochOverrideSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(code="VALIDATION_ERROR", message="Invalid stage override data", details=[serializer.errors])

        # Apply physician correction
        epoch.stage = serializer.validated_data["stage"]
        epoch.is_manually_corrected = True
        epoch.correction_reason = serializer.validated_data.get("correction_reason", "")
        epoch.corrected_at = datetime.datetime.now(datetime.timezone.utc)
        if request.user and request.user.is_authenticated:
            epoch.corrected_by = request.user
        epoch.save()

        return api_success(
            data=SleepEpochSerializer(epoch).data,
            message=f"Epoch #{epoch.epoch_index} stage updated to {epoch.get_stage_display()}."
        )

    @action(detail=False, methods=["POST"], url_path=r"(?P<study_id>[^/.]+)/epochs/bulk-override")
    def bulk_override_epochs(self, request: Request, study_id=None) -> Response:
        """
        Corrects a continuous range of epochs (e.g. epochs 100 to 140 to N2).
        POST /api/v1/studies/{study_id}/epochs/bulk-override/
        """
        try:
            study = SleepStudy.objects.get(id=study_id)
        except SleepStudy.DoesNotExist:
            return api_error(code="NOT_FOUND", message=f"Study {study_id} not found", status_code=status.HTTP_404_NOT_FOUND)

        serializer = EpochBulkOverrideSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(code="VALIDATION_ERROR", message="Invalid bulk override data", details=[serializer.errors])

        start_epoch = serializer.validated_data["start_epoch"]
        end_epoch = serializer.validated_data["end_epoch"]
        stage = serializer.validated_data["stage"]
        reason = serializer.validated_data.get("correction_reason", "")

        updated_count = SleepEpoch.objects.filter(
            study=study,
            epoch_index__gte=start_epoch,
            epoch_index__lte=end_epoch
        ).update(
            stage=stage,
            is_manually_corrected=True,
            correction_reason=reason,
            corrected_at=datetime.datetime.now(datetime.timezone.utc),
            corrected_by=request.user if request.user and request.user.is_authenticated else None
        )

        return api_success(
            data={"updated_epochs_count": updated_count, "stage": stage},
            message=f"Updated {updated_count} epochs ({start_epoch} to {end_epoch}) to stage {stage}."
        )
