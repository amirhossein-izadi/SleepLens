"""Sleep-quality parameter extraction from labeled Sleep-EDF nights.

Computes ~96 per-night parameters over the lights-off window: sleep continuity
(TST/SE/SOL/WASO/REM latency), fragmentation (awakenings, stage shifts, SFI,
arousal proxy), architecture (stage %, NREM-REM cycles, halves), EEG
spectral/entropy/microstructure (bandpower, SWA, spectral + permutation
entropy, YASA spindles and slow waves), EMG (atonia, movement index) and a
coarse airflow apnea proxy (cassette only). See REF_RANGES for adult
reference values.

Stage labels come from `--source`: expert ground truth
(<clean-root>/stages/<sid>.npy) or a model prediction folder
(<preds-root>/<model>/<sid>.npy). Signal features always use the raw PSG EDF.
Unscored epochs (expert 255 / model -1) are excluded from sleep denominators.

  python extract_features.py --source expert --limit 2        # smoke
  python extract_features.py --source expert --resume         # all 197
  python extract_features.py --source usleep --resume         # labels from a model
  python extract_features.py --source expert --no-signal      # hypnogram only (fast)

Output: <report-dir>/sqi_features_<source>_lights_off.csv (one row per night).
Needs: mne, yasa (>=0.7), scipy, scikit-learn, pandas (see requirements.txt).
"""

from __future__ import annotations

import argparse
import time
import warnings
from pathlib import Path

import mne
import numpy as np
import pandas as pd
from scipy.signal import stft, welch

warnings.filterwarnings("ignore")

from common import (  # noqa: E402
    ANN_TO_STAGE,
    CLEAN_ROOT,
    EDF_ROOT,
    EEG_CH,
    EMG_CH,
    PREDS_ROOT,
    REPORT_DIR,
    STAGES5,
    load_manifest,
)

EPOCH_S = 30.0
RESP_CH = "Resp oro-nasal"

# Ceiling for the arousal proxy: whole-night means above this are detector
# over-fire, not physiology a scorer would count (near-continuous fast
# background oscillating around the threshold gets split into hundreds of
# "events"; 9/197 nights hit it). Severe clinical fragmentation is ~30+/h.
ARI_MAX = 40.0

# Typical adult reference ranges, for interpretation only (age-dependent;
# Sleep-EDF spans 25-101 y, so elderly nights legitimately fall outside some
# of these). Sources: AASM manual and standard sleep-medicine references.
REF_RANGES = {
    "se_pct": (85.0, 100.0, ">=85% normal (mentor: 85-90%)"),
    "sol_min": (0.0, 30.0, "<=30 min normal"),
    "rem_lat_min": (60.0, 120.0, "first REM ~90 min; <60 short"),
    "waso_min": (0.0, 30.0, "lower is better"),
    "n3_pct_tst": (10.0, 25.0, "SWS; >=20% delta criterion per mentor"),
    "rem_pct_tst": (18.0, 25.0, "typical adult REM share"),
    "arousal_index": (0.0, 25.0, "AASM-like frequency-shift proxy, not AASM-scored"),
    "apnea_index": (0.0, 5.0, "coarse 1 Hz flow proxy, no SpO2"),
}

BANDS = {
    "delta": (0.5, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 12.0),
    "sigma": (12.0, 16.0),
    "beta": (16.0, 30.0),
}
TOTAL_BAND = (0.5, 30.0)


