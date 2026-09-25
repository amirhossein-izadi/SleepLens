"""Respiration proxy with explicit not-assessable handling.

A coarse flow-dip detector needs a continuous airflow signal. On Sleep-EDF the
only airflow channel is a ~1 Hz envelope, which cannot resolve respiratory
events; absence of the channel is likewise not assessable. Both cases are
reported with a reason instead of a misleading zero.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from apps.analysis.pipeline.constants import EPOCH_SECONDS

APNEA_KEYS: tuple[str, ...] = ("apnea_count", "apnea_index", "apnea_time_pct")


@dataclass(frozen=True)
class RespirationOutcome:
    """Either computed values, or the reason they cannot be assessed."""

    values: dict
    reason: str | None = None

    @property
    def assessable(self) -> bool:
        return self.reason is None


def extract_respiration_features(
    signal: np.ndarray | None,
    sample_rate: float,
    stages: np.ndarray,
) -> RespirationOutcome:
    """Flow-dip apnea proxy, or a not-assessable reason."""
    if signal is None:
        return RespirationOutcome(
            values={},
            reason="No airflow channel present in the recording (instrumentation absent).",
        )
    if sample_rate <= 1.5:
        return RespirationOutcome(
            values={},
            reason=(
                "Airflow channel is a low-rate envelope (~1 Hz); flow reductions "
                "cannot be resolved, events are not assessable."
            ),
        )

    flow = np.abs(signal)
    window = max(int(5 * sample_rate), 1)
    envelope = pd.Series(flow).rolling(window, min_periods=1, center=True).mean().to_numpy()
    baseline = (
        pd.Series(envelope).rolling(max(int(120 * sample_rate), 10), min_periods=10).median().to_numpy()
    )
    sleep_seconds = np.repeat((stages > 0).astype(bool), int(EPOCH_SECONDS * sample_rate))[: len(envelope)]
    low = (envelope < 0.10 * (baseline + 1e-9)) & sleep_seconds

    min_samples = int(10 * sample_rate)
    diff = np.diff(np.r_[0, low.astype(int), 0])
    starts, ends = np.flatnonzero(diff == 1), np.flatnonzero(diff == -1)
    runs = [(s, e) for s, e in zip(starts, ends) if e - s >= min_samples]
    merged: list[list[int]] = []
    for start, end in runs:
        if merged and start - merged[-1][1] <= int(5 * sample_rate):
            merged[-1][1] = end
        else:
            merged.append([start, end])

    tst_hours = float((stages > 0).sum()) * EPOCH_SECONDS / 3600.0
    total_seconds = len(envelope) / sample_rate if sample_rate else 0.0
    low_seconds = sum(end - start for start, end in merged) / sample_rate if sample_rate else 0.0
    return RespirationOutcome(
        values={
            "apnea_count": len(merged),
            "apnea_index": round(len(merged) / tst_hours, 2) if tst_hours else None,
            "apnea_time_pct": (
                round(100.0 * low_seconds / total_seconds, 3) if total_seconds else None
            ),
        }
    )
