# SleepLens — Regime 2 Plan: Home Ambulatory & Multi-Modal Modeling Framework

---

## 1. Executive Summary & Clinical Context

**Regime 2** focuses exclusively on the **Ambulatory Home Cohort (`sleep-cassette/`)**. This subset comprises **153 continuous polysomnographic recordings from 78 healthy volunteers** (37 men, 41 women) monitored in their own homes during two consecutive 24-hour periods.

### Key Strengths of the Home Cohort
1. **Ecological Validity**: Subjects slept in their natural, everyday domestic environments without the artificial stress or "first-night effect" of a hospital sleep laboratory.
2. **True Human Lifespan Trajectory (Aged 25 to 101 Years)**: Spans 76 years of healthy aging, enabling deep modeling of biological brain aging vs. chronological age.
3. **Rich Multi-Modal Peripheral Sensing**: Includes simultaneous monitoring of **nasal airflow respiration** and **circadian core body temperature**.

---

## 2. Multi-Rate Physiological Signals (100 Hz + 1 Hz)

The Cassette montage is a **dual-rate multi-sensor system**:

| Channel | Sampling Rate ($F_s$) | Physical Domain | Clinical & Physiological Role |
| :--- | :---: | :--- | :--- |
| **`EEG Fpz-Cz`** | **100 Hz** | Central Nervous System | Slow waves (Delta), sleep spindles (Sigma), K-complexes. Shows progressive decline with age. |
| **`EEG Pz-Oz`** | **100 Hz** | Central Nervous System | Occipital alpha waves (8–12 Hz). Disappears upon sleep onset. |
| **`EOG horizontal`**| **100 Hz** | Oculomotor System | Slow rolling eye movements in N1; rapid saccadic bursts in REM. |
| **`Resp oro-nasal`**| **1 Hz** | Autonomic / Respiratory | Nasal-oral airflow thermistor. Tracks respiratory rate, stability, and hypopnea/apnea patterns. |
| **`Temp rectal`** | **1 Hz** | Circadian / Metabolic | Core body temperature. Captures the nocturnal circadian temperature nadir ($0.5–1.0^\circ\text{C}$ drop). |
| **`EMG submental`**| **1 Hz** | Neuromuscular | Pre-rectified, averaged chin muscle tone envelope. |

---

## 3. Biological Dynamics in Regime 2

### A. The Circadian Core Body Temperature Arc
In healthy human circadian biology:
* Core body temperature begins dropping 1–2 hours before bedtime, reaches its minimum (nadir) around 04:00–05:00 AM, and climbs back up prior to waking.
* **Feature Value**: The slope of nocturnal cooling ($\frac{\Delta \text{Temp}}{\Delta t}$) correlates with sleep efficiency, sleep onset latency, and autonomic stability.

### B. Respiratory Stability Across Stages
* **N3 Deep Sleep**: Respiration is regular, deep, and metronomic with minimal cycle-to-cycle variance.
* **REM Sleep**: Respiration becomes irregular, rapid, and shallow due to brainstem dream activation.
* **Feature Value**: Respiration cycle variance directly aids in distinguishing REM from N3.

### C. Normal Brain Aging (Ages 25 to 101)
* **Delta Power Collapse**: SWS (Stage N3) delta power decreases by up to 70% between age 25 and age 85.
* **Spindle Frequency & Density Shift**: Sleep spindles become shorter and lower in amplitude.
* **WASO Expansion**: Wake after sleep onset naturally increases from $<15$ minutes in young adults to $>60$ minutes in centenarians.

---

## 4. Machine Learning Tasks for Regime 2

```
       High-Rate Signals (100 Hz)              Low-Rate Peripheral Signals (1 Hz)
   [EEG Fpz-Cz, EEG Pz-Oz, EOG]               [Resp Airflow, Temp, EMG Envelope]
   Shape: (Batch, 3, 3000)                    Shape: (Batch, 3, 30)
                │                                          │
                ▼                                          ▼
   [Fast Waveform 1D-CNN Encoder]            [Slow Peripheral 1D-CNN Encoder]
   (Feature Dim: 256)                        (Feature Dim: 64)
                │                                          │
                └────────────────────┬─────────────────────┘
                                     ▼
                      [Cross-Modal Late Fusion Layer]
                             Feature Dim: 320
                                     │
                                     ▼
                      [BiLSTM Temporal Context Layer]
                                     │
                ┌────────────────────┴────────────────────┐
                ▼                                         ▼
        [Task 1: Staging]                         [Task 2: Health]
       5-Class AASM Staging                   Biological Brain Age Regression
      (W, N1, N2, N3, REM)                    & Sleep Efficiency Prediction
```

1. **Task 1: Multi-Modal 5-Class Sleep Staging**
   * Fuses brainwaves with autonomic breathing and temperature signals.
   * *Benchmark*: Macro-F1 $\ge 0.81$, Accuracy $\ge 84\%$.
2. **Task 2: Biological Brain Age Prediction**
   * Regressing subject age from sleep EEG spectral properties.
   * Discrepancy ($\text{Brain Age} - \text{Chronological Age}$) serves as a clinical biomarker for accelerated neurodegeneration or poor sleep quality.