# ---------------------------------------------------------------- hypnogram
def hypno_features(st: np.ndarray) -> dict:
    """st: int array over the lights-off window, -1 = unscored."""
    f: dict = {}
    n = len(st)
    scored = st >= 0
    sleep = scored & (st > 0)
    f["n_epochs"] = n
    f["tib_min"] = n * EPOCH_S / 60.0
    f["uns_frac"] = float((~scored).sum() / n) if n else float("nan")
    tst_epochs = int(sleep.sum())
    f["tst_min"] = tst_epochs * EPOCH_S / 60.0
    tst_h = f["tst_min"] / 60.0
    f["se_pct"] = 100.0 * tst_epochs / scored.sum() if scored.sum() else float("nan")

    sleep_idx = np.flatnonzero(sleep)
    if len(sleep_idx) == 0:
        f.update({k: float("nan") for k in (
            "sol_min", "waso_min", "rem_lat_min", "n_awakenings",
            "awakening_index", "n_stage_shifts", "shift_index", "sfi",
            "n_rem_episodes", "mean_rem_bout_min", "longest_sleep_bout_min",
            "longest_wake_post_onset_min", "mean_sleep_bout_min")})
        for s in STAGES5[1:]:
            f[f"{s.lower()}_pct_tst"] = float("nan")
        f["wake_pct_tib"] = float("nan")
        f["trans"] = np.zeros((5, 5), dtype=int)
        return f

    onset = int(sleep_idx[0])
    f["sol_min"] = onset * EPOCH_S / 60.0
    post = st[onset:]
    post_scored = post[post >= 0]
    f["waso_min"] = float((post == 0).sum() * EPOCH_S / 60.0)
    rem_idx = np.flatnonzero((st == 4) & scored)
    rem_after = rem_idx[rem_idx >= onset]
    f["rem_lat_min"] = float((rem_after[0] - onset) * EPOCH_S / 60.0) if len(rem_after) else float("nan")

    for i, s in enumerate(STAGES5[1:], start=1):
        f[f"{s.lower()}_pct_tst"] = 100.0 * ((st == i) & scored).sum() / tst_epochs
    f["wake_pct_tib"] = 100.0 * ((st == 0) & scored).sum() / scored.sum()

    # awakenings: sleep->W transitions (W runs after onset)
    is_w = (post == 0)
    f["n_awakenings"] = int(((np.diff(is_w.astype(int)) == 1)).sum())
    f["awakening_index"] = f["n_awakenings"] / tst_h if tst_h else float("nan")

    # stage shifts between consecutive scored epochs
    chg = (np.diff(st) != 0) & scored[1:] & scored[:-1]
    f["n_stage_shifts"] = int(chg.sum())
    f["shift_index"] = f["n_stage_shifts"] / tst_h if tst_h else float("nan")
    f["sfi"] = (f["n_awakenings"] + f["n_stage_shifts"]) / tst_h if tst_h else float("nan")

    # 5x5 transition counts (scored->scored only)
    tr = np.zeros((5, 5), dtype=int)
    a, b = st[:-1], st[1:]
    ok = (a >= 0) & (b >= 0)
    np.add.at(tr, (a[ok], b[ok]), 1)
    f["trans"] = tr

    # REM episodes: contiguous REM runs >= 3 min (= candidate NREM-REM cycles)
    rem = (st == 4).astype(int)
    d = np.diff(np.r_[0, rem, 0])
    starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
    bouts = [(s, e) for s, e in zip(starts, ends) if e - s >= 6]
    f["n_rem_episodes"] = len(bouts)
    f["mean_rem_bout_min"] = float(np.mean([e - s for s, e in bouts]) * EPOCH_S / 60.0) if bouts else float("nan")

    # sleep-bout stats (contiguous sleep runs)
    sl = sleep.astype(int)
    d = np.diff(np.r_[0, sl, 0])
    s_starts, s_ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
    lens = (s_ends - s_starts) * EPOCH_S / 60.0
    f["longest_sleep_bout_min"] = float(lens.max()) if len(lens) else float("nan")
    f["mean_sleep_bout_min"] = float(lens.mean()) if len(lens) else float("nan")
    w = is_w.astype(int)
    d = np.diff(np.r_[0, w, 0])
    wlens = (np.flatnonzero(d == -1) - np.flatnonzero(d == 1)) * EPOCH_S / 60.0
    f["longest_wake_post_onset_min"] = float(wlens.max()) if len(wlens) else 0.0

    # first vs second half of TST (mentor: N1 bouts shorter early)
    mid = onset + (n - onset) // 2
    for half, seg in (("first", st[onset:mid]), ("second", st[mid:])):
        seg_sleep = seg[(seg > 0)]
        if len(seg_sleep):
            f[f"n1_pct_{half}_half"] = 100.0 * (seg_sleep == 1).sum() / len(seg_sleep)
            f[f"rem_pct_{half}_half"] = 100.0 * (seg_sleep == 4).sum() / len(seg_sleep)
        else:
            f[f"n1_pct_{half}_half"] = float("nan")
            f[f"rem_pct_{half}_half"] = float("nan")
    return f


