# SleepLens — Regime 1 Plan: Hospital & Telemetry Modeling Framework

---

## 1. Executive Summary & Clinical Context

**Regime 1** focuses exclusively on the **Hospital Telemetry Cohort (`sleep-telemetry/`)**. This subset comprises **44 polysomnographic recordings across 22 inpatient subjects** (aged 18 to 79 years) who were clinically admitted with mild difficulty falling asleep.

### The Pharmacological Trial Design
The telemetry recordings represent a randomized, double-blind, cross-over clinical drug trial:
* **Condition A (Placebo Night)**: Baseline pathological sleep profile of individuals with sleep-onset difficulty.
* **Condition B (Temazepam Night)**: Sleep under the influence of **Temazepam (33 mg)**, a standard benzodiazepine hypnotic administered 30 minutes before lights off.

### Distinct Hardware Advantage
Unlike the ambulatory home recordings, the hospital cohort transmitted **Submental EMG at full 100 Hz** ($3,000$ points/epoch), offering raw high-frequency biopotential measurements of chin muscle tone rather than an averaged 1 Hz envelope.

---

## 2. Physiological Signals & Specialized Montage

| Channel | Sampling Rate ($F_s$) | Physiological Role in Regime 1 |
| :--- | :---: | :--- |
| **`EEG Fpz-Cz`** | **100 Hz** | Frontal slow waves, sleep spindles, and K-complexes. Captures benzodiazepine-induced spindle amplification. |
| **`EEG Pz-Oz`** | **100 Hz** | Occipital alpha waves (8–12 Hz). Critical for assessing prolonged sleep-onset latency in insomniac subjects. |
| **`EOG horizontal`**| **100 Hz** | Saccades and rapid eye movements. Distinguishes active wakefulness from REM sleep. |
| **`EMG submental`** | **100 Hz** | **High-resolution chin muscle biopotential**. Solves REM vs. Wake disambiguation by detecting true motor atonia. |

---

## 3. Pharmacological Dynamics: The Temazepam Signature

Temazepam modulates GABA$_A$ receptors, altering normal sleep architecture:
1. **Sleep Onset Latency (SOL) Reduction**: Significant reduction in time from lights-out to Stage N2.
2. **Sigma / Spindle Band Amplification**: Markedly increases power in the **12–16 Hz (Sigma)** band during NREM sleep.
3. **Beta Elevation**: Induces high-frequency **Beta (16–30 Hz)** oscillations across all sleep stages ("benzodiazepine fast activity").
4. **Slow Wave Suppression**: Mild to moderate reduction in Stage N3 Delta ($0.5–2$ Hz) amplitude.

---

## 4. Multi-Task Machine Learning Objectives in Regime 1

```
                         Input: 4-Channel Epoch Tensor
                    (EEG Fpz-Cz, EEG Pz-Oz, EOG, EMG @ 100Hz)
                                       │
                                       ▼
                  [Shared Multi-Scale 1D-CNN Feature Backbone]
                                       │
                ┌──────────────────────┼──────────────────────┐
                ▼                      ▼                      ▼
        [Task 1: Primary]     [Task 2: Secondary]    [Task 3: Auxiliary]
       5-Class AASM Staging    Sleep Quality Indices   Drug Classification
      (W, N1, N2, N3, REM)     (Predict SOL & WASO)   (Placebo vs. Temazepam)
```

1. **Task 1 (Primary): 5-Class Sleep Staging with 100 Hz EMG**
   * Classifying 30s epochs into $\{W, N1, N2, N3, REM\}$.
   * *Target Benchmark*: Macro-F1 $\ge 0.82$, Overall Accuracy $\ge 85\%$.
2. **Task 2 (Clinical Regression): Sleep Onset Latency (SOL) Estimation**
   * Predicting the subject's latency to fall asleep from early-night PSG signals.
3. **Task 3 (Pharmacological AI): Binary Drug Effect Detection**
   * Classifying whole-night recordings into **Placebo vs. Temazepam** using spectral spindle density and beta elevation.

---

## 5. Step-by-Step Implementation Roadmap for Regime 1

