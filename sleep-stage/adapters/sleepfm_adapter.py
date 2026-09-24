"""SleepFMStager adapter E10: long contiguous 128Hz segments -> 5-s patches -> aggregate 6/epoch.
Vendored model code: vendors/sleepfm_bd.py (braindecode PR #1106, py3.10-compatible subset).
Weights: HF braindecode/SleepFMStager (CC BY-NC 4.0)."""
import sys
import torch  # FIRST - before pandas (WinError 1114 otherwise)
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "vendors"))
from sleepfm_bd import SleepFMStager
from base import save_probs
from canonical import load_canonical, resample_poly

_model = None

def get_model(n_chans=3):
    global _model
    if _model is None:
        _model = SleepFMStager.from_pretrained(n_chans=n_chans, n_outputs=5, n_times=3840, sfreq=128)
        _model.eval()
    return _model

def predict_record(stem, channels=("EEG Fpz-Cz", "EEG Pz-Oz", "EOG horizontal"), agg="probmean"):
    data = load_canonical(stem, channels=channels)
    proc = []
    for ch in channels:
        x = resample_poly(data[ch].astype(np.float64), 100, 128)
        # upstream safe_standardize: per-signal z-score over the whole recording
        mu, sd = float(x.mean()), float(x.std()) or 1.0
        proc.append((x - mu) / sd)
    n = min(len(p) for p in proc)
    n = (n // 640) * 640  # whole 5-s patches
    X = np.stack([p[:n] for p in proc], axis=0)  # (ch, time)
    # chunk to max_seq_length=8196 patches (whole-night LSTM context per chunk)
    PCH = 8000
    outs = []
    for s in range(0, n // 640, PCH):
        seg = X[:, s * 640:(s + PCH) * 640]
        if seg.shape[1] < 640:
            continue
        Xt = torch.from_numpy(seg).float().unsqueeze(0)
        with torch.no_grad():
            logits = get_model(len(channels))(Xt).detach().cpu().numpy()[0]  # (5, patches)
        outs.append(logits)
    logits = np.concatenate(outs, axis=1)  # (5, patches) Wake,N1,N2,N3,REM
    assert logits.shape[0] == 5
    n_ep = logits.shape[1] // 6
    logits = logits[:, :n_ep * 6].reshape(5, n_ep, 6)
    if agg == "probmean":
        e = np.exp(logits - logits.max(0, keepdims=True))
        P = e / e.sum(0, keepdims=True)
        P = P.mean(2).T
    elif agg == "logitmean":
        e = np.exp(logits.mean(2) - logits.mean(2).max(0, keepdims=True))
        P = (e / e.sum(0, keepdims=True)).T
    else:  # majority
        P = np.zeros((n_ep, 5))
        P[np.arange(n_ep), logits.argmax(0).mean(1).round().astype(int)] = 1.0
    out = pd.DataFrame({"stem": stem, "epoch_index": np.arange(n_ep)})
    for j, c in enumerate(["Wake", "N1", "N2", "N3", "REM"]):
        out[f"p_{c}"] = P[:, j]
    return out

def run(run_id, stems, **kw):
    for s in stems:
        save_probs(predict_record(s, **kw), run_id, s)
        print(run_id, s, flush=True)

if __name__ == "__main__":
    run("E10", ["SC4001", "SC4041", "ST7011"])