# ------------------------------------------------------------- signal utils
def _window_slice(psg_path: Path, ch: str, e0: int, e1: int) -> tuple[np.ndarray, float]:
    raw = mne.io.read_raw_edf(str(psg_path), preload=True, include=[ch], verbose=False)
    sf = float(raw.info["sfreq"])
    return raw.get_data()[0][int(e0 * EPOCH_S * sf): int(e1 * EPOCH_S * sf)], sf


def _epoch_matrix(x: np.ndarray, sf: float) -> np.ndarray:
    per = int(EPOCH_S * sf)
    n = len(x) // per
    return x[: n * per].reshape(n, per)


def bandpower_features(eeg: np.ndarray) -> dict:
    """Welch PSD per 30-s epoch (Fpz-Cz, volts->uV). Returns aggregates."""
    f: dict = {}
    ep = _epoch_matrix(eeg * 1e6, 100.0)
    freqs, _ = welch(ep[0], fs=100.0, nperseg=512)
    tot_m = (freqs >= TOTAL_BAND[0]) & (freqs <= TOTAL_BAND[1])
    band_m = {b: (freqs >= lo) & (freqs <= hi) for b, (lo, hi) in BANDS.items()}
    abs_p = {b: [] for b in BANDS}
    rel_p = {b: [] for b in BANDS}
    for e in ep:
        _, pxx = welch(e, fs=100.0, nperseg=512)
        tot = pxx[tot_m].sum() + 1e-12
        # spectral entropy of normalized PSD
        pn = pxx[tot_m] / tot
        f.setdefault("_se", []).append(float(-(pn * np.log2(pn + 1e-12)).sum()))
        for b in BANDS:
            a = float(pxx[band_m[b]].sum())
            abs_p[b].append(a)
            rel_p[b].append(a / tot)
    f["epochs_psd"] = len(ep)
    for b in BANDS:
        f[f"abs_{b}_mean"] = float(np.mean(abs_p[b]))
        f[f"rel_{b}_mean"] = float(np.mean(rel_p[b]))
    f["_abs_delta"] = np.array(abs_p["delta"])
    f["_rel"] = {b: np.array(v) for b, v in rel_p.items()}
    return f


def permutation_entropy(x: np.ndarray, order: int = 3) -> float:
    """Normalized permutation entropy of one epoch (order-3, delay 1)."""
    n = len(x) - order + 1
    if n <= 0:
        return float("nan")
    w = np.lib.stride_tricks.sliding_window_view(x, order)
    ranks = np.argsort(w, axis=1)
    # encode rank pattern as base-order number
    code = np.zeros(n, dtype=int)
    mult = 1
    for k in range(order):
        code += ranks[:, k] * mult
        mult *= order
    _, counts = np.unique(code, return_counts=True)
    p = counts / counts.sum()
    return float(-(p * np.log(p)).sum() / np.log(6.0))  # 3! = 6 patterns


def entropy_by_stage(eeg: np.ndarray, st: np.ndarray) -> dict:
    f: dict = {}
    ep = _epoch_matrix(eeg * 1e6, 100.0)
    n = min(len(ep), len(st))
    groups = {"wake": [0], "nrem": [1, 2, 3], "rem": [4]}
    for g, labels in groups.items():
        vals = [permutation_entropy(ep[i]) for i in range(n) if st[i] in labels]
        f[f"perm_entropy_{g}"] = float(np.nanmean(vals)) if vals else float("nan")
    return f


def _events_df(res):
    """yasa>=0.7 returns a *_Results object (None when empty); -> DataFrame."""
    if res is None:
        return None
    try:
        df = res.summary()
    except Exception:  # noqa: BLE001
        df = getattr(res, "_events", None)
    return df


def _col(df: pd.DataFrame, *names: str) -> pd.Series | None:
    for c in names:
        if c in df.columns:
            return df[c]
    return None


