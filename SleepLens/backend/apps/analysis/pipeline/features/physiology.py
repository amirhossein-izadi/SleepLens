"""EMG quality features and a cortical-arousal proxy.

The arousal detector is the same ratio-based proxy used during development
(AASM-*like*, not AASM-scored): per-second (alpha+beta)/(delta+theta) on the
frontal EEG, with a sigma-burst gate and an optional REM EMG-surge gate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import stft

from apps.analysis.pipeline.constants import EPOCH_SECONDS, SDI_FS

AROUSAL_INDEX_CAP = 40.0  # winsorize detector over-fire, per development note


def extract_emg_features(emg: np.ndarray, sample_rate: float, stages: np.ndarray) -> dict:
    """Chin EMG metrics; handles both the 1 Hz envelope and 100 Hz signals."""
    per_epoch = max(int(EPOCH_SECONDS * sample_rate), 1)
    n = min(len(emg) // per_epoch, len(stages))
    if n == 0:
        return {}
    epochs = emg[: n * per_epoch].reshape(n, per_epoch) * 1e6
    rms = np.sqrt((epochs**2).mean(axis=1))
    median = float(np.median(rms)) + 1e-9

    rem = rms[stages[:n] == 4]
    nrem = rms[np.isin(stages[:n], [1, 2, 3])]
    return {
        "emg_median_uv": round(median, 4),
        "emg_rem_mean_uv": round(float(rem.mean()), 4) if len(rem) else None,
        "emg_nrem_mean_uv": round(float(nrem.mean()), 4) if len(nrem) else None,
        "rem_atonia_ratio": (
            round(float(nrem.mean() / (rem.mean() + 1e-9)), 4) if len(rem) and len(nrem) else None
        ),
        "movement_index": round(float((rms > 3.0 * median).mean()), 4),
    }


def extract_arousal_features(
    eeg_uv: np.ndarray,
    stages: np.ndarray,
    emg: np.ndarray | None = None,
    emg_rate: float = 0.0,
) -> dict:
    """Ratio-based arousal proxy (returns count and per-hour index)."""
    if len(eeg_uv) == 0 or len(stages) == 0:
        return {}
    x = eeg_uv[: len(eeg_uv) // SDI_FS * SDI_FS]
    n_seconds = len(x) // SDI_FS
    if n_seconds < 60:
        return {}

    freqs, _, spectrum = stft(
        x, fs=SDI_FS, nperseg=2 * SDI_FS, noverlap=SDI_FS, boundary="zeros", padded=True
    )
    power = np.abs(spectrum) ** 2

    def band(low: float, high: float) -> np.ndarray:
        mask = (freqs >= low) & (freqs < high)
        return power[mask].sum(axis=0)[:n_seconds] + 1e-12

    ratio = (band(8.0, 12.0) + band(16.0, 30.0)) / (band(0.5, 4.0) + band(4.0, 8.0))
    sigma = band(11.0, 16.0)
    threshold = 0.4
    stage_seconds = np.repeat(stages.astype(int), int(EPOCH_SECONDS))[:n_seconds]
    sleep_mask = stage_seconds > 0
    hot = (ratio > threshold) & sleep_mask

    sigma_baseline = pd.Series(sigma).rolling(60, min_periods=10).median().to_numpy()
    hot &= ~((sigma > 3.0 * sigma_baseline) & np.isin(stage_seconds, [1, 2, 3]))

    diff = np.diff(np.r_[0, hot.astype(int), 0])
    starts, ends = np.flatnonzero(diff == 1), np.flatnonzero(diff == -1)
    merged: list[list[int]] = []
    for start, end in zip(starts, ends):
        if merged and start - merged[-1][1] <= 2:
            merged[-1][1] = int(end)
        else:
            merged.append([int(start), int(end)])
    events = [(s, e) for s, e in merged if e - s >= 3]
    events = [event for i, event in enumerate(events) if i == 0 or event[0] - events[i - 1][0] >= 10]

    pre_events = [
        event
        for event in events
        if event[0] >= 10
        and bool(sleep_mask[event[0] - 10 : event[0]].all())
        and bool(np.median(ratio[event[0] - 10 : event[0]]) < threshold)
    ]

    kept = pre_events
    if emg is not None and emg_rate > 0:
        emg_seconds = _emg_per_second(emg, emg_rate, n_seconds)
        baseline = pd.Series(emg_seconds).rolling(60, min_periods=10).median().to_numpy()
        surge = emg_seconds[:n_seconds] > 2.0 * baseline[:n_seconds]
        kept = [
            event
            for event in pre_events
            if stage_seconds[event[0]] != 4 or bool(surge[event[0] : event[1]].any())
        ]

    hours = float(sleep_mask.sum()) / 3600.0
    count = len(kept)
    if hours and count / hours > AROUSAL_INDEX_CAP:
        count = int(AROUSAL_INDEX_CAP * hours)
    return {
        "arousal_count": count,
        "arousal_index": round(count / hours, 2) if hours else None,
    }


def _emg_per_second(emg: np.ndarray, sample_rate: float, n_seconds: int) -> np.ndarray:
    if sample_rate >= 50:
        per_second = int(sample_rate)
        n = len(emg) // per_second
        block = (np.abs(emg[: n * per_second]) * 1e6).reshape(n, per_second)
        values = np.sqrt((block**2).mean(axis=1))
    else:  # 1 Hz rectified envelope — nearest sample per second
        idx = np.clip((np.arange(n_seconds) * sample_rate).astype(int), 0, len(emg) - 1)
        values = np.abs(emg[idx]) * 1e6
    return np.asarray(values)
