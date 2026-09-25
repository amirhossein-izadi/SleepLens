"""Pipeline constants shared by staging, sleep-depth and feature code."""

from __future__ import annotations

# Epoch grid
EPOCH_SECONDS: int = 30

# Canonical loading
CANONICAL_FS: int = 100

# Staging (AnySleep)
STAGING_FS: int = 128
STAGING_EPOCH_SAMPLES: int = EPOCH_SECONDS * STAGING_FS  # 3840
# Verified checkpoint logit order (permutation search on real recordings).
STAGING_LOGIT_ORDER: tuple[str, ...] = ("Wake", "N1", "N2", "N3", "REM")

STAGES: tuple[str, ...] = ("Wake", "N1", "N2", "N3", "REM")
STAGE_TO_INT: dict[str, int] = {stage: index for index, stage in enumerate(STAGES)}

# Sleep Depth Index
SDI_FS: int = 100
SDI_EPOCH_SAMPLES: int = EPOCH_SECONDS * SDI_FS  # 3000
SDI_BATCH_SIZE: int = 128

# Confidence bands (overridden by Django settings where available)
DEFAULT_CONFIDENCE_HIGH: float = 0.80
DEFAULT_CONFIDENCE_MEDIUM: float = 0.60

# Sleep-quality feature parameters (from the published SDI / SQI definitions)
SDI_SHALLOW_THRESHOLD: float = 0.2
EEG_BANDS: dict[str, tuple[float, float]] = {
    "delta": (0.5, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 12.0),
    "sigma": (12.0, 16.0),
    "beta": (16.0, 30.0),
}
TOTAL_BAND: tuple[float, float] = (0.5, 30.0)
