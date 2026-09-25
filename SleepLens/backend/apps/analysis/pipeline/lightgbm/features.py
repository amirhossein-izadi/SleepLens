"""Bandpower/amplitude features for the LightGBM member.

Replicates the exact recipe the production booster was trained with
(sleep-eda script 14): Hanning-windowed rFFT relative powers over
delta(0.5-4) / theta(4-8) / alpha(8-13) / sigma(11-16) / beta(13-30),
plus time-domain statistics — all at the same rounding as training.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from apps.analysis.pipeline.constants import CANONICAL_FS, EPOCH_SECONDS
from apps.analysis.pipeline.preprocess import resample_poly

FEATURE_NAMES: tuple[str, ...] = (
    "eeg_std",
    "eeg_ptp",
    "zcr",
    "delta",
    "theta",
    "alpha",
    "sigma",
    "beta",
    "eog_ptp",
    "eog_std",
    "emg_rms",
)

EPOCH_SAMPLES = EPOCH_SECONDS * CANONICAL_FS  # 3000
BANDS: dict[str, tuple[float, float]] = {
    "delta": (0.5, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "sigma": (11.0, 16.0),
    "beta": (13.0, 30.0),
}
FREQS = np.fft.rfftfreq(EPOCH_SAMPLES, 1.0 / CANONICAL_FS)
BAND_MASKS = {name: (FREQS >= low) & (FREQS <= high) for name, (low, high) in BANDS.items()}
TOTAL_MASK = (FREQS >= 0.5) & (FREQS <= 30.0)
WINDOW = np.hanning(EPOCH_SAMPLES)


def extract_baseline_features(recording: Any) -> np.ndarray | None:
    """Return (n_epochs, 11) features, or None when a channel is missing."""
    channels = recording.channels
    if not {"eeg_fpz", "eog", "emg"} <= set(channels):
        return None

    def at_100hz(role: str) -> np.ndarray:
        label = channels[role]
        signal = recording.signals[label]
        rate = recording.sample_rates[label]
        if abs(rate - CANONICAL_FS) > 1e-6:
            signal = resample_poly(signal, int(round(rate)), CANONICAL_FS)
        return signal

    eeg = at_100hz("eeg_fpz")
    eog = at_100hz("eog")

    emg_label = channels["emg"]
    emg_rate = recording.sample_rates[emg_label]
    emg = recording.signals[emg_label]

    n_eeg = len(eeg) // EPOCH_SAMPLES
    n_eog = len(eog) // EPOCH_SAMPLES
    per_epoch_emg = max(int(EPOCH_SECONDS * emg_rate), 1)
    n_emg = len(emg) // per_epoch_emg
    n_epochs = min(n_eeg, n_eog, n_emg)
    if n_epochs == 0:
        return None

    eeg_epochs = eeg[: n_epochs * EPOCH_SAMPLES].reshape(n_epochs, EPOCH_SAMPLES)
    eog_epochs = eog[: n_epochs * EPOCH_SAMPLES].reshape(n_epochs, EPOCH_SAMPLES)
    emg_epochs = emg[: n_epochs * per_epoch_emg].reshape(n_epochs, per_epoch_emg)

    spectrum = np.abs(
        np.fft.rfft((eeg_epochs - eeg_epochs.mean(axis=1, keepdims=True)) * WINDOW, axis=1)
    ) ** 2
    total = spectrum[:, TOTAL_MASK].sum(axis=1) + 1e-12
    relative = {name: spectrum[:, mask].sum(axis=1) / total for name, mask in BAND_MASKS.items()}

    features = np.column_stack(
        [
            np.round(eeg_epochs.std(axis=1), 2),
            np.round(np.ptp(eeg_epochs, axis=1), 1),
            np.round(((eeg_epochs[:, :-1] * eeg_epochs[:, 1:]) < 0).mean(axis=1), 4),
            np.round(relative["delta"], 4),
            np.round(relative["theta"], 4),
            np.round(relative["alpha"], 4),
            np.round(relative["sigma"], 4),
            np.round(relative["beta"], 4),
            np.round(np.ptp(eog_epochs, axis=1), 1),
            np.round(eog_epochs.std(axis=1), 2),
            np.round(np.sqrt((emg_epochs**2).mean(axis=1)), 3),
        ]
    )
    return features
