"""E19: fold-honest ensemble v2 — add U-Sleep CSDP (E21) to the selection pool.

Pool: AnySleep (3ch/Fpz/Pz/Fpz+EOG) + U-Sleep CSDP + RSN + LightGBM.
Per fold: pick best equal-weight combo (sizes 1..4) on the other 4 folds, apply to held-out.
E19b: same + per-fold class-bias calibration on top.
Saves runs/E19 and runs/E19b.
"""
import itertools
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
TAB = EDGE.parent / "sleep-eda" / "tables"
RUNS = EDGE / "runs"
CL = ["Wake", "N1", "N2", "N3", "REM"]
lab = {c: i for i, c in enumerate(CL)}
CANDS = ["E11", "E11a", "E11b", "E11d", "E21", "E20", "E00"]
NAMES = {"E11": "ANY3ch", "E11a": "ANYFpz", "E11b": "ANYPz", "E11d": "ANYFpz+EOG",
         "E21": "USleepCSDP", "E20": "RSN", "E00": "LGBM"}

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

base = None
for r in CANDS:
    base = load(r) if base is None else base.merge(load(r), on=["stem", "epoch_index"], how="inner")
m = base.merge(g, on=["stem", "epoch_index"], how="inner")
m["fold"] = m.stem.str[:5].map(fold_of)
m = m.dropna(subset=["fold"]).reset_index(drop=True)
A = np.stack([m[[f"{r}_{c}" for c in CL]].values for r in CANDS], axis=0)  # (K, n, 5)
y = m.label.values
fd = m.fold.values
print("n:", len(m), "pool:", len(CANDS), flush=True)

def macro_fast(yy, yp):
    cm = np.bincount(yy * 5 + yp, minlength=25).reshape(5, 5)
    tp = np.diag(cm).astype(float)
    fp = cm.sum(0) - tp
    fn = cm.sum(1) - tp
    den = 2 * tp + fp + fn
    return float(np.where(den > 0, 2 * tp / np.maximum(den, 1), 0.0).mean())

COMBOS = [list(c) for k in [1, 2, 3, 4] for c in itertools.combinations(range(len(CANDS)), k)]
BGRID = [np.array([0, bn, 0, 0, br]) for bn, br in itertools.product([-0.2, 0, 0.2, 0.4], repeat=2)]

P19 = np.zeros((len(m), 5))
P19b = np.zeros((len(m), 5))
for f in sorted(np.unique(fd)):
    tr = fd != f
    te = fd == f
    best = (-1, None)
    for cb in COMBOS:
        Ptr = A[cb][:, tr, :].mean(0)
        v = macro_fast(y[tr], Ptr.argmax(1))
        if v > best[0]:
            best = (v, cb)
    cb = best[1]
    Pte = A[cb][:, te, :].mean(0)
    P19[te] = Pte
    # bias on top of selected combo
    Ptr = A[cb][:, tr, :].mean(0)
    bb = (-1, None)
    for b in BGRID:
        Q = Ptr * np.exp(b)[None, :]
        v = macro_fast(y[tr], Q.argmax(1))
        if v > bb[0]:
            bb = (v, b)
    b = bb[1]
    Qte = Pte * np.exp(b)[None, :]
    P19b[te] = Qte / Qte.sum(1, keepdims=True)
    print(f"fold {f}: combo={[NAMES[CANDS[i]] for i in cb]} train={best[0]:.4f} | "
          f"bN1={b[1]} bREM={b[4]} train={bb[0]:.4f}", flush=True)

print(f"\nE19  combo OOF: macro={macro_fast(y, P19.argmax(1)):.4f}")
print(f"E19b combo+bias OOF: macro={macro_fast(y, P19b.argmax(1)):.4f}")

def save_oof(P, run_id):
    out = pd.DataFrame({"stem": m.stem.values, "epoch_index": m.epoch_index.values})
    for j, c in enumerate(CL):
        out[f"p_{c}"] = P[:, j]
    d = RUNS / run_id
    d.mkdir(exist_ok=True)
    for stem, sub in out.groupby("stem", sort=True):
        sub.to_parquet(d / f"{stem}.parquet", index=False)
    print(f"{run_id}: saved {out.stem.nunique()} recordings, {len(out)} epochs")

save_oof(P19, "E19")
save_oof(P19b, "E19b")
