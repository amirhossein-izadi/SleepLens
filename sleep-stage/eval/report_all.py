"""Unified report: evaluate every run that has data, both windows, print one table."""
import sys
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
TAB = EDGE.parent / "sleep-eda" / "tables"
CL = ["Wake", "N1", "N2", "N3", "REM"]

ep = pd.read_parquet(TAB / "epochs_v3.parquet")
lab = {c: i for i, c in enumerate(CL)}

def macro(y, yp):
    f = []
    for i in range(5):
        tp = ((yp == i) & (y == i)).sum(); fp = ((yp == i) & (y != i)).sum(); fn = ((yp != i) & (y == i)).sum()
        f.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    return float(np.mean(f))

NAMES = {
    "E00": "LightGBM bandpower", "E01": "YASA Fpz", "E02": "YASA Fpz+EOG",
    "E02c": "YASA Fpz+EOG (crop)", "E03": "YASA Pz+EOG",
    "E06": "SOMNUS (ensemble)", "E07": "SLEEPYLAND U-Sleep",
    "E08": "SLEEPYLAND DeepResNet", "E09": "SLEEPYLAND SleepTransformer",
    "E10": "SleepFMStager", "E11": "AnySleep 3ch", "E11a": "AnySleep Fpz only",
    "E11b": "AnySleep Pz only", "E11c": "AnySleep 2EEG", "E11d": "AnySleep Fpz+EOG",
    "E16": "Ensemble 0.7 AnySleep+0.3 RSN +bias", "E17": "Ensemble AnySleepx3+LGBM",
    "E18": "Ensemble AnySleepx3+LGBM +bias", "E20": "RobustSleepNet Fpz",
    "E21": "U-Sleep CSDP (open weights)",
    "E19": "Ens v2 ANYx2+USleepCSDP+LGBM", "E19b": "Ens v2 +bias",
}

def load(run):
    d = EDGE / "runs" / run
    fs = sorted(d.glob("*.parquet"))
    if not fs:
        return None
    return pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)

def ev(df, window):
    g = ep[ep.valid & ep.label5.isin(CL)][["stem", "cohort", "epoch", "label5", "in_bench"]].copy()
    g = g.rename(columns={"epoch": "epoch_index"})
    if window != "valid":
        g = g[g[window]]
    g["label"] = g.label5.map(lab)
    keep = ["stem", "epoch_index"] + [f"p_{c}" for c in CL]
    m = df[keep].merge(g, on=["stem", "epoch_index"], how="inner")
    if len(m) == 0:
        return None
    y = m.label.values
    P = m[[f"p_{c}" for c in CL]].values
    yp = P.argmax(1)
    out = {"n": len(m), "macro": macro(y, yp)}
    f1 = []
    for i in range(5):
        tp = ((yp == i) & (y == i)).sum(); fp = ((yp == i) & (y != i)).sum(); fn = ((yp != i) & (y == i)).sum()
        f1.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    out.update({f"f1_{c}": v for c, v in zip(CL, f1)})
    for co in ["SC", "ST"]:
        s = m[m.cohort == co]
        if len(s):
            out[f"macro_{co}"] = macro(s.label.values, s[[f"p_{c}" for c in CL]].values.argmax(1))
    return out

rows = []
for run, name in NAMES.items():
    df = load(run)
    if df is None:
        continue
    nfiles = len(sorted((EDGE / "runs" / run).glob("*.parquet")))
    r = ev(df, "in_bench")
    rf = ev(df, "valid")
    if r is None:
        continue
    rows.append({"run": run, "model": name, "recs": nfiles,
                 "bench_macro": round(r["macro"], 4), "SC": round(r.get("macro_SC", np.nan), 3),
                 "ST": round(r.get("macro_ST", np.nan), 3),
                 "N1": round(r["f1_N1"], 3), "N3": round(r["f1_N3"], 3), "REM": round(r["f1_REM"], 3),
                 "full_macro": round(rf["macro"], 4) if rf else np.nan})

t = pd.DataFrame(rows).sort_values("bench_macro", ascending=False)
print(t.to_string(index=False))
t.to_csv(EDGE / "docs" / "results_table.csv", index=False)
