"""SDI inference on our canonical data (E23-style adapter for the SQI side).

Runs the vendored SDI transformer (Zhou et al., npj Digital Medicine 2025) via our canonical
100-Hz loader instead of the module's sleepedf_clean/ pipeline. Inference only.

Input per their contract: (n_epochs, 4, 3000) @100 Hz in uV, channel order [EEG, EMG, EOG, ECG];
ECG absent in Sleep-EDF -> zero-filled. Output per epoch: sdi in 0-1 (higher = deeper) + binary REM.

Writes: sleep-quality-index/runs/<stem>.parquet  (stem, epoch_index, sdi, rem_pred)
        sleep-quality-index/runs/summary_sdi.csv (QC vs our ground truth, BENCHMARK_30)
"""
import argparse
import sys
import time
from pathlib import Path

import torch  # FIRST (Windows DLL order)
torch.set_num_threads(8)
import numpy as np
import pandas as pd
from scipy.signal import resample_poly
from scipy.stats import spearmanr
from sklearn.metrics import f1_score, precision_score, recall_score

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
ROOT = EDGE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "sleep-stage" / "adapters"))
from sdi_net import Net
from canonical import load_canonical

CKPT = HERE / "models" / "sdi_checkpoint.pt"
RUNS = EDGE / "runs"
TAB = ROOT / "sleep-eda" / "tables"
CH = ["EEG Fpz-Cz", "EMG submental", "EOG horizontal"]
CL = ["Wake", "N1", "N2", "N3", "REM"]
lab = {c: i for i, c in enumerate(CL)}
EPOCH = 3000
_model = None

def get_model():
    global _model
    if _model is None:
        state = torch.load(CKPT, map_location="cpu", weights_only=True)
        net = Net()
        net.load_state_dict(state, strict=True)
        net.eval()
        _model = net
    return _model

def build_input(stem):
    data = load_canonical(stem, channels=CH)
    dur = float(data["duration"])
    sigs = []
    for ch in CH:
        x = data[ch].astype(np.float64)
        rate = len(x) / dur
        if rate < 50.0:  # cassette EMG is a 1-Hz envelope -> bring to 100 Hz
            x = resample_poly(x, 100, int(round(rate)))
        sigs.append(x)
    n = min(len(s) for s in sigs)
    n = (n // EPOCH) * EPOCH
    x = np.stack([s[:n] for s in sigs], axis=0)          # (3, T) uV
    ecg = np.zeros_like(x[:1])                            # Sleep-EDF has no ECG
    X = np.concatenate([x, ecg], axis=0)                  # (4, T)
    n_ep = n // EPOCH
    X = X.reshape(4, n_ep, EPOCH).transpose(1, 0, 2).astype(np.float32)
    return X, n_ep

def predict(net, X, batch=128):
    sdi = np.zeros(len(X), dtype=np.float32)
    rem = np.zeros(len(X), dtype=np.uint8)
    with torch.no_grad():
        for s in range(0, len(X), batch):
            depth, rem_logits = net(torch.from_numpy(X[s:s + batch]))
            sdi[s:s + batch] = torch.sigmoid(depth).squeeze(-1).numpy()
            rem[s:s + batch] = rem_logits.argmax(-1).numpy().astype(np.uint8)
    return sdi, rem

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stems", nargs="*", default=["SC4001", "SC4041", "ST7011"])
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    ep = pd.read_parquet(TAB / "epochs_v3.parquet")
    if args.all:
        stems = sorted(ep.stem.unique())
    else:
        stems = args.stems
    RUNS.mkdir(exist_ok=True)
    net = get_model()
    rows = []
    t0 = time.time()
    for i, stem in enumerate(stems):
        X, n_ep = build_input(stem)
        ts = time.time()
        sdi, rem = predict(net, X)
        out = pd.DataFrame({"stem": stem, "epoch_index": np.arange(n_ep), "sdi": sdi, "rem_pred": rem})
        out.to_parquet(RUNS / f"{stem}.parquet", index=False)

        g = ep[(ep.stem == stem) & ep.valid & ep.label5.isin(CL) & ep.in_bench][["epoch", "label5"]]
        m = out.merge(g, left_on="epoch_index", right_on="epoch", how="inner")
        y = m.label5.map(lab).values
        s = m.sdi.values
        ordv = np.full(len(m), np.nan)
        for k, v in {0: 0, 1: 1, 2: 2, 3: 3}.items():
            ordv[y == k] = v
        ok = ~np.isnan(ordv)
        rho = spearmanr(ordv[ok], s[ok]).statistic if ok.sum() > 10 else float("nan")
        y_rem = (y == lab["REM"]).astype(int)
        p_rem = m.rem_pred.values.astype(int)
        per_stage = {c: float(s[y == lab[c]].mean()) for c in CL}
        row = {"stem": stem, "n_bench": len(m), "sec": round(time.time() - ts, 1),
               "depth_spearman": round(float(rho), 3),
               "rem_f1": round(float(f1_score(y_rem, p_rem, zero_division=0)), 4),
               "rem_precision": round(float(precision_score(y_rem, p_rem, zero_division=0)), 4),
               "rem_recall": round(float(recall_score(y_rem, p_rem, zero_division=0)), 4),
               "rem_pred_rate": round(float(p_rem.mean()), 4),
               "rem_true_rate": round(float(y_rem.mean()), 4),
               **{f"sdi_{c}": round(per_stage[c], 3) for c in CL}}
        rows.append(row)
        print(f"[{i+1}/{len(stems)}] {stem}: n={len(m)} rho={row['depth_spearman']} "
              f"REM F1={row['rem_f1']} (pred rate {row['rem_pred_rate']:.2f} vs true {row['rem_true_rate']:.2f}) "
              f"SDI: W={row['sdi_Wake']} N1={row['sdi_N1']} N2={row['sdi_N2']} N3={row['sdi_N3']} R={row['sdi_REM']} "
              f"({row['sec']}s)", flush=True)

    df = pd.DataFrame(rows)
    prev = RUNS / "summary_sdi.csv"
    if args.all and prev.is_file():
        old = pd.read_csv(prev)
        df = pd.concat([old[~old.stem.isin(df.stem)], df], ignore_index=True)
    df.sort_values("stem").to_csv(prev, index=False)
    print(f"\nwrote {prev} ({len(df)} nights, {time.time()-t0:.0f}s)")

if __name__ == "__main__":
    main()
