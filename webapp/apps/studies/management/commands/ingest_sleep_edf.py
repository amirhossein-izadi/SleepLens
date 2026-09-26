"""
Django Management Command: ingest_sleep_edf
Ingests real Sleep-EDF Polysomnography (PSG) dataset (197 recordings) into SleepLens:
- 100 unique Patients with clinical demographics (SC: 78 healthy, ST: 22 hospital)
- 197 SleepStudy records (153 Cassette Home, 44 Telemetry Hospital)
- Ground-truth SleepEpoch staging from *-Hypnogram.edf annotations
- Artifact synchronization into dedicated patient directories
Adheres to backend_coding_guidelines/03_DJANGO_PATTERNS.md.
"""

import os
import glob
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd
import pyedflib
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction

from apps.patients.models.patient import Patient, BiologicalSex
from apps.studies.models.study import SleepStudy, StudyStatus, StudyType
from apps.hypnograms.models.epoch import SleepEpoch
from infrastructure.storage.patient_storage_service import PatientStorageService

logger = logging.getLogger("SleepLensIngest")

STAGE_MAP = {
    "Sleep stage W": 0,
    "Sleep stage 1": 1,
    "Sleep stage 2": 2,
    "Sleep stage 3": 3,
    "Sleep stage 4": 3,  # AASM standard: merge stage 3 & 4 into N3
    "Sleep stage R": 4,
}