def spindle_sw_features(eeg_uv_window: np.ndarray, st: np.ndarray) -> dict:
    """YASA spindle (N2) + slow-wave (N2/N3) detection. yasa int map == ours."""
    import yasa

    f: dict = {}
    hyp = st.astype(int)
    hyp[st < 0] = -2  # unscored
    up = yasa.hypno_upsample_to_data(hyp, sf_hypno=1.0 / EPOCH_S, data=eeg_uv_window, sf_data=100.0)
    try:
        sp = _events_df(yasa.spindles_detect(eeg_uv_window, sf=100.0, hypno=up, include=(2,)))
    except Exception:  # noqa: BLE001
        sp = None
    n2_min = float(((st == 2)).sum() * EPOCH_S / 60.0)
    if sp is not None and len(sp):
        dur = _col(sp, "Duration")
        f["spindle_count_n2"] = int(len(sp))
        f["spindle_density_n2"] = len(sp) / n2_min if n2_min else float("nan")
        f["spindle_dur_mean"] = float(dur.mean()) if dur is not None else float((sp["End"] - sp["Start"]).mean())
        fq = _col(sp, "Frequency", "Freq", "FreqPeak")
        f["spindle_freq_mean"] = float(fq.mean()) if fq is not None else float("nan")
        am = _col(sp, "Amplitude", "Amp", "RMS")
        f["spindle_amp_mean"] = float(am.mean()) if am is not None else float("nan")
    else:
        f.update(spindle_count_n2=0, spindle_density_n2=0.0 if n2_min else float("nan"),
                 spindle_dur_mean=float("nan"), spindle_freq_mean=float("nan"),
                 spindle_amp_mean=float("nan"))
    try:
        sw = _events_df(yasa.sw_detect(eeg_uv_window, sf=100.0, hypno=up, include=(2, 3)))
    except Exception:  # noqa: BLE001
        sw = None
    nrem_min = float(np.isin(st, [1, 2, 3]).sum() * EPOCH_S / 60.0)
    if sw is not None and len(sw):
        dur = _col(sw, "Duration")
        f["sw_count_nrem"] = int(len(sw))
        f["sw_density_nrem"] = len(sw) / nrem_min if nrem_min else float("nan")
        na = _col(sw, "ValNegPeak", "NegAmp", "Amplitude")
        f["sw_negamp_mean"] = float(na.mean()) if na is not None else float("nan")
        f["sw_dur_mean"] = float(dur.mean()) if dur is not None else float("nan")
    else:
        f.update(sw_count_nrem=0, sw_density_nrem=0.0 if nrem_min else float("nan"),
                 sw_negamp_mean=float("nan"), sw_dur_mean=float("nan"))
    return f


