"""Full-data fusion (E12/E13), Viterbi (E14), tiny subject-wise stacker (E15).
Uses complete 197-rec runs. Stacker trained with subject-wise CV (folds5_v3)."""
import sys
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
TAB = EDGE.parent / "sleep-eda" / "tables"
CL = ["Wake", "N1", "N2", "N3", "REM"]
lab = {c: i for i, c in enumerate(CL)}

ep = pd.read_parquet(TAB / "epochs_v3.parquet")
g = ep[ep.valid & ep.label5.isin(CL)][["stem", "cohort", "epoch", "label5", "in_bench"]].copy()
g = g.rename(columns={"epoch": "epoch_index"})
g["label"] = g.label5.map(lab)
gb = g[g.in_bench]

def macro(y, yp):
    f = []
    for i in range(5):
        tp = ((yp == i) & (y == i)).sum(); fp = ((yp == i) & (y != i)).sum(); fn = ((yp != i) & (y == i)).sum()
        f.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    return float(np.mean(f))

def load(run):
    d = EDGE / "runs" / run
    fs = sorted(d.glob("*.parquet"))
    if not fs:
        return None
    df = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    return df

RUNS = ["E11", "E11a", "E11b", "E11c", "E20", "E00"]
probs = {}
for r in RUNS:
    df = load(r)
    if df is None:
        continue
    probs[r] = df[["stem", "epoch_index"] + [f"p_{c}" for c in CL]].rename(
        columns={f"p_{c}": f"{r}_{c}" for c in CL})

def build(names, window=gb):
    base = None
    for n in names:
        p = probs[n]
        base = p if base is None else base.merge(p, on=["stem", "epoch_index"], how="inner")
    m = base.merge(window, on=["stem", "epoch_index"], how="inner")
    return m

def fused(names):
    m = build(names)
    out = m[["stem", "cohort", "label"]].copy()
    for c in CL:
        out[f"p_{c}"] = np.mean([m[f"{n}_{c}"].values for n in names], axis=0)
    return out

def evaluate(df, tag):
    y = df.label.values
    P = df[[f"p_{c}" for c in CL]].values
    yp = P.argmax(1)
    print(f"{tag}: n={len(df)} macro={macro(y, yp):.4f}", flush=True)
    return macro(y, yp)

# --- fusion ---
if all(r in probs for r in ["E11", "E20"]):
    f2 = fused(["E11", "E20"]); evaluate(f2, "E12 AnySleep3ch+RSN")
if all(r in probs for r in ["E11", "E20", "E00"]):
    f3 = fused(["E11", "E20", "E00"]); evaluate(f3, "E13 AnySleep3ch+RSN+LightGBM")
if all(r in probs for r in ["E11", "E11a", "E20", "E00"]):
    f4 = fused(["E11", "E11a", "E20", "E00"]); evaluate(f4, "E13b +Fpz-only")

# --- Viterbi on best fusion and on E11 ---
def build_transition():
    ms = []
    for co in ["SC", "ST"]:
        p = TAB / f"transition_v3_valid_{co}.csv"
        if p.exists():
            t = pd.read_csv(p, index_col=0).reindex(index=CL, columns=CL).fillna(0.0)
            ms.append(t.values)
    A = np.mean(ms, axis=0)
    return np.log(A / A.sum(1, keepdims=True) + 1e-12)

logA = build_transition()
def viterbi(P, lam):
    T = len(P)
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

def evaluate_vit(df, tag, lam):
    y = df.label.values
    P = df[[f"p_{c}" for c in CL]].values
    yp = np.concatenate([viterbi(P[df.stem.values == s], lam) for s in df.stem.unique()])
    print(f"{tag} lam={lam}: macro={macro(y, yp):.4f}", flush=True)

if all(r in probs for r in ["E11", "E20", "E00"]):
    f3 = fused(["E11", "E20", "E00"])
    for lam in [0.1, 0.2, 0.3, 0.5]:
        evaluate_vit(f3, "E14 fusion+Viterbi", lam)
e11 = probs["E11"].merge(gb, on=["stem", "epoch_index"], how="inner")
for lam in [0.1, 0.2, 0.3]:
    evaluate_vit(e11.rename(columns={f"E11_{c}": f"p_{c}" for c in CL}), "E11+Viterbi", lam)
