# Sleep-EDF Database Expanded: Comprehensive Hackathon Guide for Sleep Quality Prediction

---

## 1. Executive Summary & Hackathon Context

### The Challenge
This hackathon focuses on **predicting sleep quality** using objective physiological data recorded during sleep. In modern medicine and healthcare AI, quantifying sleep quality is essential for diagnosing sleep disorders (such as insomnia, sleep apnea, and circadian rhythm disorders), evaluating therapeutic interventions, and optimizing recovery.

### The Dataset
You are working with the **Sleep-EDF Database Expanded (v1.0.0)**, collected and published on PhysioNet by Bob Kemp et al. It contains **197 whole-night / 24-hour polysomnographic (PSG) recordings** with matched expert-annotated hypnograms.

The dataset consists of two distinct sub-studies:
1. **Sleep-Cassette (`sleep-cassette/`)**: 153 recordings from 78 healthy ambulatory subjects (aged 25 to 101 years, 37 males, 41 females) recorded in their homes during two consecutive 24-hour periods.
2. **Sleep-Telemetry (`sleep-telemetry/`)**: 44 recordings from 22 hospital subjects (aged 18 to 79 years) who had mild difficulty falling asleep, recorded under a double-blind protocol (Night 1: Placebo or Temazepam; Night 2: Cross-over).

---

## 2. Directory Structure & File Architecture

```
.
├── RECORDS                     # Master list of all 197 PSG EDF files
├── RECORDS-v1                  # Legacy list of original 61 records (v1)
├── SHA256SUMS.txt              # Checksums for data integrity
├── SC-subjects.xls             # Clinical demographics & lights-off times for Cassette study
├── ST-subjects.xls             # Clinical demographics & trial protocol for Telemetry study
├── sleep-cassette/             # 153 PSG recordings + 153 Hypnograms (153 pairs)
│   ├── SC4001E0-PSG.edf
│   ├── SC4001EC-Hypnogram.edf
│   └── ...
└── sleep-telemetry/            # 44 PSG recordings + 44 Hypnograms (44 pairs)
    ├── ST7011J0-PSG.edf
    ├── ST7011JP-Hypnogram.edf
    └── ...
```

### File Naming Convention Decoded

#### Sleep Cassette Files: `SC4ssNEy-PSG.edf` / `SC4ssNEy-Hypnogram.edf`
* `SC`: Study name (**S**leep **C**assette).
* `4ss`: Subject identifier:
  * `400` = Subject 00, `401` = Subject 01, ..., `482` = Subject 82.
* `N`: Recording night:
  * `1` = First night / 24h recording.
  * `2` = Second night / 24h recording.
* `E`: Recording device/cassette category (e.g., `E`, `F`, `G`).
* `y`: Sub-identifier:
  * For PSG files: `0` (e.g., `SC4001E0-PSG.edf`).
  * For Hypnogram files: Scorer ID (e.g., `C`, `H`, `J`, `P`, `W`, etc., representing the expert sleep technician who manually scored the record).

#### Sleep Telemetry Files: `ST7ssNEy-PSG.edf` / `ST7ssNEy-Hypnogram.edf`
* `ST`: Study name (**S**leep **T**elemetry).
* `7ss`: Subject identifier:
  * `701` = Subject 01, `702` = Subject 02, ..., `724` = Subject 24.
* `N`: Trial night (`1` or `2`).
* `J`: Recording telemetry system.
* `y`: `0` for PSG, or letter indicating scorer code for Hypnogram.

---

## 3. Physiological Signals (PSG Channels)

Polysomnography (PSG) is the clinical gold standard for sleep evaluation. The signals in this dataset are:

| Channel Label | Sampling Rate ($F_s$) | Physical Unit | Signal Type | Clinical & Physiological Role |
| :--- | :--- | :--- | :--- | :--- |
| **`EEG Fpz-Cz`** | **100 Hz** | $\mu\text{V}$ | Electroencephalogram | Frontal-Central brain electrical activity. Captures slow waves (Delta), sleep spindles (11–16 Hz), and K-complexes essential for staging N2 and N3 deep sleep. |
| **`EEG Pz-Oz`** | **100 Hz** | $\mu\text{V}$ | Electroencephalogram | Parietal-Occipital brain electrical activity. Captures occipital Alpha rhythm (8–12 Hz) prominent during relaxed wakefulness with eyes closed. |
| **`EOG horizontal`**| **100 Hz** | $\mu\text{V}$ | Electrooculogram | Monitors horizontal eye movements. Critical for detecting rapid eye movements (REM sleep) and slow rolling eye movements (N1 sleep). |
| **`EMG submental`**| **1 Hz** (SC) / **100 Hz** (ST) | $\mu\text{V}$ | Electromyogram | Chin muscle tone. High during Wake, moderate in NREM, and completely suppressed (muscle atonia) during REM sleep. |
| **`Resp oro-nasal`**| **1 Hz** (SC only) | arbitrary | Respiration | Airflow through mouth and nose. Monitors respiratory rate and breathing disturbances. |
| **`Temp rectal`** | **1 Hz** (SC only) | $^\circ\text{C}$ | Temperature | Core body temperature. Reflects circadian rhythm regulation (core temperature drops during sleep). |
| **`Event marker`** | **1 Hz** (SC) / **10 Hz** (ST) | arbitrary | Event | Button pressed by patient or technician to flag clinical events. |

> **Key Modeling Takeaway:** `EEG Fpz-Cz`, `EEG Pz-Oz`, and `EOG horizontal` are present across **all 197 recordings** at identical 100 Hz sampling rates. Most state-of-the-art models use either single-channel EEG (`EEG Fpz-Cz`) or dual-channel (`EEG Fpz-Cz` + `EOG horizontal`).

---

## 4. Ground-Truth Labels & Sleep Staging System

The dataset annotations are stored as Time-Stamped Annotation Lists (TAL) inside the `-Hypnogram.edf` files. Each epoch corresponds to a **30-second duration window**.

The original annotations follow the classical **Rechtschaffen & Kales (R&K)** staging standard. In modern data science and clinical practice (AASM standard), they are typically grouped into **5 standard classes**:

| Original R&K Annotation | AASM Stage | Class Code | Description & Defining Features |
| :--- | :--- | :--- | :--- |
| **`Sleep stage W`** | **Wake (W)** | `0` | Active or relaxed wakefulness. Characterized by high-frequency EEG, prominent Alpha waves (8–12 Hz) in `Pz-Oz`, eye blinks, and high muscle tone. |
| **`Sleep stage 1`** | **N1** (Light Sleep) | `1` | Transition from wake to sleep. Loss of alpha rhythm; replacement by low-voltage mixed-frequency Theta activity (4–7 Hz), vertex sharp waves, slow eye movements. |
| **`Sleep stage 2`** | **N2** (Stable Sleep) | `2` | True physiological sleep onset. Characterized by **Sleep Spindles** (11–16 Hz bursts lasting $\ge 0.5$s) and **K-complexes** (sharp negative wave followed by slower positive wave $\ge 0.5$s). |
| **`Sleep stage 3`** | **N3** (Slow Wave Sleep) | `3` | Deep, restorative slow-wave sleep. High-amplitude ($>75\,\mu\text{V}$) slow Delta waves ($0.5–2\,\text{Hz}$) occupying 20% to 50% of the epoch. |
| **`Sleep stage 4`** | **N3** (Deep SWS) | `3` | Combined with Stage 3 in modern AASM. Delta waves occupy $>50\%$ of the epoch. Crucial for cellular repair, growth hormone release, and immune health. |
| **`Sleep stage R`** | **REM** (Dreaming) | `4` | Rapid Eye Movement sleep. Desynchronized, low-voltage EEG, sawtooth waves, bursts of rapid eye movements on EOG, and profound muscle atonia (low EMG). |
| **`Movement time`** | Excluded / Wake | - | Epoch obscured by gross body movements. Typically merged into `Wake` or excluded. |
| **`Sleep stage ?`** | Excluded | - | Unscored signal, amplifier calibration, or sensor detachment. Excluded from evaluation. |

