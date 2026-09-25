"""Ingest command test — runs against the real dataset when present."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from django.core.management import call_command

from apps.accounts.services.auth_service import UserService
from apps.studies.models import Study

pytestmark = pytest.mark.django_db

DATASET_ROOT = Path(
    os.getenv(
        "SLEEPLENS_DATASET_ROOT",
        r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0",
    )
)

requires_dataset = pytest.mark.skipif(
    not (DATASET_ROOT / "sleep-cassette").is_dir(),
    reason="Sleep-EDF dataset is not present on this machine",
)


@requires_dataset
def test_ingest_one_cassette_recording():
    owner = UserService.create_user(
        email="ingest@example.com", password="ingestpass123", full_name="Ingest Owner"
    )

    call_command(
        "ingest_sleep_edf",
        "--owner-email",
        owner.email,
        "--edf-root",
        str(DATASET_ROOT),
        "--subsets",
        "cassette",
        "--limit",
        "1",
    )

    assert Study.objects.filter(user=owner).count() == 1
    study = Study.objects.get(user=owner)
    assert study.source_path.endswith("-PSG.edf")
    assert Path(study.source_path).is_file()
    assert study.patient is not None
    assert study.patient.full_name.startswith("Sleep-EDF SC")
    labels = study.ground_truth_labels
    assert isinstance(labels, list) and len(labels) > 100
    assert set(labels) <= {-1, 0, 1, 2, 3, 4}
    assert 255 not in labels

    # Re-running the ingest is idempotent
    call_command(
        "ingest_sleep_edf",
        "--owner-email",
        owner.email,
        "--edf-root",
        str(DATASET_ROOT),
        "--subsets",
        "cassette",
        "--limit",
        "1",
    )
    assert Study.objects.filter(user=owner).count() == 1
