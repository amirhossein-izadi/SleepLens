"""Staging sub-package — AnySleep inference and the cohort-routed ensemble."""

from __future__ import annotations

from .adapter import StagingResult, predict_stages, predict_stages_with
from .ensemble import detect_cohort, predict_ensemble

__all__ = [
    "StagingResult",
    "detect_cohort",
    "predict_ensemble",
    "predict_stages",
    "predict_stages_with",
]