class Command(BaseCommand):
    help = "Ingest real Sleep-EDF Polysomnography dataset (patients, studies, ground-truth epochs)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset-dir",
            type=str,
            default=str(settings.BASE_DIR.parent / "sleep-edf-database-expanded-1.0.0"),
            help="Path to sleep-edf-database-expanded-1.0.0 directory."
        )
        parser.add_argument(
            "--regime",
            type=str,
            choices=["all", "cassette", "telemetry"],
            default="all",
            help="Which dataset regime to ingest."
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Optional limit on number of recordings to ingest."
        )
        parser.add_argument(
            "--no-trim",
            action="store_true",
            default=False,
            help="Do not trim to in-bed sleep window (keep raw 24h daytime epochs)."
        )
        parser.add_argument(
            "--segregate-dir",
            type=str,
            default=str(settings.BASE_DIR.parent / "data" / "sleep_edf_by_patient"),
            help="Directory to output patient-segregated EDF records without modifying original dataset."
        )
    def handle(self, *args, **options):
        dataset_dir = Path(options["dataset_dir"]).resolve()
        segregate_dir = Path(options["segregate_dir"]).resolve()
        segregate_dir.mkdir(parents=True, exist_ok=True)
        regime = options["regime"]
        limit = options["limit"]
        trim_in_bed = not options["no_trim"]
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"=== Ingesting Sleep-EDF Dataset from {dataset_dir} ==="
        ))

        if not dataset_dir.exists():
            self.stderr.write(self.style.ERROR(f"Dataset directory not found: {dataset_dir}"))
            return

        # 1. Parse Demographics
        sc_demos, st_demos = self._load_demographics(dataset_dir)
        self.stdout.write(f"✓ Parsed demographics: {len(sc_demos)} Cassette nights, {len(st_demos)} Telemetry nights.")

        # 2. Match PSG & Hypnogram Pairs
        pairs = self._match_pairs(dataset_dir, regime)
        if limit:
            pairs = pairs[:limit]
        self.stdout.write(f"✓ Identified {len(pairs)} PSG/Hypnogram pairs to ingest.")

        # 3. Ingest Recordings
        total_patients = 0
        total_studies = 0
        total_epochs = 0

        for idx, (psg_path, hyp_path, sub_type, subj_id, night, record_id) in enumerate(pairs, 1):
            demo_subj = (subj_id - 400) if sub_type == "cassette" else (subj_id - 700)
            demo = sc_demos.get((demo_subj, night)) if sub_type == "cassette" else st_demos.get((demo_subj, night))
            age = demo.get("age") if demo else None
            sex = demo.get("sex", "other") if demo else "other"
            lights_off = demo.get("lights_off", "") if demo else ""
            condition = demo.get("condition", "Standard Ambulatory") if demo else "Standard Ambulatory"

            p_mrn = f"SC{subj_id}" if sub_type == "cassette" else f"ST{subj_id}"
            p_name = f"Subject {subj_id}"
            p_last = "Cassette" if sub_type == "cassette" else "Telemetry"
            p_type = StudyType.CASSETTE_HOME if sub_type == "cassette" else StudyType.TELEMETRY_HOSPITAL

            # Birth date estimate
            today = datetime.date.today()
            birth_year = (today.year - age) if age else 1980
            birth_date = datetime.date(birth_year, 1, 1)

            bio_sex = BiologicalSex.MALE if sex == "male" else (BiologicalSex.FEMALE if sex == "female" else BiologicalSex.OTHER)
            history = (
                f"Sleep-EDF {sub_type.capitalize()} subject. Night {night}. "
                f"Protocol condition: {condition}. Lights-off: {lights_off}."
            )

            with transaction.atomic():
                patient, p_created = Patient.objects.get_or_create(
                    mrn=p_mrn,
                    defaults={
                        "first_name": p_name,
                        "last_name": p_last,
                        "birth_date": birth_date,
                        "biological_sex": bio_sex,
                        "medical_history": history
                    }
                )
                if p_created:
                    total_patients += 1

                # Parse Hypnogram Epochs
                raw_stages = self._parse_hypnogram(hyp_path)
                if trim_in_bed and sub_type == "cassette":
                    stages = self._trim_in_bed(raw_stages)
                else:
                    stages = raw_stages

                # Create or Update Study
                # Create or Update Study uniquely by record_id
                study = SleepStudy.objects.filter(patient=patient, metadata__record_id=record_id).first()
                study_date = today - datetime.timedelta(days=(2 - night) if night in (1, 2) else 0)
                study_defaults = {
                    "status": StudyStatus.COMPLETED,
                    "study_type": p_type,
                    "study_date": study_date,
                    "total_epochs": len(stages),
                    "duration_minutes": round(len(stages) * 0.5, 1),
                    "metadata": {
                        "dataset": "Sleep-EDF Database Expanded v1.0.0",
                        "record_id": record_id,
                        "psg_file": os.path.basename(psg_path),
                        "hypnogram_file": os.path.basename(hyp_path),
                        "night": night,
                        "age": age,
                        "sex": sex,
                        "lights_off": lights_off,
                        "condition": condition,
                        "psg_absolute_path": str(psg_path),
                        "hypnogram_absolute_path": str(hyp_path)
                    }
                }
                if study:
                    for k, v in study_defaults.items():
                        setattr(study, k, v)
                    study.save()
                else:
                    study = SleepStudy.objects.create(patient=patient, **study_defaults)
                    total_studies += 1

                # Bulk Create Epochs
                epoch_objects = []
                for ep_idx, stage_val in enumerate(stages):
                    epoch_objects.append(
                        SleepEpoch(
                            study=study,
                            epoch_index=ep_idx,
                            start_seconds=ep_idx * 30.0,
                            stage=int(stage_val),
                            ai_predicted_stage=-1,  # Unpredicted until model execution
                            confidence=1.0,         # Human-expert ground truth label
                            metrics={},             # Uncomputed until model execution
                            is_lights_off=True
                        )
                    )

                SleepEpoch.objects.filter(study=study).delete()
                SleepEpoch.objects.bulk_create(epoch_objects, batch_size=2000)
                total_epochs += len(epoch_objects)

                # Export to dedicated patient directory
                PatientStorageService.export_study_artifacts(study)

                # Segregate EDF files into dedicated patient folder in data/
                self._segregate_patient_files(segregate_dir, p_mrn, psg_path, hyp_path, demo, night, condition)
            if idx % 10 == 0 or idx == len(pairs):
                self.stdout.write(
                    f"[{idx}/{len(pairs)}] Ingested {record_id} ({len(stages)} epochs, {len(stages)*30/60:.0f} min) -> {p_mrn}"
                )

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Successfully ingested Sleep-EDF dataset!\n"
            f"  • Total Patients Created/Updated: {total_patients}\n"
            f"  • Total Sleep Studies Ingested: {total_studies} / {len(pairs)}\n"
            f"  • Total Clean Epochs Staged: {total_epochs:,}\n"
        ))

    def _load_demographics(self, base_dir: Path) -> Tuple[Dict, Dict]:
        sc_demos = {}
        sc_path = base_dir / "SC-subjects.xls"
        if sc_path.exists():
            df = pd.read_excel(sc_path)
            for _, r in df.iterrows():
                subj = int(r["subject"])
                night = int(r["night"])
                age = int(r["age"]) if not pd.isna(r["age"]) else None
                r_sex = int(r["sex (F=1)"]) if not pd.isna(r["sex (F=1)"]) else None
                sex = "female" if r_sex == 1 else ("male" if r_sex == 2 else "other")
                sc_demos[(subj, night)] = {"age": age, "sex": sex, "lights_off": str(r.get("LightsOff", ""))}

        st_demos = {}
        st_path = base_dir / "ST-subjects.xls"
        if st_path.exists():
            df = pd.read_excel(st_path, header=None)
            for i in range(2, len(df)):
                r = df.iloc[i]
                if pd.isna(r[0]):
                    continue
                subj = int(r[0])
                age = int(r[1]) if not pd.isna(r[1]) else None
                r_sex = int(r[2]) if not pd.isna(r[2]) else None
                sex = "male" if r_sex == 1 else ("female" if r_sex == 2 else "other")
                p_night = int(r[3]) if not pd.isna(r[3]) else 1
                t_night = int(r[5]) if not pd.isna(r[5]) else 2
                st_demos[(subj, p_night)] = {"age": age, "sex": sex, "condition": "Placebo", "lights_off": str(r[4])}
                st_demos[(subj, t_night)] = {"age": age, "sex": sex, "condition": "Temazepam", "lights_off": str(r[6])}

        return sc_demos, st_demos

    def _match_pairs(self, base_dir: Path, regime: str) -> List[Tuple]:
        records_path = base_dir / "RECORDS"
        records_list = []
        if records_path.exists():
            with open(records_path) as f:
                records_list = [line.strip() for line in f if line.strip()]

        pairs = []
        for rel_psg in records_list:
            psg_path = base_dir / rel_psg
            if not psg_path.exists():
                continue
            base = psg_path.name
            sub_type = "cassette" if base.startswith("SC") else "telemetry"
            if regime != "all" and sub_type != regime:
                continue

            subj_id = int(base[2:5])
            night = int(base[5])
            record_id = base.replace("-PSG.edf", "")

            # Match corresponding Hypnogram.edf
            folder = psg_path.parent
            hyp_candidates = list(folder.glob(f"{record_id[:6]}*-Hypnogram.edf"))
            if not hyp_candidates:
                continue
            hyp_path = hyp_candidates[0]
            pairs.append((psg_path, hyp_path, sub_type, subj_id, night, record_id))

        return pairs

    def _read_annotations_fallback(self, hyp_path: Path):
        """Fallback parser for non-standard EDF+ hypnogram files (e.g. ST7021JM)."""
        with open(hyp_path, "rb") as f:
            hdr = f.read(256)
            num_bytes = int(hdr[184:192].decode("ascii").strip())
            f.seek(num_bytes)
            raw_data = f.read()

        onsets, durations, descriptions = [], [], []
        for chunk in raw_data.split(b"\x00"):
            if b"\x14" in chunk:
                parts = chunk.split(b"\x14")
                parts = [p.decode("latin1", errors="ignore").strip() for p in parts if p.strip()]
                if len(parts) >= 2:
                    time_part = parts[0]
                    desc_part = parts[1]
                    if "\x15" in time_part:
                        onset_str, dur_str = time_part.split("\x15")
                        try:
                            onset = float(onset_str.replace("+", ""))
                            dur = float(dur_str)
                        except ValueError:
                            continue
                    else:
                        try:
                            onset = float(time_part.replace("+", ""))
                            dur = 30.0
                        except ValueError:
                            continue
                    onsets.append(onset)
                    durations.append(dur)
                    descriptions.append(desc_part)
        return onsets, durations, descriptions

    def _parse_hypnogram(self, hyp_path: Path) -> np.ndarray:
        try:
            h = pyedflib.EdfReader(str(hyp_path))
            onsets, durations, descriptions = h.readAnnotations()
            h.close()
        except Exception:
            onsets, durations, descriptions = self._read_annotations_fallback(hyp_path)

        labels = []
        for onset, dur, desc in zip(onsets, durations, descriptions):
            n_epochs = int(round(dur / 30.0))
            stage = STAGE_MAP.get(desc, -1)
            labels.extend([stage] * n_epochs)
        return np.array(labels, dtype=np.int64)

    def _segregate_patient_files(self, seg_root: Path, mrn: str, psg_path: Path, hyp_path: Path, demo: Dict, night: int, condition: str):
        import json, shutil
        p_dir = seg_root / mrn
        p_dir.mkdir(parents=True, exist_ok=True)

        for src in (psg_path, hyp_path):
            dst = p_dir / src.name
            if not dst.exists():
                try:
                    os.link(src, dst)
                except Exception:
                    shutil.copy2(src, dst)

        meta_file = p_dir / "patient_metadata.json"
        meta = {}
        if meta_file.exists():
            try:
                with open(meta_file, encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception:
                meta = {}

        if "mrn" not in meta:
            meta = {
                "mrn": mrn,
                "age": demo.get("age") if demo else None,
                "sex": demo.get("sex", "unknown") if demo else "unknown",
                "nights": {}
            }

        meta.setdefault("nights", {})[f"night_{night}"] = {
            "psg_file": psg_path.name,
            "hypnogram_file": hyp_path.name,
            "lights_off": demo.get("lights_off", "") if demo else "",
            "condition": condition
        }

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
    def _trim_in_bed(self, y: np.ndarray, pad_epochs: int = 60) -> np.ndarray:
        sleep_indices = np.where((y >= 1) & (y <= 4))[0]
        if len(sleep_indices) == 0:
            return y
        first_sleep = sleep_indices[0]
        last_sleep = sleep_indices[-1]
        start_idx = max(0, first_sleep - pad_epochs)
        end_idx = min(len(y), last_sleep + pad_epochs + 1)
        return y[start_idx:end_idx]
