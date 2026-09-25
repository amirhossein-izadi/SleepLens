"""Ingest the Sleep-EDF Expanded dataset into the database.

**Benchmark/development utility only.** The product does not depend on this:
users upload their own recordings. This command exists so developers can have
the reference dataset browsable in the app for benchmarks and demos.

Creates one Patient per subject and one Study per recording, storing the
expert hypnogram as ground-truth labels (0-4, -1 unscored). Files stay where
they are: the absolute path is stored in ``Study.source_path`` and the
analysis pipeline can process a study on demand (``reprocess`` endpoint).

    python manage.py ingest_sleep_edf --owner-email you@example.com \
        --edf-root C:/data/sleep-edf-database-expanded-1.0.0 [--limit 5] [--subsets both]
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import mne
import numpy as np
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User
from apps.patients.models import Patient
from apps.studies.models import Study

STAGE_MAP = {
    "Sleep stage W": 0,
    "Sleep stage 1": 1,
    "Sleep stage 2": 2,
    "Sleep stage 3": 3,
    "Sleep stage 4": 3,
    "Sleep stage R": 4,
}
EPOCH_SECONDS = 30
SUBSET_FOLDERS = {"cassette": "sleep-cassette", "telemetry": "sleep-telemetry"}


class Command(BaseCommand):
    help = "Ingest Sleep-EDF recordings (with expert hypnograms) as patients + studies."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--owner-email", required=True, help="User that owns the records.")
        parser.add_argument("--edf-root", required=True, help="Sleep-EDF dataset root folder.")
        parser.add_argument("--limit", type=int, default=0, help="Max recordings (0 = all).")
        parser.add_argument(
            "--subsets",
            choices=["cassette", "telemetry", "both"],
            default="both",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        owner = User.objects.filter(email=options["owner_email"]).first()
        if owner is None:
            raise CommandError(f"User not found: {options['owner_email']}")
        root = Path(options["edf_root"])
        if not root.is_dir():
            raise CommandError(f"Dataset root not found: {root}")

        folders = (
            [root / folder for folder in SUBSET_FOLDERS.values()]
            if options["subsets"] == "both"
            else [root / SUBSET_FOLDERS[options["subsets"]]]
        )
        pairs: list[tuple[Path, Path]] = []
        for folder in folders:
            psg_map = {path.name[:6]: path for path in sorted(folder.glob("*-PSG.edf"))}
            for hyp in sorted(folder.glob("*-Hypnogram.edf")):
                sid = hyp.name[:6]
                if sid in psg_map:
                    pairs.append((psg_map[sid], hyp))
        if options["limit"]:
            pairs = pairs[: options["limit"]]
        if not pairs:
            raise CommandError("No PSG/hypnogram pairs found.")

        demographics = _sex_age_from_sheets(root)
        created_studies = 0
        created_patients = 0
        for psg, hyp in pairs:
            sid = psg.name[:6]
            subject = sid[:5]
            labels = _hypnogram_labels(hyp)
            with transaction.atomic():
                patient, patient_created = Patient.objects.get_or_create(
                    owner=owner,
                    full_name=f"Sleep-EDF {subject}",
                    defaults={
                        "sex": demographics.get(subject, (None, "unknown"))[1],
                        "birth_year": demographics.get(subject, (None, "unknown"))[0],
                        "notes": "Ingested from the Sleep-EDF Expanded dataset.",
                    },
                )
                created_patients += int(patient_created)
                _, study_created = Study.objects.get_or_create(
                    user=owner,
                    original_filename=psg.name,
                    defaults={
                        "patient": patient,
                        "source_path": str(psg.resolve()),
                        "ground_truth_labels": labels,
                        "file_size": psg.stat().st_size,
                        "status": "uploaded",
                        "status_message": "Ingested dataset record (ground truth; analysis on demand).",
                    },
                )
                created_studies += int(study_created)
            self.stdout.write(f"  {psg.name}: epochs={len(labels)}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Ingested {created_studies} studies, {created_patients} patients "
                f"(owner={owner.email})."
            )
        )


def _hypnogram_labels(hyp_path: Path) -> list[int]:
    """Expert stages per 30-s epoch (0-4, -1 unscored)."""
    annotations = mne.read_annotations(str(hyp_path))
    total = int(np.ceil(max(onset + duration for onset, duration in zip(annotations.onset, annotations.duration)) / EPOCH_SECONDS))
    labels = np.full(total, -1, dtype=int)
    for onset, duration, description in zip(
        annotations.onset, annotations.duration, annotations.description
    ):
        stage = STAGE_MAP.get(description)
        if stage is None:
            continue
        start = int(round(onset / EPOCH_SECONDS))
        length = max(int(round(duration / EPOCH_SECONDS)), 1)
        labels[start : start + length] = stage
    return labels.tolist()


def _sex_age_from_sheets(root: Path) -> dict[str, tuple[int | None, str]]:
    """Subject -> (birth_year, sex) when the subject sheets provide it."""
    import pandas as pd
    from datetime import date

    out: dict[str, tuple[int | None, str]] = {}
    sheet = root / "SC-subjects.xls"
    if not sheet.is_file():
        return out
    try:
        frame = pd.read_excel(sheet)
    except Exception:  # noqa: BLE001 - demographics are optional
        return out
    columns = {str(column).lower(): column for column in frame.columns}
    for _, row in frame.iterrows():
        try:
            subject = f"SC{int(row[columns['subject']]):03d}"
        except (KeyError, TypeError, ValueError):
            continue
        age = row.get(columns.get("age", ""), None) if "age" in columns else None
        sex_raw = str(row.get(columns.get("sex", ""), "")).lower() if "sex" in columns else ""
        sex = "male" if sex_raw.startswith("m") else "female" if sex_raw.startswith("f") else "unknown"
        birth_year = None
        if age is not None and not pd.isna(age):
            birth_year = date.today().year - int(age)
        out[subject] = (birth_year, sex)
    return out