### Step 1: 4-Channel Preprocessing & EMG Envelope Construction
* **EEG/EOG Filtering**: 4th-order Butterworth bandpass ($0.5–35.0$ Hz) + 50 Hz notch filter.
* **100 Hz EMG Filtering**:
  * High-pass filter at $10.0$ Hz to strip motion/cardiac artifacts.
  * Rectification $|EMG(t)|$ followed by low-pass smoothing ($2.0$ Hz) to construct the submental muscle tone envelope.
* **Storage**: Cache to `../SleepLens/data/processed_telemetry/{record_id}.npz` with shape `(N, 4, 3000)`.

### Step 2: Tabular Feature Engineering (LightGBM)
* **EEG Features**: Relative band powers (Delta, Theta, Alpha, Sigma, Beta).
* **Temazepam Biomarker**: Fast-wave ratio $\frac{\text{Sigma} + \text{Beta}}{\text{Delta} + \text{Theta}}$.
* **EMG Features**:
  * Root Mean Square (RMS) voltage: $\text{RMS} = \sqrt{\frac{1}{N}\sum x_i^2}$.
  * Muscle Atonia Index (MAI): Fraction of epoch where EMG power falls below the 10th percentile baseline.
* **Demographics**: Join age, sex, and drug condition from `ST-subjects.xls`.

### Step 3: 4-Channel Deep Sequence Model (PyTorch)
* **Architecture**:
  * Input tensor: `(Batch, Seq_Len=20, Channels=4, Samples=3000)`.
  * Multi-channel 1D-CNN encoder with channel attention (SE-Net or spatial conv).
  * 2-layer Bidirectional GRU/LSTM for inter-epoch transition learning.
  * Loss: Focal Loss ($\gamma = 2.0$) with class inverse-frequency weights.

### Step 4: Strict Inpatient Validation Strategy
* **GroupKFold(5)** grouped strictly by `subject_id` (22 subjects $\rightarrow$ ~4-5 subjects per fold).
* **Guaranteed Separation**: Both the Placebo night and the Temazepam night of any individual subject MUST remain in the same fold to prevent subject-level fingerprint leakage.

---

## 6. Regime 1 Starter Code: 4-Channel PyTorch Architecture

```python
import torch
import torch.nn as nn

class Telemetry4ChEncoder(nn.Module):
    """
    4-Channel Intra-Epoch Encoder tailored for Hospital Telemetry:
    Ch 0: EEG Fpz-Cz, Ch 1: EEG Pz-Oz, Ch 2: EOG horizontal, Ch 3: EMG submental
    """
    def __init__(self, out_dim=256):
        super().__init__()
        # Parallel spectral filters
        self.conv_eeg = nn.Sequential(
            nn.Conv1d(2, 64, kernel_size=50, stride=6, padding=25), # EEG branch
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(8, stride=8)
        )
        self.conv_eog_emg = nn.Sequential(
            nn.Conv1d(2, 64, kernel_size=50, stride=6, padding=25), # EOG + EMG branch
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(8, stride=8)
        )
        self.fusion = nn.Sequential(
            nn.Conv1d(128, 256, kernel_size=8, stride=1, padding=4),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(256, out_dim),
            nn.ReLU(),
            nn.Dropout(0.3)
        )

    def forward(self, x):
        # x: (Batch, 4, 3000)
        eeg = x[:, 0:2, :]     # Fpz-Cz + Pz-Oz
        eog_emg = x[:, 2:4, :] # EOG + EMG
        
        f_eeg = self.conv_eeg(eeg)
        f_other = self.conv_eog_emg(eog_emg)
        
        merged = torch.cat([f_eeg, f_other], dim=1) # (Batch, 128, L)
        embedding = self.fusion(merged)             # (Batch, 256)
        return embedding
```

---

## 7. Action Items & Verification Targets

1. **Preprocessing Verification**: Extract all 44 recordings with 4 channels (`EEG Fpz-Cz`, `EEG Pz-Oz`, `EOG`, `EMG 100Hz`).
2. **Baseline Milestone**: Train LightGBM on 4-channel features; achieve Macro-F1 $> 0.77$.
3. **Deep Learning Milestone**: Train 4-Channel CNN+BiLSTM; achieve Macro-F1 $> 0.83$ with high REM sensitivity ($F1_{\text{REM}} > 0.85$ due to 100 Hz EMG atonia).
4. **Clinical Drug Benchmark**: Achieve $> 80\%$ accuracy classifying Placebo vs. Temazepam nights using sleep architecture features.
