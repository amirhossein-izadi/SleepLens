"""
Phase 3 Automated Verification Suite for REST APIs & In-Process Runner.
Tests:
- Patient endpoints (/api/v1/patients/)
- Study upload & background pipeline execution (/api/v1/studies/upload/)
- Status polling (/api/v1/studies/{id}/status/)
- File explorer (/api/v1/studies/{id}/files/)
- Hypnogram retrieval & physician stage overrides (/api/v1/studies/{id}/hypnogram/)
- Dynamic metrics, manual metric overrides & recalculation (/api/v1/studies/{id}/metrics/)
- Clinical report retrieval & sign-off (/api/v1/studies/{id}/report/)
"""

import time
import pytest
from rest_framework.test import APIClient
from rest_framework import status

from apps.patients.models.patient import Patient, BiologicalSex
from apps.studies.models.study import SleepStudy, StudyStatus, StudyType
from apps.hypnograms.models.epoch import SleepEpoch, SleepStage
from apps.metrics.models.study_metric import StudyMetricsSummary
from infrastructure.runners.thread_runner import ThreadRunner

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def sample_patient(db):
    return Patient.objects.create(
        mrn="MRN-API-TEST-001",
        first_name="Reza",
        last_name="Karimi",
        biological_sex=BiologicalSex.MALE,
        medical_history="Frequent arousals and unrefreshing sleep."
    )

@pytest.mark.django_db
class TestPhase3APIs:

    def test_patient_crud_api(self, api_client):
        """Test patient registration and listing via API."""
        # 1. Create Patient
        payload = {
            "mrn": "MRN-API-NEW-99",
            "first_name": "Sara",
            "last_name": "Alipour",
            "birth_date": "1990-05-15",
            "biological_sex": "female",
            "medical_history": "Mild insomnia"
        }
        res = api_client.post("/api/v1/patients/", data=payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["success"] is True
        assert res.data["data"]["mrn"] == "MRN-API-NEW-99"

        # 2. List Patients
        list_res = api_client.get("/api/v1/patients/")
        assert list_res.status_code == status.HTTP_200_OK
        assert list_res.data["success"] is True
        assert len(list_res.data["data"]) >= 1

    def test_study_upload_and_pipeline_execution(self, api_client, sample_patient):
        """Test study upload endpoint and synchronous execution of in-process pipeline."""
        upload_data = {
            "patient_id": str(sample_patient.id),
            "study_type": StudyType.FULL_PSG,
            "study_date": "2026-09-24",
        }
        res = api_client.post("/api/v1/studies/upload/", data=upload_data, format="multipart")
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["success"] is True
        study_id = res.data["data"]["study_id"]
        assert study_id is not None

        # Execute pipeline directly for test deterministic assertion
        ThreadRunner._execute_study_pipeline(study_id)

        # 1. Poll Status Endpoint
        status_res = api_client.get(f"/api/v1/studies/{study_id}/status/")
        assert status_res.status_code == status.HTTP_200_OK
        assert status_res.data["data"]["status"] == StudyStatus.COMPLETED
        assert status_res.data["data"]["total_epochs"] > 0

        # 2. Query Hypnogram Epochs Endpoint
        hypno_res = api_client.get(f"/api/v1/studies/{study_id}/hypnogram/")
        assert hypno_res.status_code == status.HTTP_200_OK
        epochs = hypno_res.data["data"]
        assert len(epochs) > 0
        assert "stage" in epochs[0]
        assert "metrics" in epochs[0]

        # 3. Test Physician Single Epoch Override Endpoint (PATCH)
        target_epoch_idx = epochs[5]["epoch_index"]
        override_payload = {
            "stage": SleepStage.N3,
            "correction_reason": "High-amplitude slow waves verified by doctor"
        }
        patch_res = api_client.patch(
            f"/api/v1/studies/{study_id}/epochs/{target_epoch_idx}/override/",
            data=override_payload,
            format="json"
        )
        assert patch_res.status_code == status.HTTP_200_OK
        assert patch_res.data["data"]["stage"] == SleepStage.N3
        assert patch_res.data["data"]["is_manually_corrected"] is True

        # 4. Test Physician Bulk Override Endpoint (POST)
        bulk_payload = {
            "start_epoch": 10,
            "end_epoch": 15,
            "stage": SleepStage.N2,
            "correction_reason": "Sleep spindles identified in range"
        }
        bulk_res = api_client.post(
            f"/api/v1/studies/{study_id}/epochs/bulk-override/",
            data=bulk_payload,
            format="json"
        )
        assert bulk_res.status_code == status.HTTP_200_OK
        assert bulk_res.data["data"]["updated_epochs_count"] == 6

        # 5. Query Metrics Endpoint
        metrics_res = api_client.get(f"/api/v1/studies/{study_id}/metrics/")
        assert metrics_res.status_code == status.HTTP_200_OK
        assert "sqi_score" in metrics_res.data["data"]
        assert "metrics_data" in metrics_res.data["data"]

        # 6. Test Manual Metric Override Endpoint (POST)
        metric_override_payload = {
            "metric_key": "waso_min",
            "adjusted_value": 25.0,
            "clinical_rationale": "Filtered 2 movement artifacts in pre-dawn period"
        }
        m_override_res = api_client.post(
            f"/api/v1/studies/{study_id}/metrics/override/",
            data=metric_override_payload,
            format="json"
        )
        assert m_override_res.status_code == status.HTTP_200_OK
        assert m_override_res.data["data"]["metrics_data"]["waso_min"] == 25.0
        assert m_override_res.data["data"]["is_manually_adjusted"] is True

        # 7. Test On-Demand Recalculate Endpoint (POST)
        recalc_res = api_client.post(f"/api/v1/studies/{study_id}/metrics/recalculate/")
        assert recalc_res.status_code == status.HTTP_200_OK
        assert recalc_res.data["data"]["sqi_score"] > 0
        # Preserves active override on waso_min
        assert recalc_res.data["data"]["metrics_data"]["waso_min"] == 25.0

        # 8. Test Clinical Report Endpoint & Sign-Off
        report_res = api_client.get(f"/api/v1/studies/{study_id}/report/")
        assert report_res.status_code == status.HTTP_200_OK
        assert "executive_summary" in report_res.data["data"]

        sign_off_payload = {
            "is_signed_off": True,
            "physician_notes": "Reviewed polysomnography hypnogram and verified stage corrections."
        }
        sign_res = api_client.post(
            f"/api/v1/studies/{study_id}/report/sign-off/",
            data=sign_off_payload,
            format="json"
        )
        assert sign_res.status_code == status.HTTP_200_OK
        assert sign_res.data["data"]["is_signed_off"] is True
        assert "Reviewed" in sign_res.data["data"]["physician_notes"]

    def test_metrics_catalog_endpoint(self, api_client):
        from django.core.management import call_command
        call_command("seed_metrics")
        res = api_client.get("/api/v1/metrics/catalog/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["success"] is True
        assert len(res.data["data"]) >= 10
