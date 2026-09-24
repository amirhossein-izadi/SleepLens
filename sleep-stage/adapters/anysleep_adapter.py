"""AnySleep adapter E11: canonical 100Hz -> 128Hz polyphase -> median/IQR clip20 -> ckpt -> T×5.
Logit order in checkpoint: [N3, N2, N1, REM, Wake] (see repo example reorder map).
NOTE: torch MUST be imported before pandas/numpy on this Windows env (OpenMP DLL conflict)."""
import sys
import torch  # FIRST - before pandas (WinError 1114 otherwise)
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path(HERE, "..", "weights", "repos", "AnySleep", "examples").resolve()))
from anysleep_no_hydra import AnySleep
from base import save_probs
from canonical import load_canonical, resample_poly

CKPT = Path(HERE, "..", "weights", "repos", "AnySleep", "models", "anysleep-run1.pth").resolve()
# Verified empirically (permutation search, pilot macro 0.861):
# checkpoint logit order = [Wake, N1, N2, N3, REM].
# (The repo example's stage_names/reorder map is plot cosmetics, NOT logit order.)
MAP = {0: "Wake", 1: "N1", 2: "N2", 3: "N3", 4: "REM"}
_model = None

def get_model():
    global _model
    if _model is None:
        _model = AnySleep(path=str(CKPT), sleep_stage_frequency=1)
        _model.eval()
    return _model

def predict_record(stem, channels=("EEG Fpz-Cz", "EEG Pz-Oz", "EOG horizontal")):
    data = load_canonical(stem, channels=channels)
    proc = []
    for ch in channels:
        x = resample_poly(data[ch].astype(np.float64), 100, 128)
        med = np.median(x)
        iqr = np.percentile(x, 75) - np.percentile(x, 25) + 1e-12
        x = np.clip((x - med) / iqr, -20, 20)
        proc.append(x)
    n = min(len(p) for p in proc)
    n = (n // 3840) * 3840  # whole 30-s epochs @128Hz
    X = np.stack([p[:n] for p in proc], axis=1)  # (time, ch)
    Xt = torch.from_numpy(X).float().unsqueeze(0)
    with torch.no_grad():
        logits = get_model()(Xt).detach().cpu().numpy()[0]  # (epochs, 5) [N3,N2,N1,REM,Wake]
    e = np.exp(logits - logits.max(1, keepdims=True))
    P = e / e.sum(1, keepdims=True)
    out = pd.DataFrame({"stem": stem, "epoch_index": np.arange(len(P))})
    for ours in ["Wake", "N1", "N2", "N3", "REM"]:
        j = [k for k, v in MAP.items() if v == ours][0]
        out[f"p_{ours}"] = P[:, j]
    return out

def run(run_id, stems):
    for s in stems:
        save_probs(predict_record(s), run_id, s)
        print(run_id, s, flush=True)

if __name__ == "__main__":
    pilot = ["SC4001", "SC4041", "ST7011"]
    run("E11", pilot)