---

## 5. What is "Sleep Quality"? Quantitative Metrics

In clinical sleep medicine, sleep quality is quantified using objective indices computed from the full-night hypnogram. Depending on your hackathon prompt, your objective is either:
1. **Sleep Stage Classification:** Classifying every 30s epoch into $\{W, N1, N2, N3, REM\}$.
2. **Quality Metric Regression / Estimation:** Predicting global summary indices from full or partial recordings.
3. **Condition Classification:** Distinguishing Good vs. Poor Sleepers, Normal vs. Sleep-Disturbed, or Placebo vs. Drug (Temazepam).

### Key Clinical Polysomnography (PSG) Metrics

#### 1. Sleep Efficiency (SE %) — *The Primary Benchmark*
$$\text{SE} = \frac{\text{Total Sleep Time (TST)}}{\text{Time in Bed (TIB)}} \times 100\%$$
* **Healthy standard:** $\ge 85\%$ (above 90% is excellent).
* **Clinical indicator:** $<85\%$ indicates insomnia, sleep disruption, or poor subjective sleep quality.

#### 2. Total Sleep Time (TST)
Total minutes spent in any sleep stage ($N1 + N2 + N3 + N4 + REM$):
$$\text{TST} = \sum (\text{Epochs}_{N1, N2, N3, N4, REM}) \times \frac{30}{60} \text{ minutes}$$
* **Healthy standard:** 7.0 to 8.5 hours (420–510 minutes).

#### 3. Time in Bed (TIB)
Total time from lights out (bedtime) to lights on (final rising time):
$$\text{TIB} = (\text{End Time} - \text{Start Time}) \text{ in bed}$$

#### 4. Sleep Onset Latency (SOL)
Duration from lights out until the first occurrence of sleep (first epoch of N1, N2, or N3):
* **Healthy standard:** 10 to 20 minutes.
* **Clinical indicator:** $>30$ minutes signifies sleep-onset insomnia; $<5$ minutes indicates severe sleep deprivation or narcolepsy.

#### 5. Wake After Sleep Onset (WASO)
Total minutes of wakefulness occurring between initial sleep onset and final awakening:
$$\text{WASO} = \sum (\text{Wake Epochs during sleep period}) \times 0.5 \text{ minutes}$$
* **Healthy standard:** $< 30$ minutes in young healthy adults.
* **Clinical indicator:** High WASO ($> 45$–$60$ min) is the primary hallmark of sleep maintenance insomnia and sleep fragmentation.

#### 6. Sleep Stage Proportions (% of TST)
* **$\% \text{N1}$:** Normally **2% – 5%**. Elevated in fragmented, restless sleep.
* **$\% \text{N2}$:** Normally **45% – 55%**. Represents baseline consolidated non-REM sleep.
* **$\% \text{N3}$ (Slow Wave Sleep / Deep Sleep):** Normally **15% – 25%**. Decreases naturally with age; severely reduced in poor sleep quality and chronic fatigue.
* **$\% \text{REM}$:** Normally **20% – 25%**. Deficits impair memory consolidation and emotional equilibrium.

#### 7. Number of Awakenings (NOA) & Sleep Fragmentation Index (SFI)
The count of transitions from any sleep stage back into Wake ($W$). Higher count indicates fractured, shallow sleep.

#### 8. REM Onset Latency
Time from sleep onset to the first epoch of REM sleep:
* **Healthy standard:** 70 to 120 minutes.
* **Clinical indicator:** Abnormally short REM latency ($<60$ min) can indicate major depression, narcolepsy, or REM rebound following sleep deprivation.

