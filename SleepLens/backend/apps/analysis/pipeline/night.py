"""Night pipeline orchestrator: one recording in, one NightResult out."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from django.conf import settings

from apps.analysis.pipeline.constants import (
    DEFAULT_CONFIDENCE_HIGH,
    DEFAULT_CONFIDENCE_MEDIUM,
    SDI_SHALLOW_THRESHOLD,
    STAGES,
)
from apps.analysis.pipeline.features import extract_night_features
from apps.analysis.pipeline.sdi import predict_sdi
from apps.analysis.pipeline.staging import predict_ensemble, predict_stages


def _run_staging(recording: Any) -> tuple[Any, str]:
    """Run the configured staging system, falling back to single AnySleep.

    ``STAGING_SYSTEM=ensemble`` (default) uses the cohort-routed four-member
    ensemble; ``anysleep`` forces the single network.
    """
    import structlog

    logger = structlog.get_logger(__name__)
    system = str(getattr(settings, "STAGING_SYSTEM", "ensemble")).lower()
    if system == "ensemble":
        try:
            return predict_ensemble(recording), "ensemble"
        except Exception as exc:  # noqa: BLE001 - never fail an upload over ensemble extras
            logger.warning("staging_ensemble_failed", error=str(exc)[:300])
    return predict_stages(recording), "anysleep_single"


@dataclass(frozen=True)
class EpochRecord:
    """One 30-s epoch result."""

    epoch_index: int
    start_sec: int
    stage: str
    probabilities: dict[str, float]
    confidence: float
    confidence_band: str
    needs_review: bool
    sdi: float | None
    rem_pred: bool | None


@dataclass(frozen=True)
class NightResult:
    """Everything the backend stores for one analyzed study."""

    epochs: list[EpochRecord]
    features: dict
    not_assessable: list[dict[str, str]]
    signal_quality: dict
    summary: dict
    duration_minutes: float
    channel_set: tuple[str, ...]
    channel_labels: tuple[str, ...]
    warnings: list[str] = field(default_factory=list)


def _confidence_band(value: float) -> str:
    high = getattr(settings, "CONFIDENCE_HIGH", DEFAULT_CONFIDENCE_HIGH)
    medium = getattr(settings, "CONFIDENCE_MEDIUM", DEFAULT_CONFIDENCE_MEDIUM)
    if value >= high:
        return "high"
    if value >= medium:
        return "medium"
    return "low"


def _analysis_window(labels: np.ndarray, pad_epochs: int = 60) -> tuple[int, int]:
    """Sleep window used for night features: first to last predicted sleep +/- 30 min.

    Scoring a full 22-hour cassette recording would report sleep efficiency over
    the whole day, which is clinically meaningless. The window mirrors the
    benchmark definition used during model development.
    """
    sleep_indices = np.flatnonzero(np.isin(labels, [1, 2, 3, 4]))
    if sleep_indices.size == 0:
        return 0, len(labels)
    start = max(0, int(sleep_indices[0]) - pad_epochs)
    end = min(len(labels), int(sleep_indices[-1]) + 1 + pad_epochs)
    return start, end


def run_night_pipeline(path: str | Path) -> NightResult:
    """Run staging + SDI + night features for one EDF recording."""
    from apps.analysis.pipeline.canonical import read_recording

    recording = read_recording(path)

    staging, staging_system = _run_staging(recording)
    sdi_result = predict_sdi(recording)

    n_epochs = min(staging.probabilities.shape[0], len(sdi_result.sdi))
    if n_epochs == 0:
        raise ValueError("No whole 30-second epochs could be analyzed.")
    probabilities = staging.probabilities[:n_epochs]
    labels = probabilities.argmax(axis=1)
    sdi_values = sdi_result.sdi[:n_epochs]
    rem_values = sdi_result.rem[:n_epochs]

    window_start, window_end = _analysis_window(labels)
    features, not_assessable, signal_quality = extract_night_features(
        recording,
        stages=labels[window_start:window_end],
        sdi=sdi_result,
        epoch_offset=window_start,
        window=(window_start, window_end),
        sdi_values=sdi_values[window_start:window_end],
        rem_values=rem_values[window_start:window_end],
    )

    epochs: list[EpochRecord] = []
    for index in range(n_epochs):
        confidence = float(probabilities[index].max())
        band = _confidence_band(confidence)
        epochs.append(
            EpochRecord(
                epoch_index=index,
                start_sec=index * 30,
                stage=STAGES[int(labels[index])],
                probabilities={
                    STAGES[class_index]: float(probabilities[index, class_index])
                    for class_index in range(5)
                },
                confidence=confidence,
                confidence_band=band,
                needs_review=band != "high",
                sdi=float(sdi_values[index]),
                rem_pred=bool(rem_values[index]),
            )
        )

    summary = _build_summary(epochs, labels, sdi_values, rem_values)
    # SDI metrics must match the windowed SQI features exactly (one source of truth).
    summary["sdi_metrics"] = _sdi_metrics(
        sdi_values[window_start:window_end],
        labels[window_start:window_end],
        rem_values[window_start:window_end],
    )
    summary["staging_system"] = staging_system
    summary["staging_members"] = list(staging.channel_set)
    summary["analysis_window"] = {
        "start_epoch": window_start,
        "end_epoch": window_end,
        "start_sec": window_start * 30,
        "end_sec": window_end * 30,
    }
    return NightResult(
        epochs=epochs,
        features=features,
        not_assessable=not_assessable,
        signal_quality=signal_quality,
        summary=summary,
        duration_minutes=round(recording.duration_sec / 60.0, 2),
        channel_set=staging.channel_set,
        channel_labels=staging.channel_labels,
        warnings=["sdi_ecg_zero_filled"] if sdi_result.ecg_zero_filled else [],
    )


def _sdi_metrics(
    sdi_values: np.ndarray,
    labels: np.ndarray,
    rem_values: np.ndarray,
) -> dict:
    """SDI night metrics over a label window (matches features/sqi exactly)."""
    sleep_mask = np.isin(labels, [1, 2, 3, 4])
    sleep_sdi = sdi_values[sleep_mask]
    if sleep_sdi.size == 0:
        return {}
    mean = float(sleep_sdi.mean())
    std = float(sleep_sdi.std())
    rem_head_mask = rem_values.astype(bool)
    return {
        "rb": round(float((sleep_sdi < SDI_SHALLOW_THRESHOLD).mean()), 4),
        "ap": round(mean, 4),
        "cv": round(std / mean, 4) if mean else None,
        "mdr": round(float(sdi_values[rem_head_mask].mean()), 4)
        if rem_head_mask.any()
        else None,
        "pr": round(float(rem_head_mask.sum()) / float(sleep_mask.sum()), 4),
    }


def _build_summary(
    epochs: list[EpochRecord],
    labels: np.ndarray,
    sdi_values: np.ndarray,
    rem_values: np.ndarray,
) -> dict:
    """Stage distribution and review load (SDI metrics added separately)."""
    total = len(epochs) or 1
    sleep_mask = np.isin(labels, [1, 2, 3, 4])
    stage_counts = {
        stage: int((labels == index).sum()) for index, stage in enumerate(STAGES)
    }
    stage_pct = {stage: round(100.0 * count / total, 2) for stage, count in stage_counts.items()}
    review = [epoch for epoch in epochs if epoch.needs_review]

    return {
        "stage_counts": stage_counts,
        "stage_pct": stage_pct,
        "sleep_pct": round(100.0 * float(sleep_mask.mean()), 2),
        "mean_confidence": round(float(np.mean([e.confidence for e in epochs])), 4),
        "needs_review_count": len(review),
        "needs_review_pct": round(100.0 * len(review) / total, 2),
    }
