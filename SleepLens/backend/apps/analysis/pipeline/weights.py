"""Model weight resolution for the analysis pipeline.

Weights live outside version control (they are large). See
``analysis_weights/MANIFEST.md`` for provenance and the exact copy commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from django.conf import settings


class MissingWeightsError(RuntimeError):
    """Raised when a required checkpoint is not present on disk."""


@dataclass(frozen=True)
class WeightPaths:
    """Absolute paths to the checkpoints used by the pipeline."""

    any_sleep: Path
    sdi: Path
    lightgbm: Path


def get_weight_paths() -> WeightPaths:
    """Return configured checkpoint paths."""
    root: Path = settings.WEIGHTS_DIR
    return WeightPaths(
        any_sleep=root / "anysleep" / "anysleep-run1.pth",
        sdi=root / "sdi" / "sdi_checkpoint.pt",
        lightgbm=root / "lightgbm" / "baseline_lgbm.txt",
    )


def assert_weights_available() -> WeightPaths:
    """Validate that every required checkpoint exists, with a clear error."""
    paths = get_weight_paths()
    missing = [str(path) for path in (paths.any_sleep, paths.sdi) if not path.is_file()]
    if missing:
        raise MissingWeightsError(
            "Missing model weights: "
            + ", ".join(missing)
            + ". See analysis_weights/MANIFEST.md for how to provide them."
        )
    return paths