---

## 6. Subject Demographics & Metadata

### `SC-subjects.xls` (Sleep Cassette)
* **`subject`**: Subject number (0 to 82).
* **`night`**: Night index (1 or 2).
* **`age`**: Age in years (range: 25 to 101).
* **`sex (F=1)`**: Biological sex (`1` = Female, `2` = Male).
* **`LightsOff`**: Time when lights were turned off for sleep (e.g. `22:45:00`, `00:38:00`).

### `ST-subjects.xls` (Sleep Telemetry)
* **`Nr`**: Subject identifier (1 to 24).
* **`Age`**: Age in years (range: 18 to 79).
* **`M1/F2`**: Biological sex (`1` = Male, `2` = Female).
* **`Placebo night`**: Night number and lights-off time for the placebo trial.
* **`Temazepam night`**: Night number and lights-off time for the Temazepam (33 mg hypnotic) trial.

> **Data Science Insight:** Age is the strongest natural predictor of sleep architecture. Elderly subjects exhibit drastically lower N3/SWS, lower sleep efficiency, and higher WASO. Incorporating `age` and `sex` into your prediction models provides immediate performance gains.

---

## 7. Crucial Preprocessing Trap: The 24-Hour Wake Problem

In the **Sleep-Cassette** subset, subjects wore ambulatory recorders for **24 continuous hours** starting in the afternoon (~16:00) before sleep and ending the next afternoon.
* As a result, the recording contains **hours of awake time before going to bed** and **hours of awake time after waking up**.
* **The Trap:** If you blindly evaluate a model on the full raw file, 70% of the epochs will be `Wake`, leading to artificially skewed metrics and poor generalization.
* **The Standard Fix in Literature:**
  1. Use `LightsOff` from `SC-subjects.xls` as the start of the in-bed window.
  2. Or, follow the universally adopted benchmark protocol: Trim the recording to include only **30 minutes of Wake before the first sleep epoch** and **30 minutes of Wake after the last sleep epoch**.

---

## 8. End-to-End Modeling Architecture

```
   Raw EDF Files (PSG + Hypnogram)
               │
               ▼
   Preprocessing & Windowing (30s Epochs)
   - Bandpass filter (0.5 - 35 Hz)
   - Notch filter (50 Hz)
   - Robust scaling (IQR / Z-score)
   - In-bed window trimming
               │
   ┌───────────┴────────────────────────┐
   ▼                                    ▼
Approach A: Feature Engineering      Approach B: Deep Learning
- Band powers (Delta, Theta, Alpha,  - 1D-CNN (Local temporal feature extractor)
  Sigma, Beta, Gamma)                - BiLSTM / Transformer (Sequence context)
- Spectral ratios (Delta/Beta, etc.) - Models: TinySleepNet, DeepSleepNet,
- Spectral Entropy & Complexity        U-Sleep, AttnSleep
- Hjorth parameters                  - End-to-end raw signal processing
   │                                    │
   ▼                                    ▼
Tabular Classifier (LightGBM/XGB)    Sequence Model Output
   │                                    │
   └───────────┬────────────────────────┘
               ▼
   Sleep Stages / Staging Hypnogram
               │
               ▼
   Macro Sleep Quality Calculation
   - Sleep Efficiency (SE %)
   - WASO, SOL, TST
   - Stage Percentages (% N3, % REM)
   - Sleep Quality Score
```

