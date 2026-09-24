# Onboarding: sleep-stage models on OUR data (no training from scratch)

All claims below trace to `papers-bank/sleep-stage/*.md` (banked full texts) or the
two chat histories (`chat-history/RESEARCHER-*.md`). v3 data contract:
`epochs_v3.parquet`, `folds5_v3.csv`, BENCHMARK_30 = training window.

## 1. Which model for inference on our data?

| # | Model | Verdict |
|---|---|---|
| 1 | **AnySleep** (`2512.14461.md`) | First to run: names our exact channels (`EEG Fpz-Cz`, `EEG Pz-Oz`, `EOG horizontal`), EDF script, 128 Hz auto-resample, `(epochs,5)` logits. Caveat: sedf-sc/sedf-st in its corpus → runnable, NOT clean zero-shot. |
| 2 | **YASA** (docs only) | Cleanest zero-shot (NSRR 3k nights, no Sleep-EDF) + SHAP explainability. Single EEG + opt EOG; NO SC EMG (envelope mismatch); `rem_detect` needs 2 EOG — unusable here. |
| 3 | **U-Sleep** | Mature CNN zero-shot reference; rigid channel expectations. |
| 4 | **SleepFMStager** | Modern: 2.4M params, 128 Hz, 5-s patches → aggregate 6/epoch; CC BY-NC check. |
| 5 | **RobustSleepNet** (`2101.02452.md`) | Temporal (T-epoch context) inference-ready; Sleep-EDF in paper → verify checkpoint provenance. |

Ladder: YASA (+Viterbi) → AnySleep → SleepFMStager → SleepDG/DIFFormer (train w/ alignment)
→ tiny stacker → partial fine-tune (last resort).

## 2. Data↔model fit (conflicts)

- ✅ Shared core everywhere: Fpz-Cz/Pz-Oz/EOG @100 Hz, 30-s epochs.
- ⚠️ Resample: 100→128 Hz (AnySleep/SleepFM-2, anti-aliased), 100→200 Hz (BIOT/LaBraM/REVE).
- ⚠️ Bipolar derivations (Fpz-Cz/Pz-Oz) vs electrode-identity embeddings (LaBraM/REVE/BIOT-C3-A1) → explicit derivation mapping, never silent rename.
- ❌ EMG: SC 1 Hz envelope vs ST 100 Hz raw — exclude from primary; harmonize (ST→1 Hz RMS) only as ablation. Never upsample SC envelope to 100 Hz.
- ❌ OSF (12-ch/64 Hz, N1+N2 merged) and full SleepFM-2 multimodal (needs ECG/resp) — transfer experiments only.
- ⚠️ SleepEDF exposure (AnySleep, SleepFM-2, RSN, SleepDIFFormer ckpt): runnable but NOT clean zero-shot; disclose + check subject overlap.

## 3. Preprocessing per model

- **AnySleep:** raw EDF → its script (128 Hz, robust scaling/clipping). Keep canonical 100 Hz copy.
- **YASA:** NO manual preprocess (internal 100 Hz + robust norm). Pass explicit `eeg_name`/`eog_name`.
- **SleepFMStager:** 100→128 Hz anti-aliased; 6× 5-s patches per 30-s epoch; reproduce upstream aggregation before inventing rules.
- **BIOT/LaBraM/REVE:** 100→200 Hz; custom derivation tokens/positions; cache embeddings → linear probe → 21-epoch BiGRU head.
- **SleepDG/DIFFormer:** native 100 Hz; Fpz-Cz+EOG; 20-epoch sequences; SC/ST domain labels; subject-aware sampling (ST=22).
- Universal: subject-disjoint folds; train-only stats; validity masks (?/Mov/GAP); BENCHMARK_30 for staging, MAIN_SLEEP for SQI.

## 4. Inference-only vs train

- Inference-only: YASA, AnySleep, U-Sleep, SleepFMStager, RSN (all +Viterbi with our `transition_v3_*`).
- Probe (tiny training): BIOT/LaBraM/REVE/SleepFM-2 frozen → linear → 21-epoch head.
- Train: SleepDG/DIFFormer/LGFNet/SleepBand/STDA-Net from scratch on our folds.
- Fine-tune (last resort): AnySleep/U-Sleep ckpt → folds; SleepFM-2 last blocks (LR backbone ≪ head).

## 5. Efficiency / accuracy / robustness / explainability

- **Efficiency:** YASA (CPU seconds) > SleepEffFormer 367k > AnySleep/U-Sleep CNN > SleepFMStager 2.4M > LGFNet/DIFFormer > REVE-Base 69M (avoid Large).
- **Accuracy anchors (own protocols, NOT comparable):** LGFNet 85.0 (N1 67.1) / SleepEffFormer 78.9 / SleepTransformer-78 78.8 (N1 48.5) / L-Seq SHHS 81.6 / AnySleep sedf ~0.77–0.81 / YASA ~73–75 (N1 ~35–42).
- **Robustness:** explicit-DG (SleepDG/DIFFormer/SleepBand/STDA) > broad-data (AnySleep) > single-domain. Always report SC/ST + WorstDomain + gap; SC→ST stress; perturbation + confidence analysis.
- **Explainability:** YASA TreeSHAP (global/class/epoch, grouped physiology) + confidence/margin + spindle/slow-wave overlays + channel-intervention (Fpz vs Pz, ±EOG) + Viterbi trace. Deep models: SleepTransformer attention, probe subject/domain decoders (shortcut audit).

