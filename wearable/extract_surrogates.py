"""Extract wearable-style motion / respiration surrogates from Sleep-EDF PSG.

Why: benchmark wearable sleep-staging models against expert PSG labels. The
PSG is used as a sensor surrogate, not as EEG input:

  EMG submental   -> motion / actigraphy proxy
  EOG horizontal  -> eye-movement activity (REM / arousal proxy)
  Resp oro-nasal  -> breathing rate + variability (breathing-belt surrogate)
  Temp rectal     -> optional slow trend (cassette only)

Native rates matter (verified on all 197 files):
  cassette : EEG/EOG 100 Hz, Resp/EMG/Temp 1 Hz (one session at 200/2 Hz)
  telemetry: EEG/EOG/EMG 100 Hz, no Resp/Temp
So high-rate EMG features exist only for telemetry; 1 Hz features exist for
all nights. EOG is the only 100 Hz non-EEG channel everywhere.

Windows/labels come from <clean-root> (lights-off window); epoch t of every
output is aligned 1:1 with stages/<sid>.npy[t].

Outputs (default ./data/wearable/):
  manifest.csv                  per-session metadata + channel availability
  features/<sid>.csv.gz         per-epoch raw + z-scored features
  windows/<sid>.npz             1 Hz and 25 Hz normalized waveforms + labels
  counts/<sid>.csv              per-minute activity counts (HypnosPy input)
  norm_stats.csv                per-session median/scale used for z-scores
  feature_dictionary.csv        feature name -> family/description
  qc.csv                        QC flags and timings
  splits.csv                    frozen subject-wise GroupKFold assignment
  yasa_pred/<sid>.npy           optional EEG-baseline predictions (--with-yasa)

Usage (from wearable/):
  python extract_surrogates.py --limit 3                    # smoke, cassette
  python extract_surrogates.py --subset both --limit 0 --jobs 6
  python extract_surrogates.py --with-yasa --limit 3
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import mne
import numpy as np
import pandas as pd
from scipy.signal import butter, find_peaks, resample_poly, sosfiltfilt
from scipy.stats import kurtosis

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent
DEFAULT_DATA_ROOT = Path(
    os.environ.get("SLEEPLENS_DATA", Path.home() / "Projects" / "sleep-analysis" / "test" / "data")
).expanduser()
DEFAULT_EDF_ROOT = Path(
    os.environ.get("SLEEPLENS_EDF", DEFAULT_DATA_ROOT / "sleep-edf-database-expanded-1.0.0")
).expanduser()
DEFAULT_CLEAN_ROOT = Path(
    os.environ.get("SLEEPLENS_CLEAN", DEFAULT_DATA_ROOT / "sleepedf_clean")
).expanduser()
DEFAULT_OUT = HERE / "data" / "wearable"

EPOCH_S = 30.0
FS_LOW = 1.0
N_LOW = int(FS_LOW * EPOCH_S)  # 30 samples/epoch
FS_HIGH = 25.0
N_HIGH = int(FS_HIGH * EPOCH_S)  # 750 samples/epoch

STAGES5 = ["WAKE", "N1", "N2", "N3", "REM"]
UNS = 255

EMG_CH = "EMG submental"
EOG_CH = "EOG horizontal"
RESP_CH = "Resp oro-nasal"
TEMP_CH = "Temp rectal"
EEG_CH = "EEG Fpz-Cz"

FEATURES = [
    # motion / chin EMG
    ("emg_rms", "motion", "RMS of native-rate EMG per 30 s epoch"),
    ("emg_std", "motion", "Standard deviation of EMG"),
    ("emg_range", "motion", "Peak-to-peak amplitude of EMG"),
    ("emg_diff_std", "motion", "Std of first difference (activity/roughness)"),
    ("emg_bp_10_45", "motion", "EMG power 10-45 Hz (>=20 Hz native only)"),
    ("emg_bp_10_20", "motion", "EMG power 10-20 Hz (>=20 Hz native only)"),
    ("emg_bp_20_45", "motion", "EMG power 20-45 Hz (>=20 Hz native only)"),
    ("emg_zcr", "motion", "Zero-crossing rate (>=20 Hz native only)"),
    ("emg_hjorth_activity", "motion", "Hjorth activity (>=20 Hz native only)"),
    ("emg_hjorth_mobility", "motion", "Hjorth mobility (>=20 Hz native only)"),
    ("emg_hjorth_complexity", "motion", "Hjorth complexity (>=20 Hz native only)"),
    ("emg_spec_entropy", "motion", "Spectral entropy 0.5-45 Hz (>=20 Hz native only)"),
    ("emg_kurtosis", "motion", "Excess kurtosis (>=20 Hz native only)"),
    ("emg_pim_count", "motion", "Proportional-integration-mode counts (adaptive threshold)"),
    ("emg_active_frac", "motion", "Fraction of samples above motion threshold"),
    # eye movement / EOG
    ("eog_var", "eye", "EOG variance per epoch (0.5-10 Hz)"),
    ("eog_bp_0_5_10", "eye", "EOG power 0.5-10 Hz"),
    ("eog_zcr", "eye", "EOG zero-crossing rate (0.5-10 Hz)"),
    ("eog_spec_entropy", "eye", "EOG spectral entropy 0.5-45 Hz"),
    ("eog_peak_rate", "eye", "Detected eye-movement/blink peaks per 30 s"),
    ("eog_amp_p95", "eye", "95th percentile |EOG| (0.5-10 Hz)"),
    # respiration / oro-nasal airflow
    ("resp_rate_bpm", "resp", "Breaths per minute (peak detection, cassette only)"),
    ("resp_rate_cv", "resp", "Within-epoch breath-interval CV (cassette only)"),
    ("resp_amp_var", "resp", "Variance of band-passed airflow (cassette only)"),
    ("resp_bp_0_1_0_5", "resp", "Airflow power 0.1-0.45 Hz (cassette only)"),
    # temperature
    ("temp_mean", "temp", "Mean rectal temperature per epoch (cassette only)"),
    ("temp_slope", "temp", "Within-epoch temperature slope (cassette only)"),
]
FEATURE_NAMES = [f[0] for f in FEATURES]
HIGH_RATE_EMG = {
    "emg_bp_10_45", "emg_bp_10_20", "emg_bp_20_45", "emg_zcr",
    "emg_hjorth_activity", "emg_hjorth_mobility", "emg_hjorth_complexity",
    "emg_spec_entropy", "emg_kurtosis",
}
LOG_FEATURES = {
    f for f in FEATURE_NAMES
    if any(t in f for t in ("rms", "var", "bp_", "amp_p95", "pim_count", "diff_std"))
}


def _sid(path: Path) -> str:
    return path.name[:6]


def pair_sessions(edf_root: Path, subset: str) -> list[tuple[Path, Path]]:
    folder = {"cassette": "sleep-cassette", "telemetry": "sleep-telemetry", "both": None}[subset]
    roots = (
        [Path(edf_root) / folder]
        if folder
        else [Path(edf_root) / "sleep-cassette", Path(edf_root) / "sleep-telemetry"]
    )
    pairs = []
    for root in roots:
        psg_map = {_sid(p): p for p in sorted(root.glob("*-PSG.edf"))}
        for hyp in sorted(root.glob("*-Hypnogram.edf")):
            sid = _sid(hyp)
            if sid in psg_map:
                pairs.append((psg_map[sid], hyp))
    return pairs


def load_clean_manifest(clean_root: Path) -> dict[str, dict]:
    man = pd.read_csv(clean_root / "manifest.csv")
    return {str(r["session"]): r for _, r in man.iterrows()}


def _bandpass(x: np.ndarray, fs: float, lo: float, hi: float, order: int = 4) -> np.ndarray:
    hi = min(hi, 0.45 * fs)
    lo = max(lo, 0.0)
    if hi <= lo or x.size < 3 * (order + 1):
        return x - np.nanmean(x)
    sos = butter(order, [lo, hi], btype="band", fs=fs, output="sos")
    return sosfiltfilt(sos, x)


def _lowpass(x: np.ndarray, fs: float, hi: float, order: int = 4) -> np.ndarray:
    if x.size < 3 * (order + 1):
        return x
    sos = butter(order, min(hi, 0.45 * fs), btype="low", fs=fs, output="sos")
    return sosfiltfilt(sos, x)


def _to_rate(x: np.ndarray, fs_in: float, fs_out: float) -> np.ndarray:
    if abs(fs_in - fs_out) < 1e-9:
        return x
    g = math.gcd(int(round(fs_in)), int(round(fs_out)))
    return resample_poly(x, int(round(fs_out)) // g, int(round(fs_in)) // g)


def _epochs(x: np.ndarray, fs: float, n_epochs: int) -> np.ndarray:
    n = int(round(EPOCH_S * fs))
    x = np.asarray(x, dtype=np.float64)[: n_epochs * n]
    return x.reshape(-1, n)


def _band_powers(ep: np.ndarray, fs: float, bands: dict[str, tuple[float, float]]) -> dict[str, np.ndarray]:
    freqs = np.fft.rfftfreq(ep.shape[1], d=1.0 / fs)
    spec = np.abs(np.fft.rfft(ep, axis=1)) ** 2 / ep.shape[1]
    out = {}
    for name, (lo, hi) in bands.items():
        m = (freqs >= lo) & (freqs < hi)
        out[name] = spec[:, m].sum(axis=1)
    return out


def _spectral_entropy(ep: np.ndarray, fs: float, lo: float = 0.5, hi: float = 45.0) -> np.ndarray:
    freqs = np.fft.rfftfreq(ep.shape[1], d=1.0 / fs)
    spec = np.abs(np.fft.rfft(ep, axis=1)) ** 2 / ep.shape[1]
    m = (freqs >= lo) & (freqs < min(hi, 0.45 * fs))
    if m.sum() < 2:
        return np.full(ep.shape[0], np.nan)
    p = spec[:, m]
    p = p / np.maximum(p.sum(axis=1, keepdims=True), 1e-12)
    ent = -(p * np.log(np.maximum(p, 1e-12))).sum(axis=1)
    return ent / np.log(p.shape[1])


def _hjorth(ep: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    var = np.var(ep, axis=1)
    d1 = np.diff(ep, axis=1)
    var_d1 = np.var(d1, axis=1)
    d2 = np.diff(d1, axis=1)
    var_d2 = np.var(d2, axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        activity = var
        mobility = np.sqrt(var_d1 / var)
        complexity = np.sqrt(var_d2 / var_d1) / mobility
    bad = ~np.isfinite(mobility) | (var <= 0)
    for a in (activity, mobility, complexity):
        a[bad] = np.nan
    return activity, mobility, complexity


def _zcr(ep: np.ndarray) -> np.ndarray:
    return np.mean(np.diff(np.sign(ep), axis=1) != 0, axis=1)


def _robust_threshold(x: np.ndarray, k: float = 1.5) -> float:
    med = np.nanmedian(x)
    mad = np.nanmedian(np.abs(x - med))
    return float(med + k * 1.4826 * mad)


def _pim(env: np.ndarray, fs: float, n_epochs: int) -> tuple[np.ndarray, np.ndarray]:
    thr = _robust_threshold(env)
    above = env > thr
    rising = np.flatnonzero(above & ~np.roll(above, 1))
    counts = np.histogram(rising, bins=np.arange(n_epochs + 1) * int(round(EPOCH_S * fs)))[0].astype(float)
    ep_above = _epochs(above.astype(np.float64), fs, n_epochs)
    active = np.nanmean(ep_above, axis=1)
    return counts, active


def _normalize_col(v: np.ndarray) -> tuple[np.ndarray, float, float]:
    med = float(np.nanmedian(v))
    mad = float(np.nanmedian(np.abs(v - med)))
    scale = 1.4826 * mad
    if not np.isfinite(scale) or scale <= 0:
        scale = float(np.nanstd(v))
    if not np.isfinite(scale) or scale <= 0:
        scale = 1.0
    z = (v - med) / scale
    return np.clip(z, -8.0, 8.0), med, scale


def _normalize_wave(x: np.ndarray, log_first: bool) -> tuple[np.ndarray, float, float]:
    flat = x.reshape(-1).astype(np.float64)
    flat = np.log1p(np.maximum(flat, 0.0)) if log_first else flat
    med = float(np.nanmedian(flat))
    mad = float(np.nanmedian(np.abs(flat - med)))
    scale = 1.4826 * mad
    if not np.isfinite(scale) or scale <= 0:
        scale = float(np.nanstd(flat)) or 1.0
    y = (flat - med) / scale
    y = np.clip(y, -5.0, 5.0).reshape(x.shape).astype(np.float16)
    return y, med, scale


def _native_rates(raw: mne.io.BaseRaw) -> dict[str, float]:
    ns = list(raw._raw_extras[0]["n_samps"])
    names = list(raw.ch_names)
    fs_max = float(raw.info["sfreq"])
    record_dur = max(ns) / fs_max
    return {ch: ns[i] / record_dur for i, ch in enumerate(names)}


def extract_one(
    psg_path: Path,
    man_row: dict,
    out_dir: Path,
    with_yasa: bool,
    overwrite: bool,
    clean_root: Path = DEFAULT_CLEAN_ROOT,
) -> tuple[dict, list[dict]]:
    sid = str(man_row["session"])
    fdir = out_dir / "features"
    wdir = out_dir / "windows"
    cdir = out_dir / "counts"
    qc_path = out_dir / "qc" / f"{sid}.json"
    yasa_done = (out_dir / "yasa_pred" / f"{sid}.npy").is_file()
    if (
        not overwrite
        and qc_path.is_file()
        and (fdir / f"{sid}.csv.gz").is_file()
        and (wdir / f"{sid}.npz").is_file()
        and (not with_yasa or yasa_done)
    ):
        qc = json.loads(qc_path.read_text())
        qc.setdefault("subject_key", f"{man_row['subset']}:{int(man_row['subject'])}")
        return qc, []

    t_start = time.time()
    stages = np.load(Path(clean_root) / "stages" / f"{sid}.npy")
    e0, e1 = int(man_row["epoch_start"]), int(man_row["epoch_end"])
    n_epochs = int(e1 - e0)
    if len(stages) != n_epochs:
        raise ValueError(f"{sid}: stages={len(stages)} != window={n_epochs}")

    header = mne.io.read_raw_edf(str(psg_path), preload=False, verbose=False)
    native = _native_rates(header)
    wanted = [c for c in (EMG_CH, EOG_CH, RESP_CH, TEMP_CH) if c in header.ch_names]
    del header

    tmin, tmax = e0 * EPOCH_S, e1 * EPOCH_S
    groups: dict[float, list[str]] = {}
    for ch in wanted:
        groups.setdefault(round(native[ch], 3), []).append(ch)
    data: dict[str, np.ndarray] = {}
    for fs_g, chans in groups.items():
        raw = mne.io.read_raw_edf(str(psg_path), include=chans, preload=True, verbose=False)
        fs = float(raw.info["sfreq"])
        start = int(round(tmin * fs))
        stop = min(int(round(tmax * fs)), raw.n_times)
        d = raw.get_data(start=start, stop=stop)
        for i, ch in enumerate(raw.ch_names):
            data[ch] = d[i]
        del raw

    feats: dict[str, np.ndarray] = {}

    # ---- motion / chin EMG -------------------------------------------------
    has_highrate_emg = False
    if EMG_CH in data:
        fs_e = native[EMG_CH]
        emg = data[EMG_CH]
        has_highrate_emg = fs_e >= 20.0
        ep = _epochs(emg, fs_e, n_epochs)
        feats["emg_rms"] = np.sqrt(np.nanmean(ep**2, axis=1))
        feats["emg_std"] = np.nanstd(ep, axis=1)
        feats["emg_range"] = np.nanmax(ep, axis=1) - np.nanmin(ep, axis=1)
        feats["emg_diff_std"] = np.nanstd(np.diff(ep, axis=1), axis=1)
        if has_highrate_emg:
            emg_f = _bandpass(emg, fs_e, 10.0, 45.0)
            env = _lowpass(np.abs(emg_f), fs_e, 5.0)
            ep_f = _epochs(emg_f, fs_e, n_epochs)
            bp = _band_powers(ep_f, fs_e, {"10_45": (10.0, 45.0), "10_20": (10.0, 20.0), "20_45": (20.0, 45.0)})
            feats["emg_bp_10_45"] = bp["10_45"]
            feats["emg_bp_10_20"] = bp["10_20"]
            feats["emg_bp_20_45"] = bp["20_45"]
            feats["emg_zcr"] = _zcr(ep_f)
            act, mob, comp = _hjorth(ep_f)
            feats["emg_hjorth_activity"], feats["emg_hjorth_mobility"] = act, mob
            feats["emg_hjorth_complexity"] = comp
            feats["emg_spec_entropy"] = _spectral_entropy(ep_f, fs_e)
            feats["emg_kurtosis"] = kurtosis(ep_f, axis=1, fisher=True)
            pim, active = _pim(env, fs_e, n_epochs)
            feats["emg_pim_count"], feats["emg_active_frac"] = pim, active
            motion25 = _to_rate(env, fs_e, FS_HIGH)
            mask_motion25 = True
        else:
            for name in ("emg_bp_10_45", "emg_bp_10_20", "emg_bp_20_45", "emg_zcr",
                         "emg_hjorth_activity", "emg_hjorth_mobility", "emg_hjorth_complexity",
                         "emg_spec_entropy", "emg_kurtosis"):
                feats[name] = np.full(n_epochs, np.nan)
            pim, active = _pim(emg, fs_e, n_epochs)
            feats["emg_pim_count"], feats["emg_active_frac"] = pim, active
            motion25 = np.zeros(n_epochs * N_HIGH, dtype=np.float64)
            mask_motion25 = False
        motion1 = _to_rate(emg, fs_e, FS_LOW)
    else:
        for name in FEATURE_NAMES:
            if name.startswith("emg_"):
                feats[name] = np.full(n_epochs, np.nan)
        motion1 = np.zeros(n_epochs * N_LOW)
        motion25 = np.zeros(n_epochs * N_HIGH)
        mask_motion25 = False

    # ---- eye movement / EOG ------------------------------------------------
    if EOG_CH in data:
        fs_o = native[EOG_CH]
        eog = data[EOG_CH]
        eog_f = _bandpass(eog, fs_o, 0.5, 10.0)
        ep = _epochs(eog_f, fs_o, n_epochs)
        feats["eog_var"] = np.nanvar(ep, axis=1)
        bp = _band_powers(ep, fs_o, {"0_5_10": (0.5, 10.0)})
        feats["eog_bp_0_5_10"] = bp["0_5_10"]
        feats["eog_zcr"] = _zcr(ep)
        feats["eog_spec_entropy"] = _spectral_entropy(ep, fs_o)
        thr = _robust_threshold(eog_f, 3.0)
        peaks, _ = find_peaks(eog_f, height=thr, distance=max(int(0.2 * fs_o), 1))
        feats["eog_peak_rate"] = np.histogram(
            peaks, bins=np.arange(n_epochs + 1) * int(round(EPOCH_S * fs_o))
        )[0].astype(float)
        feats["eog_amp_p95"] = np.nanpercentile(np.abs(ep), 95, axis=1)
        eog25 = _to_rate(eog_f, fs_o, FS_HIGH)
        eog1 = _to_rate(np.abs(eog_f), fs_o, FS_LOW)
        mask_eog25 = True
    else:
        for name in FEATURE_NAMES:
            if name.startswith("eog_"):
                feats[name] = np.full(n_epochs, np.nan)
        eog25 = np.zeros(n_epochs * N_HIGH)
        eog1 = np.zeros(n_epochs * N_LOW)
        mask_eog25 = False

    # ---- respiration / oro-nasal airflow -----------------------------------
    has_resp = RESP_CH in data
    if has_resp:
        fs_r = native[RESP_CH]
        resp = data[RESP_CH]
        resp_f = _bandpass(resp, fs_r, 0.05, 0.45)
        ep = _epochs(resp_f, fs_r, n_epochs)
        feats["resp_amp_var"] = np.nanvar(ep, axis=1)
        bp = _band_powers(ep, fs_r, {"0_1_0_5": (0.1, 0.45)})
        feats["resp_bp_0_1_0_5"] = bp["0_1_0_5"]
        prom = 0.3 * float(np.nanstd(resp_f)) if np.isfinite(np.nanstd(resp_f)) else None
        peaks, _ = find_peaks(resp_f, distance=max(int(1.5 * fs_r), 1), prominence=prom)
        ep_len = int(round(EPOCH_S * fs_r))
        rate = np.full(n_epochs, np.nan)
        rcv = np.full(n_epochs, np.nan)
        for k in range(n_epochs):
            p = peaks[(peaks >= k * ep_len) & (peaks < (k + 1) * ep_len)]
            if p.size >= 1:
                rate[k] = 60.0 * p.size / EPOCH_S
            if p.size >= 3:
                iv = np.diff(p) / fs_r
                if iv.mean() > 0:
                    rcv[k] = iv.std() / iv.mean()
        feats["resp_rate_bpm"], feats["resp_rate_cv"] = rate, rcv
        resp1 = _to_rate(resp, fs_r, FS_LOW)
    else:
        for name in ("resp_rate_bpm", "resp_rate_cv", "resp_amp_var", "resp_bp_0_1_0_5"):
            feats[name] = np.full(n_epochs, np.nan)
        resp1 = np.zeros(n_epochs * N_LOW)

    # ---- temperature -------------------------------------------------------
    has_temp = TEMP_CH in data
    if has_temp:
        fs_t = native[TEMP_CH]
        temp = data[TEMP_CH]
        ep = _epochs(temp, fs_t, n_epochs)
        feats["temp_mean"] = np.nanmean(ep, axis=1)
        t = np.arange(ep.shape[1]) / fs_t
        tc = t - t.mean()
        feats["temp_slope"] = ((ep - ep.mean(axis=1, keepdims=True)) * tc).sum(axis=1) / (tc**2).sum()
    else:
        feats["temp_mean"] = np.full(n_epochs, np.nan)
        feats["temp_slope"] = np.full(n_epochs, np.nan)

    # ---- features dataframe (raw + z) --------------------------------------
    df = pd.DataFrame({
        "session": sid,
        "subject": int(man_row["subject"]),
        "subject_key": f"{man_row['subset']}:{int(man_row['subject'])}",
        "subset": str(man_row["subset"]),
        "night": int(man_row["night"]),
        "epoch_local": np.arange(n_epochs),
        "epoch_full": e0 + np.arange(n_epochs),
        "stage": stages.astype(np.int16),
    })
    for name in FEATURE_NAMES:
        v = np.asarray(feats[name], dtype=np.float64)
        v = np.where(np.isfinite(v), v, np.nan)
        df[name] = v
    norm_rows = []
    for name in FEATURE_NAMES:
        v = df[name].to_numpy(dtype=np.float64)
        if name in LOG_FEATURES:
            v = np.log1p(np.maximum(v, 0.0))
        z, med, scale = _normalize_col(v)
        df[f"z_{name}"] = z
        norm_rows.append({"session": sid, "feature": name, "median": med, "scale": scale})

    fdir.mkdir(parents=True, exist_ok=True)
    df.to_csv(fdir / f"{sid}.csv.gz", index=False, compression="gzip")

    # ---- waveform tensors --------------------------------------------------
    wdir.mkdir(parents=True, exist_ok=True)
    motion1_n, m1_med, m1_scale = _normalize_wave(_epochs(motion1, FS_LOW, n_epochs), log_first=True)
    eog1_n, e1_med, e1_scale = _normalize_wave(_epochs(eog1, FS_LOW, n_epochs), log_first=True)
    resp1_n, r1_med, r1_scale = _normalize_wave(_epochs(resp1, FS_LOW, n_epochs), log_first=True)
    eog25_n, e25_med, e25_scale = _normalize_wave(_epochs(eog25, FS_HIGH, n_epochs), log_first=False)
    motion25_n, m25_med, m25_scale = _normalize_wave(_epochs(motion25, FS_HIGH, n_epochs), log_first=False)
    np.savez_compressed(
        wdir / f"{sid}.npz",
        motion1=motion1_n, eog1=eog1_n, resp1=resp1_n,
        eog25=eog25_n, motion25=motion25_n,
        labels=stages.astype(np.uint8),
        mask_motion25=np.array(mask_motion25), mask_eog25=np.array(mask_eog25),
        mask_resp=np.array(has_resp), mask_temp=np.array(has_temp),
        fs_low=np.array(FS_LOW), fs_high=np.array(FS_HIGH),
        epoch_start=np.array(e0),
        norm=json.dumps({
            "motion1": [m1_med, m1_scale], "eog1": [e1_med, e1_scale],
            "resp1": [r1_med, r1_scale], "eog25": [e25_med, e25_scale],
            "motion25": [m25_med, m25_scale],
        }),
    )

    # ---- per-minute activity counts (HypnosPy) -----------------------------
    cdir.mkdir(parents=True, exist_ok=True)
    minutes = np.arange(n_epochs * 30 // 60)
    act = motion1[: len(minutes) * 60].reshape(len(minutes), 60).mean(axis=1)
    start = pd.Timestamp(str(man_row["meas_date"])) if str(man_row["meas_date"]) else pd.Timestamp("1970-01-01")
    start = start + pd.Timedelta(seconds=float(man_row["lights_off_offset_s"]))
    pd.DataFrame({"time": start + pd.to_timedelta(minutes, unit="m"), "activity": act}).to_csv(
        cdir / f"{sid}.csv", index=False
    )

    yasa_path = None
    if with_yasa:
        from yasa import SleepStaging
        raw_y = mne.io.read_raw_edf(str(psg_path), preload=True, verbose=False)
        raw_y.crop(tmin=tmin, tmax=min(tmax, raw_y.times[-1]), include_tmax=False)
        raw_y.pick([EEG_CH, EOG_CH, EMG_CH])
        sl = SleepStaging(raw_y, eeg_name=EEG_CH, eog_name=EOG_CH, emg_name=EMG_CH)
        hyp = sl.predict().hypno.astype(str).to_numpy()[:n_epochs]
        pred = np.full(n_epochs, UNS, dtype=np.uint8)
        for i, s in enumerate(STAGES5):
            pred[hyp == s] = i
        (out_dir / "yasa_pred").mkdir(parents=True, exist_ok=True)
        np.save(out_dir / "yasa_pred" / f"{sid}.npy", pred)
        yasa_path = str(out_dir / "yasa_pred" / f"{sid}.npy")

    available_feats = [f for f in FEATURE_NAMES
                       if not (f.startswith("emg_") and f in HIGH_RATE_EMG and not has_highrate_emg)
                       and not (f.startswith("resp_") and not has_resp)
                       and not (f.startswith("temp_") and not has_temp)
                       and not (f.startswith("eog_") and not mask_eog25)]
    nan_feat_epochs = int(df[available_feats].isna().any(axis=1).sum())
    qc = {
        "session": sid,
        "subset": str(man_row["subset"]),
        "subject": int(man_row["subject"]),
        "subject_key": f"{man_row['subset']}:{int(man_row['subject'])}",
        "night": int(man_row["night"]),
        "window_hours": float(man_row["window_hours"]),
        "n_epochs": n_epochs,
        "n_scored": int(np.sum(stages != UNS)),
        "n_uns": int(np.sum(stages == UNS)),
        "fs_emg": native.get(EMG_CH, np.nan),
        "fs_eog": native.get(EOG_CH, np.nan),
        "fs_resp": native.get(RESP_CH, np.nan),
        "has_highrate_emg": bool(has_highrate_emg),
        "has_resp": bool(has_resp),
        "has_temp": bool(has_temp),
        "emg_flat": bool(float(np.nanstd(feats.get("emg_std", np.array([1.0])))) == 0.0),
        "n_epochs_any_nan_feature": nan_feat_epochs,
        "yasa_pred": yasa_path or "",
        "extract_sec": round(time.time() - t_start, 1),
    }
    (out_dir / "qc").mkdir(parents=True, exist_ok=True)
    qc_path.write_text(json.dumps(qc))
    (out_dir / "norm").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(norm_rows).to_csv(out_dir / "norm" / f"{sid}.csv", index=False)
    return qc, norm_rows


def _worker(args: tuple) -> dict:
    psg, man_row, out_dir, with_yasa, overwrite, clean_root = args
    sid = _sid(psg)
    try:
        qc, norm = extract_one(psg, man_row, out_dir, with_yasa, overwrite, clean_root)
        return {"qc": qc, "norm": norm, "session": sid}
    except Exception as e:  # noqa: BLE001
        return {"session": sid, "error": f"{type(e).__name__}: {e}"}


def write_splits(manifest: pd.DataFrame, out_dir: Path, folds: int) -> None:
    from sklearn.model_selection import GroupKFold

    m = manifest.sort_values("session").reset_index(drop=True)
    n_groups = int(m["subject_key"].nunique())
    if n_groups < 2:
        print("  [splits] fewer than 2 subjects; splits.csv not written", file=sys.stderr)
        return
    if folds > n_groups:
        print(f"  [splits] {n_groups} subjects < {folds} requested folds; using {n_groups}")
        folds = n_groups
    gkf = GroupKFold(n_splits=folds)
    fold = np.full(len(m), -1)
    for k, (_, test_idx) in enumerate(gkf.split(m, groups=m["subject_key"])):
        fold[test_idx] = k
    out = m[["session", "subject_key", "subset", "night"]].copy()
    out["fold"] = fold
    out.to_csv(out_dir / "splits.csv", index=False)


def write_feature_dictionary(out_dir: Path) -> None:
    pd.DataFrame(FEATURES, columns=["feature", "family", "description"]).to_csv(
        out_dir / "feature_dictionary.csv", index=False
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Wearable-style surrogate extraction from Sleep-EDF")
    ap.add_argument("--subset", choices=["cassette", "telemetry", "both"], default="cassette")
    ap.add_argument("--limit", type=int, default=0, help="number of sessions (0 = all)")
    ap.add_argument("--jobs", type=int, default=1, help="parallel sessions")
    ap.add_argument("--folds", type=int, default=5, help="subject-wise GroupKFold splits")
    ap.add_argument("--edf-root", type=Path, default=DEFAULT_EDF_ROOT, help="raw Sleep-EDF dataset root")
    ap.add_argument("--clean-root", type=Path, default=DEFAULT_CLEAN_ROOT, help="lights-off windows")
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--with-yasa", action="store_true", help="also save YASA EEG baseline predictions")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args(argv)

    if not args.edf_root.is_dir():
        print(f"Dataset not found: {args.edf_root}", file=sys.stderr)
        return 1
    try:
        clean = load_clean_manifest(args.clean_root)
    except FileNotFoundError:
        print(f"Clean labels not found in {args.clean_root}. Run prepare_windows.py first.",
              file=sys.stderr)
        return 1

    pairs = pair_sessions(args.edf_root, args.subset)
    if args.limit and args.limit > 0:
        pairs = pairs[: args.limit]
    if not pairs:
        print("No PSG/hypnogram pairs found.", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    work = []
    for psg, _ in pairs:
        sid = _sid(psg)
        if sid not in clean:
            print(f"  [skip] {sid}: not in trim manifest", file=sys.stderr)
            continue
        work.append((psg, clean[sid].to_dict(), args.out_dir,
                     args.with_yasa, args.overwrite, args.clean_root))

    print(f"Sessions: {len(work)} ({args.subset})  jobs={args.jobs}  out={args.out_dir}")
    qc_rows, errors = [], []
    if args.jobs > 1:
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            futs = [ex.submit(_worker, w) for w in work]
            for i, fut in enumerate(as_completed(futs), 1):
                r = fut.result()
                if "error" in r:
                    errors.append(r)
                    print(f"  [fail] {r['session']}: {r['error']}", file=sys.stderr)
                else:
                    qc_rows.append(r["qc"])
                    print(f"  [{i}/{len(work)}] {r['session']} ok ({r['qc']['extract_sec']}s)", flush=True)
    else:
        for i, w in enumerate(work, 1):
            r = _worker(w)
            if "error" in r:
                errors.append(r)
                print(f"  [fail] {r['session']}: {r['error']}", file=sys.stderr)
            else:
                qc_rows.append(r["qc"])
                print(f"  [{i}/{len(work)}] {r['session']} ok ({r['qc']['extract_sec']}s)", flush=True)

    qc = pd.DataFrame(qc_rows)
    if qc.empty:
        print("No sessions processed.", file=sys.stderr)
        return 1
    qc.to_csv(args.out_dir / "qc.csv", index=False)

    manifest = qc[[
        "session", "subject_key", "subset", "subject", "night", "window_hours", "n_epochs",
        "n_scored", "n_uns", "fs_emg", "fs_eog", "fs_resp", "has_highrate_emg", "has_resp",
        "has_temp",
    ]].copy()
    manifest.to_csv(args.out_dir / "manifest.csv", index=False)

    norm_files = sorted((args.out_dir / "norm").glob("*.csv"))
    if norm_files:
        pd.concat([pd.read_csv(f) for f in norm_files], ignore_index=True).to_csv(
            args.out_dir / "norm_stats.csv", index=False
        )

    write_feature_dictionary(args.out_dir)
    if len(manifest) >= 2:
        write_splits(manifest, args.out_dir, args.folds)

    print(f"\nProcessed {len(qc)} sessions ({len(errors)} failed)")
    print(f"features={args.out_dir / 'features'}  windows={args.out_dir / 'windows'}  "
          f"counts={args.out_dir / 'counts'}")
    print(f"manifest -> {args.out_dir / 'manifest.csv'}  splits -> {args.out_dir / 'splits.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
