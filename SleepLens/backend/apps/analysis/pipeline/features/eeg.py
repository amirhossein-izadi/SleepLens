"""EEG spectral and entropy features (Fpz derivation, Welch per 30-s epoch)."""

from __future__ import annotations

import numpy as np
from scipy.signal import welch

from apps.analysis.pipeline.constants import EEG_BANDS, TOTAL_BAND, SDI_FS

BANDS = EEG_BANDS
TOP = TOTAL_BAND


def _epoch_matrix(signal_uv: np.ndarray) -> np.ndarray:
    samples = int(30 * SDI_FS)
    n_epochs = len(signal_uv) // samples
    return signal_uv[: n_epochs * samples].reshape(n_epochs, samples)


def _permutation_entropy(x: np.ndarray, order: int = 3) -> float:
    n = len(x) - order + 1
    if n <= 0:
        return float("nan")
    windows = np.lib.stride_tricks.sliding_window_view(x, order)
    ranks = np.argsort(windows, axis=1)
    code = np.zeros(n, dtype=np.int64)
    multiplier = 1
    for k in range(order):
        code += ranks[:, k] * multiplier
        multiplier *= order
    _, counts = np.unique(code, return_counts=True)
    probabilities = counts / counts.sum()
    return float(-(probabilities * np.log(probabilities)).sum() / np.log(6.0))


def extract_eeg_features(signal_uv: np.ndarray, stages: np.ndarray) -> dict:
    """Band powers, slow-wave activity, spectral + permutation entropy."""
    epochs = _epoch_matrix(signal_uv)
    features: dict = {"eeg_epochs_analyzed": int(len(epochs))}
    if len(epochs) == 0:
        return features

    freqs, _ = welch(epochs[0], fs=SDI_FS, nperseg=512)
    total_mask = (freqs >= TOP[0]) & (freqs <= TOP[1])
    band_masks = {name: (freqs >= lo) & (freqs <= hi) for name, (lo, hi) in BANDS.items()}

    absolute: dict[str, list[float]] = {name: [] for name in BANDS}
    relative: dict[str, list[float]] = {name: [] for name in BANDS}
    spectral_entropy: list[float] = []
    for epoch in epochs:
        _, psd = welch(epoch, fs=SDI_FS, nperseg=512)
        total = float(psd[total_mask].sum()) + 1e-12
        normalized = psd[total_mask] / total
        spectral_entropy.append(float(-(normalized * np.log2(normalized + 1e-12)).sum()))
        for name, mask in band_masks.items():
            value = float(psd[mask].sum())
            absolute[name].append(value)
            relative[name].append(value / total)

    for name in BANDS:
        features[f"abs_{name}_mean"] = round(float(np.mean(absolute[name])), 4)
        features[f"rel_{name}_mean"] = round(float(np.mean(relative[name])), 6)

    n = min(len(epochs), len(stages))
    nrem_mask = np.isin(stages[:n], [1, 2, 3])
    if nrem_mask.any() and n:
        delta = np.asarray(absolute["delta"])[:n]
        relative_delta = np.asarray(relative["delta"])[:n]
        features["swa_nrem_mean"] = round(float(delta[nrem_mask].mean()), 4)
        features["swa_sum"] = round(float(delta[nrem_mask].sum()), 2)
        features["rel_delta_nrem"] = round(float(relative_delta[nrem_mask].mean()), 6)

    entropy = np.asarray(spectral_entropy)[:n]
    for group, labels in (("wake", [0]), ("nrem", [1, 2, 3]), ("rem", [4])):
        mask = np.isin(stages[:n], labels) if n else np.zeros(0, dtype=bool)
        features[f"spec_entropy_{group}"] = (
            round(float(entropy[mask].mean()), 4) if mask.any() else None
        )
        values = [
            _permutation_entropy(epochs[i]) for i in range(n) if stages[i] in labels
        ]
        features[f"perm_entropy_{group}"] = (
            round(float(np.nanmean(values)), 4) if values else None
        )
    return features
