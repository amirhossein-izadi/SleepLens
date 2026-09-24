"""SLEEPYLAND adapter (E06-E09): EDF -> docker usleepyland API -> majority probs -> T×5.
Models: usleep -> E07, deepresnet -> E08, transformer -> E09; ensemble(SOMNUS) -> E06.
Class order verified empirically: [Wake, N1, N2, N3, REM]; epochs 0-based from rec start.
Input dir: weights/repos/SLEEPYLAND/input/<stem>/<file>.edf ; output: .../output/<stem>_sl/<model>/majority/
"""
import sys
import shutil
import time
import numpy as np
import pandas as pd
from pathlib import Path
import requests

HERE = Path(__file__).resolve().parent
SL = HERE.parent / "weights" / "repos" / "SLEEPYLAND"
DATA = Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
API = "http://localhost:7777"
CL = ["Wake", "N1", "N2", "N3", "REM"]
MODEL_RUN = {"usleep": "E07", "deepresnet": "E08", "transformer": "E09"}
ENSEMBLE_RUN = "E06"

def _psg_path(stem):
    return next((DATA / ("sleep-cassette" if stem.startswith("SC") else "sleep-telemetry")).glob(stem + "*-PSG.edf"))

def predict(stem, model="usleep", channels=("EEG", "EOG"), folder_name=None, timeout=3600):
    folder_name = folder_name or f"{stem}_sl"
    indir = SL / "input" / stem
    indir.mkdir(parents=True, exist_ok=True)
    dst = indir / _psg_path(stem).name
    if not dst.exists():
        shutil.copy2(_psg_path(stem), dst)
    r = requests.post(f"{API}/predict_one", data=[
        ("folder_root_name", stem), ("folder_name", folder_name),
        *[("channels", c) for c in channels], ("model", model), ("file_name", ".edf"),
    ], timeout=timeout)
    r.raise_for_status()
    return folder_name

def ensemble(folder_name, models=("usleep", "deepresnet", "transformer"), timeout=3600):
    r = requests.post(f"{API}/ensemble", data=[
        ("folder_name", folder_name), *[("models", m) for m in models],
    ], timeout=timeout)
    r.raise_for_status()

def read_probs(folder_name, model, stem):
    if model == "ensemble":
        p = SL / "output" / folder_name / "ensemble" / "majority"
    else:
        p = SL / "output" / folder_name / model / "majority"
    fs = list(p.glob("*_PRED.npy"))
    if not fs:
        return None
    a = np.load(fs[0]).astype(np.float64)
    if a.ndim != 2 or a.shape[1] != 5:
        return None
    out = pd.DataFrame({"stem": stem, "epoch_index": np.arange(len(a))})
    for j, c in enumerate(CL):
        out[f"p_{c}"] = a[:, j]
    return out

def run(run_id, model, stems, channels=("EEG", "EOG")):
    from base import save_probs
    for s in stems:
        t0 = time.time()
        try:
            fn = predict(s, model=model, channels=channels)
            if model == "ensemble":
                ensemble(fn)
            df = read_probs(fn, model, s)
            if df is None:
                print(run_id, s, "no npy"); continue
            save_probs(df, run_id, s)
            print(run_id, s, f"{len(df)}ep {time.time()-t0:.0f}s", flush=True)
        except Exception as e:
            print(run_id, s, "FAIL", str(e)[:150], flush=True)

if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "usleep"
    stems = sys.argv[2:] or ["SC4001", "SC4041", "ST7011"]
    if model == "ensemble":
        # needs component predictions first; just ensemble + read
        for s in stems:
            fn = f"{s}_sl"
            try:
                ensemble(fn)
                df = read_probs(fn, "ensemble", s)
                from base import save_probs
                save_probs(df, ENSEMBLE_RUN, s)
                print("E06", s, len(df), flush=True)
            except Exception as e:
                print("E06", s, "FAIL", str(e)[:120])
    else:
        run(MODEL_RUN[model], model, stems)
