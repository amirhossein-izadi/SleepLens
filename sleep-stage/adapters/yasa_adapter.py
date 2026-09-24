"""YASA adapter: E01 (Fpz), E02 (Fpz+EOG), E03 (Pz+EOG). No manual preprocessing."""
import numpy as np
import pandas as pd
import mne
import yasa
from base import SleepStager, save_probs, CLASSES
from canonical import load_canonical

YASA2OURS = {"W": "Wake", "N1": "N1", "N2": "N2", "N3": "N3", "R": "REM"}

class YasaStager(SleepStager):
    def __init__(self, eeg="EEG Fpz-Cz", eog="EOG horizontal", name="E01"):
        self.eeg = eeg
        self.eog = eog
        self.name = name

    def predict_record(self, stem):
        chs = tuple(c for c in (self.eeg, self.eog) if c)
        data = load_canonical(stem, channels=chs)
        ch_names = list(chs)
        ch_types = ["eeg" if c != self.eog else "eog" for c in chs]
        info = mne.create_info(ch_names=ch_names, sfreq=100.0, ch_types=ch_types)
        raw = mne.io.RawArray(np.stack([data[c] for c in ch_names]), info, verbose=False)
        kwargs = dict(eeg_name=self.eeg)
        if self.eog:
            kwargs["eog_name"] = self.eog
        sls = yasa.SleepStaging(raw, **kwargs)
        hyp = sls.predict()
        proba = hyp.proba
        proba = proba.rename(columns={"W": "Wake", "WAKE": "Wake", "R": "REM", "W-": "Wake"})
        out = pd.DataFrame({"stem": stem, "epoch_index": np.arange(len(hyp))})
        for ours in CLASSES:
            out[f"p_{ours}"] = proba[ours].values if ours in proba.columns else 0.0
        return out

def run(run_id, eeg, eog, stems):
    st = YasaStager(eeg=eeg, eog=eog, name=run_id)
    for s in stems:
        df = st.predict_record(s)
        save_probs(df, run_id, s)
        print(run_id, s, len(df))

if __name__ == "__main__":
    import sys
    pilot = ["SC4001", "SC4041", "ST7011"]
    which = sys.argv[1] if len(sys.argv) > 1 else "E01"
    cfg = {"E01": ("EEG Fpz-Cz", None), "E02": ("EEG Fpz-Cz", "EOG horizontal"),
           "E03": ("EEG Pz-Oz", "EOG horizontal")}[which]
    run(which, cfg[0], cfg[1], pilot)
