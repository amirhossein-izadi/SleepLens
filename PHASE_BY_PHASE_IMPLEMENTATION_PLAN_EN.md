# Phase-by-Phase Implementation Plan: Automated Sleep Staging & Quality Prediction

---

## Architecture Overview

```
                      Raw .edf Files (PSG + Hypnogram)
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │  PHASE 1: Data Ingestion, Trimming & Signal Prep       │
        │  • Match PSG & Hypnogram pairs                         │
        │  • Map R&K -> 5-Class AASM (W, N1, N2, N3, REM)        │
        │  • 24h Wake Trimming (30 min buffer)                   │
        │  • Bandpass (0.5–35 Hz) + 50 Hz Notch Filter           │
        │  • Epoching (30s @ 100 Hz = 3,000 samples)             │
        │  • Robust Normalization & .npz caching                 │
        └────────────────────────────┬───────────────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
  ┌───────────────────────────────┐     ┌───────────────────────────────┐
  │ PHASE 2: Tabular Baseline     │     │ PHASE 3: Deep Learning        │
  │ • Welch PSD Band Powers       │     │ • 1D-CNN Intra-Epoch Encoder  │
  │ • Hjorth Complexity & Entropy │     │ • BiLSTM Inter-Epoch Context  │
  │ • Context Window (t-1, t, t+1)│     │ • Weighted CE / Focal Loss    │
  │ • Metadata (Age, Sex)         │     │ • End-to-end Raw Waveform     │
  │ • LightGBM / XGBoost Model    │     │ • TinySleepNet Architecture   │
  └──────────────┬────────────────┘     └───────────────┬───────────────┘
                 │                                      │
                 └───────────────────┬──────────────────┘
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │  PHASE 4: Temporal Smoothing & Post-Processing         │
        │  • Empirical Transition Matrix Calculation             │
        │  • HMM / Viterbi Sequence Decoding                     │
        │  • 1D Median Filter for Noise Elimination              │
        └────────────────────────────┬───────────────────────────┘
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │  PHASE 5: Zero-Leakage Validation Harness              │
        │  • Strict GroupKFold(5) by Subject ID                  │
        │  • Macro F1, Cohen's Kappa (κ), Per-Class F1           │
        │  • Confusion Matrix & Error Profiling                  │
        └────────────────────────────┬───────────────────────────┘
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │  PHASE 6: Downstream Sleep Quality Derivation          │
        │  • Compute SE%, TST, TIB, SOL, WASO, SFI               │
        │  • Stage Percentages (% N3 Deep Sleep, % REM)          │
        │  • Regression / Correlation vs Ground Truth (MAE, R²)  │
        └────────────────────────────────────────────────────────┘
```

---

## Phase 1: Data Ingestion, Trimming & Signal Preprocessing

### 1.1 Objective & Critical Challenges
Raw Polysomnography (PSG) data in EDF files contains non-standardized durations, European 50 Hz power-line contamination, and—most critically—**up to 15 hours of awake daytime activity** in the `sleep-cassette/` sub-dataset. 
Phase 1 transforms these raw streams into synchronized, artifact-filtered, normalized 30-second epoch arrays.

### 1.2 Technical Specifications
* **Input:** `SC4ssNE0-PSG.edf` + `SC4ssNEy-Hypnogram.edf` (or `ST7...`).
* **Output:** Preprocessed `.npz` archive per recording containing:
  * `x`: Array of shape `(N_epochs, 3000)` representing filtered `EEG Fpz-Cz` (and optionally `Pz-Oz`, `EOG`).
  * `y`: Array of shape `(N_epochs,)` with integer labels $\in \{0, 1, 2, 3, 4\}$.
  * `fs`: Sampling rate ($100$ Hz).
  * `subject_id`: Integer identifier for GroupKFold validation.
* **Filter Specifications:**
  * Bandpass: 4th-order zero-phase Butterworth filter, passband $0.5 - 35.0$ Hz.
  * Notch: 2nd-order IIR notch filter at $50.0$ Hz ($Q = 30$).
