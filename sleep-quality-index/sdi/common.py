"""Shared paths and Sleep-EDF label conventions for the SDI pipeline.

Data roots resolve in this order:
  1. CLI flags on the entry scripts (--edf-root / --clean-root / --preds-root)
  2. Environment: SLEEPLENS_DATA (base), SLEEPLENS_EDF, SLEEPLENS_CLEAN,
     SLEEPLENS_PREDS
  3. Default: ~/Projects/sleep-analysis/test/data (development checkout)

Stage encoding: 0=WAKE, 1=N1, 2=N2, 3=N3, 4=REM. Expert arrays from
sleepedf_clean/stages/ use 255 for unscored; model prediction arrays use -1.
Sleep-EDF hypnogram stages 3 and 4 are both merged into N3.

The SDI model was trained on 4-channel input (EEG C4, chin EMG, EOG right,
ECG); Sleep-EDF substitutes Fpz-Cz and has no ECG, and cassette EMG is a 1-Hz
envelope. Results are always reported per subset/input condition and never
pooled (see INPUT_CONDITION).
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

MODULE_DIR = Path(__file__).resolve().parent
DATA_ROOT = Path(
    os.environ.get("SLEEPLENS_DATA", Path.home() / "Projects" / "sleep-analysis" / "test" / "data")
).expanduser()
EDF_ROOT = Path(
    os.environ.get("SLEEPLENS_EDF", DATA_ROOT / "sleep-edf-database-expanded-1.0.0")
).expanduser()
CLEAN_ROOT = Path(os.environ.get("SLEEPLENS_CLEAN", DATA_ROOT / "sleepedf_clean")).expanduser()
PREDS_ROOT = Path(os.environ.get("SLEEPLENS_PREDS", DATA_ROOT / "preds")).expanduser()
SDI_OUT_ROOT = MODULE_DIR / "data" / "sdi"
REPORT_DIR = MODULE_DIR / "reports"
MODEL_CKPT = MODULE_DIR / "models" / "sdi_checkpoint.pt"

STAGES5 = ["WAKE", "N1", "N2", "N3", "REM"]
INT_FROM_STAGE = {s: i for i, s in enumerate(STAGES5)}
STAGE_FROM_INT = {i: s for s, i in INT_FROM_STAGE.items()}

EEG_CH = "EEG Fpz-Cz"
EOG_CH = "EOG horizontal"
EMG_CH = "EMG submental"

# SDI input conditions vs the paper's 4-channel C4/EOG(R)/EMG/ECG setup: both
# Sleep-EDF subsets substitute Fpz-Cz and zero-fill ECG; cassette EMG is a
# 1-Hz envelope. Report cassette and telemetry separately, never pooled.
INPUT_CONDITION = {
    "sleep-cassette": "cassette_emg_1hz_no_ecg",
    "sleep-telemetry": "telemetry_emg_100hz_no_ecg",
}

_SUBSET_FOLDER = {"cassette": "sleep-cassette", "telemetry": "sleep-telemetry"}


def _sid(path: Path) -> str:
    return path.name[:6]


def load_manifest(clean_root: Path = CLEAN_ROOT) -> pd.DataFrame:
    man_path = Path(clean_root) / "manifest.csv"
    if not man_path.is_file():
        raise FileNotFoundError(
            f"{man_path} not found. Run: python {MODULE_DIR / 'prepare_windows.py'}"
        )
    return pd.read_csv(man_path)


def manifest_windows(clean_root: Path = CLEAN_ROOT) -> dict[str, tuple[int, int]]:
    return {
        str(r.session): (int(r.epoch_start), int(r.epoch_end))
        for r in load_manifest(clean_root).itertuples()
    }


def pair_sessions(edf_root: Path = EDF_ROOT, subset: str = "both") -> list[tuple[Path, Path]]:
    folder = _SUBSET_FOLDER.get(subset)
    roots = (
        [Path(edf_root) / folder]
        if folder
        else [Path(edf_root) / "sleep-cassette", Path(edf_root) / "sleep-telemetry"]
    )
    pairs = []
    for root in roots:
        psg_map = {_sid(p): p for p in sorted(root.glob("*-PSG.edf"))}
        for hyp in sorted(root.glob("*-Hypnogram.edf")):
            sid = _sid(hyp)
            if sid in psg_map:
                pairs.append((psg_map[sid], hyp))
    return pairs


def stage_file(
    sid: str,
    source: str = "expert",
    clean_root: Path = CLEAN_ROOT,
    preds_root: Path = PREDS_ROOT,
) -> Path:
    """Window-aligned stage ints 0-4 for a session: expert npy or model pred npy."""
    if source == "expert":
        return Path(clean_root) / "stages" / f"{sid}.npy"
    return Path(preds_root) / source / f"{sid}.npy"


def load_stages_int16(
    sid: str,
    source: str = "expert",
    clean_root: Path = CLEAN_ROOT,
    preds_root: Path = PREDS_ROOT,
) -> np.ndarray:
    """Stages as int16 with unscored (-1): expert 255 and model values < 0."""
    a = np.load(stage_file(sid, source, clean_root, preds_root))
    st = a.astype(np.int16)
    st[a == 255] = -1
    return st
