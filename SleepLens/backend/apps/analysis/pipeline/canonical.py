"""EDF loading and channel discovery for the analysis pipeline.

Reads raw EDF samples with pyedflib (no filtering, no resampling) and maps
sleep-lab channel labels to the roles the models need. The Sleep-EDF Expanded
naming is recognised out of the box; a fuzzy fallback covers common variants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from pyedflib import EdfReader


class ChannelError(ValueError):
    """Raised when the recording cannot supply the channels we need."""


@dataclass(frozen=True)
class Recording:
    """Raw signals plus the role map discovered from the EDF header."""

    signals: dict[str, np.ndarray]
    sample_rates: dict[str, float]
    duration_sec: float
    channels: dict[str, str] = field(default_factory=dict)
    labels: tuple[str, ...] = ()
    start_datetime: str = ""


def _find(labels: list[str], *needles: str) -> str | None:
    """First label containing any needle (case-insensitive)."""
    for label in labels:
        lowered = label.lower()
        if any(needle in lowered for needle in needles):
            return label
    return None


def _find_pz(labels: list[str]) -> str | None:
    """Posterior EEG label ('Pz-Oz'), without matching 'Fpz-Cz'."""
    for label in labels:
        lowered = label.lower()
        if "pz-oz" in lowered or "pz oz" in lowered or "pz o" in lowered:
            return label
    for label in labels:
        lowered = label.lower()
        if "pz" in lowered and "fpz" not in lowered:
            return label
    return None


def discover_channels(labels: list[str]) -> dict[str, str]:
    """Map roles -> EDF label. Missing optional roles are simply absent."""
    roles: dict[str, str] = {}
    eeg_fpz = _find(labels, "fpz", "f pz", "fz-cz")
    eeg_pz = _find_pz(labels)
    # generic EEG fallback when a single derivation is present
    generic_eeg = _find(labels, "eeg")
    if eeg_fpz is None and generic_eeg is not None:
        eeg_fpz = generic_eeg
    if eeg_fpz:
        roles["eeg_fpz"] = eeg_fpz
    if eeg_pz and eeg_pz != eeg_fpz:
        roles["eeg_pz"] = eeg_pz
    eog = _find(labels, "eog")
    emg = _find(labels, "emg")
    resp = _find(labels, "resp", "flow", "airflow", "nasal")
    ecg = _find(labels, "ecg", "ekg")
    if eog:
        roles["eog"] = eog
    if emg:
        roles["emg"] = emg
    if resp:
        roles["resp"] = resp
    if ecg:
        roles["ecg"] = ecg
    return roles


def read_recording(path: str | Path) -> Recording:
    """Read every channel of an EDF file as raw float64 samples."""
    with EdfReader(str(path)) as reader:
        labels = [reader.getLabel(index) for index in range(reader.signals_in_file)]
        signals: dict[str, np.ndarray] = {}
        sample_rates: dict[str, float] = {}
        for index, label in enumerate(labels):
            signals[label] = np.asarray(reader.readSignal(index), dtype=np.float64)
            sample_rates[label] = float(reader.getSampleFrequency(index))
        duration = float(reader.getFileDuration())
        start = reader.getStartdatetime()
    roles = discover_channels(labels)
    if "eeg_fpz" not in roles:
        raise ChannelError(
            "No frontal EEG channel found (looked for Fpz-Cz / Fpz / generic EEG)."
        )
    if not signals:
        raise ChannelError("The EDF file contains no signals.")
    return Recording(
        signals=signals,
        sample_rates=sample_rates,
        duration_sec=duration,
        channels=roles,
        labels=tuple(labels),
        start_datetime=start.isoformat() if start else "",
    )