* **AASM Label Mapping:**
  ```
  'Sleep stage W' -> 0 (Wake)
  'Sleep stage 1' -> 1 (N1)
  'Sleep stage 2' -> 2 (N2)
  'Sleep stage 3' -> 3 (N3)
  'Sleep stage 4' -> 3 (N3 - merged into N3)
  'Sleep stage R' -> 4 (REM)
  'Movement time' -> Dropped
  'Sleep stage ?' -> Dropped
  ```
* **In-Bed Wake Trimming:**
  * Find the index of the first non-wake epoch ($t_{\text{first}}$) and last non-wake epoch ($t_{\text{last}}$).
  * Keep only $30 \text{ min} = 60 \text{ epochs}$ of Wake prior to $t_{\text{first}}$, and $60 \text{ epochs}$ of Wake after $t_{\text{last}}$.

### 1.3 Step-by-Step Implementation Code

```python
import os
import glob
import pyedflib
import numpy as np
from scipy.signal import butter, filtfilt, iirnotch

def create_filters(fs=100.0, lowcut=0.5, highcut=35.0, notch_freq=50.0, notch_q=30.0):
    nyq = 0.5 * fs
    b_band, a_band = butter(4, [lowcut / nyq, highcut / nyq], btype='band')
    b_notch, a_notch = iirnotch(notch_freq / nyq, notch_q)
    return (b_band, a_band), (b_notch, a_notch)

def preprocess_single_record(psg_path, hyp_path, output_dir, epoch_sec=30, fs_target=100):
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.basename(psg_path).replace('-PSG.edf', '')
    out_file = os.path.join(output_dir, f"{base_name}.npz")
    if os.path.exists(out_file):
        return out_file

    # 1. Read Hypnogram Annotations
    hyp = pyedflib.EdfReader(hyp_path)
    onsets, durations, descriptions = hyp.readAnnotations()
    hyp.close()

    stage_map = {
        'Sleep stage W': 0,
        'Sleep stage 1': 1,
        'Sleep stage 2': 2,
        'Sleep stage 3': 3,
        'Sleep stage 4': 3,
        'Sleep stage R': 4
    }

    epoch_labels = []
    for onset, dur, desc in zip(onsets, durations, descriptions):
        n_ep = int(round(dur / epoch_sec))
        label = stage_map.get(desc, -1) # -1 for ?, Movement, etc.
        epoch_labels.extend([label] * n_ep)
    epoch_labels = np.array(epoch_labels)

    # 2. Read PSG Signal (EEG Fpz-Cz)
    psg = pyedflib.EdfReader(psg_path)
    labels = psg.getSignalLabels()
    ch_idx = labels.index('EEG Fpz-Cz')
    fs = psg.getSampleFrequency(ch_idx)
    raw_signal = psg.readSignal(ch_idx)
    psg.close()

    # 3. Apply Filters
    (b_band, a_band), (b_notch, a_notch) = create_filters(fs=fs)
    filtered = filtfilt(b_band, a_band, raw_signal)
    filtered = filtfilt(b_notch, a_notch, filtered)

    # 4. Segment into 30s epochs
    samples_per_epoch = int(epoch_sec * fs)
    total_epochs = min(len(filtered) // samples_per_epoch, len(epoch_labels))
    
    x = filtered[:total_epochs * samples_per_epoch].reshape(total_epochs, samples_per_epoch)
    y = epoch_labels[:total_epochs]

    # 5. Trim 24h Wake (Cassette study artifact)
    sleep_indices = np.where((y >= 1) & (y <= 4))[0]
    if len(sleep_indices) == 0:
        return None # No sleep found

    first_sleep = sleep_indices[0]
    last_sleep = sleep_indices[-1]
    pad = int(30 * 60 / epoch_sec) # 60 epochs (30 min)

    start_idx = max(0, first_sleep - pad)
    end_idx = min(total_epochs, last_sleep + pad + 1)

    x_trimmed = x[start_idx:end_idx]
    y_trimmed = y[start_idx:end_idx]

    # Filter out unscored epochs (-1)
    valid_mask = y_trimmed != -1
    x_valid = x_trimmed[valid_mask]
    y_valid = y_trimmed[valid_mask]

    # 6. Robust per-record scaling
    median = np.median(x_valid)
    iqr = np.percentile(x_valid, 75) - np.percentile(x_valid, 25)
    iqr = iqr if iqr > 1e-6 else 1.0
    x_scaled = (x_valid - median) / iqr

    # Extract subject ID for GroupKFold
    # Pattern: SC4001E0 -> subject 400; ST7011J0 -> subject 701
    subj_str = base_name[2:5]
    subject_id = int(subj_str)

    np.savez_compressed(
        out_file,
        x=x_scaled.astype(np.float32),
        y=y_valid.astype(np.int64),
        subject_id=subject_id,
        fs=fs
    )
    return out_file
```

