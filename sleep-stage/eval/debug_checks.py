"""Debug matrix: epoch-shift sweep + class-permutation check for every run.
Usage: python debug_checks.py E01 E02 E11 E20"""
import sys
import itertools
import numpy as np
import pandas as pd
from pathlib import Path

EDGE = Path(__file__).resolve().parents[1]
TAB = EDGE.parent / "sleep-eda" / "tables"
CL = ["Wake", "N1", "N2", "N3", "REM"]
LAB = {c: i for i, c in enumerate(CL)}

ep = pd.read_parquet(TAB / "epochs_v3.parquet")
g = ep[ep.valid & ep.label5.isin(CL)][["stem", "cohort", "epoch", "label5"]].copy()
g = g.rename(columns={"epoch": "epoch_index"})
g["label"] = g.label5.map(LAB)

def macro(y, yp):
    f = []
    for i in range(5):
        tp = ((yp == i) & (y == i)).sum(); fp = ((yp == i) & (y != i)).sum(); fn = ((yp != i) & (y == i)).sum()
        f.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    return float(np.mean(f))

def load(run):
    d = EDGE / "runs" / run
    files = sorted(d.glob("*.parquet"))
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True) if files else None

for run in sys.argv[1:]:
    p = load(run)
    if p is None or len(p) == 0:
        print(f"{run}: no parquet files"); continue
    m = p.merge(g, on=["stem", "epoch_index"], how="inner")
    y = m.label.values
    P = m[[f"p_{c}" for c in CL]].values
    # shift sweep on epoch_index
    base = m[["stem", "epoch_index"] + [f"p_{c}" for c in CL]].copy()
    print(f"== {run} n={len(m)} ==")
    best = None
    for s in range(-5, 6):
        q = base.copy(); q["epoch_index"] = q["epoch_index"] - s
        mm = q.merge(g, on=["stem", "epoch_index"], how="inner")
        if len(mm) < 0.5 * len(m):
            continue
        v = macro(mm.label.values, mm[[f"p_{c}" for c in CL]].values.argmax(1))
        if best is None or v > best[0]:
            best = (v, s)
        print(f"  shift {s:+d}: {v:.4f}")
    print(f"  BEST shift {best[1]:+d} -> {best[0]:.4f} (nominal 0: {macro(y, P.argmax(1)):.4f})")
    # class permutation
    yp0 = P.argmax(1)
    bperm = (macro(y, yp0), tuple(range(5)))
    for perm in itertools.permutations(range(5)):
        v = macro(y, P[:, list(perm)].argmax(1))
        if v > bperm[0]:
            bperm = (v, perm)
    print(f"  best class perm {bperm[1]} -> {bperm[0]:.4f}")
    # predicted class distribution vs truth
    print("  pred hist:", np.bincount(yp0, minlength=5) / len(yp0))
    print("  true hist:", np.bincount(y, minlength=5) / len(y))
