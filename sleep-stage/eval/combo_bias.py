"""E18: fold-honest best combo + class-bias calibration stacked."""
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
g = ep[ep.valid & ep.label5.isin(CL) & ep.in_bench][["stem", "epoch", "label5"]].copy()
g = g.rename(columns={"epoch": "epoch_index"})
g["label"] = g.label5.map(lab)
folds = pd.read_csv(TAB / "folds5_v3.csv")
fold_of = dict(zip(folds.subject, folds.fold))

def load(run):
    fs = sorted((EDGE / "runs" / run).glob("*.parquet"))
    df = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    return df[["stem", "epoch_index"] + [f"p_{c}" for c in CL]].rename(
        columns={f"p_{c}": f"{run}_{c}" for c in CL})

COMBO = ["E11", "E11a", "E11b", "E00"]
base = None
for r in COMBO:
    base = load(r) if base is None else base.merge(load(r), on=["stem", "epoch_index"], how="inner")
m = base.merge(g, on=["stem", "epoch_index"], how="inner")
m["fold"] = m.stem.str[:5].map(fold_of)
m = m.dropna(subset=["fold"])

def macro(y, yp):
    f = []
    for i in range(5):
        tp = ((yp == i) & (y == i)).sum(); fp = ((yp == i) & (y != i)).sum(); fn = ((yp != i) & (y == i)).sum()
        f.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    return float(np.mean(f))

def bias_apply(P, b):
    return (np.log(P + 1e-12) + b).argmax(1)

BGRID = [np.array([0, bn, 0, 0, br]) for bn, br in itertools.product([-0.2, 0, 0.2, 0.4], repeat=2)]
oof_y, oof_p = [], []
for f in sorted(m.fold.unique()):
    tr = m[m.fold != f]; te = m[m.fold == f]
    Ptr = np.mean([tr[[f"{n}_{c}" for c in CL]].values for n in COMBO], axis=0)
    best = (-1, None)
    for b in BGRID:
        v = macro(tr.label.values, bias_apply(Ptr, b))
        if v > best[0]:
            best = (v, b)
    b = best[1]
    Pte = np.mean([te[[f"{n}_{c}" for c in CL]].values for n in COMBO], axis=0)
    oof_y.append(te.label.values); oof_p.append(bias_apply(Pte, b))
    print(f"fold {f}: bN1={b[1]} bREM={b[4]} (train {best[0]:.4f})", flush=True)

y = np.concatenate(oof_y); yp = np.concatenate(oof_p)
mf = macro(y, yp)
print(f"\nE18 combo+bias OOF: macro={mf:.4f}")
# per-class
f1 = []
for i in range(5):
    tp = ((yp == i) & (y == i)).sum(); fp = ((yp == i) & (y != i)).sum(); fn = ((yp != i) & (y == i)).sum()
    f1.append(round(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0, 3))
print("per-class:", dict(zip(CL, f1)))
