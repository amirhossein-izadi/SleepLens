"""AnySleep channel-attention interpretability.

Part A: whole-recording attention (13 skip-connection layers x 3 channels) per recording.
Part B: sliding-window (20 min) attention -> aggregated per TRUE sleep stage.

Hooks replicate SkipConnectionBlock's alpha exactly:
  x_att = x.mean(-1) -> mlp -> softmax over channels.
Usage: python interp_attention.py [--n 16] [--test]
"""
import sys
import time
import argparse
import torch  # FIRST (Windows DLL order)
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
TAB = EDGE.parent / "sleep-eda" / "tables"
sys.path.insert(0, str(EDGE / "weights" / "repos" / "AnySleep" / "examples"))
sys.path.insert(0, str(EDGE / "adapters"))
from anysleep_no_hydra import AnySleep
from canonical import load_canonical, resample_poly

CKPT = EDGE / "weights" / "repos" / "AnySleep" / "models" / "anysleep-run1.pth"
CH = ["EEG Fpz-Cz", "EEG Pz-Oz", "EOG horizontal"]
SHORT = ["Fpz", "Pz", "EOG"]
CL = ["Wake", "N1", "N2", "N3", "REM"]
lab = {c: i for i, c in enumerate(CL)}
W = 40   # window length in epochs (20 min)
S = 5    # stride in epochs

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=16)
ap.add_argument("--test", action="store_true")
args = ap.parse_args()

# ---- data ----
ep = pd.read_parquet(TAB / "epochs_v3.parquet")
g = ep[ep.valid & ep.label5.isin(CL)][["stem", "cohort", "epoch", "label5"]].copy()
g["label"] = g.label5.map(lab)

ent = g.groupby("stem").label.value_counts(normalize=True).groupby("stem").apply(
    lambda p: float(-(p * np.log(p + 1e-12)).sum()))
rng = np.random.default_rng(0)
sel = []
for co in ["SC", "ST"]:
    stems = sorted(g[g.cohort == co].stem.unique())
    k = min(args.n // 2, len(stems))
    pick = rng.choice(stems, size=k, replace=False)
    sel += sorted(pick.tolist())
if args.test:
    sel = sel[:2]
print("recordings:", len(sel))

# ---- model + hooks ----
model = AnySleep(path=str(CKPT), sleep_stage_frequency=1)
model.eval()
alphas = []

def make_hook(idx):
    def hook(module, inp, out):
        x = inp[0]
        x_att = x.mean(dim=-1).reshape(-1, x.shape[2])
        a = module.mlp(x_att).reshape(x.shape[0], -1)
        a = module.softmax(a)
        alphas.append((idx, a.detach().cpu().numpy()))
    return hook

for i, m in enumerate(model.skip_connections):
    m.register_forward_hook(make_hook(i))
NLAY = len(model.skip_connections)
print("attention layers:", NLAY)

def load_signal(stem):
    data = load_canonical(stem, channels=CH)
    proc = []
    for ch in CH:
        x = resample_poly(data[ch].astype(np.float64), 100, 128)
        med = np.median(x)
        iqr = np.percentile(x, 75) - np.percentile(x, 25) + 1e-12
        proc.append(np.clip((x - med) / iqr, -20, 20))
    n = min(len(p) for p in proc)
    n = (n // 3840) * 3840
    return np.stack([p[:n] for p in proc], axis=1)

rec_rows, win_rows = [], []
t0 = time.time()
for si, stem in enumerate(sel):
    X = load_signal(stem)
    T = len(X) // 3840
    Xt = torch.from_numpy(X).float().unsqueeze(0)
    # ---- Part A: whole recording ----
    alphas.clear()
    with torch.no_grad():
        _ = model(Xt)
    A = np.stack([a[0] for _, a in sorted(alphas)], axis=0)  # (NLAY, 3)
    for li in range(NLAY):
        rec_rows.append({"stem": stem, "cohort": g[g.stem == stem].cohort.iloc[0],
                         "layer": li, **{f"a_{c}": float(A[li, k]) for k, c in enumerate(SHORT)}})
    # ---- Part B: sliding windows ----
    gl = g[g.stem == stem].set_index("epoch").label
    for st in range(0, T - W + 1, S):
        Xw = torch.from_numpy(X[st * 3840:(st + W) * 3840]).float().unsqueeze(0)
        alphas.clear()
        with torch.no_grad():
            out = model(Xw)
        Aw = np.stack([a[0] for _, a in sorted(alphas)], axis=0)  # (NLAY, 3)
        ctr = st + W // 2
        row = {"stem": stem, "start_epoch": st, "center_epoch": ctr}
        for li in range(NLAY):
            for k, c in enumerate(SHORT):
                row[f"L{li}_{c}"] = float(Aw[li, k])
        # stage composition of window (true labels present)
        labs = gl.reindex(range(st, st + W)).dropna().astype(int)
        for c in CL:
            row[f"n_{c}"] = int((labs == lab[c]).sum())
        win_rows.append(row)
    print(f"[{si+1}/{len(sel)}] {stem} T={T} windows={len(range(0, T-W+1, S))} "
          f"({time.time()-t0:.0f}s)", flush=True)

pd.DataFrame(rec_rows).to_csv(EDGE / "docs" / "interp_attn_recording.csv", index=False)
pd.DataFrame(win_rows).to_parquet(EDGE / "docs" / "interp_attn_windows.parquet")
print("saved", len(rec_rows), "rec rows,", len(win_rows), "window rows")

# ---- aggregate per stage (epoch-level weighted by true stage) ----
w = pd.DataFrame(win_rows)
acc, cnt = {}, {}
for _, r in w.iterrows():
    for c in CL:
        n = int(r[f"n_{c}"])
        if n == 0:
            continue
        cnt[c] = cnt.get(c, 0) + n
        for li in range(NLAY):
            key = (c, li)
            acc.setdefault(key, np.zeros(3))
            acc[key] += n * np.array([r[f"L{li}_{x}"] for x in SHORT])
rows = []
for (c, li), v in acc.items():
    a = v / cnt[c]
    rows.append({"stage": c, "layer": li, **{f"a_{x}": round(float(a[k]), 4) for k, x in enumerate(SHORT)}})
pd.DataFrame(rows).to_csv(EDGE / "docs" / "interp_attn_by_stage.csv", index=False)

# summary: mean over all layers + deepest layer
s = pd.DataFrame(rows)
print("\n== mean attention over all 13 layers, by TRUE stage ==")
agg = s.groupby("stage")[["a_Fpz", "a_Pz", "a_EOG"]].mean().reindex(CL).round(3)
print(agg.to_string())
print("\n== deepest layer (L12 = connector) ==")
d = s[s.layer == NLAY - 1].set_index("stage")[["a_Fpz", "a_Pz", "a_EOG"]].reindex(CL).round(3)
print(d.to_string())
