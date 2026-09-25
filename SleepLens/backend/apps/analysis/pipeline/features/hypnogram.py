"""Continuity, fragmentation and architecture features from a stage series."""

from __future__ import annotations

import numpy as np

from apps.analysis.pipeline.constants import EPOCH_SECONDS, STAGES

SLEEP_STAGES: tuple[int, ...] = (1, 2, 3, 4)
WAKE = 0
N1, N2, N3, REM = 1, 2, 3, 4


def _safe_mean(values: list[float]) -> float | None:
    return float(np.mean(values)) if values else None


def extract_hypnogram_features(stages: np.ndarray) -> dict:
    """Continuity / fragmentation / architecture metrics for one night."""
    features: dict = {}
    n = len(stages)
    sleep_mask = np.isin(stages, SLEEP_STAGES)
    sleep_idx = np.flatnonzero(sleep_mask)

    features["n_epochs"] = int(n)
    features["tib_min"] = round(n * EPOCH_SECONDS / 60.0, 2)
    tst_epochs = int(sleep_mask.sum())
    features["tst_min"] = round(tst_epochs * EPOCH_SECONDS / 60.0, 2)
    tst_hours = features["tst_min"] / 60.0 if features["tst_min"] else 0.0
    features["se_pct"] = round(100.0 * tst_epochs / n, 2) if n else None

    if sleep_idx.size == 0:  # no sleep detected at all
        features.update(
            {
                "sol_min": None,
                "waso_min": None,
                "rem_lat_min": None,
                "n_awakenings": 0,
                "awakening_index": None,
                "n_stage_shifts": 0,
                "shift_index": None,
                "sfi": None,
                "n_rem_episodes": 0,
                "mean_rem_bout_min": None,
                "longest_sleep_bout_min": None,
                "mean_sleep_bout_min": None,
                "longest_wake_post_onset_min": None,
                "transitions": {},
            }
        )
        for index, name in enumerate(STAGES[1:], start=1):
            features[f"{name.lower()}_pct_tst"] = None
            features[f"{name.lower()}_pct_first_half"] = None
            features[f"{name.lower()}_pct_second_half"] = None
        features["wake_pct_tib"] = round(100.0 * (stages == WAKE).sum() / n, 2) if n else None
        return features

    onset = int(sleep_idx[0])
    post = stages[onset:]
    features["sol_min"] = round(onset * EPOCH_SECONDS / 60.0, 2)
    features["waso_min"] = round(float((post == WAKE).sum() * EPOCH_SECONDS / 60.0), 2)

    rem_idx = np.flatnonzero(stages == REM)
    rem_after = rem_idx[rem_idx >= onset]
    features["rem_lat_min"] = (
        round(float((rem_after[0] - onset) * EPOCH_SECONDS / 60.0), 2)
        if rem_after.size
        else None
    )

    for index, name in enumerate(STAGES[1:], start=1):
        share = 100.0 * int((stages == index).sum()) / tst_epochs
        features[f"{name.lower()}_pct_tst"] = round(share, 2)
    features["wake_pct_tib"] = round(100.0 * int((stages == WAKE).sum()) / n, 2)

    is_wake = post == WAKE
    n_awakenings = int((np.diff(is_wake.astype(int)) == 1).sum())
    features["n_awakenings"] = n_awakenings
    features["awakening_index"] = round(n_awakenings / tst_hours, 2) if tst_hours else None

    changes = np.diff(stages)
    n_shifts = int((changes != 0).sum())
    features["n_stage_shifts"] = n_shifts
    features["shift_index"] = round(n_shifts / tst_hours, 2) if tst_hours else None
    features["sfi"] = (
        round((n_awakenings + n_shifts) / tst_hours, 2) if tst_hours else None
    )

    transitions = {
        STAGES[i]: {STAGES[j]: int(((stages[:-1] == i) & (stages[1:] == j)).sum()) for j in range(5)}
        for i in range(5)
    }
    features["transitions"] = transitions

    features.update(_rem_bouts(stages))
    features.update(_bouts(stages, sleep_mask, is_wake))
    features.update(_halves(stages, onset, tst_epochs))
    return features


def _rem_bouts(stages: np.ndarray) -> dict:
    """REM runs of >= 3 minutes (candidate NREM-REM cycles)."""
    mask = (stages == REM).astype(int)
    diff = np.diff(np.r_[0, mask, 0])
    starts, ends = np.flatnonzero(diff == 1), np.flatnonzero(diff == -1)
    lengths = [(end - start) for start, end in zip(starts, ends) if end - start >= 6]
    return {
        "n_rem_episodes": len(lengths),
        "mean_rem_bout_min": (
            round(float(np.mean(lengths)) * EPOCH_SECONDS / 60.0, 2) if lengths else None
        ),
    }


def _bouts(stages: np.ndarray, sleep_mask: np.ndarray, is_wake: np.ndarray) -> dict:
    mask = sleep_mask.astype(int)
    diff = np.diff(np.r_[0, mask, 0])
    lengths = (
        (np.flatnonzero(diff == -1) - np.flatnonzero(diff == 1)) * EPOCH_SECONDS / 60.0
    )
    wake_mask = is_wake.astype(int)
    wake_diff = np.diff(np.r_[0, wake_mask, 0])
    wake_lengths = (
        (np.flatnonzero(wake_diff == -1) - np.flatnonzero(wake_diff == 1))
        * EPOCH_SECONDS
        / 60.0
    )
    return {
        "longest_sleep_bout_min": round(float(lengths.max()), 2) if lengths.size else None,
        "mean_sleep_bout_min": round(float(lengths.mean()), 2) if lengths.size else None,
        "longest_wake_post_onset_min": (
            round(float(wake_lengths.max()), 2) if wake_lengths.size else 0.0
        ),
    }


def _halves(stages: np.ndarray, onset: int, tst_epochs: int) -> dict:
    middle = onset + (len(stages) - onset) // 2
    out: dict = {}
    for label, segment in (("first", stages[onset:middle]), ("second", stages[middle:])):
        sleeping = segment[np.isin(segment, SLEEP_STAGES)]
        for index, name in enumerate(STAGES[1:], start=1):
            key = f"{name.lower()}_pct_{label}_half"
            out[key] = (
                round(100.0 * int((sleeping == index).sum()) / len(sleeping), 2)
                if len(sleeping)
                else None
            )
    return out
