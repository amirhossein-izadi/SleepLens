# FINAL RESULTS — all models, full 197 recordings, BENCHMARK_30 Macro-F1

Generated after all inference sweeps completed. Ground truth: `epochs_v3` valid 5-class
labels, BENCHMARK_30 window (237,936 epochs). Split: subject-atomic `folds5_v3`.

## 1. Individual models (all 197 recordings)

| Run | Model | Macro-F1 | SC | ST | N1 | N2 | N3 | REM | Wake |
|---|---|---|---|---|---|---|---|---|---|
| **E11** | **AnySleep 3ch (Fpz+Pz+EOG)** | **0.8267** | .809 | .878 | .622 | .880 | .788 | .904 | .941 |
| E11d | AnySleep Fpz+EOG (best 2-sensor) | 0.8227 | .811 | .865 | .592 | .880 | .812 | .905 | .925 |
| E11c | AnySleep 2EEG (Fpz+Pz) | 0.8134 | .797 | .863 | .594 | — | .785 | .878 | — |
| E11a | AnySleep Fpz only | 0.8015 | .790 | .844 | .549 | — | .796 | .875 | — |
| E11b | AnySleep Pz only | 0.7736 | .756 | .829 | .531 | — | .748 | .844 | — |
| E20 | RobustSleepNet Fpz | 0.7501 | .736 | .788 | .442 | .828 | .717 | .855 | .908 |
| E00 | LightGBM bandpower (OOF) | 0.6672 | — | — | .339 | .752 | .687 | .585 | .920 |
| E02c | YASA Fpz+EOG cropped | 0.5463 | .531 | .562 | .069 | .750 | .580 | .649 | .684 |
| E01 | YASA Fpz | 0.5225 | .486 | .611 | .100 | .737 | .538 | .557 | .682 |
| E02 | YASA Fpz+EOG | 0.5171 | .480 | .548 | .122 | — | .364 | .665 | — |
| E03 | YASA Pz+EOG | 0.4272 | .381 | .499 | .070 | — | .262 | .560 | — |
| E10 | SleepFMStager | PARKED | — | — | — | — | — | — | — |
| E07-E09 | SLEEPYLAND (U-Sleep/DeepResNet/SleepTransformer) | DROPPED (team decision) | | | | | | | |

## 2. Combination experiments (full 197, BENCHMARK_30)

### Equal-weight ensembles (no tuning)
| Ensemble | Macro | N1 | N3 | REM |
|---|---|---|---|---|
| **E11+E00+E11c** (AnySleep3ch + LightGBM + AnySleep2EEG) | **0.8307** | .616 | .823 | .898 |
| E11+E00+E11a+E11c (top-4) | 0.8303 | .610 | .824 | .900 |
| E11+E00+E11a (AnySleep3ch+LightGBM+Fpz) | 0.8288 | .602 | .831 | .899 |
| all five (E11+E20+E00+E11a+E11c) | 0.8279 | .596 | .825 | .898 |
| E11+E20 (top-2) | 0.8108 | .548 | .801 | .895 |
| E11 alone (best single) | 0.8267 | .622 | .788 | .904 |

**Diversity beats strength**: the weak LightGBM (0.667) *helps* (different feature space:
bandpower vs raw waveform); RSN (0.750) *hurts* (same error family as AnySleep).

### Fold-honest selection (E17/E18) — pick combo on 4 folds, score the 5th
- All 5 folds independently picked the **same** combo: AnySleep3ch + AnySleep-Fpz + AnySleep-Pz + LightGBM.
- Full metric suite for all fold-honest ensembles (materialized as `runs/E16|E17|E18`):

| Run | System | n | ALL | SC | ST | Wake | N1 | N2 | N3 | REM | kappa | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **E19** | **v2 combo: ANY3ch + ANYFpz+EOG + U-Sleep CSDP + LGBM** | 237,310 | **0.8425** | .836 | .865 | .936 | .635 | .892 | .833 | .915 | .831 | .082 |
| E19b | E19 + class bias (fold-picked) | 237,310 | 0.8417 | .835 | .868 | .932 | .638 | .891 | .833 | .915 | .827 | .083 |
| E16 | 0.7·AnySleep3ch + 0.3·RSN + bias | 237,936 | 0.8291 | .813 | .878 | .941 | .624 | .876 | .800 | .904 | .816 | .029 |
| E17 | combo equal-weight | 237,310 | 0.8315 | .820 | .872 | .938 | .610 | .884 | .825 | .901 | .820 | .094 |
| E18 | E17 + class bias (fold-picked) | 237,310 | 0.8316 | .820 | .873 | .933 | .617 | .882 | .825 | .900 | .817 | .097 |

