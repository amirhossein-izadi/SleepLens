"""Fusion + Viterbi (E12/E13/E14) on pilot: average probs of available models, then Viterbi
decode with transition matrix from sleep-eda (transition_v3_*)."""
import sys
import itertools
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
TAB = EDGE.parent / "sleep-eda" / "tables"
CL = ["Wake", "N1", "N2", "N3", "REM"]

ep = pd.read_parquet(TAB / "epochs_v3.parquet")
g = ep[ep.valid & ep.label5.isin(CL)][["stem", "cohort", "epoch", "label5"]].copy()
g = g.rename(columns={"epoch": "epoch_index"})
g["label"] = g.label5.map({c: i for i, c in enumerate(CL)})

def macro(y, yp):
    f = []
    for i in range(5):
        tp = ((yp == i) & (y == i)).sum(); fp = ((yp == i) & (y != i)).sum(); fn = ((yp != i) & (y == i)).sum()
        f.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    return float(np.mean(f))

def load(run):
    d = EDGE / "runs" / run
    fs = sorted(d.glob("*.parquet"))
    return pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True) if fs else None

def build_transition():
    """Combine SC+ST transition matrices from v3 (adjacency-only) as log-probs."""
    ms = []
    for co in ["SC", "ST"]:
        p = TAB / f"transition_v3_valid_{co}.csv"
        if p.exists():
            t = pd.read_csv(p, index_col=0).reindex(index=CL, columns=CL).fillna(0.0)
            ms.append(t.values)
    A = np.mean(ms, axis=0)
    A = A / A.sum(1, keepdims=True)
    return np.log(A + 1e-12)

def viterbi(P, logA, lam):
    """P: (T,5) probs. Returns MAP path with transition weight lam."""
    T = len(P)
    logP = np.log(P + 1e-12) + lam * logA[0]  # init: no prior; use uniform
    dp = np.log(P[0] + 1e-12)
    bp = np.zeros((T, 5), dtype=int)
    for t in range(1, T):
        cand = dp[:, None] + lam * logA
        bp[t] = cand.argmax(0)
        dp = cand.max(0) + np.log(P[t] + 1e-12)
    path = np.zeros(T, dtype=int)
    path[-1] = dp.argmax()
    for t in range(T - 2, -1, -1):
        path[t] = bp[t + 1, path[t + 1]]
    return path

logA = build_transition()
runs = {r: load(r) for r in ["E11", "E20", "E07"] if load(r) is not None}
print("available runs:", list(runs))

# E12: best-2 fusion (AnySleep + RSN), E13: best-3
def fuse(names):
    base = None
    for n in names:
        p = runs[n][["stem", "epoch_index"] + [f"p_{c}" for c in CL]].copy()
        base = p if base is None else base.merge(p, on=["stem", "epoch_index"], suffixes=("", f"_{n}"))
    # average by stem/epoch across model columns
    out = runs[names[0]][["stem", "epoch_index"]].copy()
    for c in CL:
        cols = [f"p_{c}"] + [f"p_{c}_{n}" for n in names[1:]]
        out[f"p_{c}"] = np.mean([base[col].values for col in cols], axis=0)
    return out

def evaluate_frame(df, tag, lam=0.0):
    m = df.merge(g, on=["stem", "epoch_index"], how="inner")
    y = m.label.values
    P = m[[f"p_{c}" for c in CL]].values
    if lam == 0.0:
        yp = P.argmax(1)
    else:
        yp = np.concatenate([viterbi(P[m.stem.values == s], logA, lam) for s in m.stem.unique()])
    print(f"{tag}: n={len(m)} macro={macro(y, yp):.4f}", flush=True)
    return macro(y, yp)

if len(runs) >= 2:
    f2 = fuse(["E11", "E20"])
    evaluate_frame(f2, "E12 fuse AnySleep+RSN")
    evaluate_frame(f2, "E12+Viterbi(0.3)", lam=0.3)
if len(runs) >= 3:
    f3 = fuse(["E11", "E20", "E07"])
    evaluate_frame(f3, "E13 fuse AnySleep+RSN+USleep")
    for lam in [0.1, 0.3, 0.5]:
        evaluate_frame(f3, f"E14 fuse3+Viterbi({lam})", lam=lam)
# single-model Viterbi for reference
for r in ["E11", "E20", "E07"]:
    if r in runs:
        for lam in [0.3]:
            evaluate_frame(runs[r], f"{r}+Viterbi({lam})", lam=lam)