### 1.4 Verification & Quality Checks
1. Check output shape: `x.shape[1]` must strictly equal `3000` samples.
2. Confirm label distribution: All classes `0, 1, 2, 3, 4` should be present across recordings.
3. Check signal amplitude: Post-IQR values should predominantly fall in the range $[-5.0, +5.0]$.

---

## Phase 2: Feature Engineering & Tabular Baseline (Track A)

### 2.1 Objective
Before diving into multi-hour deep learning runs, build a high-performance tabular baseline using **LightGBM / XGBoost**. This establishes an interpretable benchmark and validates the feature distributions.

### 2.2 Feature Extraction per 30-Second Epoch ($F_s = 100$ Hz)
* **Power Spectral Density (Welch's method):**
  * Frequency resolution $\Delta f = 0.25$ Hz (window length $4$ s = 400 samples, 50% overlap).
  * Compute absolute and relative power in standard physiological frequency bands:
    * Delta ($\delta$): $0.5 - 4.0$ Hz (Deep sleep biomarker).
    * Theta ($\theta$): $4.0 - 8.0$ Hz (Drowsiness, N1).
    * Alpha ($\alpha$): $8.0 - 12.0$ Hz (Wake with eyes closed in Pz-Oz).
    * Sigma ($\sigma$): $12.0 - 16.0$ Hz (Sleep spindles in N2).
    * Beta ($\beta$): $16.0 - 30.0$ Hz (Cortical activation, wake).
  * Spectral Ratios: $\frac{\text{Delta}}{\text{Theta}}$, $\frac{\text{Delta}}{\text{Beta}}$, $\frac{\text{Theta}}{\text{Alpha}}$.
* **Signal Complexity & Information:**
  * **Hjorth Activity:** $\text{Var}(x(t))$
  * **Hjorth Mobility:** $\sqrt{\frac{\text{Var}(x'(t))}{\text{Var}(x(t))}}$
  * **Hjorth Complexity:** $\frac{\text{Mobility}(x'(t))}{\text{Mobility}(x(t))}$
  * **Spectral Entropy:** $H_s = -\sum p_i \log_2(p_i)$ over normalized PSD.
* **Time-Domain Statistics:**
  * Mean, Standard Deviation, Skewness, Kurtosis, Zero-Crossing Rate (ZCR).
* **Context Windowing (Markovian Temporal Dynamics):**
  * Sleep architecture is continuous. An epoch's stage depends strongly on adjacent epochs.
  * For epoch $t$, concatenate features of $t-1$, $t$, and $t+1$.

### 2.3 Step-by-Step Implementation Code

```python
import numpy as np
import scipy.signal as signal
from scipy.stats import skew, kurtosis
import lightgbm as lgb
from sklearn.metrics import classification_report, f1_score

def compute_epoch_features(epoch, fs=100.0):
    # 1. Time-Domain
    mean_val = np.mean(epoch)
    std_val = np.std(epoch)
    skew_val = skew(epoch)
    kurt_val = kurtosis(epoch)
    zcr = np.mean(np.diff(epoch > 0) != 0)

    # 2. Hjorth Parameters
    d1 = np.diff(epoch)
    d2 = np.diff(d1)
    var_zero = np.var(epoch) + 1e-8
    var_d1 = np.var(d1) + 1e-8
    var_d2 = np.var(d2) + 1e-8
    
    activity = var_zero
    mobility = np.sqrt(var_d1 / var_zero)
    complexity = np.sqrt(var_d2 / var_d1) / mobility

    # 3. Frequency-Domain via Welch PSD
    freqs, psd = signal.welch(epoch, fs=fs, nperseg=int(4 * fs), noverlap=int(2 * fs))
    total_power = np.sum(psd) + 1e-8

    def bandpower(f_low, f_high):
        idx = np.where((freqs >= f_low) & (freqs < f_high))[0]
        return np.sum(psd[idx])

    delta = bandpower(0.5, 4.0)
    theta = bandpower(4.0, 8.0)
    alpha = bandpower(8.0, 12.0)
    sigma = bandpower(12.0, 16.0)
    beta = bandpower(16.0, 30.0)

    # Relative Powers
    rel_delta = delta / total_power
    rel_theta = theta / total_power
    rel_alpha = alpha / total_power
    rel_sigma = sigma / total_power
    rel_beta = beta / total_power

    # Spectral Entropy
    psd_norm = psd / total_power
    spec_entropy = -np.sum(psd_norm * np.log2(psd_norm + 1e-12))

    return np.array([
        mean_val, std_val, skew_val, kurt_val, zcr,
        activity, mobility, complexity,
        rel_delta, rel_theta, rel_alpha, rel_sigma, rel_beta,
        spec_entropy,
        (delta + 1e-8) / (theta + 1e-8),
        (delta + 1e-8) / (beta + 1e-8)
    ])

def add_temporal_context(features):
    """Concatenates (t-1, t, t+1) features for each epoch."""
    n_epochs, n_feat = features.shape
    context_features = np.zeros((n_epochs, 3 * n_feat), dtype=np.float32)
    for i in range(n_epochs):
        prev_f = features[i - 1] if i > 0 else features[i]
        curr_f = features[i]
        next_f = features[i + 1] if i < n_epochs - 1 else features[i]
        context_features[i] = np.concatenate([prev_f, curr_f, next_f])
    return context_features
```

---

## Phase 3: Deep Learning Sequence Modeling (Track B)

### 3.1 Objective & Model Topology
To push performance beyond 84% accuracy, implement an end-to-end deep neural network that directly takes the raw 3,000-sample waveform as input. The network combines:
1. **Intra-Epoch Feature Extractor:** A multi-scale 1D Convolutional Neural Network (CNN) that learns both high-frequency morphology (spindles, K-complexes) and low-frequency oscillations (delta waves).
2. **Inter-Epoch Sequence Context:** A Bidirectional LSTM (BiLSTM) or Gated Recurrent Unit (GRU) operating over consecutive sequences of epochs to learn sleep-stage transitions.

```
Raw Waveform: (Batch, Seq_Len=20, Channels=1, Samples=3000)
                              │
                              ▼
           [Time-Distributed 1D-CNN Encoder]
           ├── Small Filter Branch (Kernel=50, Stride=6) -> Spindles, Beta
           ├── Large Filter Branch (Kernel=400, Stride=50) -> Delta Waves
           ├── Max Pooling + Dropout + Concat
           └── Output: (Batch, Seq_Len=20, Embed_Dim=256)
                              │
                              ▼
           [Bidirectional LSTM / Sequence Context]
           ├── BiLSTM(input_size=256, hidden_size=128, num_layers=2)
           └── Output: (Batch, Seq_Len=20, Hidden=256)
                              │
                              ▼
           [Dense Classification Head]
           └── Linear(256 -> 5) + Softmax
```

### 3.2 PyTorch Implementation Architecture

```python
import torch
import torch.nn as nn

class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, stride, pool_size):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(in_channels, out_channels, kernel_size, stride=stride, padding=kernel_size//2),
            nn.BatchNorm1d(out_channels),
            nn.ReLU(),
            nn.MaxPool1d(pool_size, stride=pool_size),
            nn.Dropout(0.2)
        )
    def forward(self, x):
        return self.conv(x)

class IntraEpochEncoder(nn.Module):
    """Multi-scale 1D-CNN feature extractor for a single 30s epoch (3000 samples)."""
    def __init__(self):
        super().__init__()
        # Branch 1: High frequency / fine temporal resolution
        self.branch1 = nn.Sequential(
            ConvBlock(1, 64, kernel_size=50, stride=6, pool_size=8),
            ConvBlock(64, 128, kernel_size=8, stride=1, pool_size=4),
            ConvBlock(128, 128, kernel_size=8, stride=1, pool_size=2)
        )
        # Branch 2: Low frequency / coarse temporal resolution
        self.branch2 = nn.Sequential(
            ConvBlock(1, 64, kernel_size=400, stride=50, pool_size=4),
            ConvBlock(64, 128, kernel_size=6, stride=1, pool_size=2),
            ConvBlock(128, 128, kernel_size=6, stride=1, pool_size=2)
        )
        self.fc = nn.Sequential(
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Dropout(0.3)
        )

    def forward(self, x):
        # x: (B, 1, 3000)
        out1 = self.branch1(x)
        out2 = self.branch2(x)
        # Global pooling and concatenation
        p1 = torch.mean(out1, dim=-1)
        p2 = torch.mean(out2, dim=-1)
        feat = torch.cat([p1, p2], dim=1) # (B, 256)
        return feat

class SleepSeqModel(nn.Module):
    """End-to-end Sequence Model over sequences of L consecutive epochs."""
    def __init__(self, num_classes=5, hidden_dim=128):
        super().__init__()
        self.cnn_encoder = IntraEpochEncoder()
        self.lstm = nn.LSTM(
            input_size=256,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.3
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64),
            nn.ReLU(),
            nn.Linear(64, num_classes)
        )

    def forward(self, x_seq):
        # x_seq: (Batch, Seq_Len, 1, 3000)
        B, L, C, S = x_seq.shape
        x_flat = x_seq.view(B * L, C, S)
        feats = self.cnn_encoder(x_flat) # (B*L, 256)
        feats = feats.view(B, L, -1)     # (B, L, 256)

        lstm_out, _ = self.lstm(feats)   # (B, L, hidden_dim*2)
        logits = self.classifier(lstm_out) # (B, L, num_classes)
        return logits
```

---

## Phase 4: Temporal Smoothing & Post-Processing

### 4.1 Objective
Classifiers evaluated per-epoch make occasional physiologically invalid errors (such as predicting $N3 \rightarrow W \rightarrow N3$ within a single 30-second window, which violates sleep continuity). Post-processing filters out high-frequency prediction noise and enforces realistic transition dynamics.

### 4.2 Techniques
1. **Transition Matrix & Viterbi Decoding:**
   * Calculate the empirical transition probability matrix $A_{i,j} = P(S_t = j \mid S_{t-1} = i)$ across all training hypnograms.
   * Combine classifier emission probabilities $P(S_t \mid X_t)$ with transition matrix $A$ to find the globally optimal state sequence using the Viterbi algorithm.
2. **Median Filter:**
   * Apply a 1D median filter of window size 3 or 5 epochs over the predicted integer sequence.

### 4.3 Implementation Code

```python
import numpy as np
from scipy.signal import medfilt

def build_transition_matrix(y_true_list, num_classes=5):
    """Computes empirical sleep stage transition probabilities."""
    counts = np.zeros((num_classes, num_classes)) + 1e-4 # Laplace smoothing
    for seq in y_true_list:
        for i in range(len(seq) - 1):
            s_from = seq[i]
            s_to = seq[i + 1]
            if 0 <= s_from < num_classes and 0 <= s_to < num_classes:
                counts[s_from, s_to] += 1
    trans_matrix = counts / np.sum(counts, axis=1, keepdims=True)
    return trans_matrix

def viterbi_decode(prob_matrix, trans_matrix):
    """
    Finds maximum likelihood sequence of sleep stages.
    prob_matrix: (N_epochs, 5) predicted probabilities from model
    trans_matrix: (5, 5) state transition matrix
    """
    T, K = prob_matrix.shape
    log_trans = np.log(trans_matrix + 1e-12)
    log_emiss = np.log(prob_matrix + 1e-12)

    viterbi = np.zeros((T, K))
    backpointer = np.zeros((T, K), dtype=int)

    # Initialization
    viterbi[0] = log_emiss[0]

    # Recursion
    for t in range(1, T):
        for j in range(K):
            scores = viterbi[t - 1] + log_trans[:, j] + log_emiss[t, j]
            backpointer[t, j] = np.argmax(scores)
            viterbi[t, j] = np.max(scores)

    # Backtracking
    best_path = np.zeros(T, dtype=int)
    best_path[-1] = np.argmax(viterbi[-1])
    for t in range(T - 2, -1, -1):
        best_path[t] = backpointer[t + 1, best_path[t + 1]]

    return best_path
```

---

## Phase 5: Zero-Leakage Validation Harness

### 5.1 The Rule of Zero Data Leakage
* **NEVER split epochs randomly.** Epochs from the same night/subject share profound biological autocorrelation. Random splitting leaks patient identity into the validation fold, artificially inflating accuracy by 10–15% while collapsing on unseen test subjects.
* **MANDATORY:** Use **`GroupKFold(n_splits=5)`** grouped strictly on `subject_id`. All recordings belonging to the same participant (e.g. Night 1 and Night 2) must reside entirely in either Train or Validation.

### 5.2 Metrics Hierarchy
* **Primary Metric:** **Macro-averaged F1-score** ($Macro\text{-}F1 = \frac{1}{5}\sum_{c=0}^4 F1_c$). This treats all stages equally and severely penalizes models that fail on minority classes ($N1 \approx 5\%$).
* **Secondary Metric:** **Cohen's Kappa ($\kappa$)** (measures agreement corrected for chance agreement).
* **Diagnostic Metric:** $5 \times 5$ Confusion Matrix.

### 5.3 Complete Validation Harness

```python
import numpy as np
from sklearn.model_selection import GroupKFold
from sklearn.metrics import classification_report, cohen_kappa_score, confusion_matrix

def run_group_kfold_cv(X, y, groups, train_fn, predict_fn, n_splits=5):
    gkf = GroupKFold(n_splits=n_splits)
    oof_preds = np.zeros_like(y)
    fold_f1s = []
    fold_kappas = []

    print(f"Starting {n_splits}-Fold Subject-Wise Cross Validation...")

    for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups)):
        X_tr, y_tr = X[train_idx], y[train_idx]
        X_va, y_va = X[val_idx], y[val_idx]

        # Train model
        model = train_fn(X_tr, y_tr)

        # Predict probabilities and classes
        preds_va = predict_fn(model, X_va)
        oof_preds[val_idx] = preds_va

        f1 = f1_score(y_va, preds_va, average='macro')
        kappa = cohen_kappa_score(y_va, preds_va)
        fold_f1s.append(f1)
        fold_kappas.append(kappa)

        print(f"Fold {fold+1}: Macro F1 = {f1:.4f}, Cohen's Kappa = {kappa:.4f}")

    overall_f1 = f1_score(y, oof_preds, average='macro')
    overall_kappa = cohen_kappa_score(y, oof_preds)
    cm = confusion_matrix(y, oof_preds)

    print("\n=== FINAL CROSS-VALIDATION RESULTS ===")
    print(f"Overall Macro F1: {overall_f1:.4f} (Mean: {np.mean(fold_f1s):.4f} +/- {np.std(fold_f1s):.4f})")
    print(f"Overall Cohen's Kappa: {overall_kappa:.4f}")
    print("\nClassification Report:")
    print(classification_report(y, oof_preds, target_names=['W', 'N1', 'N2', 'N3', 'REM'], digits=4))
    print("\nConfusion Matrix:")
    print(cm)
    return oof_preds, fold_f1s
```

---

## Phase 6: Downstream Sleep Quality Metric Derivation

### 6.1 Objective
Once the full-night 30s hypnogram sequence is predicted, derive the clinical polysomnography (PSG) sleep quality indicators. Compare predicted vs ground-truth metrics using Mean Absolute Error (MAE) and Pearson correlation ($r$).

### 6.2 Formula Definitions
1. **Total Sleep Time (TST):**
   $$\text{TST} = \sum (\text{Epochs}_{N1, N2, N3, REM}) \times \frac{30}{60} \text{ min}$$
2. **Time in Bed (TIB):**
   $$\text{TIB} = \text{Total In-Bed Epochs} \times \frac{30}{60} \text{ min}$$
3. **Sleep Efficiency (SE %):**
   $$\text{SE} = \frac{\text{TST}}{\text{TIB}} \times 100\%$$
4. **Sleep Onset Latency (SOL):**
   $$\text{SOL} = (\text{Index of first sleep epoch} - \text{Index of lights off}) \times 0.5 \text{ min}$$
5. **Wake After Sleep Onset (WASO):**
   $$\text{WASO} = \sum (\text{Wake epochs between first and last sleep}) \times 0.5 \text{ min}$$
6. **Slow Wave Deep Sleep Ratio:**
   $$\% N3 = \frac{\text{Minutes in N3}}{\text{TST}} \times 100\%$$

### 6.3 Metric Computation Script

```python
import numpy as np

def calculate_quality_metrics(stages, epoch_sec=30):
    sleep_mask = np.isin(stages, [1, 2, 3, 4]) # N1, N2, N3, REM
    sleep_indices = np.where(sleep_mask)[0]

    if len(sleep_indices) == 0:
        return {'SE': 0.0, 'TST': 0.0, 'WASO': 0.0, 'SOL': 0.0, 'pct_N3': 0.0}

    first_sleep = sleep_indices[0]
    last_sleep = sleep_indices[-1]

    tib_min = len(stages) * (epoch_sec / 60)
    tst_min = len(sleep_indices) * (epoch_sec / 60)
    se_pct = (tst_min / tib_min) * 100.0

    sol_min = first_sleep * (epoch_sec / 60)

    # Wake between sleep onset and end
    waso_epochs = np.sum(stages[first_sleep:last_sleep+1] == 0)
    waso_min = waso_epochs * (epoch_sec / 60)

    # Stage percentages
    n3_min = np.sum(stages == 3) * (epoch_sec / 60)
    rem_min = np.sum(stages == 4) * (epoch_sec / 60)

    pct_n3 = (n3_min / tst_min) * 100.0 if tst_min > 0 else 0.0
    pct_rem = (rem_min / tst_min) * 100.0 if tst_min > 0 else 0.0

    return {
        'Sleep_Efficiency_pct': round(se_pct, 2),
        'Total_Sleep_Time_min': round(tst_min, 1),
        'Time_in_Bed_min': round(tib_min, 1),
        'WASO_min': round(waso_min, 1),
        'SOL_min': round(sol_min, 1),
        'pct_N3_Deep_Sleep': round(pct_n3, 2),
        'pct_REM': round(pct_rem, 2)
    }

def evaluate_quality_metric_prediction(true_hypnograms, pred_hypnograms):
    """Evaluates MAE between true clinical metrics and predicted metrics."""
    true_metrics = [calculate_quality_metrics(seq) for seq in true_hypnograms]
    pred_metrics = [calculate_quality_metrics(seq) for seq in pred_hypnograms]

    keys = ['Sleep_Efficiency_pct', 'Total_Sleep_Time_min', 'WASO_min', 'pct_N3_Deep_Sleep']
    results = {}
    for k in keys:
        y_true = np.array([m[k] for m in true_metrics])
        y_pred = np.array([m[k] for m in pred_metrics])
        mae = np.mean(np.abs(y_true - y_pred))
        corr = np.corrcoef(y_true, y_pred)[0, 1]
        results[k] = {'MAE': round(mae, 3), 'Pearson_r': round(corr, 3)}
    return results
```

---

## Summary Action Checklist for the Hackathon Team

| Phase | Milestone / Deliverable | Target Metric / Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Preprocessing script & cached `.npz` files | 197 clean `.npz` files, $3000$ points/epoch | **Critical (Do First)** |
| **Phase 2** | Feature extraction & LightGBM baseline | Macro-F1 $> 0.74$, Overall Accuracy $> 79\%$ | **High** |
| **Phase 3** | TinySleepNet 1D-CNN + BiLSTM model | Macro-F1 $> 0.80$, Overall Accuracy $> 84\%$ | **High** |
| **Phase 4** | HMM / Viterbi post-processing | $+1.5\%$ to $+2.5\%$ boost in Macro-F1 | **Medium** |
| **Phase 5** | Strict GroupKFold(5) validation pipeline | Zero leakage, unbiased validation scores | **Critical** |
| **Phase 6** | Polysomnography sleep quality calculator | Derived SE%, WASO, SOL with MAE reported | **High** |
