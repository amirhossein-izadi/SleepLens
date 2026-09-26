# SleepLens — Regime 3 Plan: Combined & Cross-Domain Generalization Framework

---

## 1. Executive Summary & Big-Picture Vision

**Regime 3** encompasses the **entire unified dataset: 197 polysomnographic recordings across 100 distinct subjects** (totaling **237,942 epochs** and **1,982.85 hours** of monitored sleep).

This regime unifies:
1. **78 Healthy Ambulatory Subjects** (Ages 25–101, home environment, natural circadian cycles).
2. **22 Hospital Inpatient Subjects** (Ages 18–79, clinical sleep-onset difficulty, double-blind Temazepam vs. Placebo).

### Why Regime 3 is Crucial for Competition Success
* **Maximum Statistical Power**: 237,942 clean epochs provide sufficient volume to train deep sequence models without overfitting.
* **Clinical Transferability & Domain Robustness**: In real-world medical AI, an algorithm trained in one hospital or device must generalize to patients at home and vice versa. Regime 3 provides the exact testbed to prove cross-domain generalization.

---

## 2. Universal Harmonized Channel Backbone

To ensure compatibility across all 197 recordings and 100 subjects, Regime 3 operates on the **standardized tri-channel montage** recorded identically at **100 Hz**:

```
Input Epoch Tensor: Shape (Batch, Channels=3, Samples=3000)
├── Channel 0: EEG Fpz-Cz     (100 Hz, Frontal-Central Brain Activity)
├── Channel 1: EEG Pz-Oz      (100 Hz, Parietal-Occipital Alpha Rhythm)
└── Channel 2: EOG horizontal (100 Hz, Eye Movement Dynamics)
```

*(Note: Single-channel evaluation on `EEG Fpz-Cz` alone is also maintained as an official literature baseline).*

---

## 3. The Three Experimental Benchmarks in Regime 3

```
                                 Regime 3 Framework
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
  [Benchmark 3A]                   [Benchmark 3B]                   [Benchmark 3C]
Unified Master Model           Zero-Shot Domain Shift          Domain Adaptation & Transfer
Train & evaluate across        Train on 78 Home subjects ->    Pre-train on 153 Home records ->
all 100 subjects using         Zero-Shot test on 22 Hospital   Fine-tune on Hospital records
5-Fold GroupKFold              patients (and vice versa)       (Measure adaptation gain)
```

### Benchmark 3A: Unified Master Model (Full Dataset Benchmark)
* **Goal**: Maximize macro-performance across the entire combined population.
* **Protocol**: 5-Fold `GroupKFold` grouped strictly by `subject_id` (20 subjects per test fold, stratified across age, sex, and cohort).
* **Target Metric**: **Macro-F1 $\ge 0.84$**, **Overall Accuracy $\ge 86\%$**, **Cohen's $\kappa \ge 0.80$**.

### Benchmark 3B: Cross-Domain Generalization (Zero-Shot Transfer)
* **Experiment 1 (Home $\rightarrow$ Hospital)**:
  * **Train on**: 153 Sleep-Cassette recordings (78 healthy home subjects).
  * **Evaluate on**: 44 Sleep-Telemetry recordings (22 hospital insomniac patients).
  * *Research Question*: How well does a model trained on healthy natural sleep handle patients with sleep latency disorders and hypnotic medications?
* **Experiment 2 (Hospital $\rightarrow$ Home)**:
  * **Train on**: 44 Sleep-Telemetry recordings (22 hospital subjects).
  * **Evaluate on**: 153 Sleep-Cassette recordings (78 healthy home subjects).
  * *Research Question*: Can a small clinical dataset generalize to a broad healthy population spanning ages 25 to 101?

### Benchmark 3C: Transfer Learning & Domain Adaptation
* **Protocol**: Pre-train the 1D-CNN + BiLSTM feature backbone on the 153 home recordings. Freeze or fine-tune with a low learning rate ($10^{-5}$) on a subset of the hospital telemetry data.
* *Target Metric*: Demonstrate $+3\%$ to $+5\%$ Macro-F1 improvement over training from scratch on the smaller clinical cohort.

---

## 4. Dissecting the Sources of Domain Shift

When transferring between Cassette and Telemetry, models encounter three distinct domain shifts:

