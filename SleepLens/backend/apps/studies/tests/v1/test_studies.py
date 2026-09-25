"""API tests for study upload, filtering, split result streams, PSQI and reports."""

from __future__ import annotations

import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.patients.services.patient_service import PatientService
from apps.studies.models import NightFeatures, PSQI, Study, StudyEpoch

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def no_processing(monkeypatch):
    """Never run the real pipeline during API tests."""
    monkeypatch.setattr("apps.analysis.tasks.process_study.delay", lambda study_id: None)


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch):
    """Deterministic markdown from the LLM client."""
    monkeypatch.setattr(
        "apps.reports.services.report_service.chat",
        lambda messages: "# Sleep report — mocked\n\nAll good.",
    )


def _edf_upload(name: str = "night-PSG.edf") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, b"0" * 2048, content_type="application/octet-stream")


def _full_psqi() -> dict:
    return {
        "subjective_quality": 1,
        "sleep_latency": 2,
        "sleep_duration": 0,
        "habitual_efficiency": 1,
        "disturbances": 1,
        "medication_use": 0,
        "daytime_dysfunction": 2,
    }


class TestStudyUpload:
    def test_upload_creates_study(self, authenticated_client, user):
        url = reverse("studies_api:v1:studies-list")
        response = authenticated_client.post(url, {"file": _edf_upload()}, format="multipart")
        assert response.status_code == 201
        assert response.json()["data"]["status"] == "uploaded"
        assert Study.objects.filter(user=user).count() == 1

    def test_upload_rejects_wrong_extension(self, authenticated_client):
        url = reverse("studies_api:v1:studies-list")
        response = authenticated_client.post(
            url, {"file": _edf_upload("notes.txt")}, format="multipart"
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_upload_requires_auth(self, api_client):
        url = reverse("studies_api:v1:studies-list")
        response = api_client.post(url, {"file": _edf_upload()}, format="multipart")
        assert response.status_code == 401

    def test_upload_with_patient_and_psqi(self, authenticated_client, user):
        patient = PatientService.create_patient(
            owner=user, full_name="Jane Doe", birth_year=1980, sex="female"
        )
        url = reverse("studies_api:v1:studies-list")
        response = authenticated_client.post(
            url,
            {
                "file": _edf_upload(),
                "patient": str(patient.id),
                "psqi": json.dumps(_full_psqi()),
            },
            format="multipart",
        )
        assert response.status_code == 201
        body = response.json()["data"]
        assert body["patient"]["full_name"] == "Jane Doe"
        assert body["psqi_taken"] is True
        assert body["psqi_global_score"] == sum(_full_psqi().values())

    def test_upload_with_partial_psqi_is_rejected(self, authenticated_client):
        url = reverse("studies_api:v1:studies-list")
        response = authenticated_client.post(
            url,
            {"file": _edf_upload(), "psqi": json.dumps({"subjective_quality": 1})},
            format="multipart",
        )
        assert response.status_code == 400
        assert "PSQI" in str(response.json()["error"]["details"])
        assert not PSQI.objects.exists()

    def test_upload_with_foreign_patient_is_404(self, authenticated_client):
        from apps.accounts.services.auth_service import UserService

        stranger = UserService.create_user(
            email="stranger@example.com", password="strangerpass1", full_name="Stranger"
        )
        foreign = PatientService.create_patient(owner=stranger, full_name="Not Yours")
        url = reverse("studies_api:v1:studies-list")
        response = authenticated_client.post(
            url, {"file": _edf_upload(), "patient": str(foreign.id)}, format="multipart"
        )
        assert response.status_code == 404


class TestStudyAccess:
    def test_list_only_own_studies(self, authenticated_client, user):
        Study.objects.create(
            user=user, file="studies/x.edf", original_filename="mine.edf", file_size=10
        )
        url = reverse("studies_api:v1:studies-list")
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response.json()["metadata"]["total"] == 1

    def test_detail_other_users_study_is_404(self, authenticated_client):
        from apps.accounts.services.auth_service import UserService

        other = UserService.create_user(
            email="other@example.com", password="otherpass123", full_name="Other"
        )
        foreign = Study.objects.create(
            user=other, file="studies/y.edf", original_filename="foreign.edf", file_size=10
        )
        url = reverse("studies_api:v1:studies-detail", args=[foreign.id])
        assert authenticated_client.get(url).status_code == 404


class TestStudyFiltering:
    @pytest.fixture
    def three_studies(self, user):
        alpha = Study.objects.create(
            user=user, file="studies/a.edf", original_filename="alpha-night.edf", file_size=1
        )
        beta = Study.objects.create(
            user=user, file="studies/b.edf", original_filename="beta-night.edf", file_size=1
        )
        gamma = Study.objects.create(
            user=user,
            file="studies/c.edf",
            original_filename="gamma-night.edf",
            file_size=1,
            status="completed",
        )
        Study.objects.filter(id=alpha.id).update(created_at="2026-01-01T10:00:00Z")
        Study.objects.filter(id=beta.id).update(created_at="2026-02-01T10:00:00Z")
        Study.objects.filter(id=gamma.id).update(created_at="2026-03-01T10:00:00Z")
        return alpha, beta, gamma

    def test_search_by_name(self, authenticated_client, three_studies):
        url = reverse("studies_api:v1:studies-list") + "?search=beta"
        body = authenticated_client.get(url).json()
        assert body["metadata"]["total"] == 1
        assert body["data"][0]["original_filename"] == "beta-night.edf"

    def test_filter_by_status(self, authenticated_client, three_studies):
        url = reverse("studies_api:v1:studies-list") + "?status=completed"
        assert authenticated_client.get(url).json()["metadata"]["total"] == 1

    def test_filter_by_date_range(self, authenticated_client, three_studies):
        url = reverse("studies_api:v1:studies-list") + "?date_from=2026-01-15&date_to=2026-02-15"
        body = authenticated_client.get(url).json()
        assert body["metadata"]["total"] == 1
        assert body["data"][0]["original_filename"] == "beta-night.edf"

    def test_invalid_date_is_400(self, authenticated_client, three_studies):
        url = reverse("studies_api:v1:studies-list") + "?date_from=15-01-2026"
        response = authenticated_client.get(url)
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_ordering_by_name(self, authenticated_client, three_studies):
        url = reverse("studies_api:v1:studies-list") + "?ordering=original_filename"
        names = [row["original_filename"] for row in authenticated_client.get(url).json()["data"]]
        assert names == sorted(names)


@pytest.fixture
def processed_study(user):
    """A study with two epochs and both feature groups."""
    study = Study.objects.create(
        user=user, file="studies/p.edf", original_filename="p.edf", file_size=10, n_epochs=2
    )
    StudyEpoch.objects.create(
        study=study,
        epoch_index=0,
        start_sec=0,
        stage="N2",
        probabilities={"Wake": 0.05, "N1": 0.1, "N2": 0.7, "N3": 0.1, "REM": 0.05},
        confidence=0.7,
        confidence_band="medium",
        needs_review=True,
        sdi=0.62,
        rem_pred=False,
    )
    StudyEpoch.objects.create(
        study=study,
        epoch_index=1,
        start_sec=30,
        stage="REM",
        probabilities={"Wake": 0.02, "N1": 0.05, "N2": 0.08, "N3": 0.0, "REM": 0.85},
        confidence=0.85,
        confidence_band="high",
        needs_review=False,
        sdi=0.31,
        rem_pred=True,
    )
    NightFeatures.objects.create(
        study=study,
        values={"tst_min": 400.0, "sfi": 12.0, "sdi_ap": 0.5},
        not_assessable=[
            {"key": "apnea_index", "reason": "no airflow channel"},
            {"key": "sdi_dfa", "reason": "series too short"},
        ],
    )
    return study


class TestSplitEndpoints:
    def test_ssc_frames(self, authenticated_client, processed_study):
        url = reverse("studies_api:v1:studies-ssc", args=[processed_study.id])
        data = authenticated_client.get(url).json()["data"]
        assert data["n_epochs"] == 2
        assert data["frames"]["stage"] == [2, 4]  # N2, REM
        assert data["frames"]["confidence"] == [0.7, 0.85]
        assert data["frames"]["needs_review"] == [True, False]
        assert len(data["frames"]["probabilities"][0]) == 5
        assert data["review_summary"]["needs_review_count"] == 1

    def test_sdi_frames(self, authenticated_client, processed_study):
        url = reverse("studies_api:v1:studies-sdi", args=[processed_study.id])
        data = authenticated_client.get(url).json()["data"]
        assert data["frames"]["sdi"] == [0.62, 0.31]
        assert data["frames"]["rem_pred"] == [0, 1]
        assert data["model"] == "sdi_transformer"

    def test_features_split_by_group(self, authenticated_client, processed_study):
        ssc_url = reverse("studies_api:v1:studies-features-ssc", args=[processed_study.id])
        sqi_url = reverse("studies_api:v1:studies-features-sqi", args=[processed_study.id])
        ssc = authenticated_client.get(ssc_url).json()["data"]
        sqi = authenticated_client.get(sqi_url).json()["data"]
        assert ssc["values"] == {"tst_min": 400.0, "sfi": 12.0}
        assert [mark["key"] for mark in ssc["not_assessable"]] == ["apnea_index"]
        assert sqi["values"] == {"sdi_ap": 0.5}
        assert [mark["key"] for mark in sqi["not_assessable"]] == ["sdi_dfa"]

    def test_night_summary(self, authenticated_client, processed_study):
        url = reverse("studies_api:v1:studies-night", args=[processed_study.id])
        data = authenticated_client.get(url).json()["data"]
        assert data["n_epochs"] == 2
        assert data["original_filename"] == "p.edf"


class TestPSQI:
    def test_get_empty(self, authenticated_client, user):
        study = Study.objects.create(
            user=user, file="studies/q.edf", original_filename="q.edf", file_size=1
        )
        url = reverse("studies_api:v1:studies-psqi", args=[study.id])
        assert authenticated_client.get(url).json()["data"]["taken"] is False

    def test_put_full_psqi(self, authenticated_client, user):
        study = Study.objects.create(
            user=user, file="studies/q.edf", original_filename="q.edf", file_size=1
        )
        url = reverse("studies_api:v1:studies-psqi", args=[study.id])
        response = authenticated_client.put(url, _full_psqi(), format="json")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["taken"] is True
        assert data["global_score"] == sum(_full_psqi().values())

    def test_put_partial_psqi_rejected(self, authenticated_client, user):
        study = Study.objects.create(
            user=user, file="studies/q.edf", original_filename="q.edf", file_size=1
        )
        url = reverse("studies_api:v1:studies-psqi", args=[study.id])
        response = authenticated_client.put(url, {"subjective_quality": 1}, format="json")
        assert response.status_code == 400

    def test_delete_psqi(self, authenticated_client, user):
        study = Study.objects.create(
            user=user, file="studies/q.edf", original_filename="q.edf", file_size=1
        )
        PSQI.objects.create(study=study, **_full_psqi())
        url = reverse("studies_api:v1:studies-psqi", args=[study.id])
        assert authenticated_client.delete(url).json()["data"]["taken"] is False


class TestReports:
    def test_report_before_generation(self, authenticated_client, processed_study):
        url = reverse("studies_api:v1:studies-report", args=[processed_study.id])
        body = authenticated_client.get(url).json()["data"]
        assert body["available"] is False
        assert body["markdown"] is None

    def test_generate_and_fetch_report(self, authenticated_client, processed_study):
        url = reverse("studies_api:v1:studies-report-generate", args=[processed_study.id])
        response = authenticated_client.post(url)
        assert response.status_code == 201
        body = response.json()["data"]
        assert body["markdown"].startswith("# Sleep report")
        assert body["prompt_version"] == "v2"

        fetch = authenticated_client.get(
            reverse("studies_api:v1:studies-report", args=[processed_study.id])
        ).json()["data"]
        assert fetch["available"] is True
        assert fetch["markdown"] == body["markdown"]
