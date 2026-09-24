"""YASA full-197 sweep with crop-before-inference (advisor test C). run_id: E01c/E02c/E03c."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from yasa_adapter import YasaStager
from base import save_probs
import pandas as pd

TAB = HERE.parents[1] / "sleep-eda" / "tables"
ep = pd.read_parquet(TAB / "epochs_v3.parquet")
stems = sorted(ep.stem.unique())

CFG = {"E01c": ("EEG Fpz-Cz", None), "E02c": ("EEG Fpz-Cz", "EOG horizontal"),
       "E03c": ("EEG Pz-Oz", "EOG horizontal")}
which = sys.argv[1] if len(sys.argv) > 1 else "E02c"
eeg, eog = CFG[which]
st = YasaStager(eeg=eeg, eog=eog, name=which, crop_bench=True)
outdir = HERE.parent / "runs" / which
done = {p.stem for p in outdir.glob("*.parquet")} if outdir.exists() else set()
for i, s in enumerate(stems):
    if s in done:
        continue
    try:
        df = st.predict_record(s)
        g = ep[(ep.stem == s) & ep.valid & ep.in_bench]
        if len(g):
            e0 = int(g.epoch.min())
            df["epoch_index"] = df["epoch_index"] + e0
        save_probs(df, which, s)
    except Exception as e:
        print(which, s, "FAIL", str(e)[:100])
    if (i + 1) % 25 == 0:
        print(which, f"{i+1}/{len(stems)}", flush=True)
print(which, "done")
