"""SDI-based sleep-quality composite (the project's official definition).

Mirrors ``sleep-quality-index/sdi/estimate_quality.py``: over sleep epochs the
SDI model yields RB/AP/CV/MDR/PR; each is standardized against a reference
population (the 197 Sleep-EDF nights with expert windows), oriented so higher
is better, averaged with equal weights, and converted to an empirical 0-100
percentile within that reference population.

This is a research composite, NOT a clinical scale. The percentile answers
"where does this night sit relative to the reference population" — it is the
SQI model output, not an ad-hoc UI heuristic.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# Orientation: -1 = lower raw value is better.
COMPONENTS: dict[str, int] = {"rb": -1, "ap": 1, "cv": -1, "mdr": 1, "pr": 1}

# .../<workspace>/SleepLens/sleep-quality-index/sdi/reports
_DEFAULT_REFERENCE_DIR = (
    Path(__file__).resolve().parents[5] / "sleep-quality-index" / "sdi" / "reports"
)


@dataclass(frozen=True)
class ReferencePopulation:
    """Component mean/std + the empirical composite distribution."""

    means: dict[str, float]
    stds: dict[str, float]
    sorted_composites: np.ndarray


@dataclass(frozen=True)
class CompositeResult:
    z: dict[str, float]
    composite: float
    percentile: float


_reference: ReferencePopulation | None = None


def _reference_dir() -> Path:
    return Path(os.environ.get("SQI_REFERENCE_DIR", str(_DEFAULT_REFERENCE_DIR)))


def load_reference() -> ReferencePopulation:
    """Component stats + composite distribution from the Sleep-EDF reference."""
    global _reference
    if _reference is not None:
        return _reference

    reference_dir = _reference_dir()
    features_path = reference_dir / "sdi_night_features_expert_lights_off.csv"
    composite_path = reference_dir / "sdi_composite_expert_lights_off.csv"

    if not features_path.is_file() or not composite_path.is_file():
        raise FileNotFoundError(
            f"SQI reference CSVs not found under {reference_dir}; set SQI_REFERENCE_DIR "
            "to the sleep-quality-index/sdi/reports folder."
        )

    features = pd.read_csv(features_path)
    composites = pd.read_csv(composite_path)

    means: dict[str, float] = {}
    stds: dict[str, float] = {}
    for component in COMPONENTS:
        column = pd.to_numeric(features[component], errors="coerce").dropna()
        means[component] = float(column.mean())
        std = float(column.std(ddof=1))
        stds[component] = std if std > 1e-9 else 1.0

    composite_values = pd.to_numeric(composites["sdi_composite"], errors="coerce").dropna()

    _reference = ReferencePopulation(
        means=means,
        stds=stds,
        sorted_composites=np.sort(composite_values.to_numpy(dtype=float)),
    )
    return _reference


def compute_composite(metrics: dict) -> CompositeResult | None:
    """Composite + percentile from a night's sdi_metrics (rb/ap/cv/mdr/pr).

    Returns None when the metrics are incomplete — a missing component is
    never faked.
    """
    try:
        reference = load_reference()
    except FileNotFoundError:
        return None

    raw: dict[str, float] = {}
    for component in COMPONENTS:
        value = metrics.get(component)
        if value is None:
            return None
        raw[component] = float(value)

    z: dict[str, float] = {}
    total = 0.0
    for component, orientation in COMPONENTS.items():
        z_value = (raw[component] - reference.means[component]) / reference.stds[component]
        z[component] = round(orientation * z_value, 4)
        total += orientation * z_value
    composite = total / len(COMPONENTS)

    # Empirical percentile within the reference population.
    sorted_scores = reference.sorted_composites
    rank = float(np.searchsorted(sorted_scores, composite, side="right"))
    percentile = round(100.0 * rank / len(sorted_scores), 2)

    return CompositeResult(
        z=z,
        composite=round(composite, 4),
        percentile=min(100.0, max(0.0, percentile)),
    )


def reference_row_for_session(session_id: str) -> dict | None:
    """Reference-composite row for one Sleep-EDF session (evaluation only)."""
    composite_path = _reference_dir() / "sdi_composite_expert_lights_off.csv"
    if not composite_path.is_file():
        return None
    frame = pd.read_csv(composite_path)
    sessions = frame["session"].astype(str)
    stem = Path(session_id).name[:6]  # e.g. "SC4001" from "SC4001E0-PSG.edf"
    match = frame[sessions == stem]
    if match.empty:
        return None
    row = match.iloc[0]
    return {
        "session": str(row["session"]),
        "composite": float(row["sdi_composite"]),
        "percentile": float(row["sdi_percentile"]),
        "n_sleep": int(row["n_sleep"]),
    }
