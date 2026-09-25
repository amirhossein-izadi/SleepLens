"""Assemble all night-level feature groups into one payload."""

from __future__ import annotations

from typing import Any

import numpy as np

from apps.analysis.pipeline.constants import CANONICAL_FS, EPOCH_SECONDS
from apps.analysis.pipeline.preprocess import resample_poly
from apps.analysis.pipeline.sdi.adapter import SdiResult

from .eeg import extract_eeg_features
from .hypnogram import extract_hypnogram_features
from .microstructure import extract_microstructure_features
from .physiology import extract_arousal_features, extract_emg_features
from .resp import APNEA_KEYS, extract_respiration_features
from .sleep_depth import extract_sleep_depth_features


def _not_assessable(key: str, reason: str) -> dict[str, str]:
    return {"key": key, "reason": reason}


def _window_slice(
    signal: np.ndarray, sample_rate: float, offset_epochs: int, n_epochs: int
) -> np.ndarray:
    """Seconds-aligned slice of a channel for the analysis window."""
    start = int(offset_epochs * EPOCH_SECONDS * sample_rate)
    stop = int((offset_epochs + n_epochs) * EPOCH_SECONDS * sample_rate)
    return signal[start:stop]


def extract_night_features(
    recording: Any,
    stages: np.ndarray,
    sdi: SdiResult,
    epoch_offset: int = 0,
    window: tuple[int, int] | None = None,
    sdi_values: np.ndarray | None = None,
    rem_values: np.ndarray | None = None,
) -> tuple[dict, list[dict[str, str]], dict]:
    """Return (values, not_assessable, signal_quality) for one night window."""
    channels = recording.channels
    n_epochs = len(stages)
    values: dict = {}
    not_assessable: list[dict[str, str]] = []

    # 1. Hypnogram-derived (continuity, fragmentation, architecture)
    values.update(extract_hypnogram_features(stages))

    # 2. Sleep-depth model features (prefixed sdi_; served as the SQI group)
    if sdi_values is not None:
        values.update(extract_sleep_depth_features(sdi_values, stages, rem_values))

    # 2. Frontal EEG at 100 Hz
    eeg_label = channels["eeg_fpz"]
    eeg = _window_slice(
        recording.signals[eeg_label], recording.sample_rates[eeg_label], epoch_offset, n_epochs
    )
    if abs(recording.sample_rates[eeg_label] - CANONICAL_FS) > 1e-6:
        eeg = resample_poly(eeg, int(round(recording.sample_rates[eeg_label])), CANONICAL_FS)
    eeg_uv = eeg  # EDF stores microvolts for EEG

    values.update(extract_eeg_features(eeg_uv, stages))
    values.update(extract_microstructure_features(eeg_uv, stages))

    # 3. EMG-derived
    emg_signal = None
    emg_rate = 0.0
    if "emg" in channels:
        emg_label = channels["emg"]
        emg_rate = recording.sample_rates[emg_label]
        emg_signal = _window_slice(
            recording.signals[emg_label], emg_rate, epoch_offset, n_epochs
        )
        values.update(extract_emg_features(emg_signal, emg_rate, stages))

    # 4. Arousal proxy (EMG surge gate only when a usable EMG exists)
    values.update(
        extract_arousal_features(
            eeg_uv,
            stages,
            emg=emg_signal if (emg_signal is not None and emg_rate > 0) else None,
            emg_rate=emg_rate,
        )
    )
    if emg_signal is None:
        not_assessable.append(
            _not_assessable("arousal_rem_emg_gate", "No EMG channel; REM arousal gate skipped.")
        )

    # 5. Respiration
    resp_signal = None
    resp_rate = 0.0
    if "resp" in channels:
        resp_label = channels["resp"]
        resp_rate = recording.sample_rates[resp_label]
        resp_signal = _window_slice(
            recording.signals[resp_label], resp_rate, epoch_offset, n_epochs
        )
    respiration = extract_respiration_features(resp_signal, resp_rate, stages)
    if respiration.assessable:
        values.update(respiration.values)
    else:
        for key in APNEA_KEYS:
            not_assessable.append(_not_assessable(key, respiration.reason or "Not assessable."))

    # 6. Movement annotations are not part of an uploaded EDF recording.
    not_assessable.append(
        _not_assessable(
            "move_annot_frac",
            "Movement/artefact annotations are not present in the uploaded EDF.",
        )
    )

    signal_quality = {
        "channels": channels,
        "sample_rates": {label: recording.sample_rates[label] for label in channels.values()},
        "substitutions": {
            "sdi_ecg_zero_filled": sdi.ecg_zero_filled,
            "sdi_emg_upsampled_from_1hz": sdi.emg_upsampled_from_1hz,
        },
        "analysis_window": {
            "start_epoch": int(window[0]) if window else 0,
            "end_epoch": int(window[1]) if window else n_epochs,
            "start_sec": int(window[0]) * EPOCH_SECONDS if window else 0,
            "end_sec": int(window[1]) * EPOCH_SECONDS if window else n_epochs * EPOCH_SECONDS,
            "n_epochs": int(n_epochs),
        },
        "n_epochs_total": int(len(sdi.sdi)),
        "sleep_epochs": int(np.isin(stages, [1, 2, 3, 4]).sum()),
    }
    return values, not_assessable, signal_quality
