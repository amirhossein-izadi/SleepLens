"""AnySleep channel ablation (E11a/b/c): Fpz / Pz / 2EEG. Full-197 sweep."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import torch  # FIRST
import pandas as pd
from anysleep_adapter import predict_record
from base import save_probs

TAB = HERE.parents[1] / "sleep-eda" / "tables"
stems = sorted(pd.read_parquet(TAB / "epochs_v3.parquet").stem.unique())

CFG = {
    "E11a": ("EEG Fpz-Cz",),
    "E11b": ("EEG Pz-Oz",),
    "E11c": ("EEG Fpz-Cz", "EEG Pz-Oz"),
}
which = sys.argv[1] if len(sys.argv) > 1 else "E11a"
channels = CFG[which]
outdir = HERE.parent / "runs" / which
done = {p.stem for p in outdir.glob("*.parquet")} if outdir.exists() else set()
for i, s in enumerate(stems):
    if s in done:
        continue
    try:
        df = predict_record(s, channels=channels)
        save_probs(df, which, s)
    except Exception as e:
        print(which, s, "FAIL", str(e)[:110], flush=True)
    if (i + 1) % 25 == 0:
        print(which, f"{i+1}/{len(stems)}", flush=True)
print(which, "done")
