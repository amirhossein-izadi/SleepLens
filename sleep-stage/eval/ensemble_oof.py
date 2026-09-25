"""Materialize fold-honest OOF predictions for the ensemble systems (E16/E17/E18)
as runs/<id>/*.parquet, so the standard evaluator can report the full metric suite.

E16: w*AnySleep3ch + (1-w)*RSN + class biases (w, bN1, bREM selected per fold)
E17: equal avg of AnySleep3ch + AnySleepFpz + AnySleepPz + LightGBM (fixed combo)
E18: E17 combo + class biases (bN1, bREM selected per fold)
"""
import itertools
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
TAB = EDGE.parent / "sleep-eda" / "tables"
CL = ["Wake", "N1", "N2", "N3", "REM"]
lab = {c: i for i, c in enumerate(CL)}
RUNS = EDGE / "runs"

ep = pd.read_parquet(TAB / "epochs_v3.parquet")
g = ep[ep.valid & ep.label5.isin(CL)][["stem", "epoch", "label5"]].rename(
    columns={"epoch": "epoch_index"})
g["label"] = g.label5.map(lab)
folds = pd.read_csv(TAB / "folds5_v3.csv")
fold_of = dict(zip(folds.subject, folds.fold))

def load(run):
    fs = sorted((RUNS / run).glob("*.parquet"))
    d = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    return d[["stem", "epoch_index"] + [f"p_{c}" for c in CL]].rename(
        columns={f"p_{c}": f"{run}_{c}" for c in CL})

def macro(y, yp):
    f = []
    for i in range(5):
        tp = ((yp == i) & (y == i)).sum(); fp = ((yp == i) & (y != i)).sum(); fn = ((yp != i) & (y == i)).sum()
        f.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    return float(np.mean(f))

def merge_members(members):
    base = None
    for r in members:
        base = load(r) if base is None else base.merge(load(r), on=["stem", "epoch_index"], how="inner")
    m = base.merge(g, on=["stem", "epoch_index"], how="inner")
    m["fold"] = m.stem.str[:5].map(fold_of)
    return m.dropna(subset=["fold"]).reset_index(drop=True)

def probs_of(m, members):
    P = np.mean([m[[f"{r}_{c}" for c in CL]].values for r in members], axis=0)
    return P

def apply_bias(P, b):
    Q = P * np.exp(np.asarray(b))[None, :]
    return Q / Q.sum(1, keepdims=True)

def save_oof(m, P, run_id):
    out = pd.DataFrame({"stem": m.stem.values, "epoch_index": m.epoch_index.values})
    for j, c in enumerate(CL):
        out[f"p_{c}"] = P[:, j]
    d = RUNS / run_id
    d.mkdir(exist_ok=True)
    for stem, sub in out.groupby("stem", sort=True):
        sub.to_parquet(d / f"{stem}.parquet", index=False)
    print(f"{run_id}: saved {out.stem.nunique()} recordings, {len(out)} epochs")

# ---------- E17 / E18: combo fixed ----------
COMBO = ["E11", "E11a", "E11b", "E00"]
m = merge_members(COMBO)
P17 = np.zeros((len(m), 5))
P18 = np.zeros((len(m), 5))
BGRID = [np.array([0, bn, 0, 0, br]) for bn, br in itertools.product([-0.2, 0, 0.2, 0.4], repeat=2)]
for f in sorted(m.fold.unique()):
    tr = m.fold != f; te = ~tr
    Ptr = probs_of(m[tr], COMBO); Pte = probs_of(m[te], COMBO)
    P17[te.values] = Pte
    best = (-1, None)
    for b in BGRID:
        v = macro(m.label.values[tr], apply_bias(Ptr, b).argmax(1))
        if v > best[0]:
            best = (v, b)
    P18[te.values] = apply_bias(Pte, best[1])
    print(f"E18 fold {f}: bN1={best[1][1]} bREM={best[1][4]} (train {best[0]:.4f})", flush=True)
save_oof(m, P17, "E17")
save_oof(m, P18, "E18")

# ---------- E16: w*E11 + (1-w)*E20 + biases ----------
m2 = merge_members(["E11", "E20"])
P16 = np.zeros((len(m2), 5))
WG = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
for f in sorted(m2.fold.unique()):
    tr = m2.fold != f; te = ~tr
    A = m2[tr][[f"E11_{c}" for c in CL]].values
    B = m2[tr][[f"E20_{c}" for c in CL]].values
    Ate = m2[te][[f"E11_{c}" for c in CL]].values
    Bte = m2[te][[f"E20_{c}" for c in CL]].values
    best = (-1, None)
    for w in WG:
        Ptr = w * A + (1 - w) * B
        for b in BGRID:
            v = macro(m2.label.values[tr], apply_bias(Ptr, b).argmax(1))
            if v > best[0]:
                best = (v, (w, b))
    w, b = best[1]
    P16[te.values] = apply_bias(w * Ate + (1 - w) * Bte, b)
    print(f"E16 fold {f}: w={w} bN1={b[1]} bREM={b[4]} (train {best[0]:.4f})", flush=True)
save_oof(m2, P16, "E16")
print("done")
