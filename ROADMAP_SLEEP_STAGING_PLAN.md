# Sleep Stage Staging Roadmap: 30-Second Epoch Classification

---

## Architecture & Strategic Overview

The target is **Automated Sleep Staging**: classifying continuous **30-second epochs** of physiological signals into **5 AASM classes**:
* `0`: **Wake (W)**
* `1`: **N1 (Light Sleep)**
* `2`: **N2 (Stable Sleep)**
* `3`: **N3 (Slow Wave / Deep Sleep)** (Stages 3 & 4 combined)
* `4`: **REM (Rapid Eye Movement)**

```
Input: Raw PSG Signal (EEG Fpz-Cz, EEG Pz-Oz, EOG horizontal)
               │
               ▼
[Step 1] Ingestion & Preprocessing
         - 24h Wake Trimming (30 min buffer before first sleep & after last sleep)
         - Bandpass Filtering (0.5 – 35 Hz) + 50 Hz Notch Filter
         - 30s Windowing: 3000 samples per epoch @ 100 Hz
               │
               ├─────────────────────────────────────────────┐
               ▼                                             ▼
[Track A] Feature-Engineered Baseline          [Track B] End-to-End Deep Learning
         - Band Powers (Welch PSD)                       - 1D-CNN (Local intra-epoch features)
         - Hjorth Parameters & Entropy                   - BiLSTM/Transformer (Inter-epoch context)
         - Context Windows (t-1, t, t+1)                 - Loss: Weighted Cross-Entropy / Focal Loss
         - Classifier: LightGBM / XGBoost                - Reference: TinySleepNet / DeepSleepNet
               │                                             │
               └──────────────────────┬──────────────────────┘
                                      ▼
[Step 3] Post-Processing & Temporal Smoothing
         - Transition Matrix / Hidden Markov Model (HMM) Viterbi Decoding
         - Smoothing out biologically impossible transitions (e.g. N3 -> REM -> N3 in 30s)
                                      ▼
[Step 4] Validation & Evaluation
         - GroupKFold(5) grouped by Subject ID (Strict Zero-Leakage)
         - Metrics: Macro-F1, Cohen's Kappa (κ), Per-Class F1, Confusion Matrix
                                      ▼
[Step 5] Downstream Sleep Quality Derivation
         - Compute Sleep Efficiency (SE), WASO, TST, SOL, SFI from predicted hypnogram
```

---

## Step-by-Step Execution Plan

### Step 1: Data Preprocessing & Trimming Pipeline
* **Objective:** Clean raw signals, isolate sleep periods, and create standard 30s arrays.
* **Key Tasks:**
  1. Parse `.edf` files using `pyedflib`.
  2. Map R&K labels to 5 AASM classes; drop `Movement time` and `?`.
  3. **In-bed Wake Trimming:** Only keep 30 minutes of Wake before the first non-wake epoch and 30 minutes of Wake after the last non-wake epoch.
  4. Apply a **0.5 – 35 Hz Butterworth Bandpass Filter** (order 4, zero-phase `scipy.signal.filtfilt`) and a **50 Hz Notch Filter**.
  5. Segment signals into $30 \times 100 = 3000$ points per epoch.
  6. Standardize per recording using Robust Scaler (median and interquartile range) to avoid outlier distortion.
* **Deliverable:** Preprocessing script producing preprocessed `.npz` or `.parquet` files for fast caching.

---

### Step 2: Track A — Fast Tabular Baseline (LightGBM / XGBoost)
* **Objective:** Establish an immediate, strong baseline within 1–2 hours.
* **Feature Extraction per 30s Epoch:**
  * **Frequency Domain (via `scipy.signal.welch`):**
    * Delta ($0.5–4$ Hz), Theta ($4–8$ Hz), Alpha ($8–12$ Hz), Sigma ($12–16$ Hz), Beta ($16–30$ Hz).
    * Relative band powers and power ratios ($\frac{\text{Delta}}{\text{Theta}}$, $\frac{\text{Delta}}{\text{Beta}}$, $\frac{\text{Alpha}}{\text{Delta}}$).
  * **Signal Complexity:** Hjorth Activity, Mobility, Complexity; Spectral Entropy.
  * **Time Domain:** Mean, standard deviation, skewness, kurtosis, zero-crossing rate.
  * **Temporal Context:** Concatenate features of epoch $t-1$, $t$, and $t+1$ (tripling the feature vector).
  * **Demographics:** Append `age` and `sex` from `SC-subjects.xls` / `ST-subjects.xls`.
* **Model Training:** LightGBM multi-class classifier with `class_weight='balanced'`.
* **Expected Performance:** ~78–81% Accuracy, Macro-F1 ~0.72–0.75.

---

### Step 3: Track B — Deep Learning Sequence Architecture
* **Objective:** High-scoring, publication-grade model.
* **Model Architecture (TinySleepNet style):**
  1. **Intra-Epoch Feature Extractor (1D-CNN):**
     * Two parallel or sequential convolutional branches:
       * Small filter branch (kernel size ~ 0.5s = 50 samples): captures high-frequency waves (spindles, beta).
       * Large filter branch (kernel size ~ 4s = 400 samples): captures slow waves (delta, theta).
     * Batch Normalization + ReLU + Max Pooling + Dropout.
  2. **Inter-Epoch Temporal Model (Sequence Model):**
     * Bi-directional LSTM (hidden dimension 128) over sequences of $L$ consecutive epochs (e.g., $L = 20$ or full night).
     * Residual connections between CNN representations and LSTM outputs.
  3. **Loss Function:**
     * Weighted Cross-Entropy or Multi-Class Focal Loss to counter class imbalance ($N1 \approx 5\%$, $N2 \approx 50\%$).
* **Expected Performance:** ~84–86% Accuracy, Macro-F1 ~0.78–0.82.

---

### Step 4: Strict Validation Setup (Zero-Leakage)
* **Grouping:** Use `sklearn.model_selection.GroupKFold(n_splits=5)`.
* **Group Column:** `subject_id` (Never split by file or epoch).
* **Evaluation Metrics:**
  * **Primary:** Macro-Averaged F1-Score (unweighted mean of F1 across all 5 classes).
  * **Secondary:** Cohen's Kappa ($\kappa$) and Overall Accuracy.
  * **Diagnostic:** 5x5 Confusion Matrix to analyze confusion between N1 vs W and N2 vs N3.

---

### Step 5: Post-Processing & Temporal Smoothing
* **Problem:** Independent epoch classifiers make sporadic, non-physiological classification switches (e.g. $N3 \rightarrow W \rightarrow N3$ in a 30-second interval).
* **Solution:**
  1. **Hidden Markov Model (HMM) or Viterbi Decoding:** Fit transition probabilities $P(S_{t} \mid S_{t-1})$ on training hypnograms and use Viterbi decoding over predicted class probabilities.
  2. **Median Filtering:** Apply a 1D median filter of window size 3 or 5 epochs to smooth isolated noise spikes.

---

### Step 6: Derive Sleep Quality Indices
* Using the predicted 30s hypnograms, calculate:
  * **Sleep Efficiency (SE %)**: $\frac{\text{TST}}{\text{TIB}} \times 100\%$
  * **Sleep Onset Latency (SOL)**: Minutes from lights off to first sleep epoch.
  * **Wake After Sleep Onset (WASO)**: Minutes of wake after initial sleep onset.
  * **Deep Sleep %**: Percentage of total sleep in N3.
  * **Sleep Fragmentation Index (SFI)**: Awakenings per hour of sleep.
