"""E24: 5 parallel binary class experts (one per class) + user's combination rules.

Per fold (fold-honest):
  - For each class c: choose the expert MODEL k_c = argmax binary-F1(p_c >= t) on the other 4 folds,
    over a pool of our models; record its threshold t_c and its train binary F1 (reliability).
  - Apply to held-out fold; combine:
      |S| == 1  -> that class
      |S| > 1   -> vote: argmax_c p_c * f1_c        (E24)   or   (p_c/t_c) * f1_c  (E24b)
      |S| == 0  -> fallback to the most accurate overall model = E19 argmax
"""
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
TAB = EDGE.parent / "sleep-eda" / "tables"
RUNS = EDGE / "runs"
CL = ["Wake", "N1", "N2", "N3", "REM"]
lab = {c: i for i, c in enumerate(CL)}

POOL = ["E11", "E11a", "E11b", "E11c", "E11d", "E16", "E17", "E18", "E19", "E19b", "E20", "E21", "E00"]
FB = "E19"  # fallback model (best overall system)

ep = pd.read_parquet(TAB / "epochs_v3.parquet")
g = ep[ep.valid & ep.label5.isin(CL) & ep.in_bench][["stem", "epoch", "label5"]].rename(
    columns={"epoch": "epoch_index"})
g["label"] = g.label5.map(lab)
folds = pd.read_csv(TAB / "folds5_v3.csv")
fold_of = dict(zip(folds.subject, folds.fold))

def load(run):
    fs = sorted((RUNS / run).glob("*.parquet"))
    d = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    return d[["stem", "epoch_index"] + [f"p_{c}" for c in CL]].rename(
        columns={f"p_{c}": f"{run}_{c}" for c in CL})

m = None
for r in POOL:
    d = load(r)
    m = d if m is None else m.merge(d, on=["stem", "epoch_index"], how="inner")
m = m.merge(g, on=["stem", "epoch_index"], how="inner")
m["fold"] = m.stem.str[:5].map(fold_of)
m = m.dropna(subset=["fold"]).reset_index(drop=True)
A = np.stack([m[[f"{r}_{c}" for c in CL]].values for r in POOL], axis=0)  # (K, n, 5)
y = m.label.values
fd = m.fold.values
print(f"n={len(m)} pool={len(POOL)}")

def macro(yy, yp):
    cm = np.bincount(yy * 5 + yp, minlength=25).reshape(5, 5)
    tp = np.diag(cm).astype(float); fp = cm.sum(0) - tp; fn = cm.sum(1) - tp
    den = 2 * tp + fp + fn
    return float(np.where(den > 0, 2 * tp / np.maximum(den, 1), 0.0).mean())

def bin_f1_curve(y1, p, thrs):
    out = np.empty(len(thrs))
    for i, t in enumerate(thrs):
        msk = p >= t
        tp = (msk & (y1 == 1)).sum(); fp = (msk & (y1 == 0)).sum(); fn = ((~msk) & (y1 == 1)).sum()
        out[i] = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    return out

THRS = np.arange(0.05, 0.96, 0.025)
P24 = np.zeros((len(m), 5))
P24b = np.zeros((len(m), 5))
P25 = np.zeros((len(m), 5))
P25b = np.zeros((len(m), 5))
picks_log = []
for f in sorted(np.unique(fd)):
    tr = fd != f
    te = fd == f
    experts = {}
    for c in range(5):
        y1 = (y[tr] == c).astype(int)
        best = (-1.0, None, None)
        for k in range(len(POOL)):
            cur = bin_f1_curve(y1, A[k][tr, c], THRS)
            j = int(np.argmax(cur))
            if cur[j] > best[0]:
                best = (float(cur[j]), k, float(THRS[j]))
        experts[c] = best  # (trainF1, model_idx, thr)
    picks_log.append({"fold": int(f), **{CL[c]: f"{POOL[experts[c][1]]}(t={experts[c][2]:.2f},F1={experts[c][0]:.3f})" for c in range(5)}})
    f1s = np.array([experts[c][0] for c in range(5)])
    thrs = np.array([experts[c][2] for c in range(5)])
    ks = [experts[c][1] for c in range(5)]
    Pte = np.stack([A[ks[c]][te, c] for c in range(5)], axis=1)  # (n_te, 5) expert probs
    fb = A[POOL.index(FB)][te, :].argmax(1)
    ypA = fb.copy(); ypB = fb.copy()
    for i in range(len(Pte)):
        S = np.where(Pte[i] >= thrs)[0]
        if len(S) == 1:
            ypA[i] = ypB[i] = S[0]
        elif len(S) > 1:
            ypA[i] = S[np.argmax(Pte[i, S] * f1s[S])]
            ypB[i] = S[np.argmax((Pte[i, S] / thrs[S]) * f1s[S])]
    P24[te, :] = 0.0; P24[te, ypA] = 1.0
    P24b[te, :] = 0.0; P24b[te, ypB] = 1.0
    # soft variants: confidence * reliability, no hard thresholds
    Q = Pte * f1s[None, :]
    P25[te, :] = Q / np.maximum(Q.sum(1, keepdims=True), 1e-12)
    Qb = (Pte / thrs[None, :]) * f1s[None, :]
    P25b[te, :] = Qb / np.maximum(Qb.sum(1, keepdims=True), 1e-12)
    print(f"fold {f}: " + " | ".join(f"{CL[c]}={POOL[experts[c][1]]}@{experts[c][2]:.2f}" for c in range(5)), flush=True)

pd.DataFrame(picks_log).to_csv(EDGE / "docs" / "e24_expert_picks.csv", index=False)
fb_yp = A[POOL.index(FB)].argmax(1)
print(f"\nE24  (hard, vote p*f1)     : macro={macro(y, P24.argmax(1)):.4f}")
print(f"E24b (hard, vote p/thr*f1) : macro={macro(y, P24b.argmax(1)):.4f}")
print(f"E25  (soft p*f1)           : macro={macro(y, P25.argmax(1)):.4f}")
print(f"E25b (soft p/thr*f1)       : macro={macro(y, P25b.argmax(1)):.4f}")
print(f"E19 fallback ref           : macro={macro(y, fb_yp):.4f}")
for name, P_ in [("E24", P24), ("E24b", P24b), ("E25", P25), ("E25b", P25b)]:
    yp = P_.argmax(1)
    cm = np.bincount(y * 5 + yp, minlength=25).reshape(5, 5)
    tp = np.diag(cm).astype(float); fp = cm.sum(0) - tp; fn = cm.sum(1) - tp
    den = 2 * tp + fp + fn
    print(f"{name} per-class F1: " + " ".join(f"{CL[i]}={v:.3f}" for i, v in
          enumerate(np.where(den > 0, 2 * tp / np.maximum(den, 1), 0.0))))

for P_, run_id in [(P24, "E24"), (P24b, "E24b"), (P25, "E25"), (P25b, "E25b")]:
    out = pd.DataFrame({"stem": m.stem.values, "epoch_index": m.epoch_index.values})
    for j, c in enumerate(CL):
        out[f"p_{c}"] = P_[:, j]
    d = RUNS / run_id
    d.mkdir(exist_ok=True)
    for stem, sub in out.groupby("stem", sort=True):
        sub.to_parquet(d / f"{stem}.parquet", index=False)
    print(f"{run_id}: saved {out.stem.nunique()} recordings")
