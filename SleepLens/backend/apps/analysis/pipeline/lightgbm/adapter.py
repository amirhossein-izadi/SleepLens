"""LightGBM inference member (bandpower baseline, 0.667 standalone)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import numpy as np

from apps.analysis.pipeline.constants import STAGES
from apps.analysis.pipeline.lightgbm.features import extract_baseline_features
from apps.analysis.pipeline.weights import get_weight_paths


def lightgbm_available() -> bool:
    """True when the booster file is present on disk."""
    return get_weight_paths().lightgbm.is_file()


@lru_cache(maxsize=1)
def _load_booster() -> Any:
    import lightgbm as lgb

    return lgb.Booster(model_file=str(get_weight_paths().lightgbm))


def predict_lightgbm(recording: Any) -> np.ndarray | None:
    """Return (n_epochs, 5) probabilities in STAGES order, or None."""
    if not lightgbm_available():
        return None
    features = extract_baseline_features(recording)
    if features is None:
        return None
    booster = _load_booster()
    probabilities = np.asarray(booster.predict(features), dtype=np.float64)
    if probabilities.shape[1] != len(STAGES):
        raise ValueError("Unexpected booster output shape for the 5-class task.")
    return probabilities
