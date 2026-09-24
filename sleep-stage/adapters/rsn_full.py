"""RSN full-197 sweep. Skips done stems."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rsn_adapter import predict_record
from base import save_probs
import pandas as pd

TAB = HERE.parents[1] / "sleep-eda" / "tables"
ep = pd.read_parquet(TAB / "epochs_v3.parquet")
stems = sorted(ep.stem.unique())
outdir = HERE.parent / "runs" / "E20"
done = {p.stem for p in outdir.glob("*.parquet")} if outdir.exists() else set()
for i, s in enumerate(stems):
    if s in done:
        continue
    try:
        save_probs(predict_record(s), "E20", s)
    except Exception as e:
        print("E20", s, "FAIL", str(e)[:120])
    if (i + 1) % 20 == 0:
        print("E20", f"{i+1}/{len(stems)}", flush=True)
print("E20 done")
