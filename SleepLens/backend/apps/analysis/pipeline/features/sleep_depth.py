"""Sleep-depth (SDI model) night features.

Implements the biomarker set from the SDI paper on the whole-night depth
series: RB / AP / CV / SK / MDR / PR plus distribution and complexity
measures (approximate entropy, detrended fluctuation analysis).
"""

from __future__ import annotations

import numpy as np
from scipy.stats import skew as scipy_skew

from apps.analysis.pipeline.constants import SDI_SHALLOW_THRESHOLD

DEEP_THRESHOLD = 0.8


def _approximate_entropy(x: np.ndarray, m: int = 2, r_fraction: float = 0.2) -> float:
    """Standard approximate entropy (Pincus) on a normalized series."""
    if len(x) < m + 2:
        return float("nan")
    r = r_fraction * float(np.std(x)) or 1e-9

    def phi(order: int) -> float:
        windows = np.lib.stride_tricks.sliding_window_view(x, order)
        counts = np.array(
            [np.sum(np.max(np.abs(windows - w), axis=1) <= r) for w in windows], dtype=float
        )
        return float(np.mean(np.log(counts / len(windows))))

    return float(phi(m) - phi(m + 1))


def _detrended_fluctuation(x: np.ndarray) -> float:
    """DFA scaling exponent (alpha1-like) over geometric window sizes."""
    if len(x) < 16:
        return float("nan")
    centered = x - float(np.mean(x))
    walk = np.cumsum(centered)
    sizes = np.unique(np.floor(np.geomspace(4, max(5, len(walk) // 4), 8)).astype(int))
    fluct = []
    used = []
    for size in sizes:
        segments = len(walk) // size
        if segments < 2:
            continue
        rms = []
        for index in range(segments):
            segment = walk[index * size : (index + 1) * size]
            t = np.arange(size)
            fit = np.polyfit(t, segment, 1)
            rms.append(np.sqrt(np.mean((segment - np.polyval(fit, t)) ** 2)))
        if rms and np.mean(rms) > 0:
            used.append(size)
            fluct.append(np.mean(rms))
    if len(used) < 3:
        return float("nan")
    slope = np.polyfit(np.log(used), np.log(fluct), 1)[0]
    return float(slope)


def extract_sleep_depth_features(
    sdi_values: np.ndarray,
    labels: np.ndarray,
    rem_values: np.ndarray | None = None,
) -> dict:
    """Night-level SDI features over the analysis window (keys prefixed sdi_).

    REM-based features (MDR, PR) use the SDI model's own REM head — the paper's
    definition — falling back to staging REM when the head is unavailable.
    """
    features: dict = {}
    if len(sdi_values) == 0:
        return features

    sleep_mask = np.isin(labels, [1, 2, 3, 4])
    sleep_sdi = sdi_values[sleep_mask]
    if sleep_sdi.size == 0:
        return features

    mean = float(sleep_sdi.mean())
    std = float(sleep_sdi.std())
    if rem_values is not None and len(rem_values) == len(labels):
        rem_mask = rem_values.astype(bool)
    else:
        rem_mask = labels == 4
    shallow_minutes = float((sleep_sdi < SDI_SHALLOW_THRESHOLD).sum()) * 0.5
    deep_minutes = float((sleep_sdi > DEEP_THRESHOLD).sum()) * 0.5

    features.update(
        {
            "sdi_rb": round(float((sleep_sdi < SDI_SHALLOW_THRESHOLD).mean()), 4),
            "sdi_ap": round(mean, 4),
            "sdi_cv": round(std / mean, 4) if mean else None,
            "sdi_skew": round(float(scipy_skew(sleep_sdi)), 4) if sleep_sdi.size > 2 else None,
            "sdi_mdr": round(float(sdi_values[rem_mask].mean()), 4) if rem_mask.any() else None,
            "sdi_pr": round(float(rem_mask.sum()) / float(sleep_mask.sum()), 4),
            "sdi_mean_sleep": round(mean, 4),
            "sdi_std_sleep": round(std, 4),
            "sdi_p05": round(float(np.percentile(sleep_sdi, 5)), 4),
            "sdi_p95": round(float(np.percentile(sleep_sdi, 95)), 4),
            "sdi_shallow_minutes": round(shallow_minutes, 1),
            "sdi_deep_minutes": round(deep_minutes, 1),
            "sdi_auc": round(float(sleep_sdi.sum()) * 0.5, 1),
            "sdi_apen": round(_approximate_entropy(sleep_sdi), 4),
            "sdi_dfa": round(_detrended_fluctuation(sleep_sdi), 4),
        }
    )
    return features
