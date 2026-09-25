"""Raw-signal access for the frontend: channel list, previews, downloads.

The product previews the *actual uploaded recording*: a decimated whole-night
stream for the overview chart and a per-epoch snippet for zoomed inspection.
Decimation returns min/max envelopes so spikes stay visible at any zoom.
"""

from __future__ import annotations

from math import ceil
from pathlib import Path
from typing import Any

import numpy as np
from pyedflib import EdfReader
from rest_framework.exceptions import NotFound, ValidationError

MAX_CHANNELS = 8
MAX_PREVIEW_POINTS = 4000
MAX_DURATION_SEC = 3600.0
EPOCH_SECONDS = 30.0


def recording_path(study: Any) -> Path:
    """Absolute path of the study's recording (upload or in-place ingest)."""
    if study.source_path:
        path = Path(study.source_path)
    else:
        path = Path(study.file.path)
    if not path.is_file():
        raise NotFound("Recording file is not available.")
    return path


def list_channels(study: Any) -> list[dict[str, Any]]:
    """Available EDF channels with sample rates and sample counts."""
    with EdfReader(str(recording_path(study))) as reader:
        counts = reader.getNSamples()
        return [
            {
                "label": reader.getLabel(index),
                "sample_rate": float(reader.getSampleFrequency(index)),
                "n_samples": int(counts[index]),
            }
            for index in range(reader.signals_in_file)
        ]


def _open(study: Any) -> tuple[EdfReader, list[str], list[float], float]:
    reader = EdfReader(str(recording_path(study)))
    labels = [reader.getLabel(index) for index in range(reader.signals_in_file)]
    rates = [float(reader.getSampleFrequency(index)) for index in range(reader.signals_in_file)]
    duration = float(reader.getFileDuration())
    return reader, labels, rates, duration


def _select_indices(labels: list[str], requested: list[str] | None) -> list[int]:
    if not requested:
        return list(range(min(len(labels), MAX_CHANNELS)))
    indices: list[int] = []
    for name in requested:
        needle = name.strip().lower()
        if not needle:
            continue
        exact = [i for i, label in enumerate(labels) if label.lower() == needle]
        fuzzy = [i for i, label in enumerate(labels) if needle in label.lower()]
        matches = exact or fuzzy
        if not matches:
            raise ValidationError({"channels": f"Channel not found in the recording: {name}"})
        index = matches[0]
        if index not in indices:
            indices.append(index)
    if not indices:
        raise ValidationError({"channels": "No usable channels requested."})
    if len(indices) > MAX_CHANNELS:
        raise ValidationError({"channels": f"At most {MAX_CHANNELS} channels per request."})
    return indices


def _decimate_minmax(t: np.ndarray, values: np.ndarray, max_points: int) -> dict[str, list[float]]:
    """Min/max envelope decimation (keeps spikes) or raw points when short."""
    n = len(values)
    if n <= max_points:
        return {"t": np.round(t, 3).tolist(), "v": np.round(values, 3).tolist()}
    bucket = int(ceil(n / max_points))
    padded = np.pad(values, (0, bucket * ceil(n / bucket) - n), mode="edge")
    reshaped = padded.reshape(-1, bucket)
    mins = reshaped.min(axis=1)
    maxs = reshaped.max(axis=1)
    centers = t[::bucket][: len(mins)]
    return {
        "t": np.round(centers, 3).tolist(),
        "min": np.round(mins, 3).tolist(),
        "max": np.round(maxs, 3).tolist(),
    }


def preview(
    study: Any,
    *,
    channels: list[str] | None = None,
    start_sec: float = 0.0,
    duration_sec: float | None = None,
    max_points: int = 1200,
) -> dict[str, Any]:
    """Decimated multichannel preview for the overview chart."""
    if start_sec < 0:
        raise ValidationError({"start_sec": "Must be >= 0."})
    max_points = max(50, min(int(max_points), MAX_PREVIEW_POINTS))

    reader, labels, rates, file_duration = _open(study)
    try:
        duration = file_duration - start_sec if duration_sec is None else float(duration_sec)
        if duration <= 0 or start_sec >= file_duration:
            raise ValidationError({"duration_sec": "Requested window is outside the recording."})
        duration = min(duration, MAX_DURATION_SEC, file_duration - start_sec)

        series: dict[str, dict[str, list[float]]] = {}
        selected: list[dict[str, Any]] = []
        for index in _select_indices(labels, channels):
            start_sample = int(start_sec * rates[index])
            n_samples = int(duration * rates[index])
            values = np.asarray(reader.readSignal(index, start_sample, n_samples), dtype=float)
            t = start_sec + np.arange(len(values)) / rates[index]
            series[labels[index]] = _decimate_minmax(t, values, max_points)
            selected.append({"label": labels[index], "sample_rate": rates[index]})
    finally:
        reader.close()

    return {
        "study_id": str(study.id),
        "start_sec": round(start_sec, 3),
        "duration_sec": round(duration, 3),
        "file_duration_sec": round(file_duration, 3),
        "max_points": max_points,
        "channels": selected,
        "available_channels": list_channels(study),
        "series": series,
    }


def epoch_snippet(
    study: Any,
    *,
    epoch_index: int,
    channels: list[str] | None = None,
    points: int = 750,
) -> dict[str, Any]:
    """One 30-second epoch at up to ``points`` samples per channel."""
    if epoch_index < 0:
        raise ValidationError({"epoch_index": "Must be >= 0."})
    points = max(50, min(int(points), 3000))

    reader, labels, rates, file_duration = _open(study)
    try:
        start_sec = epoch_index * EPOCH_SECONDS
        if start_sec >= file_duration:
            raise ValidationError({"epoch_index": "Beyond the recording."})
        series: dict[str, dict[str, list[float]]] = {}
        selected: list[dict[str, Any]] = []
        for index in _select_indices(labels, channels):
            start_sample = int(start_sec * rates[index])
            n_samples = int(EPOCH_SECONDS * rates[index])
            values = np.asarray(reader.readSignal(index, start_sample, n_samples), dtype=float)
            if len(values) > points:  # stride-average for a smooth trace
                factor = int(ceil(len(values) / points))
                usable = (len(values) // factor) * factor
                values = values[:usable].reshape(-1, factor).mean(axis=1)
                rate_effective = rates[index] / factor
            else:
                rate_effective = rates[index]
            t = start_sec + np.arange(len(values)) / rate_effective
            series[labels[index]] = {"t": np.round(t, 3).tolist(), "v": np.round(values, 3).tolist()}
            selected.append({"label": labels[index], "sample_rate": round(rate_effective, 3)})
    finally:
        reader.close()

    return {
        "study_id": str(study.id),
        "epoch_index": epoch_index,
        "start_sec": round(start_sec, 3),
        "duration_sec": EPOCH_SECONDS,
        "channels": selected,
        "series": series,
    }
