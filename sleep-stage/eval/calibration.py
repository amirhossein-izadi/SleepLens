"""Fold-honest calibration (E16): per-fold weight search + class-bias tuning on 4 folds,
applied to the held-out fold. Reports OOF macro (no test leakage)."""
import sys
import itertools
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
TAB = EDGE.parent / "sleep-eda" / "tables"
CL = ["Wake", "N1", "N2", "N3", "REM"]
lab = {c: i for i, c in enumerate(CL)}

ep = pd.read_parquet(TAB / "epochs_v3.parquet")
g = ep[ep.valid & ep.label5.isin(CL) & ep.in_bench][["stem", "cohort", "epoch", "label5"]].copy()
g = g.rename(columns={"epoch": "epoch_index"})
g["label"] = g.label5.map(lab)

folds = pd.read_csv(TAB / "folds5_v3.csv")
fold_of = dict(zip(folds.subject, folds.fold))

def load(run):
    d = EDGE / "runs" / run
    fs = sorted(d.glob("*.parquet"))
    df = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    return df[["stem", "epoch_index"] + [f"p_{c}" for c in CL]].rename(
        columns={f"p_{c}": f"{run}_{c}" for c in CL})

def macro(y, yp):
    f = []
    for i in range(5):
        tp = ((yp == i) & (y == i)).sum(); fp = ((yp == i) & (y != i)).sum(); fn = ((yp != i) & (y == i)).sum()
        f.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    return float(np.mean(f))

A = load("E11"); B = load("E20")
m = A.merge(B, on=["stem", "epoch_index"], how="inner").merge(g, on=["stem", "epoch_index"], how="inner")
m["fold"] = m.stem.str[:5].map(fold_of)
m = m.dropna(subset=["fold"])
print("n:", len(m))

PA = m[[f"E11_{c}" for c in CL]].values
PB = m[[f"E20_{c}" for c in CL]].values
y = m.label.values

def apply_bias(P, b):
    return (np.log(P + 1e-12) + b).argmax(1)

# grid: fusion weight w for AnySleep, and class biases from a small search
WGRID = [0.6, 0.7, 0.8, 0.9, 1.0]
BGRID = [np.array(v) for v in itertools.product([-0.4, -0.2, 0.0, 0.2, 0.4], repeat=2)]  # biases for N1, REM
oof = []
for f in sorted(m.fold.unique()):
    tr = m.fold != f
    te = m.fold == f
    Ptr = WGRID and None
    best = (-1, None, None)
    for w in WGRID:
        P = w * PA[tr.values] + (1 - w) * PB[tr.values]
        for bn, br in [(b[0], b[1]) for b in BGRID]:
            b = np.array([0.0, bn, 0.0, 0.0, br])
            v = macro(y[tr.values], apply_bias(P, b))
            if v > best[0]:
                best = (v, w, (bn, br))
    v, w, (bn, br) = best
    Pte = w * PA[te.values] + (1 - w) * PB[te.values]
    yp = apply_bias(Pte, np.array([0.0, bn, 0.0, 0.0, br]))
    oof.append((te.values, yp))
    print(f"fold {f}: w={w} bN1={bn} bREM={br} (train {v:.4f})", flush=True)

y_all = np.concatenate([y[t] for t, _ in oof])
yp_all = np.concatenate([p for _, p in oof])
print(f"\nE16 OOF calibrated fusion: macro={macro(y_all, yp_all):.4f}")
# reference: E11 alone on same epochs
print(f"reference E11 alone     : macro={macro(y, PA.argmax(1)):.4f}")
print(f"reference E20 alone     : macro={macro(y, PB.argmax(1)):.4f}")