3. **Task 3: Sleep Quality & Architecture Estimation**
   * Predicting Sleep Efficiency (SE %), WASO, and Deep Sleep % ($N3 / TST$).

---

## 5. Step-by-Step Implementation Roadmap for Regime 2

### Step 1: Multi-Rate Preprocessing & Extraction
* **100 Hz Streams** (`EEG Fpz-Cz`, `EEG Pz-Oz`, `EOG`):
  * 4th-order Butterworth bandpass ($0.5–35.0$ Hz) + 50 Hz notch filter.
  * Segment into $30 \times 100 = 3,000$ points/epoch.
* **1 Hz Peripheral Streams** (`Resp`, `Temp`, `EMG`):
  * Segment into $30 \times 1 = 30$ points/epoch.
  * Respiration normalized by zero-mean unit-variance per recording.
  * Temperature converted to relative temperature deviation $\Delta T(t) = T(t) - T_{\text{mean}}$.
* **Storage**: Cache to `../SleepLens/data/processed_cassette/{record_id}.npz`.

### Step 2: Tabular Feature Engineering (LightGBM)
* **Spectral EEG Features**: Welch PSD in Delta, Theta, Alpha, Sigma, Beta + Hjorth parameters.
* **Respiratory Features**:
  * Mean airflow amplitude, coefficient of variation ($CV_{\text{resp}} = \frac{\sigma}{\mu}$), and breathing rate (spectral peak between $0.15 - 0.35$ Hz).
* **Circadian Temperature Features**:
  * Absolute core temperature, nocturnal temperature derivative ($\frac{dT}{dt}$), and deviation from 24h baseline.
* **Demographic Metadata**: Join `age` and `sex` from `SC-subjects.xls`.

### Step 3: Dual-Rate Deep Learning Architecture (PyTorch)
* Build a two-stream neural network:
  * **Stream A (High-Rate)**: Multi-scale 1D-CNN operating on `(B, 3, 3000)` $\rightarrow$ vector of size 256.
  * **Stream B (Low-Rate)**: Compact 1D-CNN operating on `(B, 3, 30)` $\rightarrow$ vector of size 64.
  * Concatenate to dimension 320 $\rightarrow$ 2-layer BiLSTM $\rightarrow$ 5-class classification head.

### Step 4: Strict Ambulatory Validation Strategy
* **GroupKFold(5)** grouped on `subject_id` across all 78 subjects (~15-16 subjects per fold).
* Both consecutive recording nights of any subject remain together in either Train or Validation.

---

## 6. Regime 2 Starter Code: Dual-Rate Multi-Modal PyTorch Module

```python
import torch
import torch.nn as nn

class DualRateMultiModalEncoder(nn.Module):
    """
    Dual-Rate Multi-Modal Encoder for the Cassette Home Cohort:
    - High-Rate: (B, 3, 3000) -> EEG Fpz-Cz, EEG Pz-Oz, EOG horizontal @ 100 Hz
    - Low-Rate:  (B, 3, 30)   -> Resp oro-nasal, Temp rectal, EMG envelope @ 1 Hz
    """
    def __init__(self, out_dim=320):
        super().__init__()
        # High-Rate 100 Hz Branch (Brain & Eye)
        self.fast_branch = nn.Sequential(
            nn.Conv1d(3, 64, kernel_size=50, stride=6, padding=25),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(8, stride=8),
            nn.Conv1d(64, 128, kernel_size=8, stride=1, padding=4),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        
        # Low-Rate 1 Hz Branch (Respiration, Core Temp, Muscle Envelope)
        self.slow_branch = nn.Sequential(
            nn.Conv1d(3, 32, kernel_size=5, stride=1, padding=2),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        
        self.fusion_fc = nn.Sequential(
            nn.Linear(256 + 64, out_dim),
            nn.ReLU()
        )

    def forward(self, x_fast, x_slow):
        # x_fast: (B, 3, 3000), x_slow: (B, 3, 30)
        f_fast = self.fast_branch(x_fast) # (B, 256)
        f_slow = self.slow_branch(x_slow) # (B, 64)
        
        combined = torch.cat([f_fast, f_slow], dim=-1) # (B, 320)
        fused = self.fusion_fc(combined)               # (B, 320)
        return fused
```

---

## 7. Action Items & Verification Targets

1. **Preprocessing Verification**: Extract all 153 Cassette records with dual-rate arrays (`x_100hz` shape `(N, 3, 3000)`, `x_1hz` shape `(N, 3, 30)`).
2. **Ablation Benchmark**: Compare staging performance with and without `Resp` and `Temp` (evaluate the performance delta contributed by peripheral sensing).
3. **Brain Age Benchmark**: Train an age regression model on healthy sleep EEG; evaluate Mean Absolute Error (MAE target: $\le 7.5$ years).
4. **Deep Staging Milestone**: Achieve Macro-F1 $> 0.81$ on 5-class sleep staging across the 78 home subjects.
