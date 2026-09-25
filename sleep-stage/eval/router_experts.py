"""E22 (domain router) + E23 (per-class binary experts with F1-weighted voting).

Part 1: router matrix — SC branch x ST branch over our best models, pooled bench macro.
Part 2: per-class threshold experts on E19 OOF probs, fold-honest; voting rule:
  candidates = classes with p_c >= thr_c; none -> argmax p; ties -> argmax (p_c * f1_c).
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

ep = pd.read_parquet(TAB / "epochs_v3.parquet")
g = ep[ep.valid & ep.label5.isin(CL) & ep.in_bench][["stem", "cohort", "epoch", "label5"]].rename(
    columns={"epoch": "epoch_index"})
g["label"] = g.label5.map(lab)
folds = pd.read_csv(TAB / "folds5_v3.csv")
fold_of = dict(zip(folds.subject, folds.fold))

def load(run):
    fs = sorted((RUNS / run).glob("*.parquet"))
    d = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    return d[["stem", "epoch_index"] + [f"p_{c}" for c in CL]].rename(
        columns={f"p_{c}": f"{run}_{c}" for c in CL})

def macro(yy, yp):
    cm = np.bincount(yy * 5 + yp, minlength=25).reshape(5, 5)
    tp = np.diag(cm).astype(float); fp = cm.sum(0) - tp; fn = cm.sum(1) - tp
    den = 2 * tp + fp + fn
    return float(np.where(den > 0, 2 * tp / np.maximum(den, 1), 0.0).mean())

# ---------- Part 1: router matrix ----------
NEED = ["E19", "E16", "E11", "E21", "E20"]
P = {r: load(r) for r in NEED}
print("== router matrix (pooled bench macro) ==")
print(f"{'SC branch':10s} " + " ".join(f"{st:>8s}" for st in ["E16", "E11", "E19", "E21"]))
best_router = (-1, None)
R = {}
for sc in NEED:
    row = []
    for st in ["E16", "E11", "E19", "E21"]:
        a = P[sc].merge(g, on=["stem", "epoch_index"], how="inner")
        parts = []
        for mm, branch in [(a[a.cohort == "SC"], sc), (a[a.cohort == "ST"], st)]:
            if len(mm) == 0:
                continue
            if branch == sc:
                parts.append(mm)
            else:
                b = P[st].merge(g, on=["stem", "epoch_index"], how="inner")
                sub = mm[["stem", "epoch_index", "cohort", "label"]].merge(
                    b[["stem", "epoch_index"] + [f"{st}_{c}" for c in CL]],
                    on=["stem", "epoch_index"], how="inner")
                for c in CL:
                    sub[f"{sc}_{c}"] = sub[f"{st}_{c}"]
                    sub = sub.drop(columns=[f"{st}_{c}"])
                parts.append(sub)
        full = pd.concat(parts, ignore_index=True)
        y = full.label.values
        yp = full[[f"{sc}_{c}" for c in CL]].values.argmax(1)
        v = macro(y, yp)
        row.append(v)
        R[(sc, st)] = v
        if v > best_router[0]:
            best_router = (v, (sc, st))
    print(f"{sc:10s} " + " ".join(f"{x:8.4f}" for x in row))
print(f"best router: SC->{best_router[1][0]}, ST->{best_router[1][1]}  pooled={best_router[0]:.4f}")

# ---------- Part 2: per-class threshold experts (E23) ----------
m = P["E19"].merge(g, on=["stem", "epoch_index"], how="inner")
m["fold"] = m.stem.str[:5].map(fold_of)
m = m.dropna(subset=["fold"]).reset_index(drop=True)
Pm = m[[f"E19_{c}" for c in CL]].values
y = m.label.values
fd = m.fold.values
print(f"\nE23 base n={len(m)}")

def bin_f1(yy, mask_pred):
    tp = (mask_pred & (yy == 1)).sum(); fp = (mask_pred & (yy == 0)).sum(); fn = ((~mask_pred) & (yy == 1)).sum()
    return 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0

THR = np.arange(0.05, 0.96, 0.025)
P23 = np.zeros((len(m), 5))
P23b = np.zeros((len(m), 5))  # alt tie-break rule p_c/thr_c
for f in sorted(np.unique(fd)):
    tr = fd != f
    te = fd == f
    thrs, f1s = [], []
    for c in range(5):
        ytr = (y[tr] == c).astype(int)
        p = Pm[tr, c]
        best = (0.0, 0.2)
        for t in THR:
            v = bin_f1(ytr, p >= t)
            if v > best[0]:
                best = (v, t)
        thrs.append(best[1]); f1s.append(best[0])
    thrs = np.array(thrs); f1s = np.array(f1s)
    Pte = Pm[te]
    yp = Pte.argmax(1).copy()
    yp2 = yp.copy()
    for i in range(len(Pte)):
        cand = np.where(Pte[i] >= thrs)[0]
        if len(cand) == 1:
            yp[i] = yp2[i] = cand[0]
        elif len(cand) > 1:
            yp[i] = cand[np.argmax(Pte[i, cand] * f1s[cand])]
            yp2[i] = cand[np.argmax(Pte[i, cand] / thrs[cand])]
    P23[te, :] = 0.0
    P23[te, yp] = 1.0
    P23b[te, :] = 0.0
    P23b[te, yp2] = 1.0
    print(f"fold {f}: thr={np.round(thrs, 2)} trainF1={np.round(f1s, 3)}")

print(f"\nE23 per-class experts (vote p*f1): OOF macro={macro(y, P23.argmax(1)):.4f}")
print(f"E23b per-class experts (vote p/thr): OOF macro={macro(y, P23b.argmax(1)):.4f}")
print(f"E19 reference on same rows        : macro={macro(y, Pm.argmax(1)):.4f}")

for P_, run_id in [(P23, "E23"), (P23b, "E23b")]:
    out = pd.DataFrame({"stem": m.stem.values, "epoch_index": m.epoch_index.values})
    for j, c in enumerate(CL):
        out[f"p_{c}"] = P_[:, j]
    d = RUNS / run_id
    d.mkdir(exist_ok=True)
    for stem, sub in out.groupby("stem", sort=True):
        sub.to_parquet(d / f"{stem}.parquet", index=False)
    print(f"{run_id}: saved {out.stem.nunique()} recordings")
