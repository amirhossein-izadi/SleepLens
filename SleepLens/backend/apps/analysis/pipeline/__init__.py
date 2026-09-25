"""Self-contained sleep analysis pipeline.

Everything the backend needs to turn an uploaded PSG recording into
per-epoch sleep staging, per-epoch sleep depth, and night-level sleep
quality features lives inside this package. It never imports from the
experimental notebooks/scripts folders.
"""

from __future__ import annotations

# Windows note: torch must be imported before pandas/numpy in this environment
# (OpenMP DLL conflict -> WinError 1114 c10.dll). Keep this import first.
import torch  # noqa: F401  (import-order guard)

from .night import NightResult, run_night_pipeline

__all__ = ["NightResult", "run_night_pipeline"]
