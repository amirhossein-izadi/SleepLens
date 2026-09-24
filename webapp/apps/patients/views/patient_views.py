"""
Patient views for SleepLens API.
Adheres to backend_coding_guidelines/08_API_DESIGN.md
"""

from rest_framework import viewsets, status
from rest_framework.request import Request
from rest_framework.response import Response

from apps.patients.models.patient import Patient
from apps.patients.serializers.patient_serializer import (
    PatientReadSerializer,
    PatientWriteSerializer,
)
from common.responses import api_success, api_error

class PatientViewSet(viewsets.ModelViewSet):
    """Endpoints for managing patient demographic records."""
    queryset = Patient.objects.all().order_by("-created_at")

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PatientWriteSerializer
        return PatientReadSerializer

    def list(self, request: Request, *args, **kwargs) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        serializer = PatientReadSerializer(queryset, many=True)
        return api_success(
            data=serializer.data,
            metadata={"total": queryset.count()}
        )

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        serializer = PatientReadSerializer(instance)
        return api_success(data=serializer.data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = PatientWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="VALIDATION_ERROR",
                message="Invalid patient data",
                details=[{"field": k, "message": str(v[0])} for k, v in serializer.errors.items()],
                status_code=status.HTTP_400_BAD_REQUEST
            )
        patient = serializer.save()
        read_serializer = PatientReadSerializer(patient)
        return api_success(
            data=read_serializer.data,
            message="Patient registered successfully",
            status_code=status.HTTP_201_CREATED
        )
