"""EEG microstructure: spindles (N2) and slow waves (N2/N3) via YASA."""

from __future__ import annotations

import numpy as np

from apps.analysis.pipeline.constants import EPOCH_SECONDS, SDI_FS


def _events_frame(result) -> object | None:
    if result is None:
        return None
    try:
        return result.summary()
    except Exception:  # noqa: BLE001 - yasa >=0.7 result objects vary
        return getattr(result, "_events", None)


def _column(frame, *names: str):
    for name in names:
        if hasattr(frame, "columns") and name in frame.columns:
            return frame[name]
    return None


def extract_microstructure_features(signal_uv: np.ndarray, stages: np.ndarray) -> dict:
    """Spindle and slow-wave metrics, conditioned on detected stages."""
    import yasa

    features: dict = {}
    if len(signal_uv) == 0 or len(stages) == 0:
        return features

    hypno = stages.astype(int)
    try:
        upsampled = yasa.hypno_upsample_to_data(
            hypno,
            sf_hypno=1.0 / EPOCH_SECONDS,
            data=signal_uv,
            sf_data=float(SDI_FS),
        )
    except Exception:  # noqa: BLE001
        return features

    n2_minutes = float((stages == 2).sum()) * EPOCH_SECONDS / 60.0
    try:
        spindles = _events_frame(
            yasa.spindles_detect(signal_uv, sf=SDI_FS, hypno=upsampled, include=(2,))
        )
    except Exception:  # noqa: BLE001
        spindles = None
    if spindles is not None and len(spindles):
        duration = _column(spindles, "Duration")
        frequency = _column(spindles, "Frequency", "Freq", "FreqPeak")
        amplitude = _column(spindles, "Amplitude", "Amp", "RMS")
        features["spindle_count_n2"] = int(len(spindles))
        features["spindle_density_n2"] = (
            round(len(spindles) / n2_minutes, 3) if n2_minutes else None
        )
        features["spindle_dur_mean"] = (
            round(float(duration.mean()), 4) if duration is not None else None
        )
        features["spindle_freq_mean"] = (
            round(float(frequency.mean()), 4) if frequency is not None else None
        )
        features["spindle_amp_mean"] = (
            round(float(amplitude.mean()), 4) if amplitude is not None else None
        )
    else:
        features.update(
            spindle_count_n2=0,
            spindle_density_n2=0.0 if n2_minutes else None,
            spindle_dur_mean=None,
            spindle_freq_mean=None,
            spindle_amp_mean=None,
        )

    nrem_minutes = float(np.isin(stages, [1, 2, 3]).sum()) * EPOCH_SECONDS / 60.0
    try:
        slow_waves = _events_frame(
            yasa.sw_detect(signal_uv, sf=SDI_FS, hypno=upsampled, include=(2, 3))
        )
    except Exception:  # noqa: BLE001
        slow_waves = None
    if slow_waves is not None and len(slow_waves):
        duration = _column(slow_waves, "Duration")
        negative = _column(slow_waves, "ValNegPeak", "NegAmp", "Amplitude")
        features["sw_count_nrem"] = int(len(slow_waves))
        features["sw_density_nrem"] = (
            round(len(slow_waves) / nrem_minutes, 3) if nrem_minutes else None
        )
        features["sw_negamp_mean"] = (
            round(float(negative.mean()), 4) if negative is not None else None
        )
        features["sw_dur_mean"] = (
            round(float(duration.mean()), 4) if duration is not None else None
        )
    else:
        features.update(
            sw_count_nrem=0,
            sw_density_nrem=0.0 if nrem_minutes else None,
            sw_negamp_mean=None,
            sw_dur_mean=None,
        )
    return features
