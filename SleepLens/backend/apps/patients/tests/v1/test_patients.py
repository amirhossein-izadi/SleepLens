"""API tests for the patients endpoints."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.patients.models import Patient

pytestmark = pytest.mark.django_db


class TestPatients:
    def test_create_patient(self, authenticated_client, user):
        url = reverse("patients_api:v1:patients-list")
        response = authenticated_client.post(
            url,
            {"full_name": "Jane Doe", "birth_year": 1980, "sex": "female", "notes": "night 1"},
            format="json",
        )
        assert response.status_code == 201
        assert response.json()["data"]["full_name"] == "Jane Doe"
        assert Patient.objects.filter(owner=user).count() == 1

    def test_list_only_own_patients(self, authenticated_client, user):
        from apps.accounts.services.auth_service import UserService
        from apps.patients.services.patient_service import PatientService

        PatientService.create_patient(owner=user, full_name="Mine")
        stranger = UserService.create_user(
            email="stranger2@example.com", password="strangerpass1", full_name="S"
        )
        PatientService.create_patient(owner=stranger, full_name="Not Mine")

        url = reverse("patients_api:v1:patients-list")
        body = authenticated_client.get(url).json()
        assert body["metadata"]["total"] == 1
        assert body["data"][0]["full_name"] == "Mine"

    def test_search_patients(self, authenticated_client, user):
        from apps.patients.services.patient_service import PatientService

        PatientService.create_patient(owner=user, full_name="Alice Smith")
        PatientService.create_patient(owner=user, full_name="Bob Jones")
        url = reverse("patients_api:v1:patients-list") + "?search=alice"
        assert authenticated_client.get(url).json()["metadata"]["total"] == 1

    def test_invalid_birth_year_is_400(self, authenticated_client):
        url = reverse("patients_api:v1:patients-list")
        response = authenticated_client.post(
            url, {"full_name": "X", "birth_year": 1700}, format="json"
        )
        assert response.status_code == 400

    def test_foreign_patient_is_404(self, authenticated_client):
        from apps.accounts.services.auth_service import UserService
        from apps.patients.services.patient_service import PatientService

        stranger = UserService.create_user(
            email="stranger3@example.com", password="strangerpass1", full_name="S"
        )
        foreign = PatientService.create_patient(owner=stranger, full_name="Theirs")
        url = reverse("patients_api:v1:patients-detail", args=[foreign.id])
        assert authenticated_client.get(url).status_code == 404

    def test_update_patient(self, authenticated_client, user):
        from apps.patients.services.patient_service import PatientService

        patient = PatientService.create_patient(owner=user, full_name="Old Name")
        url = reverse("patients_api:v1:patients-detail", args=[patient.id])
        response = authenticated_client.patch(url, {"full_name": "New Name"}, format="json")
        assert response.status_code == 200
        assert response.json()["data"]["full_name"] == "New Name"

    def test_delete_patient_keeps_studies(self, authenticated_client, user):
        from apps.patients.services.patient_service import PatientService
        from apps.studies.models import Study

        patient = PatientService.create_patient(owner=user, full_name="To Delete")
        study = Study.objects.create(
            user=user,
            patient=patient,
            file="studies/d.edf",
            original_filename="d.edf",
            file_size=1,
        )
        url = reverse("patients_api:v1:patients-detail", args=[patient.id])
        assert authenticated_client.delete(url).status_code == 204
        study.refresh_from_db()
        assert study.patient is None  # study survives, unlinked
        assert Study.objects.filter(id=study.id).exists()

    def test_patient_studies_list(self, authenticated_client, user):
        from apps.patients.services.patient_service import PatientService
        from apps.studies.models import Study

        patient = PatientService.create_patient(owner=user, full_name="Night Owner")
        Study.objects.create(
            user=user,
            patient=patient,
            file="studies/n1.edf",
            original_filename="n1.edf",
            file_size=1,
        )
        Study.objects.create(
            user=user,
            patient=patient,
            file="studies/n2.edf",
            original_filename="n2.edf",
            file_size=1,
        )
        url = reverse("patients_api:v1:patients-studies", args=[patient.id])
        data = authenticated_client.get(url).json()["data"]
        assert len(data) == 2
        assert {row["original_filename"] for row in data} == {"n1.edf", "n2.edf"}