## Frequency-band mismatch fixes (minor problems)
Resampling handles rate; bands are model-internal. Real risks: (a) anti-alias filter choice — reuse model's own resampler; (b) ST telemetry-error epochs — mask via `epoch_quality_v3` marker flags; (c) SC/ST gain differences — per-record robust norm, never global; (d) N1 definition (OSF merges N1/N2 — excluded from primary).

## 6. Deep-read deltas (verified line-by-line in banked texts — supersedes history hearsay)

**SLEEPYLAND/SOMNUS (`2506.08574.md`, fetched this pass):** 220k hrs ID + 84k OOD,
pretrained U-Sleep + DeepResNet + SleepTransformer, containerized
(`biomedical-signal-processing/sleepyland`). SEDF_SC (78/153) + SEDF_ST (22/44) are
OOD sets. SOMNUS = plain soft-vote over architectures×channels, wins 94.9% of
24-dataset comparisons (MF1 68.7–87.2), beats best human on DOD-H/OOD. Run order:
U-Sleep → DeepResNet → SleepTransformer → SOMNUS, each EEG-only then EEG+EOG.
Phase 2 immediately after YASA.

**AnySleep (`2512.14461.md`, read fully):** OUR sedf-sc (115/15/23) AND sedf-st (30/6/8)
are in its training table — definitively not zero-shot on our data. Train: 35-epoch
sequences, CE, AMSGrad Adam LR 1e-5, batch 64, early-stop on val Macro-F1 (patience 100).
Sampling stratified stage×dataset (α=0.5) + RobustSleepNet-style channel subsampling.
Preproc: 128 Hz polyphase, per-rec per-channel median/IQR, clip [−20,20], NO bandpass.
Model ~3.16M params, 13 channel-attention modules, 14.36-min receptive field, full-recording
inference. Results: sedf-sc 0.81, sedf-st 0.77–0.79; 2-ch MF1 0.726–0.760 (single-ch min
0.710 occipital); EOG > extra-EEG as complementary modality; EMG excluded (no gain).
Repo `github.com/dslaborg/AnySleep` ships code + models + splits (license: verify on repo).

**SleepDG (`2401.05363.md`, read fully):** Fpz-Cz + horizontal EOG @100 Hz, L=20, d=512,
bandpass 0.3–35 + z-score, ±30-min SleepEDFx trim. Loss = CE + 0.5·rec + 0.5·epoch-align
(mean+cov) + 0.5·seq-align (Pearson inter-epoch corr); Adam 1e-3, 50 epochs, batch 32.
SleepEDFx-as-target 77.44/71.29 (BASE 73.89/67.02); avg 75.03/69.64. Ablation: epoch-align
+3.57/+4.07, seq-align +2.37/+3.16. 8× RTX 3080. Repo `wjq-learning/SleepDG`.

**SleepDIFFormer (`2508.15215.md`, read fully):** SleepEDFx-197 in protocol table
(W26/N1 10.6/N2 37.6/N3 8.2/REM 14.5), same ±30-min crop, 0.3–35 Hz, 100 Hz, z-score.
N=20, d=128, 4× MDTA (4 heads) + 1 inter-epoch MHSA (8 heads), λrec=λalign=0.5,
Adam 5e-4, batch 16, RTX 4090. Avg 76.32/71.83 (+1.29/+2.19 over SleepDG);
SleepEDFx-target 78.19/72.44. Ablation: signal-embedding +2.8/+3.25, DA +0.71/+0.53,
FA +0.88/+0.75, DA-for-inter-epoch HURTS (−1.41/−1.48). Attention maps show
beta→Wake, SEM@1s→N1, spindle@6s + K-complex@7s→N2, delta@12–13s→N3, blink+sawtooth→REM.
Repo `Ben1001409/SleepDIFFormer` + checkpoint (SleepEDFx-exposed — disclose).

## 7. Phased implementation queue (from updated history — stop after compare)

Phase 1 (YASA×5: Fpz, Fpz+EOG, Pz+EOG, fusion, +Viterbi) → Phase 2 (SLEEPYLAND×4)
→ Phase 3 (SleepFMStager: `from_pretrained(n_chans=4, n_outputs=5, n_times=3840,
sfreq=128)`, resample 100→128, aggregate 6×5-s) → Phase 4 (AnySleep:
`examples/predict_edf_file_logits_plain.py` → `(1,epochs,5)` npy) → STOP AND COMPARE
(Macro-F1, N1/REM, SC/ST, params, runtime). Only then: tiny stacker → partial fine-tune.
Dropped for now: OSF/REVE/BIOT/LaBraM probes, RobustSleepNet (optional).
