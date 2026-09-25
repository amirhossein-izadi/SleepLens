"""Signal preprocessing helpers shared by the pipeline models."""

from __future__ import annotations

import numpy as np
from scipy.signal import resample_poly as scipy_resample_poly


def resample_poly(x: np.ndarray, src: int, dst: int) -> np.ndarray:
    """Polyphase resampling to ``dst`` from ``src`` Hz."""
    if src == dst:
        return np.asarray(x, dtype=np.float64)
    from math import gcd

    factor = gcd(int(src), int(dst))
    return scipy_resample_poly(x, int(dst) // factor, int(src) // factor).astype(np.float64)


def robust_scale(x: np.ndarray) -> np.ndarray:
    """Median/IQR scaling with a +/-20 clip (AnySleep preprocessing)."""
    median = np.median(x)
    iqr = np.percentile(x, 75) - np.percentile(x, 25) + 1e-12
    return np.clip((x - median) / iqr, -20.0, 20.0)


def zscore(x: np.ndarray) -> np.ndarray:
    """Whole-signal z-score with a zero-variance guard."""
    std = float(x.std()) or 1.0
    return (x - float(x.mean())) / std


def truncate_to_epochs(x: np.ndarray, samples_per_epoch: int) -> np.ndarray:
    """Keep only whole epochs."""
    n = (len(x) // samples_per_epoch) * samples_per_epoch
    return x[:n]
