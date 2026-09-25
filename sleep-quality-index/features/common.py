"""Shared paths and Sleep-EDF label conventions for the features pipeline.

Data roots resolve in this order:
  1. CLI flags on the entry scripts (--edf-root / --clean-root / --preds-root)
  2. Environment: SLEEPLENS_DATA (base), SLEEPLENS_EDF, SLEEPLENS_CLEAN,
     SLEEPLENS_PREDS
  3. Default: ~/Projects/sleep-analysis/test/data (development checkout)

Stage encoding: 0=WAKE, 1=N1, 2=N2, 3=N3, 4=REM. Expert arrays from
sleepedf_clean/stages/ use 255 for unscored; model prediction arrays use -1.
Sleep-EDF hypnogram stages 3 and 4 are both merged into N3.
"""

from __future__ import annotations

import os
from pathlib import Path

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
REPORT_DIR = MODULE_DIR / "reports"

STAGES5 = ["WAKE", "N1", "N2", "N3", "REM"]
INT_FROM_STAGE = {s: i for i, s in enumerate(STAGES5)}
STAGE_FROM_INT = {i: s for s, i in INT_FROM_STAGE.items()}

EEG_CH = "EEG Fpz-Cz"
EOG_CH = "EOG horizontal"
EMG_CH = "EMG submental"
RESP_CH = "Resp oro-nasal"

ANN_TO_STAGE = {
    "Sleep stage W": "WAKE",
    "Sleep stage 1": "N1",
    "Sleep stage 2": "N2",
    "Sleep stage 3": "N3",
    "Sleep stage 4": "N3",
    "Sleep stage R": "REM",
    "Sleep stage ?": "UNS",
}


def load_manifest(clean_root: Path = CLEAN_ROOT) -> pd.DataFrame:
    man_path = Path(clean_root) / "manifest.csv"
    if not man_path.is_file():
        raise FileNotFoundError(
            f"{man_path} not found. Run: python {MODULE_DIR / 'prepare_windows.py'}"
        )
    return pd.read_csv(man_path)
