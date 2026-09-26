"""
PSG Sample Recording Generator for SleepLens Phase 8 E2E Testing.
Generates realistic multi-channel Sleep-EDF style patient archive (.zip).
Adheres to backend_coding_guidelines/02_PYTHON_CODING_STANDARDS.md.
"""

import json
import zipfile
from pathlib import Path
from typing import Dict, Any

def generate_epoch_payload(epoch_idx: int, stage: int) -> Dict[str, Any]:
    """Generates realistic micro-metrics for an epoch based on AASM stage."""
    # Stage codes: 0=Wake, 1=N1, 2=N2, 3=N3, 4=REM
    if stage == 0:  # Wake
        delta, theta, alpha, sigma, beta = 8.5, 12.0, 48.0, 10.0, 24.5
        spindles, slow_waves, emg_rms = 0, 0, 12.4
        flow = 98.0
    elif stage == 1:  # N1
        delta, theta, alpha, sigma, beta = 14.0, 36.0, 15.0, 12.0, 14.0
        spindles, slow_waves, emg_rms = 0, 0, 6.2
        flow = 94.0
    elif stage == 2:  # N2
        delta, theta, alpha, sigma, beta = 28.0, 18.0, 8.0, 38.5, 9.0
        spindles, slow_waves, emg_rms = 2, 1, 3.5
        flow = 91.0
    elif stage == 3:  # N3 Deep Sleep
        delta, theta, alpha, sigma, beta = 64.0, 10.0, 4.0, 12.0, 5.0
        spindles, slow_waves, emg_rms = 0, 4, 2.8
        flow = 88.0
    else:  # 4 = REM
        delta, theta, alpha, sigma, beta = 11.0, 38.0, 12.0, 8.0, 22.0
        spindles, slow_waves, emg_rms = 0, 0, 1.1  # Muscle atonia
        flow = 84.0

    return {
        "epoch_index": epoch_idx,
        "stage": stage,
        "start_seconds": epoch_idx * 30.0,
        "duration_seconds": 30.0,
        "channels": ["EEG Fpz-Cz", "EEG Pz-Oz", "EOG horizontal", "EMG submental", "Resp Nasal"],
        "sampling_rate_hz": 100,
        "spectral_bands": {
            "delta_0_5_4hz": delta,
            "theta_4_8hz": theta,
            "alpha_8_12hz": alpha,
            "sigma_12_16hz": sigma,
            "beta_16_30hz": beta
        },
        "microstructure": {
            "spindles_detected": spindles,
            "slow_waves_detected": slow_waves,
            "emg_rms_uv": emg_rms,
            "nasal_flow_pct": flow
        }
    }

def create_realistic_psg_zip(target_zip: Path, num_epochs: int = 120) -> Path:
    """
    Creates a standardized multi-channel Polysomnography patient archive.
    Simulates a 1-hour sleep study (120 thirty-second epochs).
    """
    target_zip.parent.mkdir(parents=True, exist_ok=True)

    # 1. Generate realistic sleep progression
    # 0-10: Wake, 11-20: N1, 21-65: N2, 66-90: N3, 91-115: REM, 116-119: Wake
    stages = []
    for i in range(num_epochs):
        if i <= 10:
            stages.append(0)
        elif i <= 20:
            stages.append(1)
        elif i <= 65:
            stages.append(2)
        elif i <= 90:
            stages.append(3)
        elif i <= 115:
            stages.append(4)
        else:
            stages.append(0)

    with zipfile.ZipFile(target_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Write epoch files
        hypno_rows = ["epoch_idx,onset_sec,stage,annotation"]
        for idx, stage in enumerate(stages):
            data = generate_epoch_payload(idx, stage)
            zf.writestr(f"epochs/epoch_{idx:04d}_report.json", json.dumps(data, indent=2))
            hypno_rows.append(f"{idx},{idx * 30.0},{stage},AASM_S_{stage}")

        # Hypnogram annotation CSV
        zf.writestr("hypnogram/annotations.csv", "\n".join(hypno_rows))

        # Patient demographics
        demographics = {
            "subject_id": "PSG-PAT-8819",
            "first_name": "Siavash",
            "last_name": "Ghomayshi",
            "age": 51,
            "biological_sex": "male",
            "bmi": 27.4,
            "epworth_score": 14,
            "referral_reason": "Excessive daytime somnolence, witnessed apneas, restless legs."
        }
        zf.writestr("metadata/demographics.json", json.dumps(demographics, indent=2))

        # Study protocol & sensor montage
        montage = {
            "sampling_frequency_hz": 100,
            "channels": [
                {"name": "EEG Fpz-Cz", "type": "EEG", "unit": "uV", "filter": "0.5-35 Hz"},
                {"name": "EEG Pz-Oz", "type": "EEG", "unit": "uV", "filter": "0.5-35 Hz"},
                {"name": "EOG horizontal", "type": "EOG", "unit": "uV", "filter": "0.5-15 Hz"},
                {"name": "EMG submental", "type": "EMG", "unit": "uV", "filter": "10-100 Hz"},
                {"name": "Resp Nasal", "type": "Flow", "unit": "%", "filter": "0.05-15 Hz"}
            ],
            "epoch_length_sec": 30,
            "lights_off_utc": "2026-09-24T22:30:00Z"
        }
        zf.writestr("signals/montage_spec.json", json.dumps(montage, indent=2))

        # Clinical referral note
        referral_text = (
            "PATIENT CLINICAL REFERRAL NOTE\n"
            "Patient: Siavash Ghomayshi, 51 yo male.\n"
            "Chief Complaint: Chronic unrefreshing sleep and loud habitual snoring.\n"
            "History: Mild hypertension, nocturnal leg jerks.\n"
            "Objective: Diagnostic overnight polysomnography to evaluate OSA vs RLS.\n"
        )
        zf.writestr("clinical_notes/referral_letter.txt", referral_text)

    return target_zip
