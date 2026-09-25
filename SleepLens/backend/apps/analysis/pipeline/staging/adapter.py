"""AnySleep staging adapter.

Runs the attention U-Sleep checkpoint on a chosen set of channels. The
auto-picked set prefers Fpz + Pz + EOG, falls back to Fpz + EOG and finally
Fpz only (measured ablations: 0.827 / 0.823 / 0.801 macro-F1).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Sequence

import numpy as np
import torch

from apps.analysis.pipeline.constants import (
    CANONICAL_FS,
    STAGING_EPOCH_SAMPLES,
    STAGING_FS,
)
from apps.analysis.pipeline.preprocess import resample_poly, robust_scale
from apps.analysis.pipeline.weights import get_weight_paths

from .anysleep_model import AnySleep


@dataclass(frozen=True)
class StagingResult:
    """Per-epoch stage probabilities for one recording."""

    probabilities: np.ndarray  # (n_epochs, 5) in STAGES order
    channel_set: tuple[str, ...]
    channel_labels: tuple[str, ...]

    def labels(self) -> np.ndarray:
        return self.probabilities.argmax(axis=1)


@lru_cache(maxsize=1)
def _load_model() -> AnySleep:
    path = get_weight_paths().any_sleep
    model = AnySleep(path=str(path), sleep_stage_frequency=1)
    model.eval()
    return model


def auto_channel_roles(recording: Any) -> list[str]:
    """Role names to feed the model when no explicit set is given."""
    channels = recording.channels
    if "eeg_fpz" in channels and "eeg_pz" in channels and "eog" in channels:
        return ["eeg_fpz", "eeg_pz", "eog"]
    if "eeg_fpz" in channels and "eog" in channels:
        return ["eeg_fpz", "eog"]
    return ["eeg_fpz"]


def predict_stages_with(recording: Any, roles: Sequence[str]) -> StagingResult:
    """Run AnySleep on an explicit channel-role set."""
    label_names = [recording.channels[role] for role in roles]

    processed = []
    for label in label_names:
        signal = recording.signals[label]
        signal = resample_poly(signal, CANONICAL_FS, STAGING_FS)
        processed.append(robust_scale(signal))

    n_samples = min(len(channel) for channel in processed)
    n_epochs = n_samples // STAGING_EPOCH_SAMPLES
    if n_epochs == 0:
        raise ValueError("Recording is shorter than one 30-second epoch.")

    stacked = np.stack(
        [channel[: n_epochs * STAGING_EPOCH_SAMPLES] for channel in processed], axis=1
    )
    model = _load_model()
    outputs = []
    with torch.no_grad():
        for start in range(0, n_epochs, 512):
            stop = min(start + 512, n_epochs)
            batch = torch.from_numpy(
                stacked[start * STAGING_EPOCH_SAMPLES : stop * STAGING_EPOCH_SAMPLES]
            ).float().unsqueeze(0)
            logits = model(batch).detach().cpu().numpy()[0]
            outputs.append(logits)
    logits = np.concatenate(outputs, axis=0)
    exp = np.exp(logits - logits.max(axis=1, keepdims=True))
    probabilities = exp / exp.sum(axis=1, keepdims=True)

    return StagingResult(
        probabilities=probabilities,
        channel_set=tuple(roles),
        channel_labels=tuple(label_names),
    )


def predict_stages(recording: Any) -> StagingResult:
    """Run AnySleep with the auto-picked channel set."""
    return predict_stages_with(recording, auto_channel_roles(recording))
