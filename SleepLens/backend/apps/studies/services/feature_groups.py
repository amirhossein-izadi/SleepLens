"""Feature grouping — SSC-derived vs SQI(model)-derived.

All SDI model features carry an ``sdi_`` prefix; everything else is computed
from the staging stream and the raw signal conditioned on it.
"""

from __future__ import annotations

SQI_PREFIX = "sdi_"


def split_features(values: dict) -> tuple[dict, dict]:
    """Return (ssc_features, sqi_features)."""
    ssc = {key: value for key, value in values.items() if not key.startswith(SQI_PREFIX)}
    sqi = {key: value for key, value in values.items() if key.startswith(SQI_PREFIX)}
    return ssc, sqi


def split_not_assessable(entries: list[dict]) -> tuple[list[dict], list[dict]]:
    """Return (ssc_entries, sqi_entries) for not-assessable marks."""
    ssc = [entry for entry in entries if not str(entry.get("key", "")).startswith(SQI_PREFIX)]
    sqi = [entry for entry in entries if str(entry.get("key", "")).startswith(SQI_PREFIX)]
    return ssc, sqi
