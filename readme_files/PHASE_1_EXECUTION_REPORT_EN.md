# SleepLens — Phase 1 Execution Report: Data Ingestion & Preprocessing

---

## 1. Executive Summary

Phase 1 of the SleepLens project (Data Preprocessing and Ingestion) has been **100% completed across all 197 Polysomnography (PSG) and Hypnogram pairs**. 

Every raw, multi-channel `.edf` file has been transformed into a standardized, filtered, 24-hour-trimmed, robustly normalized, and metadata-enriched `.npz` archive ready for machine learning and deep learning pipelines.

### Key Milestones Achieved
* **Total Recordings Processed**: **197 / 197** (100% success rate, 0 failures).
  * Sleep-Cassette (Home study): **153 recordings**.
  * Sleep-Telemetry (Hospital study): **44 recordings**.
* **Total Clean Epochs Generated**: **237,942 thirty-second epochs**.
* **Total In-Bed Duration Analyzed**: **1,982.85 hours** (average of ~10.06 hours per recording, including the standardized 30-minute pre- and post-sleep wake buffers).
* **Data Quality & Integrity**: **0 NaNs, 0 Infs** across all 237,942 epochs.
* **Storage Location**: `../SleepLens/data/processed/*.npz`.

---

## 2. Preprocessing Architecture & Methodology

```
   Raw .edf Files (PSG + Hypnogram)
               │
               ▼
[Step 1] File Pairing & Matching (197 Pairs Verified)
               │
               ▼
[Step 2] Ground-Truth Annotation Parsing
         ├── Primary Parser: pyedflib.readAnnotations()
         └── Fallback Parser: Custom pure-Python TAL parser for non-standard EDF+ headers
               │
               ▼
[Step 3] AASM 5-Class Standardization
         'Sleep stage W' -> 0 (Wake)
         'Sleep stage 1' -> 1 (N1)
         'Sleep stage 2' -> 2 (N2)
         'Sleep stage 3' & 'Sleep stage 4' -> 3 (N3 Slow Wave Sleep)
         'Sleep stage R' -> 4 (REM)
         Movement & Unscored (?) -> Dropped
               │
               ▼
[Step 4] In-Bed Wake Trimming (Crucial)
         Trims 15+ hours of daytime recording down to:
         [30 min Wake] + [Sleep Period] + [30 min Wake]
               │
               ▼
[Step 5] Digital Filtering (EEG Fpz-Cz, EEG Pz-Oz, EOG horizontal)
         ├── 4th-Order Butterworth Bandpass (0.5 – 35.0 Hz, zero-phase filtfilt)
         └── 2nd-Order IIR Notch Filter (50.0 Hz, Q=30)
               │
               ▼
[Step 6] 30-Second Epoch Slicing
         Each epoch: 3,000 samples @ 100 Hz
               │
               ▼
[Step 7] Robust Normalization & Metadata Attachment
         x_scaled = (x - median) / IQR
         Append: Age, Sex, Night, Study, Subject ID, Record ID
               │
               ▼
Compressed Archive: ../SleepLens/data/processed/{record_id}.npz
```

---

## 3. Critical Challenges Resolved

### A. The 24-Hour Daytime Wake Bias
* **The Problem**: In the ambulatory Cassette study, recorders were connected at ~16:00 in the afternoon and ran until the next afternoon. Evaluating on the raw files would mean over 70% of the dataset is daylight wakefulness, completely biasing any machine learning classifier.
* **The Solution**: We implemented an in-bed trimming algorithm that identifies the first sleep epoch ($t_{\text{first}}$) and the last sleep epoch ($t_{\text{last}}$), preserving exactly 30 minutes (60 epochs) of wake prior to sleep onset and 30 minutes after final awakening.

### B. Non-Compliant EDF+ Headers in Hospital Telemetry
* **The Problem**: 7 telemetry files (`ST7021J0`, `ST7071J0`, `ST7092J0`, `ST7131J0`, `ST7132J0`, `ST7141J0`, `ST7142J0`) failed `pyedflib`'s strict header syntax validation due to non-standard date spacing in the ASCII header.
* **The Solution**: We engineered a custom, pure-Python fallback Time-Stamped Annotation List (TAL) parser that reads raw byte-level TAL markers (`\x14` and `\x15`). This successfully extracted 100% of the annotations for these 7 records with zero data loss.

