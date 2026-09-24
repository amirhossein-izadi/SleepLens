"""Universal adapter interface: every model returns T×5 probs on canonical v3 epoch indices."""
import numpy as np
import pandas as pd
from pathlib import Path

CLASSES = ["Wake", "N1", "N2", "N3", "REM"]
EDGE = Path(__file__).resolve().parents[1]

class SleepStager:
    name = "base"
    def predict_record(self, psg_path, hyp_path=None):
        """Return DataFrame: epoch_index, p_Wake, p_N1, p_N2, p_N3, p_REM.
        epoch_index = 30-s grid index from recording start (onset/30), matching epochs_v3."""
        raise NotImplementedError

def save_probs(df, run_id, stem):
    out = Path(EDGE, "runs", run_id)
    out.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out / f"{stem}.parquet", index=False)
    return out / f"{stem}.parquet"
