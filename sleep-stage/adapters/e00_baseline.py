"""E00 cheap baseline: LightGBM on per-epoch bandpower features (from sleep-eda parquets).
Subject-wise CV using folds5_v3. Sanity floor + ensemble diversity."""
import sys
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
TAB = EDGE.parent / "sleep-eda" / "tables"
CL = ["Wake", "N1", "N2", "N3", "REM"]

def macro(y, yp):
    f = []
    for i in range(5):
        tp = ((yp == i) & (y == i)).sum(); fp = ((yp == i) & (y != i)).sum(); fn = ((yp != i) & (y == i)).sum()
        f.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    return float(np.mean(f))

feats = []
for b in [0, 1, 2]:
    p = TAB / f"baseline_full_b{b}.parquet"
    if p.exists():
        feats.append(pd.read_parquet(p))
df = pd.concat(feats, ignore_index=True)
df = df[df.label.isin(CL)].copy()
df["stem5"] = df.recording_id.str[:5]
print("epochs:", len(df), "stems:", df.recording_id.nunique())

folds = pd.read_csv(TAB / "folds5_v3.csv")
fold_of = dict(zip(folds.subject, folds.fold))
df["fold"] = df.stem5.map(fold_of)
df = df.dropna(subset=["fold"])
print("after fold join:", len(df))

FEATS = ["eeg_std", "eeg_ptp", "zcr", "delta", "theta", "alpha", "sigma", "beta",
         "eog_ptp", "eog_std", "emg_rms"]
import lightgbm as lgb

all_rows = []
for f in sorted(df.fold.unique()):
    tr = df[df.fold != f]
    te = df[df.fold == f]
    clf = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=63,
                             class_weight="balanced", n_jobs=8, verbose=-1)
    clf.fit(tr[FEATS], tr.label.map({c: i for i, c in enumerate(CL)}))
    P = clf.predict_proba(te[FEATS])
    yp = P.argmax(1)
    y = te.label.map({c: i for i, c in enumerate(CL)}).values
    print(f"fold {f}: n={len(te)} macro={macro(y, yp):.4f}", flush=True)
    out = pd.DataFrame({"stem": te.recording_id.str[:6], "epoch_index": te.epoch_index,
                        "fold": f})
    for j, c in enumerate(CL):
        out[f"p_{c}"] = P[:, j]
    out["label"] = y
    all_rows.append(out)

res = pd.concat(all_rows, ignore_index=True)
outdir = EDGE / "runs" / "E00"
outdir.mkdir(parents=True, exist_ok=True)
res.to_parquet(outdir / "oof.parquet", index=False)
print("E00 OOF macro:", round(macro(res.label.values, res[[f"p_{c}" for c in CL]].values.argmax(1)), 4))