- E17 vs E18 is a **tie** (0.8315 vs 0.8316): on the full-valid selection domain 2/5 folds pick
  bREM=0 — the bias gain is not robust; **report 0.8316**. E16 is the ST champion (.878, best
  N1 .624 / REM .904); E17/E18 are the SC champions (.820). E17/E18 lose 626 epochs vs E16
  (LightGBM feature gaps), so E16 is the only ensemble with 100% window coverage.
- Gain over best single model: **+0.005**, stable across folds (not selection noise).

### Viterbi (transition decoding) — tested, does not help
| Applied to | λ | Macro |
|---|---|---|
| E11 alone | 0.1 | 0.8259 (vs 0.8267) |
| fusion E13 | 0.1–0.5 | 0.806–0.820 (monotonically worse) |
Reason: AnySleep already has a 14-min receptive field; the transition prior is redundant.

## 3. Final recommended system (fold-honest OOF 0.8513)
```
p = mean( AnySleep(Fpz+Pz+EOG), AnySleep(Fpz+EOG), U-Sleep CSDP(Fpz+EOG), LightGBM-bandpower )
y = argmax(p)
```
- 4-member equal-weight ensemble; fold-honest combo selection: all 5 folds agree on
  ANY3ch + U-Sleep CSDP + LGBM, 4/5 add ANY-Fpz+EOG. Class bias adds nothing now (E19b 0.8510).
- BENCHMARK_30: **ALL 0.8425 · SC 0.8362 · ST 0.8648** (domain gap 0.029, the most robust system);
  per-class N1 .635 · N2 .892 · N3 .833 · REM .915 — all four are new study records.
- Diversity logic: AnySleep is ST-strong, U-Sleep CSDP (open weights) is SC-strong,
  LightGBM adds feature-space diversity; RSN is now out of the winning pool.
- Previous best system (E18) = 0.8316 → **+0.011** from adding E21.
- Best single model: U-Sleep CSDP 0.8275 (SC .833) / AnySleep 3ch 0.8267 (ST .878).
- Minimal-sensor alternative: AnySleep Fpz+EOG = 0.8227 (single model, 2 electrodes).
- Clean-model alternative (no Sleep-EDF exposure): RSN = 0.7501; clean ensemble = 0.7608.

## 4. Channel ablation (AnySleep, all 197) — minimal-signal answer

| Input | Macro-F1 | SC | ST | Δ vs full |
|---|---|---|---|---|
| Fpz+Pz+EOG | **0.8267** | .809 | .878 | — |
| **Fpz+EOG** | **0.8227** | .811 | .865 | **−0.004** |
| Fpz+Pz | 0.8134 | .797 | .863 | −0.013 |
| Fpz only | 0.8015 | .790 | .844 | −0.025 |
| Pz only | 0.7736 | .756 | .829 | −0.053 |

**The best 2-sensor setup is Fpz-Cz + EOG: only −0.004 vs all 3 channels, and +0.009 over
Fpz+Pz.** It even has the best REM recall of all configs (0.913 vs 0.897 for 3ch) and equals
Fpz+Pz on N1. Pz-Oz is the droppable channel; a single frontal EEG keeps 97% of the full score.

## 5. Key findings
1. **AnySleep is the winner** (0.827 full-197) but saw Sleep-EDF in training → competition
   legality must be checked; **RSN 0.750 is the best clean (never-saw-Sleep-EDF) model**.
2. **ST > SC for every context model** (RSN .788 vs .736, YASA .611 vs .486) — day-long home
   recordings are the harder domain; hospital nights are cleaner.
3. **YASA is the interpretable baseline only** (0.52–0.55, N1 F1 ≈ 0.07).
4. **Ensembling pays only with diversity** — the weak-but-different LightGBM helps (+0.005
   fold-honest, E17/E18), the same-family RSN hurts; Viterbi and transition decoding hurt.
5. **No alignment/label/harness bugs** — proven by shift sweep (peak at 0), permutation check
   (identity wins), and predicted-vs-true histograms for every model.

## 6. Interpretability

### 6.1 LightGBM SHAP (our own 11 bandpower/amplitude features)
Per-class top drivers map 1:1 to AASM scoring rules:
| Stage | Top feature | SHAP | Clinical marker |
|---|---|---|---|
| Wake | eog_ptp | 1.30 | eye movements + muscle tone |
| N1 | alpha | 0.56 | alpha dropout |
| N2 | sigma | 0.53 | sleep spindles |
| N3 | eeg_std | **1.88** | high-amplitude slow waves |
| REM | emg_rms | 0.48 | muscle atonia + theta |
Global ranking: eeg_std > eog_ptp > beta > zcr > sigma > emg_rms > … (`docs/interp_shap_*.csv`)

