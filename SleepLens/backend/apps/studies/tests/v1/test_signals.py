"""Tests for the raw-signal preview endpoints (frontend charts + material)."""

from __future__ import annotations

import pytest
from django.core.files.base import ContentFile
from django.urls import reverse

from apps.studies.models import Study
from apps.studies.tests.edf_factory import synthetic_edf_bytes

pytestmark = pytest.mark.django_db


@pytest.fixture
def study_with_recording(user):
    payload = synthetic_edf_bytes()
    study = Study.objects.create(
        user=user,
        original_filename="night-PSG.edf",
        file_size=len(payload),
    )
    study.file.save("night-PSG.edf", ContentFile(payload), save=True)
    return study


class TestSignals:
    def test_channel_list_and_preview(self, authenticated_client, study_with_recording):
        url = reverse("studies_api:v1:studies-signals", args=[study_with_recording.id])
        data = authenticated_client.get(url).json()["data"]
        labels = [channel["label"] for channel in data["available_channels"]]
        assert "EEG Fpz-Cz" in labels
        assert any(channel["label"] == "EEG Fpz-Cz" and channel["sample_rate"] == 100.0
                   for channel in data["available_channels"])
        # whole-file preview defaults
        assert data["file_duration_sec"] == pytest.approx(120.0, abs=1.0)
        assert "EEG Fpz-Cz" in data["series"]
        assert len(data["series"]["EEG Fpz-Cz"]["t"]) > 100

    def test_preview_decimates_with_minmax_envelope(self, authenticated_client, study_with_recording):
        url = reverse("studies_api:v1:studies-signals", args=[study_with_recording.id])
        data = authenticated_client.get(url, {"max_points": 50, "duration_sec": 60}).json()["data"]
        series = data["series"]["EEG Fpz-Cz"]
        assert "min" in series and "max" in series
        assert len(series["min"]) <= 51
        assert all(low <= high for low, high in zip(series["min"], series["max"]))

    def test_preview_channel_filter(self, authenticated_client, study_with_recording):
        url = reverse("studies_api:v1:studies-signals", args=[study_with_recording.id])
        data = authenticated_client.get(url, {"channels": "EOG horizontal"}).json()["data"]
        assert list(data["series"].keys()) == ["EOG horizontal"]

    def test_unknown_channel_is_400(self, authenticated_client, study_with_recording):
        url = reverse("studies_api:v1:studies-signals", args=[study_with_recording.id])
        response = authenticated_client.get(url, {"channels": "EEG Nope"})
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_epoch_snippet(self, authenticated_client, study_with_recording):
        url = reverse(
            "studies_api:v1:studies-signal-epoch",
            args=[study_with_recording.id, 2],
        )
        data = authenticated_client.get(url, {"channels": "EEG Fpz-Cz"}).json()["data"]
        assert data["epoch_index"] == 2
        assert data["start_sec"] == 60.0
        assert len(data["series"]["EEG Fpz-Cz"]["v"]) == 750  # stride-averaged to 25 Hz

    def test_epoch_beyond_recording_is_400(self, authenticated_client, study_with_recording):
        url = reverse(
            "studies_api:v1:studies-signal-epoch",
            args=[study_with_recording.id, 100],
        )
        response = authenticated_client.get(url)
        assert response.status_code == 400

    def test_download_recording(self, authenticated_client, study_with_recording):
        url = reverse("studies_api:v1:studies-download", args=[study_with_recording.id])
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/octet-stream"
        assert len(b"".join(response.streaming_content)) == study_with_recording.file_size
