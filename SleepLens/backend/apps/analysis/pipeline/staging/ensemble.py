"""Staging ensemble (our best system, E22/E19 design).

Cassette-like recordings run the four-member ensemble
    AnySleep(Fpz+Pz+EOG) + AnySleep(Fpz) + AnySleep(Pz) + LightGBM
with equal weights (0.8458 macro-F1 on Sleep-EDF). Telemetry-like recordings
use AnySleep(Fpz+Pz+EOG) alone, matching the router that won during model
development. Degrades gracefully: missing Pz drops the single-channel members,
a missing EMG/EOG drops the LightGBM member.
"""

from __future__ import annotations

import numpy as np
import structlog

from apps.analysis.pipeline.lightgbm import predict_lightgbm

from .adapter import StagingResult, auto_channel_roles, predict_stages_with

logger = structlog.get_logger(__name__)


def detect_cohort(recording) -> str:
    """Cassette (home) vs telemetry (hospital) from channel evidence."""
    channels = recording.channels
    labels = [label.lower() for label in getattr(recording, "labels", ())]
    emg_rate = recording.sample_rates[channels["emg"]] if "emg" in channels else 0.0

    if "resp" in channels or any("temp" in label for label in labels):
        return "cassette"
    if "emg" in channels and emg_rate >= 50.0:
        return "telemetry"
    if "emg" in channels and emg_rate < 50.0:
        return "cassette"
    return "cassette" if recording.duration_sec > 15 * 3600 else "telemetry"


def predict_ensemble(recording) -> StagingResult:
    """Run the cohort-routed staging ensemble."""
    base = predict_stages_with(recording, auto_channel_roles(recording))
    members: list[tuple[str, np.ndarray]] = [
        ("anysleep_" + "+".join(base.channel_set), base.probabilities)
    ]

    if {"eeg_fpz", "eeg_pz"} <= set(recording.channels):
        for role in ("eeg_fpz", "eeg_pz"):
            single = predict_stages_with(recording, [role])
            members.append((f"anysleep_{role}", single.probabilities))

    cohort = detect_cohort(recording)
    if cohort == "cassette":
        lightgbm = predict_lightgbm(recording)
        if lightgbm is not None:
            members.append(("lightgbm", lightgbm))
        else:
            logger.info("ensemble_lightgbm_skipped", reason="missing channels or booster")
    else:
        logger.info("ensemble_telemetry_single_member", cohort=cohort)

    n_epochs = min(len(probabilities) for _, probabilities in members)
    average = np.mean(
        [probabilities[:n_epochs] for _, probabilities in members], axis=0
    )
    return StagingResult(
        probabilities=average,
        channel_set=tuple(name for name, _ in members),
        channel_labels=base.channel_labels,
    )
