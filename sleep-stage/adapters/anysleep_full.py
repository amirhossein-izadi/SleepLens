"""AnySleep 3ch full-197 sweep (E11) with resume."""
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
outdir = HERE.parent / "runs" / "E11"
done = {p.stem for p in outdir.glob("*.parquet")} if outdir.exists() else set()
for i, s in enumerate(stems):
    if s in done:
        continue
    try:
        save_probs(predict_record(s), "E11", s)
    except Exception as e:
        print("E11", s, "FAIL", str(e)[:110], flush=True)
    if (i + 1) % 25 == 0:
        print("E11", f"{i+1}/{len(stems)}", flush=True)
print("E11 done")