def arousal_proxy(eeg: np.ndarray, emg: np.ndarray, emg_sf: float, st: np.ndarray) -> dict:
    """AASM-like cortical-arousal detector (NOT AASM scoring).

    Per-second frequency ratio (alpha+beta)/(delta+theta) on Fpz-Cz (STFT,
    2-s window, 1-s steps); candidate seconds = ratio > 0.4 during sleep.
    NREM sigma-burst (spindle) seconds are excluded pre-merge; hot runs are
    merged across gaps <=2 s, kept if >=3 s and >=10 s apart. Each onset
    needs 10 s of prior sleep whose median ratio stays below threshold
    (abrupt shift into fast activity), and REM onsets additionally need a
    chin-EMG surge (>2x trailing 60-s median; works on the 1 Hz cassette
    envelope and 100 Hz telemetry RMS alike). K-complexes need no gate:
    a delta surge lowers the ratio. Scale-free (ratio), so no EEG
    normalization trap. Whole-night index is winsorized at ARI_MAX (40/h):
    above that the background itself is fast and runs are over-counted.
    """
    sf = 100.0
    x = (eeg * 1e6)[: len(eeg) // int(sf) * int(sf)]
    n_sec = len(x) // int(sf)
    freqs, _, Z = stft(x, fs=sf, nperseg=int(2 * sf), noverlap=int(sf),
                       boundary="zeros", padded=True)
    P = np.abs(Z) ** 2

    def band(lo: float, hi: float) -> np.ndarray:
        m = (freqs >= lo) & (freqs < hi)
        return P[m].sum(axis=0)[:n_sec] + 1e-12

    fast = band(8.0, 12.0) + band(16.0, 30.0)
    slow = band(0.5, 4.0) + band(4.0, 8.0)
    sigma = band(11.0, 16.0)
    ratio = fast / slow
    TH = 0.4
    stage_1s = np.repeat(st.astype(int), int(EPOCH_S))[:n_sec]
    sleep_1s = stage_1s > 0
    hot = (ratio > TH) & sleep_1s
    # spindle gate: sigma bursts in NREM are normal microstructure, not arousals
    sig_base = pd.Series(sigma).rolling(60, min_periods=10).median().to_numpy()
    hot = hot & ~((sigma > 3.0 * sig_base) & np.isin(stage_1s, [1, 2, 3]))
    # merge hot runs across gaps <=2 s, keep merged runs >=3 s, >=10 s apart
    d = np.diff(np.r_[0, hot.astype(int), 0])
    starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
    merged: list[list[int]] = []
    for s, e in zip(starts, ends):
        if merged and s - merged[-1][1] <= 2:
            merged[-1][1] = int(e)
        else:
            merged.append([int(s), int(e)])
    events = [(s, e) for s, e in merged if e - s >= 3]
    events = [ev for i, ev in enumerate(events)
              if i == 0 or ev[0] - events[i - 1][0] >= 10]
    # abrupt-shift precondition: 10 s prior sleep, median ratio below threshold
    pre = [ev for ev in events
           if ev[0] >= 10 and bool(sleep_1s[ev[0] - 10:ev[0]].all())
           and bool(np.median(ratio[ev[0] - 10:ev[0]]) < TH)]
    # REM EMG gate: 1-s EMG series vs trailing median, surge must overlap event
    n_es = len(emg) // int(emg_sf)
    if emg_sf >= 50:
        ep = (np.abs(emg[: n_es * int(emg_sf)]) * 1e6).reshape(n_es, int(emg_sf))
        emg_1s = np.sqrt((ep ** 2).mean(axis=1))
    else:  # 1 Hz rectified envelope: nearest sample per second
        take = np.clip((np.arange(n_sec) * emg_sf).astype(int), 0, len(emg) - 1)
        emg_1s = np.abs(emg[take]) * 1e6
    emg_base = pd.Series(emg_1s).rolling(60, min_periods=10).median().to_numpy()
    surge = emg_1s[:n_sec] > 2.0 * emg_base[:n_sec]
    kept = [s for s, e in pre
            if stage_1s[s] != 4 or bool(surge[s:e].any())]
    tst_h = sleep_1s.sum() / 3600.0
    n = len(kept)
    if tst_h and n / tst_h > ARI_MAX:  # winsorize over-fire nights, keep count/index consistent
        n = int(ARI_MAX * tst_h)
    return {
        "arousal_count": n,
        "arousal_index": n / tst_h if tst_h else float("nan"),
    }


def emg_features(emg: np.ndarray, sf: float, st: np.ndarray) -> dict:
    """Chin EMG in Sleep-EDF is a 1 Hz rectified envelope: per-epoch RMS."""
    per = max(int(EPOCH_S * sf), 1)
    n = min(len(emg) // per, len(st))
    ep = emg[: n * per].reshape(n, per) * 1e6
    rms = np.sqrt((ep[:n] ** 2).mean(axis=1))
    med = float(np.median(rms)) + 1e-9
    rem = rms[np.array([st[i] == 4 for i in range(n)])]
    nrem = rms[np.array([st[i] in (1, 2, 3) for i in range(n)])]
    return {
        "emg_median_uv": med,
        "emg_rem_mean_uv": float(rem.mean()) if len(rem) else float("nan"),
        "emg_nrem_mean_uv": float(nrem.mean()) if len(nrem) else float("nan"),
        "rem_atonia_ratio": float(nrem.mean() / (rem.mean() + 1e-9)) if len(rem) and len(nrem) else float("nan"),
        "movement_index": float((rms > 3.0 * med).mean()),
    }


def apnea_proxy(psg_path: Path, e0: int, e1: int, st: np.ndarray) -> dict:
    """Coarse apnea proxy on 1 Hz oro-nasal flow (cassette only).

    Event = |flow| envelope < 10% of trailing 120-s median for >=10 s during
    sleep. No SpO2 -> hypopneas unreliable (skipped by design).
    """
    try:
        flow, sf = _window_slice(psg_path, RESP_CH, e0, e1)
    except (ValueError, KeyError, OSError):
        return {"apnea_count": float("nan"), "apnea_index": float("nan"),
                "apnea_time_pct": float("nan"), "has_flow": 0}
    sf = float(sf)
    env = pd.Series(np.abs(flow)).rolling(max(int(5 * sf), 1), min_periods=1, center=True).mean().to_numpy()
    base = pd.Series(env).rolling(max(int(120 * sf), 10), min_periods=10).median().to_numpy()
    sleep_s = np.repeat((st > 0).astype(bool), int(EPOCH_S * sf))[: len(env)]
    low = (env < 0.10 * (base + 1e-9)) & sleep_s
    per = int(10 * sf)
    d = np.diff(np.r_[0, low.astype(int), 0])
    starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
    runs = [(s, e) for s, e in zip(starts, ends) if e - s >= per]
    merged = []
    for s, e in runs:
        if merged and s - merged[-1][1] <= int(5 * sf):
            merged[-1][1] = e
        else:
            merged.append([s, e])
    tst_h = (st > 0).sum() * EPOCH_S / 3600.0
    ap_s = sum(e - s for s, e in merged) / sf
    return {
        "apnea_count": len(merged),
        "apnea_index": len(merged) / tst_h if tst_h else float("nan"),
        "apnea_time_pct": 100.0 * ap_s / (len(env) / sf),
        "has_flow": 1,
    }


def movement_annotation_frac(hyp_path: Path, e0: int, e1: int) -> float:
    """Fraction of window covered by hypnogram annotations that are neither
    stages nor '?' (e.g. Movement time)."""
    try:
        ann = mne.read_annotations(str(hyp_path))
    except (FileNotFoundError, OSError):
        return float("nan")
    w0, w1 = e0 * EPOCH_S, e1 * EPOCH_S
    tot = 0.0
    for onset, dur, desc in zip(ann.onset, ann.duration, ann.description):
        if desc in ANN_TO_STAGE:
            continue
        ov = max(0.0, min(onset + dur, w1) - max(onset, w0))
        tot += ov
    return tot / (w1 - w0) if w1 > w0 else float("nan")


# ------------------------------------------------------------------ driver
def load_stage_source(
    source: str, sid: str, clean_root: Path = CLEAN_ROOT, preds_root: Path = PREDS_ROOT
) -> np.ndarray | None:
    if source == "expert":
        p = Path(clean_root) / "stages" / f"{sid}.npy"
        if not p.is_file():
            return None
        a = np.load(p)
        st = a.astype(np.int16)
        st[a == 255] = -1
        return st
    p = Path(preds_root) / source / f"{sid}.npy"
    if not p.is_file():
        return None
    return np.load(p).astype(np.int16)


def run_one(
    psg: Path,
    hyp: Path,
    e0: int,
    e1: int,
    sid: str,
    source: str,
    with_signal: bool,
    clean_root: Path = CLEAN_ROOT,
    preds_root: Path = PREDS_ROOT,
) -> dict | None:
    st_full = load_stage_source(source, sid, clean_root, preds_root)
    if st_full is None:
        return None
    st = st_full[: max(e1 - e0, 0)]
    if len(st) != e1 - e0:  # model preds mirror the window; expert file IS the window
        if source == "expert" and len(st_full) == e1 - e0:
            st = st_full
        else:
            return None
    row: dict = {"session": sid, "source": source}
    t0 = time.time()
    hf = hypno_features(st)
    tr = hf.pop("trans")
    for i in range(5):
        for j in range(5):
            hf[f"tr_{STAGES5[i]}_{STAGES5[j]}"] = int(tr[i, j])
    row.update(hf)
    row["move_annot_frac"] = movement_annotation_frac(hyp, e0, e1)

    if with_signal:
        eeg, _ = _window_slice(psg, EEG_CH, e0, e1)
        bp = bandpower_features(eeg)
        abs_delta = bp.pop("_abs_delta")
        rel = bp.pop("_rel")
        row.update({k: v for k, v in bp.items() if not k.startswith("_")})
        nrem_m = np.isin(st[: len(abs_delta)], [1, 2, 3])
        row["swa_nrem_mean"] = float(abs_delta[nrem_m].mean()) if nrem_m.sum() else float("nan")
        row["swa_sum"] = float(abs_delta[nrem_m].sum())
        row["rel_delta_nrem"] = float(rel["delta"][: len(st)][nrem_m].mean()) if nrem_m.sum() else float("nan")
        se = np.array(bp.get("_se", []))
        # spectral entropy per group via epoch index reuse
        ep_n = min(len(se), len(st))
        for g, labels in (("nrem", [1, 2, 3]), ("rem", [4]), ("wake", [0])):
            m = np.isin(st[:ep_n], labels)
            row[f"spec_entropy_{g}"] = float(se[:ep_n][m].mean()) if m.sum() else float("nan")
        row.update(entropy_by_stage(eeg, st))
        row.update(spindle_sw_features(eeg * 1e6, st))
        emg, emg_sf = _window_slice(psg, EMG_CH, e0, e1)
        row.update(arousal_proxy(eeg, emg, emg_sf, st))
        row.update(emg_features(emg, emg_sf, st))
        row.update(apnea_proxy(psg, e0, e1, st))
    row["elapsed_s"] = round(time.time() - t0, 1)
    return row


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Sleep-quality parameter extraction (lights-off)")
    ap.add_argument("--source", default="expert",
                    help="expert | usleep | tinysleepnet | yasa (preds dir name)")
    ap.add_argument("--subset", choices=["cassette", "telemetry", "both"], default="both")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-signal", action="store_true", help="hypnogram features only")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--edf-root", type=Path, default=EDF_ROOT, help="raw Sleep-EDF dataset root")
    ap.add_argument("--clean-root", type=Path, default=CLEAN_ROOT, help="lights-off windows")
    ap.add_argument("--preds-root", type=Path, default=PREDS_ROOT,
                    help="per-epoch staging predictions (for --source <model>)")
    ap.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    args = ap.parse_args(argv)

    try:
        man = load_manifest(args.clean_root)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    man = man[man["subset"].str.contains("cassette" if args.subset == "cassette"
                                         else "telemetry" if args.subset == "telemetry"
                                         else "sleep")]
    rows_all = list(man.itertuples())
    if args.limit:
        rows_all = rows_all[: args.limit]

    out = args.report_dir / f"sqi_features_{args.source}_lights_off.csv"
    done: set[str] = set()
    if args.resume and out.is_file():
        done = set(pd.read_csv(out, usecols=["session"])["session"].astype(str))
        print(f"resume: {len(done)} sessions already in {out.name}")

    rows: list[dict] = []
    n_skip = 0
    for r in rows_all:
        sid = str(r.session)
        if sid in done:
            n_skip += 1
            continue
        psg = args.edf_root / str(r.subset) / str(r.psg)
        hyp = args.edf_root / str(r.subset) / str(r.hypnogram)
        try:
            row = run_one(psg, hyp, int(r.epoch_start), int(r.epoch_end),
                          sid, args.source, not args.no_signal,
                          args.clean_root, args.preds_root)
        except Exception as e:  # noqa: BLE001
            print(f"  [fail] {sid}: {type(e).__name__}: {e}")
            continue
        if row is None:
            print(f"  [missing] {sid}")
            continue
        rows.append(row)
        print(f"  {sid} TST={row['tst_min']:.0f}m SE={row['se_pct']:.1f}% "
              f"SOL={row['sol_min']:.1f} WASO={row['waso_min']:.0f} "
              f"({row['elapsed_s']}s)", flush=True)

    if done and out.is_file():
        prev = pd.read_csv(out)
        df = pd.concat([prev, pd.DataFrame(rows)], ignore_index=True)
    else:
        df = pd.DataFrame(rows)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"\nwrote {out} ({len(df)} nights, {n_skip} resumed)")
    if len(df):
        cols = ["tst_min", "se_pct", "sol_min", "waso_min", "rem_lat_min",
                "n1_pct_tst", "n2_pct_tst", "n3_pct_tst", "rem_pct_tst", "sfi"]
        if "arousal_index" in df:
            cols += ["arousal_index", "spindle_density_n2", "apnea_index"]
        print(df[[c for c in cols if c in df]].mean(numeric_only=True).round(2).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
