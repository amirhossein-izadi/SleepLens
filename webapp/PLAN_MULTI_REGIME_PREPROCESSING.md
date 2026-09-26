# SleepLens — Multi-Regime Data Preprocessing Specification & Roadmap

---

## 1. Executive Overview & Multi-Regime Strategy

To support the three distinct modeling regimes defined for the project, our data preprocessing architecture must provide three tailored data representations while maintaining mathematical rigor and reproducibility:

```
                               Raw Sleep-EDF Database (.edf)
                                             │
                   ┌─────────────────────────┼─────────────────────────┐
                   ▼                         ▼                         ▼
         [REGIME 1 PIPELINE]        [REGIME 2 PIPELINE]        [REGIME 3 PIPELINE]
        Hospital / Telemetry          Home / Cassette         Combined / Harmonized
         4 Channels @ 100 Hz         Dual-Rate Multi-Modal     3 Universal Channels @ 100Hz
      (EEG x2, EOG, Raw 100Hz EMG) (100Hz EEG/EOG + 1Hz Resp,  (EEG Fpz-Cz, EEG Pz-Oz, EOG)
                                     Temp, EMG Envelope)       
                   │                         │                         │
                   ▼                         ▼                         ▼
        data/processed_telemetry/  data/processed_cassette/    data/processed/ (COMPLETED)
           (44 .npz files)           (153 .npz files)             (197 .npz files)
```

---

## 2. Multi-Regime Channel & Sampling Rate Matrix

| Parameter / Signal | Regime 1: Hospital Telemetry | Regime 2: Home Cassette | Regime 3: Unified Combined |
| :--- | :---: | :---: | :---: |
| **Cohort Focus** | 22 Inpatient Insomnia Subjects | 78 Healthy Home Volunteers | All 100 Subjects Combined |
| **File Count** | 44 Recordings | 153 Recordings | 197 Recordings |
| **`EEG Fpz-Cz`** | 100 Hz (3,000 samples/epoch) | 100 Hz (3,000 samples/epoch) | 100 Hz (3,000 samples/epoch) |
| **`EEG Pz-Oz`** | 100 Hz (3,000 samples/epoch) | 100 Hz (3,000 samples/epoch) | 100 Hz (3,000 samples/epoch) |
| **`EOG horizontal`** | 100 Hz (3,000 samples/epoch) | 100 Hz (3,000 samples/epoch) | 100 Hz (3,000 samples/epoch) |
| **`EMG submental`** | **100 Hz Raw Biopotential** | **1 Hz Muscle Envelope** | *Excluded (Format mismatch)* |
| **`Resp oro-nasal`** | *Not available* | **1 Hz Airflow Thermistor** | *Excluded (Only in Cassette)* |
| **`Temp rectal`** | *Not available* | **1 Hz Core Temperature** | *Excluded (Only in Cassette)* |
| **Output Tensor Shape**| `(N, 4, 3000)` | `x_fast`: `(N, 3, 3000)`<br>`x_slow`: `(N, 3, 30)` | `(N, 3, 3000)` |
| **Status** | *Implementation Spec Below* | *Implementation Spec Below* | **100% Completed (237,942 epochs)** |

---

## 3. Signal Processing Algorithms per Modality

### A. Brain & Ocular Signals (`EEG Fpz-Cz`, `EEG Pz-Oz`, `EOG horizontal`) — All Regimes
* **Bandpass Filtering**:
  * 4th-order Butterworth digital filter ($0.5–35.0$ Hz) applied via forward-backward filtering (`scipy.signal.filtfilt`) to guarantee zero phase distortion.
  * Blocks DC baseline drift ($<0.5$ Hz) and high-frequency muscle spikes ($>35$ Hz).
* **Notch Filtering**:
  * 2nd-order IIR notch filter at $50.0$ Hz with quality factor $Q = 30$ to eliminate European AC power-line hum.
* **Normalization**:
  * Per-recording Robust Scaling:
    $$x_{\text{scaled}}(t) = \frac{x(t) - \text{median}(x)}{\text{IQR}(x)} \quad \text{where } \text{IQR} = Q_{75} - Q_{25}$$

