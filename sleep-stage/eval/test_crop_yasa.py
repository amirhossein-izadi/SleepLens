"""Advisor test C: crop recording to BENCHMARK_30 interval BEFORE inference.
YASA only (context-sensitive model). Compare against full-recording inference."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "adapters"))
sys.path.insert(0, str(HERE))
import numpy as np
import pandas as pd
import mne
import yasa
from canonical import load_canonical

TAB = HERE.parents[1] / "sleep-eda" / "tables"
ep = pd.read_parquet(TAB / "epochs_v3.parquet")
CL = ["Wake", "N1", "N2", "N3", "REM"]

def macro(y, yp):
    f = []
    for i in range(5):
        tp = ((yp == i) & (y == i)).sum(); fp = ((yp == i) & (y != i)).sum(); fn = ((yp != i) & (y == i)).sum()
        f.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    return float(np.mean(f))

for stem in ["SC4001", "SC4041", "ST7011"]:
    g = ep[(ep.stem == stem) & ep.valid & ep.in_bench]
    if len(g) == 0:
        print(stem, "no bench epochs"); continue
    e0, e1 = int(g.epoch.min()), int(g.epoch.max())
    data = load_canonical(stem, channels=("EEG Fpz-Cz", "EOG horizontal"))
    sf = 100
    sl = slice(e0 * 30 * sf, (e1 + 1) * 30 * sf)
    x = data["EEG Fpz-Cz"][sl].reshape(1, -1)
    e = data["EOG horizontal"][sl].reshape(1, -1)
    raw = mne.io.RawArray(np.vstack([x, e]), mne.create_info(["EEG Fpz-Cz", "EOG horizontal"], 100.0, ["eeg", "eog"]), verbose=False)
    sls = yasa.SleepStaging(raw, eeg_name="EEG Fpz-Cz", eog_name="EOG horizontal")
    hyp = sls.predict()
    proba = hyp.proba.rename(columns={"W": "Wake", "WAKE": "Wake", "R": "REM"})
    pred = np.array([CL.index(proba.iloc[i][CL].idxmax()) for i in range(len(proba))])
    pred = np.array([CL.index(c) if c in CL else 0 for c in (proba[CL].idxmax(axis=1))])
    y = g.sort_values("epoch").label5.map({c: i for i, c in enumerate(CL)}).values
    n = min(len(y), len(pred))
    print(f"{stem} crop-BENCH: n={n} macro={macro(y[:n], pred[:n]):.4f}")

    # reference: full-recording run from E02
    full = pd.read_parquet(HERE.parent / "runs" / "E02" / f"{stem}.parquet")
    m = full.merge(g[["epoch", "label5"]], left_on="epoch_index", right_on="epoch", how="inner")
    yp = m[[f"p_{c}" for c in CL]].values.argmax(1)
    yf = m.label5.map({c: i for i, c in enumerate(CL)}).values
    print(f"{stem} full-rec  : n={len(m)} macro={macro(yf, yp):.4f}")