| Domain Dimension | Home Cohort (`sleep-cassette`) | Hospital Cohort (`sleep-telemetry`) | Engineering Mitigation |
| :--- | :--- | :--- | :--- |
| **Environmental Shift** | Natural bedroom, low ambient anxiety | Hospital bed, clinical monitors, unfamiliar room | Per-record robust IQR normalization |
| **Pathological Shift** | Healthy volunteers (no sleep complaints) | Clinical difficulty initiating sleep (insomnia) | Class-balanced Focal Loss |
| **Pharmacological Shift**| Drug-free baseline | Temazepam (elevated spindles & beta, reduced delta) | Multi-scale temporal CNN filters |
| **Hardware Shift** | Analog magnetic cassette tape (1989) | Radio-frequency wireless broadcast (1994) | Butterworth bandpass + Notch filtering |

---

## 5. Model Architecture for Regime 3: The Ensemble Strategy

To achieve top competition placement, deploy a **Hybrid Multi-Model Ensemble**:

```
                         Input: 3-Channel 30s Epoch
                       (EEG Fpz-Cz, EEG Pz-Oz, EOG)
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
       [Model 1: Deep Learning]                 [Model 2: Tabular GBDT]
      TinySleepNet / U-Sleep                   LightGBM / CatBoost
      (Dual-scale 1D-CNN + BiLSTM)             (Welch PSD + Hjorth + Context)
                 │                                       │
                 ▼                                       ▼
        Predicted Probabilities                 Predicted Probabilities
        P_deep: (N, 5)                          P_gbdt: (N, 5)
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     ▼
                      [Probability Blending / Stacking]
                         P_final = 0.65 * P_deep + 0.35 * P_gbdt
                                     │
                                     ▼
                      [Phase 4: HMM Viterbi Sequence Decoder]
                                     │
                                     ▼
                      Final 5-Class Staging Hypnogram
```

---

## 6. Implementation Code: Cross-Domain Evaluation Harness

```python
import numpy as np
from sklearn.metrics import classification_report, f1_score, cohen_kappa_score

def evaluate_cross_domain_transfer(train_records, test_records, model_trainer, predictor):
    """
    Evaluates cross-domain generalization:
    Trains on train_records (e.g. all Cassette) and evaluates on test_records (e.g. all Telemetry).
    """
    print(f"Training on {len(train_records)} source domain records...")
    # 1. Aggregate source training data
    X_train_list, y_train_list = [], []
    for f in train_records:
        d = np.load(f)
        # 3 channels: Fpz-Cz, Pz-Oz, EOG
        x = np.stack([d['x_fpz'], d['x_pz'], d['x_eog']], axis=1) # (N, 3, 3000)
        X_train_list.append(x)
        y_train_list.append(d['y'])
        
    X_train = np.concatenate(X_train_list, axis=0)
    y_train = np.concatenate(y_train_list, axis=0)

    # 2. Train model on source domain
    model = model_trainer(X_train, y_train)

    # 3. Evaluate on target domain
    print(f"Evaluating zero-shot transfer on {len(test_records)} target domain records...")
    all_y_true, all_y_pred = [], []
    for f in test_records:
        d = np.load(f)
        x_test = np.stack([d['x_fpz'], d['x_pz'], d['x_eog']], axis=1)
        y_test = d['y']
        
        preds = predictor(model, x_test)
        all_y_true.append(y_test)
        all_y_pred.append(preds)

    y_true = np.concatenate(all_y_true)
    y_pred = np.concatenate(all_y_pred)

    macro_f1 = f1_score(y_true, y_pred, average='macro')
    kappa = cohen_kappa_score(y_true, y_pred)
    acc = np.mean(y_true == y_pred)

    print("\n=== ZERO-SHOT CROSS-DOMAIN RESULTS ===")
    print(f"Target Accuracy: {acc:.4f}")
    print(f"Target Macro-F1: {macro_f1:.4f}")
    print(f"Target Cohen's Kappa: {kappa:.4f}")
    print(classification_report(y_true, y_pred, target_names=['W', 'N1', 'N2', 'N3', 'REM'], digits=4))
    
    return {'acc': acc, 'macro_f1': macro_f1, 'kappa': kappa}
```

---

## 7. Action Items & Verification Targets

1. **Dataset Unification**: Complete validation of all 197 `.npz` files with the harmonized 3-channel structure (`x_fpz`, `x_pz`, `x_eog`).
2. **Benchmark 3A (Master Model)**: Train Unified LightGBM and Unified 1D-CNN+BiLSTM on all 100 subjects; establish state-of-the-art Macro-F1 $> 0.84$.
3. **Benchmark 3B (Domain Transfer)**: Execute Home $\rightarrow$ Hospital transfer. Quantify the domain gap ($\Delta F1 = F1_{\text{in-domain}} - F1_{\text{cross-domain}}$).
4. **Sleep Quality Generalization**: Verify that predicted sleep efficiency (SE %) and WASO correlate strongly ($r > 0.85$) with ground truth across both cohorts.
