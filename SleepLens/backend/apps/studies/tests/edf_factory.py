"""Synthetic EDF factory for signal-endpoint tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
from pyedflib import EdfWriter

FS = 100
SECONDS = 120


def synthetic_edf_bytes(*, seconds: int = SECONDS, fs: int = FS) -> bytes:
    """Minimal Sleep-EDF-shaped recording: 4 channels @100 Hz + 1 Hz airflow."""
    samples = fs * seconds
    rng = np.random.default_rng(11)
    headers = [
        ("EEG Fpz-Cz", fs),
        ("EEG Pz-Oz", fs),
        ("EOG horizontal", fs),
        ("EMG submental", fs),
        ("Resp oro-nasal", 1),
    ]
    with tempfile.NamedTemporaryFile(suffix=".edf", delete=False) as handle:
        path = Path(handle.name)

    writer = EdfWriter(str(path), n_channels=len(headers))
    writer.setSignalHeaders(
        [
            {
                "label": label,
                "dimension": "uV",
                "sample_frequency": rate,
                "physical_max": 1000.0,
                "physical_min": -1000.0,
                "digital_max": 32767,
                "digital_min": -32768,
                "transducer": "synthetic",
                "prefilter": "none",
            }
            for label, rate in headers
        ]
    )
    slow = 25.0 * np.sin(2 * np.pi * 1.0 * np.arange(samples) / fs)
    data = [
        (rng.standard_normal(samples) * 8 + slow).astype(np.float64),
        (rng.standard_normal(samples) * 8).astype(np.float64),
        (rng.standard_normal(samples) * 4).astype(np.float64),
        (rng.standard_normal(samples) * 2).astype(np.float64),
        (np.abs(rng.standard_normal(seconds)) * 40).astype(np.float64),
    ]
    writer.writeSamples(data)
    writer.close()

    payload = path.read_bytes()
    path.unlink(missing_ok=True)
    return payload