### B. High-Resolution 100 Hz Submental EMG (Regime 1 Only)
* **Physiological Goal**: Capture chin muscle tone to detect motor atonia in REM sleep vs. hypertonia in Wake.
* **Filtering Pipeline**:
  1. High-pass filter at $10.0$ Hz (Butterworth 4th-order) to strip electrocardiogram (ECG) cross-talk and head movement artifacts.
  2. 50 Hz IIR notch filter to remove power-grid contamination.
  3. Low-pass filter at $45.0$ Hz to respect the Nyquist limit ($50$ Hz).
  4. Compute Root-Mean-Square (RMS) envelope and robust scaling.

### C. Low-Frequency Autonomic Streams (Regime 2 Only)
* **`Resp oro-nasal` (1 Hz)**:
  * Measures nasal-oral temperature changes from inhaling (cool ambient air) and exhaling (warm body air).
  * 30 samples per 30-second epoch.
  * Z-score normalization: $\frac{Resp(t) - \mu_{\text{resp}}}{\sigma_{\text{resp}}}$.
* **`Temp rectal` (1 Hz)**:
  * Measures core body temperature ($^\circ\text{C}$).
  * Changes slowly over the night ($0.5–1.0^\circ\text{C}$ drop).
  * Baseline deviation transformation:
    $$\Delta T(t) = T(t) - \text{mean}(T_{\text{night}})$$
    This removes individual baseline temperature variations (e.g. $36.8^\circ\text{C}$ vs $37.2^\circ\text{C}$) and isolates the circadian nocturnal cooling curve.
* **`EMG submental` Envelope (1 Hz)**:
  * 30 samples per epoch representing averaged muscle tension. Scaled by min-max scaling into $[0, 1]$.

---

## 4. In-Bed Wake Trimming Specification (Universal Standard)

The 24-hour ambulatory recording bias must be controlled consistently across all three regimes:

```
[Daytime Awake (10+ hours)] -> TRUNCATED
                  │
[In-Bed Window Begins]
├── 30 Minutes (60 Epochs) of Wake prior to sleep onset
├── Active Sleep Period (All Epochs of N1, N2, N3, REM + WASO)
└── 30 Minutes (60 Epochs) of Wake after final awakening
                  │
[Daytime Awake (Morning)] -> TRUNCATED
```

* **Algorithm**:
  1. Detect the index of the first non-wake epoch ($t_{\text{first}}$) and last non-wake epoch ($t_{\text{last}}$).
  2. Set `start_epoch` = $\max(0, t_{\text{first}} - 60)$.
  3. Set `end_epoch` = $\min(N_{\text{total}}, t_{\text{last}} + 61)$.
  4. Drop any epochs marked as unscored (`-1` or `?`) or gross movement (`Movement time`).

---

## 5. Storage Architecture & Directory Layout

```text
../SleepLens/data/
├── processed/                   # REGIME 3: Harmonized Universal Dataset (197 files)
│   ├── SC4001E0.npz             # Contains: x_fpz, x_pz, x_eog (all @ 100Hz), y, metadata
│   ├── ST7011J0.npz
│   └── ... (197 files, 237,942 epochs, COMPLETED)
│
├── processed_telemetry/         # REGIME 1: Hospital Telemetry Dataset (44 files)
│   ├── ST7011J0.npz             # Contains: x_4ch (shape N, 4, 3000), y, drug_condition
│   ├── ST7012J0.npz
│   └── ... (44 files, specialized 100Hz EMG)
│
└── processed_cassette/          # REGIME 2: Home Cassette Dataset (153 files)
    ├── SC4001E0.npz             # Contains: x_fast (N, 3, 3000), x_slow (N, 3, 30), y, age
    ├── SC4002E0.npz
    └── ... (153 files, multi-modal Resp & Temp)
```

---

## 6. Implementation Code: Regime 1 & Regime 2 Preprocessing Extension

The following Python script extends our existing `preprocess.py` to produce the specialized Regime 1 (`processed_telemetry`) and Regime 2 (`processed_cassette`) datasets:

```python
import os
import pyedflib
import numpy as np
from scipy.signal import butter, filtfilt, iirnotch

def preprocess_regime1_record(psg_path, hyp_path, out_dir, fallback_reader, epoch_sec=30):
    """
    Extracts 4 channels at 100 Hz for Regime 1 (Telemetry):
    Ch 0: EEG Fpz-Cz, Ch 1: EEG Pz-Oz, Ch 2: EOG horizontal, Ch 3: EMG submental (100 Hz)
    """
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.basename(psg_path).replace('-PSG.edf', '')
    out_file = os.path.join(out_dir, f"{base}.npz")
    if os.path.exists(out_file):
        return base, "exists"

    psg = pyedflib.EdfReader(psg_path)
    labels = psg.getSignalLabels()
    
    idx_fpz = labels.index('EEG Fpz-Cz')
    idx_pz  = labels.index('EEG Pz-Oz')
    idx_eog = labels.index('EOG horizontal')
    idx_emg = labels.index('EMG submental')
    
    fs = psg.getSampleFrequency(idx_fpz)
    raw_fpz = psg.readSignal(idx_fpz)
    raw_pz  = psg.readSignal(idx_pz)
    raw_eog = psg.readSignal(idx_eog)
    raw_emg = psg.readSignal(idx_emg)
    psg.close()

    # Bandpass filters
    nyq = 0.5 * fs
    b_eeg, a_eeg = butter(4, [0.5 / nyq, 35.0 / nyq], btype='band')
    b_emg, a_emg = butter(4, [10.0 / nyq, 45.0 / nyq], btype='band')
    b_notch, a_notch = iirnotch(50.0 / nyq, 30.0)

    f_fpz = filtfilt(b_notch, a_notch, filtfilt(b_eeg, a_eeg, raw_fpz))
    f_pz  = filtfilt(b_notch, a_notch, filtfilt(b_eeg, a_eeg, raw_pz))
    f_eog = filtfilt(b_notch, a_notch, filtfilt(b_eeg, a_eeg, raw_eog))
    f_emg = filtfilt(b_notch, a_notch, filtfilt(b_emg, a_emg, raw_emg))

    # Read annotations, trim in-bed wake, and stack to shape (N, 4, 3000)
    # ... (applies same trimming and saving logic)
    return base, "success"

def preprocess_regime2_record(psg_path, hyp_path, out_dir, epoch_sec=30):
    """
    Extracts Dual-Rate channels for Regime 2 (Cassette):
    Fast (100 Hz): EEG Fpz-Cz, EEG Pz-Oz, EOG horizontal (3000 samples)
    Slow (1 Hz):   Resp oro-nasal, Temp rectal, EMG envelope (30 samples)
    """
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.basename(psg_path).replace('-PSG.edf', '')
    out_file = os.path.join(out_dir, f"{base}.npz")
    if os.path.exists(out_file):
        return base, "exists"

    psg = pyedflib.EdfReader(psg_path)
    labels = psg.getSignalLabels()
    
    # 100 Hz channels
    raw_fpz = psg.readSignal(labels.index('EEG Fpz-Cz'))
    raw_pz  = psg.readSignal(labels.index('EEG Pz-Oz'))
    raw_eog = psg.readSignal(labels.index('EOG horizontal'))
    
    # 1 Hz channels
    raw_resp = psg.readSignal(labels.index('Resp oro-nasal'))
    raw_temp = psg.readSignal(labels.index('Temp rectal'))
    raw_emg  = psg.readSignal(labels.index('EMG submental'))
    psg.close()

    # Temperature baseline transformation: Delta T = T - mean(T)
    delta_temp = raw_temp - np.mean(raw_temp)
    # Respiration Z-scoring
    z_resp = (raw_resp - np.mean(raw_resp)) / (np.std(raw_resp) + 1e-6)

    # Segment and save into x_fast (N, 3, 3000) and x_slow (N, 3, 30)
    return base, "success"
```

---

## 7. Verification & Quality Control Matrix

| Check | Regime 1 (Telemetry) | Regime 2 (Cassette) | Regime 3 (Harmonized) |
| :--- | :--- | :--- | :--- |
| **Recordings Count** | Exactly 44 files | Exactly 153 files | Exactly 197 files |
| **Tensor Consistency** | All tensors `(N, 4, 3000)` | Fast: `(N, 3, 3000)`<br>Slow: `(N, 3, 30)` | All tensors `(N, 3, 3000)` |
| **NaN / Inf Check** | 0 NaNs across all channels | 0 NaNs across all channels | **Verified: 0 NaNs, 0 Infs** |
| **Label Values** | Exactly $\{0, 1, 2, 3, 4\}$ | Exactly $\{0, 1, 2, 3, 4\}$ | **Verified: 5 AASM classes** |
| **Trimming Check** | 30m Wake buffer enforced | 30m Wake buffer enforced | **Verified: 237,942 clean epochs** |
