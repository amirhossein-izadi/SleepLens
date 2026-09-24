"""YASA full-197 sweep: E01 (Fpz), E02 (Fpz+EOG), E03 (Pz+EOG). Skips done stems."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from yasa_adapter import YasaStager
from base import save_probs
import pandas as pd

TAB = Path(HERE).parents[1] / "sleep-eda" / "tables"
ep = pd.read_parquet(TAB / "epochs_v3.parquet")
stems = sorted(ep.stem.unique())

CFG = {"E01": ("EEG Fpz-Cz", None), "E02": ("EEG Fpz-Cz", "EOG horizontal"),
       "E03": ("EEG Pz-Oz", "EOG horizontal")}
which = sys.argv[1] if len(sys.argv) > 1 else "E01"
eeg, eog = CFG[which]
st = YasaStager(eeg=eeg, eog=eog, name=which)
outdir = HERE.parent / "runs" / which
done = {p.stem for p in outdir.glob("*.parquet")} if outdir.exists() else set()
for i, s in enumerate(stems):
    if s in done:
        continue
    try:
        save_probs(st.predict_record(s), which, s)
    except Exception as e:
        print(which, s, "FAIL", str(e)[:120])
    if (i + 1) % 25 == 0:
        print(which, f"{i+1}/{len(stems)}", flush=True)
print(which, "done")
