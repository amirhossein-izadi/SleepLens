"""Fold-honest ensemble selection: pick the best combo on 4 folds, evaluate on the 5th.
Guards against selecting the winning combo by looking at full-data macro."""
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

CANDS = ["E11", "E11a", "E11b", "E11c", "E20", "E00"]
P = {r: load(r) for r in CANDS}
base = None
for r in CANDS:
    base = P[r] if base is None else base.merge(P[r], on=["stem", "epoch_index"], how="inner")
m = base.merge(g, on=["stem", "epoch_index"], how="inner")
m["fold"] = m.stem.str[:5].map(fold_of)
m = m.dropna(subset=["fold"])
print("n:", len(m))

def macro(y, yp):
    f = []
    for i in range(5):
        tp = ((yp == i) & (y == i)).sum(); fp = ((yp == i) & (y != i)).sum(); fn = ((yp != i) & (y == i)).sum()
        f.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    return float(np.mean(f))

combos = []
for k in [1, 2, 3, 4]:
    combos += [list(c) for c in itertools.combinations(CANDS, k)]
print("combos:", len(combos))

oof_y, oof_p = [], []
picks = []
for f in sorted(m.fold.unique()):
    tr = m[m.fold != f]; te = m[m.fold == f]
    best = (-1, None)
    for c in combos:
        pr = np.mean([tr[[f"{n}_{x}" for x in CL]].values for n in c], axis=0)
        v = macro(tr.label.values, pr.argmax(1))
        if v > best[0]:
            best = (v, c)
    c = best[1]
    pr = np.mean([te[[f"{n}_{x}" for x in CL]].values for n in c], axis=0)
    oof_y.append(te.label.values); oof_p.append(pr.argmax(1))
    picks.append((f, "+".join(c), round(best[0], 4)))
    print(f"fold {f}: picked {picks[-1][1]} (train {picks[-1][2]})", flush=True)

y = np.concatenate(oof_y); yp = np.concatenate(oof_p)
print(f"\nE17 fold-honest ensemble: macro={macro(y, yp):.4f}")
e11 = m[[f"E11_{c}" for c in CL]].values
print(f"reference E11 alone     : macro={macro(m.label.values, e11.argmax(1)):.4f}")