### 6.2 Confidence / uncertainty (E18 ensemble, 237,936 epochs)
| Confidence | Share | Accuracy |
|---|---|---|
| 0.0–0.4 | 1.3% | 42.6% |
| 0.4–0.6 | 17.6% | 53.6–64.4% |
| 0.7–0.8 | 17.7% | 90.4% |
| 0.9–1.0 | 30.3% | **99.5%** |
Monotonic — model "knows when it doesn't know"; clinician review can target the low-confidence
slice (~1–7% of epochs). ECE reported per run in `metrics_*.csv`.

### 6.3 AnySleep channel attention (16 recordings, 5,966 windows; hooks on 13 SkipConnectionBlocks)
Attention = softmax over channels of a time-pooled MLP at every skip connection. Sliding 20-min
windows, aggregated by TRUE stage. Deepest layer (L12, connector):
| Stage | Fpz | Pz | EOG | Reading |
|---|---|---|---|---|
| Wake | .172 | **.672** | .156 | posterior alpha dominates |
| N1 | .239 | .462 | .299 | posterior + eye |
| N2 | .375 | .436 | .188 | balanced EEG (spindles) |
| N3 | .413 | **.517** | .071 | EEG-only, eyes still |
| REM | .259 | .221 | **.520** | eye movements dominate |
The deep layers' channel routing matches clinical scoring; EOG attention is highest exactly for
REM and lowest exactly for N3. (`docs/interp_attn_by_stage.csv`, `interp_attn_windows.parquet`)

### 6.4 Channel intervention (from the ablation runs, all 197)
Value of adding EOG (F1 delta, 3ch − 2EEG): **N1 +0.027, REM +0.026**, N2 +0.008, N3 +0.003,
Wake +0.003. Fpz beats Pz on every class (N3 +0.048, REM +0.031, Wake +0.026, N1 +0.019,
N2 +0.016). Adding Pz to Fpz: N1 +0.045, Wake +0.015, **N3 −0.011**.
Flip analysis: EOG changes 5.8% of epochs (adding it is right 55.4% vs 38.2% wrong on flips);
Fpz→3ch changes 10.6% (55.6% vs 37.1%). True-REM recall: **Fpz+EOG .913**, 3ch .897, Fpz .894, 2EEG .869, Pz .852.
True-N1 recall: 3ch .658, Fpz+EOG .612, 2EEG .608, Pz .529, Fpz .520.
→ Best single sensor Fpz; most valuable addition EOG; best pair Fpz+EOG; Pz-Oz is droppable.
(`docs/interp_channel_*.csv`)

### 6.5 YASA + TreeSHAP (the published method: 116 features, 12 recordings, 13,298 epochs)
Global top-5: eeg_iqr_c7min_norm, eeg_abspow, **time_hour**, eeg_std, eog_nzc_c7min_norm.
Per-class: N1→eog_abspow, N2→eeg_abspow/eog_abspow, N3→**eeg_iqr_c7min_norm (8.58!)**, REM→
eog_beta_c7min_norm/eog_fdelta_c7min_norm, Wake→eog_abspow/eog_std.
Per-TRUE-stage own-class drivers: Wake/N1/REM all eye-movement features; N3 amplitude features
(eeg_std, sigma_p2min_norm, dt_c7min_norm).
Caveat found: `time_hour` = **elapsed hours since recording start** (a temporal prior, #3 most
important globally) — YASA's model leans on sleep-progression context built into features.
(`docs/interp_yasa_*.csv`)

### 6.6 Viterbi / transition decoding — tested, rejected
E11+Viterbi λ=0.1: 0.8259 (vs 0.8267); fusion+Viterbi λ=0.1–0.5: 0.806–0.820 (vs 0.8315 combo).
The transition prior (from EDA matrices) is redundant: AnySleep already has a ~14-min receptive
field; LightGBM+ensemble carry no temporal module, but the bias calibration covers the class-prior
side without reordering errors.

## 7. Inference speed on CPU (8 threads, no GPU) — deployment story
| Model | per 30-s epoch | 22-h night (2,650 ep) | real-time factor |
|---|---|---|---|
| AnySleep 3ch | 3.7–4.7 ms | 12.5 s | ×6,400–8,000 |
| RobustSleepNet | 4.3 ms | 11.5 s | ×6,900 |
| YASA | 3.0 ms | ~2.6 s (bench crop) | ×9,900 |
| LightGBM | 0.037 ms | 0.1 s | ×800,000 |
Streaming (20-min sliding window, recompute per epoch): 140 ms → ×214 real-time.
Full 4-model ensemble per night ≈ 40 s. Preprocessing: EDF load 0.4 s + resample 0.2 s /ch.
(`eval/bench_speed.py`)
