"""Patient viewset — full CRUD (owner-scoped) plus the patient's study list."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.patients.api.v1.serializers.patient import PatientSerializer
from apps.patients.models import Patient
from apps.patients.services.patient_service import PatientService
from apps.studies.api.v1.serializers.study import StudySerializer


class PatientViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """CRUD endpoints for the current user's patients.

    Deleting a patient keeps their studies (``Study.patient`` becomes null).
    """

    serializer_class = PatientSerializer
    lookup_field = "id"

    def get_queryset(self):
        queryset = Patient.objects.filter(owner=self.request.user)
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(full_name__icontains=search)
        ordering = self.request.query_params.get("ordering", "full_name").strip()
        allowed = {"full_name", "-full_name", "created_at", "-created_at"}
        return queryset.order_by(ordering if ordering in allowed else "full_name")

    @extend_schema(
        operation_id="patients_list",
        summary="List patients (filter with ?search=, sort with ?ordering=)",
        tags=["Patients"],
        responses={200: PatientSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        operation_id="patients_studies",
        summary="All studies of one patient (newest first)",
        tags=["Patients"],
        responses={200: StudySerializer(many=True)},
    )
    @action(detail=True, methods=["get"])
    def studies(self, request, id: str | None = None) -> Response:
        patient = PatientService.get_owned_patient(owner=request.user, patient_id=id)
        rows = patient.studies.order_by("-created_at")
        return Response(StudySerializer(rows, many=True).data)

    def perform_create(self, serializer: PatientSerializer) -> None:
        PatientService.create_patient(owner=self.request.user, **serializer.validated_data)
