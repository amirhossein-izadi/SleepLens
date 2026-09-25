"""N1/REM-focused ensemble analysis: per-class F1 for every combination (saved preds, fast)."""
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

def load(run):
    fs = sorted((EDGE / "runs" / run).glob("*.parquet"))
    df = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    return df[["stem", "epoch_index"] + [f"p_{c}" for c in CL]].rename(
        columns={f"p_{c}": f"{run}_{c}" for c in CL})

RUNS = ["E11", "E11c", "E11a", "E11b", "E20", "E00", "E02c"]
P = {}
for r in RUNS:
    try:
        P[r] = load(r)
    except Exception:
        pass
print("loaded:", list(P))

def f1s(y, yp):
    out = []
    for i in range(5):
        tp = ((yp == i) & (y == i)).sum(); fp = ((yp == i) & (y != i)).sum(); fn = ((yp != i) & (y == i)).sum()
        out.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    return out

def eval_combo(names, w=None):
    base = None
    for n in names:
        base = P[n] if base is None else base.merge(P[n], on=["stem", "epoch_index"], how="inner")
    m = base.merge(g, on=["stem", "epoch_index"], how="inner")
    w = w or [1 / len(names)] * len(names)
    pr = sum(wi * m[[f"{n}_{c}" for c in CL]].values for wi, n in zip(w, names))
    y = m.label.values
    yp = pr.argmax(1)
    f = f1s(y, yp)
    return np.mean(f), f, len(m)

print("\n== singles ==")
for r in RUNS:
    mf, f, n = eval_combo([r])
    print(f"{r:5s} macro={mf:.4f} N1={f[1]:.3f} REM={f[4]:.3f} N3={f[3]:.3f} n={n}")

print("\n== equal-weight ensembles ==")
for k in [2, 3, 4, 5]:
    for combo in itertools.combinations([r for r in ["E11", "E20", "E00", "E11a", "E11c"] if r in P], k):
        mf, f, n = eval_combo(list(combo))
        print(f"{'+'.join(combo):22s} macro={mf:.4f} N1={f[1]:.3f} REM={f[4]:.3f} N3={f[3]:.3f}")

print("\n== weighted AnySleep/RSN sweep (N1 focus) ==")
for w in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
    mf, f, n = eval_combo(["E11", "E20"], [w, 1 - w])
    print(f"w={w}: macro={mf:.4f} N1={f[1]:.3f} REM={f[4]:.3f}")
