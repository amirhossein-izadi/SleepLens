"""SDI transformer adapter (Zhou et al., npj Digital Medicine 8:203, 2025).

Input contract: 30-s epochs @100 Hz, channel order [EEG, EMG, EOG, ECG] in
uV (mV for ECG). Sleep-EDF has no ECG, so the channel is zero-filled; when
the EMG is a 1 Hz envelope (cassette) it is upsampled. Both substitutions are
reported back so the report can mark the SDI as zero-shot / not validated.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np
import torch

from apps.analysis.pipeline.constants import (
    CANONICAL_FS,
    SDI_BATCH_SIZE,
    SDI_EPOCH_SAMPLES,
    SDI_FS,
)
from apps.analysis.pipeline.preprocess import resample_poly
from apps.analysis.pipeline.weights import get_weight_paths

from .net import Net


@dataclass(frozen=True)
class SdiResult:
    """Per-epoch sleep depth index and REM flag."""

    sdi: np.ndarray  # (n_epochs,) float in [0, 1], higher = deeper
    rem: np.ndarray  # (n_epochs,) uint8 0/1
    ecg_zero_filled: bool
    emg_upsampled_from_1hz: bool
    channel_labels: tuple[str, ...]


@lru_cache(maxsize=1)
def _load_model() -> Net:
    path = get_weight_paths().sdi
    state = torch.load(path, map_location="cpu", weights_only=True)
    model = Net()
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def _to_100hz(signal: np.ndarray, sample_rate: float) -> np.ndarray:
    if abs(sample_rate - SDI_FS) < 1e-6:
        return signal
    if sample_rate < 50.0:  # 1 Hz envelope -> upsample
        return resample_poly(signal, 1, SDI_FS)
    return resample_poly(signal, int(round(sample_rate)), SDI_FS)


def predict_sdi(recording: Any) -> SdiResult:
    """Return per-epoch SDI and REM predictions for a recording."""
    channels = recording.channels
    labels: list[str] = []
    signals: list[np.ndarray] = []
    emg_upsampled = False

    eeg_label = channels["eeg_fpz"]
    signals.append(_to_100hz(recording.signals[eeg_label], recording.sample_rates[eeg_label]))
    labels.append(eeg_label)

    if "emg" in channels:
        emg_label = channels["emg"]
        emg_rate = recording.sample_rates[emg_label]
        emg_upsampled = emg_rate < 50.0
        signals.append(_to_100hz(recording.signals[emg_label], emg_rate))
        labels.append(emg_label)
    else:
        signals.append(np.zeros_like(signals[0]))
        labels.append("EMG(zeros)")

    if "eog" in channels:
        eog_label = channels["eog"]
        signals.append(_to_100hz(recording.signals[eog_label], recording.sample_rates[eog_label]))
        labels.append(eog_label)
    else:
        signals.append(np.zeros_like(signals[0]))
        labels.append("EOG(zeros)")

    ecg_zero_filled = "ecg" not in channels
    if ecg_zero_filled:
        signals.append(np.zeros_like(signals[0]))
        labels.append("ECG(zeros)")
    else:
        ecg_label = channels["ecg"]
        signals.append(_to_100hz(recording.signals[ecg_label], recording.sample_rates[ecg_label]))
        labels.append(ecg_label)

    n_samples = min(len(signal) for signal in signals)
    n_epochs = n_samples // SDI_EPOCH_SAMPLES
    if n_epochs == 0:
        raise ValueError("Recording is shorter than one 30-second epoch.")

    stacked = np.stack([signal[: n_epochs * SDI_EPOCH_SAMPLES] for signal in signals], axis=0)
    tensor = stacked.reshape(4, n_epochs, SDI_EPOCH_SAMPLES).transpose(1, 0, 2).astype(np.float32)

    model = _load_model()
    sdi = np.zeros(n_epochs, dtype=np.float64)
    rem = np.zeros(n_epochs, dtype=np.uint8)
    with torch.no_grad():
        for start in range(0, n_epochs, SDI_BATCH_SIZE):
            batch = torch.from_numpy(tensor[start : start + SDI_BATCH_SIZE])
            depth, rem_logits = model(batch)
            sdi[start : start + SDI_BATCH_SIZE] = (
                torch.sigmoid(depth).squeeze(-1).cpu().numpy()
            )
            rem[start : start + SDI_BATCH_SIZE] = (
                rem_logits.argmax(-1).cpu().numpy().astype(np.uint8)
            )

    return SdiResult(
        sdi=sdi,
        rem=rem,
        ecg_zero_filled=ecg_zero_filled,
        emg_upsampled_from_1hz=emg_upsampled,
        channel_labels=tuple(labels),
    )
