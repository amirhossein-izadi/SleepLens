"""U-Sleep CSDP (open weights) adapter E21: Fpz-Cz + EOG.

Their exact preprocessing (run_usleep.py): 100Hz -> bandpass 0.1-40Hz (Butter order 5,
zero-phase) -> per-channel median/IQR scale -> clip +/-20 -> polyphase resample to 128Hz
-> edge-pad to whole 30-s epochs. Long recordings chunked 480 epochs / 60 overlap.
Checkpoint logits: (batch, 5, n) with class order [Wake, N1, N2, N3, REM] = ours.
NOTE: torch MUST be imported before pandas on this Windows env (OpenMP DLL conflict)."""
import sys
import torch  # FIRST - before pandas (WinError 1114 otherwise)
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.signal import butter, resample_poly, sosfiltfilt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(Path(HERE, "..", "weights", "repos", "usleep-csdp").resolve()))
from canonical import load_canonical
from base import save_probs, CLASSES
from usleep import USleep

CKPT = Path(HERE, "..", "weights", "repos", "usleep-csdp", "models", "best-usleep.ckpt").resolve()
CH = ["EEG Fpz-Cz", "EOG horizontal"]
MAP = {0: "Wake", 1: "N1", 2: "N2", 3: "N3", 4: "REM"}
FS_IN = 100.0
FS_OUT = 128
EPOCH = 30 * FS_OUT
CHUNK = 480
OVERLAP = 60
_model = None

def get_model():
    global _model
    if _model is None:
        ck = torch.load(CKPT, map_location="cpu", weights_only=False)
        hp = ck["hyper_parameters"]
        net = USleep(num_channels=2, initial_filters=hp["initial_filters"],
                     complexity_factor=hp["complexity_factor"],
                     progression_factor=hp["progression_factor"])
        sd = {k[len("model."):]: v for k, v in ck["state_dict"].items() if k.startswith("model.")}
        net.load_state_dict(sd, strict=True)
        net.eval()
        _model = net
    return _model

def predict_record(stem):
    data = load_canonical(stem, channels=CH)
    x = np.stack([data[c].astype(np.float64) for c in CH], axis=0)  # (2, T) @100Hz
    sos = butter(5, [0.1, 40.0], btype="bandpass", fs=FS_IN, output="sos")
    x = sosfiltfilt(sos, x, axis=-1)
    center = np.median(x, axis=-1, keepdims=True)
    q25, q75 = np.percentile(x, [25.0, 75.0], axis=-1, keepdims=True)
    scale = np.maximum(q75 - q25, 1e-8)
    x = np.clip((x - center) / scale, -20.0, 20.0)
    x = resample_poly(x, FS_OUT, int(FS_IN), axis=-1).astype(np.float32)
    n = x.shape[-1] // EPOCH
    pad = (-x.shape[-1]) % EPOCH
    if pad:
        x = np.pad(x, ((0, 0), (0, pad)), mode="edge")
    t = torch.from_numpy(x).unsqueeze(0)  # (1, 2, T)
    model = get_model()
    P = np.zeros((n, len(CLASSES)), dtype=np.float64)
    with torch.no_grad():
        if n <= CHUNK:
            out = torch.softmax(model(t), dim=1)[0].T.numpy()  # (n_padded, 5)
            P[:, :] = out[:n]
        else:
            for s in range(0, n, CHUNK - OVERLAP):
                e = min(s + CHUNK, n)
                seg = t[:, :, s * EPOCH:e * EPOCH]
                out = torch.softmax(model(seg), dim=1)[0].T.numpy()
                take_s = s + (OVERLAP // 2 if s > 0 else 0)
                take_e = e - ((OVERLAP - OVERLAP // 2) if e < n else 0)
                P[take_s:take_e] = out[take_s - s:take_e - s]
    out_df = pd.DataFrame({"stem": stem, "epoch_index": np.arange(n)})
    for ours in CLASSES:
        j = [k for k, v in MAP.items() if v == ours][0]
        out_df[f"p_{ours}"] = P[:, j]
    return out_df

def run(run_id, stems):
    for s in stems:
        save_probs(predict_record(s), run_id, s)
        print(run_id, s, flush=True)

if __name__ == "__main__":
    pilot = ["SC4001", "SC4041", "ST7011"]
    run("E21", pilot)