### Feature Engineering for Tabular Models (LightGBM / XGBoost)
If building a feature-based pipeline, extract these features for each 30-second epoch:
1. **Time Domain Statistics:** Mean, variance, standard deviation, skewness, kurtosis, zero-crossing rate.
2. **Frequency Domain (PSD via Welch's Method):**
   * Delta Power ($0.5 - 4\,\text{Hz}$) $\rightarrow$ Deep sleep biomarker.
   * Theta Power ($4 - 8\,\text{Hz}$) $\rightarrow$ N1 drowsiness biomarker.
   * Alpha Power ($8 - 12\,\text{Hz}$) $\rightarrow$ Relaxed wakefulness biomarker.
   * Sigma Power ($12 - 16\,\text{Hz}$) $\rightarrow$ Sleep spindle biomarker (N2).
   * Beta Power ($16 - 30\,\text{Hz}$) $\rightarrow$ Cortical arousal / wake biomarker.
   * Power Ratios: $\frac{\text{Delta}}{\text{Theta}}$, $\frac{\text{Delta}}{\text{Beta}}$, $\frac{\text{Alpha}}{\text{Delta}}$.
3. **Non-linear & Complexity Features:**
   * Hjorth Activity, Mobility, and Complexity.
   * Spectral Entropy, Sample Entropy, Permutation Entropy.
4. **Contextual Temporal Features:**
   * Features from previous epoch ($t-1$) and next epoch ($t+1$). Sleep stages are continuous and Markovian; contextual smoothing boosts accuracy by 5–10%.

---

## 9. Validation Strategy & Leakage Prevention

### Rule 1: Subject-Wise Split (GroupKFold) — MANDATORY
* **DO NOT** perform random cross-validation over individual epochs!
* Consecutive epochs from the same night/subject share profound autocorrelation. Random splitting causes catastrophic data leakage and falsely high cross-validation scores that collapse on the test set.
* **Always split by `subject` ID using `GroupKFold(n_splits=5)` or `LeaveOneGroupOut`.**

### Rule 2: Handling Class Imbalance
* In a typical sleep study, `N2` is ~50% of sleep, while `N1` is only ~5%.
* Use class-weighted cross-entropy loss, Focal Loss, or balanced sampling in your classifiers.
* Report **Macro F1-Score** and **Cohen's Kappa ($\kappa$)** alongside Overall Accuracy.

---

## 10. Starter Python Implementation

Here is a ready-to-run Python script for reading PSG signals, parsing hypnograms, and calculating clinical sleep quality metrics:

```python
import pyedflib
import numpy as np
import pandas as pd

def load_psg_and_hypnogram(psg_path, hyp_path, epoch_sec=30):
    """
    Reads PSG channels and expands hypnogram annotations to 30s epochs.
    """
    # 1. Read PSG Signals
    psg = pyedflib.EdfReader(psg_path)
    labels = psg.getSignalLabels()
    
    # Extract EEG Fpz-Cz
    fpz_idx = labels.index('EEG Fpz-Cz')
    fs = psg.getSampleFrequency(fpz_idx)
    eeg_fpz = psg.readSignal(fpz_idx)
    psg.close()
    
    # 2. Read Hypnogram Annotations
    hyp = pyedflib.EdfReader(hyp_path)
    onsets, durations, descriptions = hyp.readAnnotations()
    hyp.close()
    
    # Expand annotations into 30s epochs
    stage_sequence = []
    stage_map = {
        'Sleep stage W': 'W',
        'Sleep stage 1': 'N1',
        'Sleep stage 2': 'N2',
        'Sleep stage 3': 'N3',
        'Sleep stage 4': 'N3', # Combine N3 and N4 into N3 (AASM)
        'Sleep stage R': 'REM',
        'Movement time': 'M',
        'Sleep stage ?': '?'
    }
    
    for onset, dur, desc in zip(onsets, durations, descriptions):
        n_epochs = int(round(dur / epoch_sec))
        mapped = stage_map.get(desc, '?')
        stage_sequence.extend([mapped] * n_epochs)
        
    stages = np.array(stage_sequence)
    return eeg_fpz, fs, stages

def compute_clinical_sleep_metrics(stages, epoch_sec=30):
    """
    Computes standard Polysomnography (PSG) sleep quality metrics.
    Trims wake to 30 min before and after the sleep period.
    """
    sleep_mask = np.isin(stages, ['N1', 'N2', 'N3', 'REM'])
    sleep_indices = np.where(sleep_mask)[0]
    
    if len(sleep_indices) == 0:
        return {'Error': 'No sleep detected in recording'}
        
    first_sleep = sleep_indices[0]
    last_sleep = sleep_indices[-1]
    
    # Standard trimming: 30 minutes wake before sleep onset, 30 minutes wake after sleep end
    pad_epochs = int(30 * 60 / epoch_sec)
    start_idx = max(0, first_sleep - pad_epochs)
    end_idx = min(len(stages), last_sleep + pad_epochs + 1)
    
    in_bed = stages[start_idx:end_idx]
    
    tib_min = len(in_bed) * (epoch_sec / 60)
    in_bed_sleep = np.isin(in_bed, ['N1', 'N2', 'N3', 'REM'])
    tst_min = np.sum(in_bed_sleep) * (epoch_sec / 60)
    
    # Sleep Efficiency (SE %)
    se = (tst_min / tib_min) * 100 if tib_min > 0 else 0
    
    # Sleep Onset Latency (SOL)
    sol_min = (first_sleep - start_idx) * (epoch_sec / 60)
    
    # Wake After Sleep Onset (WASO)
    wake_epochs_during_sleep = np.sum(stages[first_sleep:last_sleep+1] == 'W')
    waso_min = wake_epochs_during_sleep * (epoch_sec / 60)
    
    # Stage Durations and Percentages of TST
    stage_durations = {st: np.sum(in_bed == st) * (epoch_sec / 60) for st in ['W', 'N1', 'N2', 'N3', 'REM']}
    stage_percentages = {f'pct_{st}': (stage_durations[st] / tst_min * 100) if tst_min > 0 else 0 
                         for st in ['N1', 'N2', 'N3', 'REM']}
    
    # Number of Awakenings
    sleep_period = stages[first_sleep:last_sleep+1]
    awakenings = 0
    in_wake = False
    for st in sleep_period:
        if st == 'W' and not in_wake:
            awakenings += 1
            in_wake = True
        elif st != 'W':
            in_wake = False

    return {
        'Time_in_Bed_min': round(tib_min, 1),
        'Total_Sleep_Time_min': round(tst_min, 1),
        'Sleep_Efficiency_pct': round(se, 2),
        'Sleep_Onset_Latency_min': round(sol_min, 1),
        'WASO_min': round(waso_min, 1),
        'Awakenings_count': awakenings,
        'Stage_Percentages': stage_percentages,
        'Stage_Durations_min': stage_durations
    }

# Example run
if __name__ == '__main__':
    eeg, fs, stages = load_psg_and_hypnogram(
        'sleep-cassette/SC4001E0-PSG.edf', 
        'sleep-cassette/SC4001EC-Hypnogram.edf'
    )
    metrics = compute_clinical_sleep_metrics(stages)
    print("Computed Sleep Quality Metrics for SC4001 Night 1:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
```

---

## 11. Winning Strategies for the Hackathon

1. **Leverage Temporal Continuity (Context is King):**
   * Sleep stages do not jump randomly. An epoch of N2 is almost always preceded and followed by N2 or N3.
   * Adding a Bidirectional LSTM or simple sliding window context ($t-2, t-1, t, t+1, t+2$) over your predictions improves classification accuracy by up to 8%.
2. **Combine Subject Metadata with Signal Features:**
   * Merge `age` and `sex` from `SC-subjects.xls` and `ST-subjects.xls`. Age strongly modulates Delta wave amplitude and sleep spindle density.
3. **Multi-Task Learning:**
   * If the hackathon requires predicting a continuous Sleep Quality Score, train your network to simultaneously predict the 5-class sleep stage (auxiliary loss) and the global score (primary loss).
4. **Use Established Deep Architectures:**
   * If deep learning is permitted, adapt **TinySleepNet** or **U-Sleep**, which are specifically benchmarked and known to achieve $>84\%$ macro accuracy on Sleep-EDF.
