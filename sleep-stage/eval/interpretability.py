"""Interpretability pack: (1) TreeSHAP on E00 LightGBM, (4) confidence/uncertainty analysis.
Outputs: docs/interp_shap_global.csv, docs/interp_shap_class.csv, docs/interp_confidence.csv"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
TAB = EDGE.parent / "sleep-eda" / "tables"
CL = ["Wake", "N1", "N2", "N3", "REM"]
lab = {c: i for i, c in enumerate(CL)}
FEATS = ["eeg_std", "eeg_ptp", "zcr", "delta", "theta", "alpha", "sigma", "beta",
         "eog_ptp", "eog_std", "emg_rms"]

# --- load features + folds ---
feats = []
for b in [0, 1, 2]:
    p = TAB / f"baseline_full_b{b}.parquet"
    if p.exists():
        feats.append(pd.read_parquet(p))
df = pd.concat(feats, ignore_index=True)
df = df[df.label.isin(CL)].copy()
df["stem5"] = df.recording_id.str[:5]
folds = pd.read_csv(TAB / "folds5_v3.csv")
fold_of = dict(zip(folds.subject, folds.fold))
df["fold"] = df.stem5.map(fold_of)
df = df.dropna(subset=["fold"])
y = df.label.map(lab).values

import lightgbm as lgb
import shap

# train on folds 1-4, explain on fold 0 (held out)
tr = df[df.fold != 0]; te = df[df.fold == 0]
clf = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=63,
                         class_weight="balanced", n_jobs=8, verbose=-1)
clf.fit(tr[FEATS], tr.label.map(lab))

samp = te.sample(min(4000, len(te)), random_state=0)
X = samp[FEATS]
expl = shap.TreeExplainer(clf)
sv = expl.shap_values(X)  # list per class (older shap) or 3D array
if isinstance(sv, list):
    sv = np.stack(sv, axis=2)  # (n, f, 5)
print("shap array:", sv.shape)

# global mean |SHAP| per feature
glob = pd.DataFrame({"feature": FEATS,
                     "mean_abs_shap": np.abs(sv).mean(axis=(0, 2))}).sort_values("mean_abs_shap", ascending=False)
glob.to_csv(EDGE / "docs" / "interp_shap_global.csv", index=False)
print("\nGLOBAL (mean |SHAP|):"); print(glob.to_string(index=False))

# per-class top features
rows = []
for j, c in enumerate(CL):
    imp = np.abs(sv[:, :, j]).mean(0)
    order = np.argsort(-imp)
    rows.append({"class": c, **{f"#{k+1}": FEATS[i] for k, i in enumerate(order[:4])},
                 **{f"val_{k+1}": round(float(imp[i]), 4) for k, i in enumerate(order[:4])}})
cls = pd.DataFrame(rows)
cls.to_csv(EDGE / "docs" / "interp_shap_class.csv", index=False)
print("\nPER-CLASS top features:"); print(cls.to_string(index=False))

# --- confidence analysis on the final ensemble (E18 combo) ---
def load(run):
    fs = sorted((EDGE / "runs" / run).glob("*.parquet"))
    d = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    return d[["stem", "epoch_index"] + [f"p_{c}" for c in CL]].rename(
        columns={f"p_{c}": f"{run}_{c}" for c in CL})
COMBO = ["E11", "E11a", "E11b", "E00"]
base = None
for r in COMBO:
    base = load(r) if base is None else base.merge(load(r), on=["stem", "epoch_index"], how="inner")
ep = pd.read_parquet(TAB / "epochs_v3.parquet")
g = ep[ep.valid & ep.label5.isin(CL) & ep.in_bench][["stem", "epoch", "label5"]].rename(columns={"epoch": "epoch_index"})
g["label"] = g.label5.map(lab)
m = base.merge(g, on=["stem", "epoch_index"], how="inner")
P = np.mean([m[[f"{n}_{c}" for c in CL]].values for n in COMBO], axis=0)
conf = P.max(1)
ent = -(P * np.log(P + 1e-12)).sum(1)
correct = (P.argmax(1) == m.label.values)
rows = []
for lo, hi in [(0, .4), (.4, .5), (.5, .6), (.6, .7), (.7, .8), (.8, .9), (.9, 1.001)]:
    msk = (conf >= lo) & (conf < hi)
    if msk.sum():
        rows.append({"conf_bin": f"{lo:.1f}-{hi:.1f}", "n": int(msk.sum()),
                     "share": round(float(msk.mean()), 4),
                     "accuracy": round(float(correct[msk].mean()), 4),
                     "mean_entropy": round(float(ent[msk].mean()), 4)})
cc = pd.DataFrame(rows)
cc.to_csv(EDGE / "docs" / "interp_confidence.csv", index=False)
print("\nCONFIDENCE CALIBRATION (ensemble):"); print(cc.to_string(index=False))
