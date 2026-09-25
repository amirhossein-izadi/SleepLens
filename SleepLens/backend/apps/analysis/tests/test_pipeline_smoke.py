"""End-to-end pipeline smoke test on a synthetic EDF.

Runs the real staging + SDI models and the feature extraction on a tiny
recording. Skipped automatically when the checkpoints are not present.
"""

from __future__ import annotations

import numpy as np
import pytest
from pyedflib import EdfWriter

from apps.analysis.pipeline import run_night_pipeline
from apps.analysis.pipeline.canonical import read_recording
from apps.analysis.pipeline.lightgbm import FEATURE_NAMES, extract_baseline_features
from apps.analysis.pipeline.lightgbm.adapter import lightgbm_available
from apps.analysis.pipeline.weights import get_weight_paths

pytestmark = pytest.mark.django_db

WEIGHTS_AVAILABLE = get_weight_paths().any_sleep.is_file() and get_weight_paths().sdi.is_file()
requires_weights = pytest.mark.skipif(
    not WEIGHTS_AVAILABLE, reason="model checkpoints are not present"
)

FS = 100
SECONDS = 180
SAMPLES = FS * SECONDS


def _write_synthetic_edf(path) -> None:
    """4 channels @100 Hz (EEG/EEG/EOG/EMG) + 1 Hz airflow."""
    rng = np.random.default_rng(7)
    writer = EdfWriter(str(path), n_channels=5)
    headers = [
        {"label": "EEG Fpz-Cz", "dimension": "uV", "sample_frequency": FS},
        {"label": "EEG Pz-Oz", "dimension": "uV", "sample_frequency": FS},
        {"label": "EOG horizontal", "dimension": "uV", "sample_frequency": FS},
        {"label": "EMG submental", "dimension": "uV", "sample_frequency": FS},
        {"label": "Resp oro-nasal", "dimension": "uV", "sample_frequency": 1},
    ]
    for header in headers:
        header.update(
            {
                "physical_max": 1000.0,
                "physical_min": -1000.0,
                "digital_max": 32767,
                "digital_min": -32768,
                "transducer": "synthetic",
                "prefilter": "none",
            }
        )
    writer.setSignalHeaders(headers)
    slow = 30.0 * np.sin(2 * np.pi * 1.0 * np.arange(SAMPLES) / FS)  # delta-ish
    data = [
        (rng.standard_normal(SAMPLES) * 10 + slow).astype(np.float64),
        (rng.standard_normal(SAMPLES) * 10).astype(np.float64),
        (rng.standard_normal(SAMPLES) * 5).astype(np.float64),
        (rng.standard_normal(SAMPLES) * 2).astype(np.float64),
        (np.abs(rng.standard_normal(SECONDS)) * 50).astype(np.float64),
    ]
    writer.writeSamples(data)
    writer.close()


@requires_weights
def test_pipeline_runs_end_to_end(tmp_path):
    edf_path = tmp_path / "synthetic-PSG.edf"
    _write_synthetic_edf(edf_path)

    result = run_night_pipeline(edf_path)

    # Epoch grid: 180 s -> 6 epochs, all models must agree on >= 1
    assert len(result.epochs) >= 4
    assert result.duration_minutes == pytest.approx(3.0, abs=0.2)

    # Staging output is a proper distribution, staged into known labels
    first = result.epochs[0]
    assert first.stage in {"Wake", "N1", "N2", "N3", "REM"}
    assert sum(first.probabilities.values()) == pytest.approx(1.0, abs=1e-6)
    assert 0.0 <= first.confidence <= 1.0
    assert first.confidence_band in {"high", "medium", "low"}
    assert first.needs_review == (first.confidence_band != "high")

    # Sleep depth head is present for every epoch
    assert all(epoch.sdi is not None and 0.0 <= epoch.sdi <= 1.0 for epoch in result.epochs)
    assert all(isinstance(epoch.rem_pred, bool) for epoch in result.epochs)

    # Night features: hypnogram group always computable on a staged night
    assert "tst_min" in result.features
    assert "se_pct" in result.features
    assert "transitions" in result.features

    # ECG is absent in Sleep-EDF style recordings -> substitution must be flagged
    assert result.signal_quality["substitutions"]["sdi_ecg_zero_filled"] is True

    # 1-Hz airflow envelope -> apnea metrics are not assessable, with reasons
    keys = {entry["key"] for entry in result.not_assessable}
    assert {"apnea_count", "apnea_index", "apnea_time_pct"} <= keys

    # Summary carries the chart-ready review and SDI metrics
    assert "stage_counts" in result.summary
    assert "sdi_metrics" in result.summary

    # Ensemble routing: cassette-like input uses the four-member ensemble
    assert result.summary["staging_system"] in {"ensemble", "anysleep_single"}
    if lightgbm_available():
        assert result.summary["staging_system"] == "ensemble"
        assert len(result.summary["staging_members"]) == 4


@requires_weights
def test_lightgbm_features_shape(tmp_path):
    edf_path = tmp_path / "synthetic-PSG.edf"
    _write_synthetic_edf(edf_path)
    recording = read_recording(edf_path)

    features = extract_baseline_features(recording)

    assert features is not None
    assert features.shape[1] == len(FEATURE_NAMES) == 11
    assert features.shape[0] >= 4  # 180 s -> 6 epochs, allow rounding slack
