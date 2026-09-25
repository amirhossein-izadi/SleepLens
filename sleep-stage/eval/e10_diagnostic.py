"""E10 decisive diagnostic: find the input regime where SleepFMStager stops being constant-Wake.

Configs: scale {z1, z26, raw-uV} x channels {3, 4} x windowing {whole-night chunks, 30-s windows}.
Reports per-stem class distribution (% of epochs) and bench macro-F1 per config.
"""
import sys
import time
import torch  # FIRST (Windows DLL order)
torch.set_num_threads(4)
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
sys.path.insert(0, str(EDGE / "vendors"))
sys.path.insert(0, str(EDGE / "adapters"))
from sleepfm_bd import SleepFMStager
from canonical import load_canonical, resample_poly

CL = ["Wake", "N1", "N2", "N3", "REM"]
lab = {c: i for i, c in enumerate(CL)}
TAB = EDGE.parent / "sleep-eda" / "tables"
ep = pd.read_parquet(TAB / "epochs_v3.parquet")
g = ep[ep.valid & ep.label5.isin(CL) & ep.in_bench][["stem", "epoch", "label5"]].rename(
    columns={"epoch": "epoch_index"})
g["label"] = g.label5.map(lab)

MODELS = {}
def get_model(n_chans):
    if n_chans not in MODELS:
        m = SleepFMStager.from_pretrained(n_chans=n_chans, n_outputs=5, n_times=3840, sfreq=128)
        m.eval()
        MODELS[n_chans] = m
    return MODELS[n_chans]

def load_sig(stem, channels):
    data = load_canonical(stem, channels=channels)
    proc = []
    for ch in channels:
        x = resample_poly(data[ch].astype(np.float64), 100, 128)
        proc.append(x)
    n = min(len(p) for p in proc)
    n = (n // 640) * 640
    return np.stack([p[:n] for p in proc], axis=0)  # (ch, time) @128Hz

def scale_sig(X, mode):
    if mode == "uv":
        return X
    out = []
    for c in range(X.shape[0]):
        x = X[c]
        mu, sd = float(x.mean()), float(x.std()) or 1.0
        y = (x - mu) / sd
        out.append(y * (26.0 if mode == "z26" else 1.0))
    return np.stack(out, axis=0)

def probs_of(logits):  # (5, P)
    e = np.exp(logits - logits.max(0, keepdims=True))
    return e / e.sum(0, keepdims=True)

def predict_chunks(model, X, PCH=8000):
    n_patch = X.shape[1] // 640
    outs = []
    for s in range(0, n_patch, PCH):
        seg = X[:, s * 640:(s + PCH) * 640]
        if seg.shape[1] < 640:
            continue
        with torch.no_grad():
            lg = model(torch.from_numpy(seg).float().unsqueeze(0))[0].numpy()
        outs.append(lg)
    return np.concatenate(outs, axis=1)

def predict_30s(model, X):
    n_ep = X.shape[1] // 3840
    out = np.zeros((5, n_ep))
    for e in range(n_ep):
        seg = X[:, e * 3840:(e + 1) * 3840]
        with torch.no_grad():
            lg = model(torch.from_numpy(seg).float().unsqueeze(0))[0].numpy()  # (5, 6)
        out[:, e] = lg.mean(1)
    return out

def macro(y, yp):
    f = []
    for i in range(5):
        tp = ((yp == i) & (y == i)).sum(); fp = ((yp == i) & (y != i)).sum(); fn = ((yp != i) & (y == i)).sum()
        f.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    return float(np.mean(f))

STEMS = ["SC4001", "SC4041", "ST7011"]
CH3 = ["EEG Fpz-Cz", "EEG Pz-Oz", "EOG horizontal"]
CH4 = CH3 + ["EOG horizontal"]          # count test (pool is permutation-invariant)
CH4E = CH3 + ["EMG submental"]          # real 4th modality, ST only (100 Hz there)
CONFIGS = [
    ("z1_3ch_chunks", "z1", CH3, "chunks", None),
    ("rawuV_3ch_chunks", "uv", CH3, "chunks", None),
    ("z26_3ch_chunks", "z26", CH3, "chunks", None),
    ("z1_4ch_chunks", "z1", CH4, "chunks", None),
    ("z1_3ch_30s_ST", "z1", CH3, "30s", ("ST7011",)),
    ("z1_4chEMG_chunks_ST", "z1", CH4E, "chunks", ("ST7011",)),
]

CSV = EDGE / "docs" / "e10_diagnostic.csv"
sig_cache = {}
rows = []
for name, mode, chs, win, only in CONFIGS:
    wrote = False
    for stem in STEMS:
        if only and stem not in only:
            continue
        key = (stem, tuple(chs))
        if key not in sig_cache:
            sig_cache[key] = load_sig(stem, chs)
        X = scale_sig(sig_cache[key].copy(), mode)
        model = get_model(len(chs))
        t0 = time.time()
        if win == "chunks":
            P = probs_of(predict_chunks(model, X))
            n_ep = P.shape[1] // 6
            P = P[:, :n_ep * 6].reshape(5, n_ep, 6).mean(2)
        else:
            L = predict_30s(model, X)  # (5, n_ep)
            P = np.zeros_like(L)
            for i in range(L.shape[1]):
                e = np.exp(L[:, i] - L[:, i].max())
                P[:, i] = e / e.sum()
        yp = P.argmax(0)
        dist = {CL[i]: round(float((yp == i).mean()), 3) for i in range(5)}
        gt = g[g.stem == stem].set_index("epoch_index").label
        yv = gt.reindex(np.arange(len(yp))).values
        msk = ~pd.isna(yv)
        mf = macro(yv[msk].astype(int), yp[msk]) if msk.sum() else float("nan")
        rows.append({"config": name, "stem": stem, "n_epochs": len(yp), "macro_bench": round(mf, 4),
                     **dist, "sec": round(time.time() - t0, 1)})
        print(f"{name:20s} {stem}: macro={mf:.4f} " + " ".join(f"{k}={v:.2f}" for k, v in dist.items())
              + f" ({time.time()-t0:.0f}s)", flush=True)
        pd.DataFrame(rows).to_csv(CSV, index=False)
        wrote = True

t = pd.DataFrame(rows)
t.to_csv(EDGE / "docs" / "e10_diagnostic.csv", index=False)
print("\n== summary (mean over 3 stems) ==")
agg = t.groupby("config")[["macro_bench"] + CL].mean().round(3)
print(agg.to_string())