---

## 4. Dataset Statistics & 5-Class Distribution

### A. Demographic Breakdown
* **Total Distinct Subjects**: 100 individuals.
* **Age Distribution**: 18 to 101 years ($54.8 \pm 22.6$ years).
* **Sex Distribution**: 112 Female records, 85 Male records.

### B. Sleep Stage Distribution (AASM Standard)

| Class Code | Sleep Stage | Epoch Count | Percentage | Clinical Description |
| :---: | :--- | :---: | :---: | :--- |
| **`0`** | **Wake (W)** | **70,146** | **29.48%** | In-bed wakefulness (before sleep, after sleep, and WASO) |
| **`1`** | **N1 (Light Sleep)** | **25,175** | **10.58%** | Transitional sleep, theta activity (4–7 Hz) |
| **`2`** | **N2 (Stable Sleep)** | **88,983** | **37.40%** | Baseline NREM sleep, spindles (12–16 Hz) and K-complexes |
| **`3`** | **N3 (Deep / Slow Wave)**| **19,454** | **8.18%** | Restorative delta sleep ($0.5–2$ Hz, $>75\,\mu\text{V}$) |
| **`4`** | **REM (Dream Sleep)** | **34,184** | **14.37%** | Rapid eye movements, desynchronized EEG, muscle atonia |
| **Total** | **All Stages** | **237,942** | **100.00%** | **1,982.85 hours of high-quality PSG data** |

---

## 5. Processed File Schema (`.npz`)

Each file saved under `../SleepLens/data/processed/{record_id}.npz` contains:

| Key | Shape | Dtype | Description |
| :--- | :--- | :--- | :--- |
| **`x_fpz`** | `(N, 3000)` | `float32` | Filtered, IQR-scaled `EEG Fpz-Cz` (Primary brainwave channel) |
| **`x_pz`** | `(N, 3000)` | `float32` | Filtered, IQR-scaled `EEG Pz-Oz` (Occipital alpha channel) |
| **`x_eog`** | `(N, 3000)` | `float32` | Filtered, IQR-scaled `EOG horizontal` (Eye movements channel) |
| **`y`** | `(N,)` | `int64` | Ground-truth AASM stage labels $\in \{0, 1, 2, 3, 4\}$ |
| **`subject_id`**| scalar | `int` | Integer subject ID (for GroupKFold splitting) |
| **`night`** | scalar | `int` | Night number (1 or 2) |
| **`age`** | scalar | `int` | Age of subject in years |
| **`sex`** | scalar | `int` | Standardized biological sex (`1` = Female, `2` = Male) |
| **`study`** | scalar | `str` | `'cassette'` (home) or `'telemetry'` (hospital) |
| **`record_id`**| scalar | `str` | E.g., `'SC4001E0'`, `'ST7011J0'` |
| **`epoch_indices`**| `(N,)` | `int` | Index of each epoch relative to the original raw recording |
| **`fs`** | scalar | `int` | Sampling frequency ($100$ Hz) |

---

## 6. How to Load Data for Modeling (Phase 2 & Phase 3)

```python
import glob
import numpy as np

# Load a single recording
record_path = "../SleepLens/data/processed/SC4001E0.npz"
data = np.load(record_path)

x_fpz = data['x_fpz']      # Shape: (N, 3000)
y = data['y']              # Shape: (N,)
subject_id = data['subject_id'] # Use for GroupKFold
age = data['age']
sex = data['sex']

print(f"Loaded {record_path}: {len(y)} epochs for Subject {subject_id} (Age {age}, Sex {sex})")

# Load all records into memory / generator
all_files = sorted(glob.glob("../SleepLens/data/processed/*.npz"))
print(f"Total dataset files ready for training: {len(all_files)}")
```

---

## 7. Next Steps: Phase 2 (Tabular Baseline)

With Phase 1 complete:
1. Proceed to **Phase 2**: Implement feature extraction (Welch PSD, Hjorth parameters, spectral entropy, and context windows) in `../SleepLens/src/features.py`.
2. Train a **LightGBM / XGBoost** baseline using 5-fold `GroupKFold` by `subject_id` to establish your first benchmark score.
