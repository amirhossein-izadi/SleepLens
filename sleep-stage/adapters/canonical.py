"""Canonical 100-Hz loader + v3 epoch alignment. Never resample/filter here."""
import numpy as np
import pandas as pd
from pathlib import Path
from pyedflib import EdfReader

DATA = Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
EDGE = Path(__file__).resolve().parents[1]
EP = None

def epochs_v3():
    global EP
    if EP is None:
        EP = pd.read_parquet(Path(EDGE, "..", "sleep-eda", "tables", "epochs_v3.parquet"))
    return EP

def load_canonical(stem, channels=("EEG Fpz-Cz", "EEG Pz-Oz", "EOG horizontal")):
    """Return dict channel -> full 100-Hz signal + start datetime + nsamples.
    Raw values, no filtering, no resampling, no normalization."""
    psg = next((DATA / ("sleep-cassette" if stem.startswith("SC") else "sleep-telemetry")).glob(stem + "*-PSG.edf"))
    out = {}
    with EdfReader(str(psg)) as f:
        out["start"] = f.getStartdatetime()
        out["duration"] = f.getFileDuration()
        lab = [f.getLabel(k) for k in range(f.signals_in_file)]
        for ch in channels:
            out[ch] = np.array(f.readSignal(lab.index(ch)), dtype=np.float64)
    out["path"] = psg
    return out

def epoch_slice(sig, epoch_idx, sf=100, epoch_sec=30):
    s = int(epoch_idx * epoch_sec * sf)
    return sig[s:s + int(epoch_sec * sf)]

def resample_poly(x, src=100, dst=128):
    from math import gcd
    from scipy.signal import resample_poly as rp
    g = gcd(src, dst)
    return rp(x, dst // g, src // g).astype(np.float64)
