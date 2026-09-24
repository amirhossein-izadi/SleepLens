# papers-bank/sleep-stage — index

Problem: 5-class sleep staging (Wake/N1/N2/N3/REM, Macro-F1) on Sleep-EDF Expanded
(SC 153 home + ST 44 hospital, Fpz-Cz/Pz-Oz/EOG @100 Hz, EMG mismatched).
Goal: inference-first (no train from scratch); fine-tune/adapters worst case.
Tiers kill redundancy: CORE = decides our experiments; SUPPORTING = method/backup evidence.

## CORE papers (banked full text — `*.md` spine = arXiv id)

| File | Paper | Repo / checkpoint / license | Why core |
|---|---|---|---|
| 2506.08574.md | SLEEPYLAND/SOMNUS (npj 2026) | `biomedical-signal-processing/sleepyland` — containerized, pretrained U-Sleep+DeepResNet+SleepTransformer | Top: SEDF_SC/ST as OOD, SOMNUS wins 94.9%, MF1 68.7–87.2 |
| 2512.14461.md | AnySleep (2025) | `github.com/dslaborg/AnySleep` — `examples/predict_edf_file_logits_plain.py` → `(1,epochs,5)` npy | Primary runnable: exact channels, sedf-sc 0.81 / sedf-st 0.77–0.79 (in-train!) |
| 2401.05363.md | SleepDG (AAAI 2024) | `github.com/wjq-learning/SleepDG` — PyTorch | DG baseline: Fpz-Cz+EOG, L=20, λ=0.5×3, SleepEDFx-target 77.44/71.29 |
| 2508.15215.md | SleepDIFFormer (2025) | `github.com/Ben1001409/SleepDIFFormer` — code + checkpoint | Modern DG: DSA/DCA, avg 76.32/71.83 (+1.29/+2.19 over SleepDG) |
| 2101.02452.md | RobustSleepNet (2021) | `Dreem-Organization/RobustSleepNet` — MIT, EDF CLI, `inference_on_edf_file` | Temporal zero-shot; Sleep-EDF-exposed → verify ckpt |
| 2105.11043.md | SleepTransformer (2022) | `pquochuy/SleepTransformer` + Zenodo 7927282 (SHHS), CC-BY-NC-4.0 | Reference: 21-epoch, EDF-78 78.8 / N1 48.5; TF1 stack |
| 2301.03441.md | L-SeqSleepNet (2023) | `pquochuy/l-seqsleepnet` + SHHS weights, CC-BY-NC-4.0 | Long context (~200 epochs, SHHS 81.6); TF1 |
| 1809.10932.md | SeqSleepNet (TNSRE 2019) | `pquochuy/SeqSleepNet` | Hierarchical RNN reference |
| 2007.05492.md | XSleepNet (TPAMI 2021) | `pquochuy/xsleepnet` + Zenodo 5809258/5809496/5809511 | Multi-view classical reference |
| 1910.11162.md | U-Time (NeurIPS 2019) | `perslev/U-Time` (also hosts U-Sleep) | Segmentation baseline family |
| U-Sleep_notes.md | U-Sleep (npj 2021, doi:10.1038/s41746-021-00440-5) | `perslev/U-Time`, hosted sleep.ai.ku.dk | Mature zero-shot: 15.6k participants, mean F1 .79, N1 .53 |
| TinySleepNet_notes.md | TinySleepNet (EMBC 2020) | `akaraspt/tinysleepnet` (no official ckpt) | Low-compute baseline: ~77–78.5 MF1 |
| 2007.05492.md | XSleepNet (TPAMI 2021) | `pquochuy/xsleepnet` + Zenodo 5809258/5809496/5809511, CC-BY-4.0 | Multi-view classical reference |
| 1809.10932.md | SeqSleepNet (TNSRE 2019) | `pquochuy/SeqSleepNet` | Hierarchical RNN reference |
| 1910.11162.md | U-Time (NeurIPS 2019) | `perslev/U-Time` (also hosts U-Sleep) | Segmentation baseline family |
| 2607.25197.md | LGFNet (2026) | repo unverified — check before use | Advanced supervised: 88.7/85.0, N1 67.1 (own protocol) |
| 2305.10351.md | BIOT (NeurIPS 2023) | `ycq091044/BIOT`, MIT, ckpts (PREST / SHHS+PREST) | Best probe: SHHS sleep in pretraining, 200 Hz |
| 2609.06849.md | SleepFM-2 (2026) | release unverified — check | Transfer-only: 128 Hz, 1-s patches, 2.57M, SleepEDF-exposed |
| 2603.00190.md | OSF (ICML 2026) | `yang-ai-lab/OSF-Open-Sleep-FM` + HF `OSF-Base` | Research-only: 12-ch/64 Hz, merges N1+N2 |

## SUPPORTING papers (banked; method/backup, not decision drivers)

| File | Paper | Note |
|---|---|---|
| 2609.22148.md | SleepEffFormer (2026) | Lightweight: 367k, 83.9/78.9; `Nishi-Kanta-Paul/SleepStage` |
| 2607.04851.md | SleepBand (2026) | Single-source DG for strict SC→ST; `lzcn/sleep-band` |
| 2605.06736.md | STDA-Net (2026) | Unlabeled-target adaptation (SC labels + ST signals) |
| 2510.12070.md | MEASURE (2025) | DG comparison; EDF-20 81.5; `ku-milab/Measure` |
| 2310.06715.md | S4Sleep (2023) | SSM design space |
| 2110.15278.md | ContraWR (2023) | SSL on Sleep-EDF derivations; `ycq091044/ContraWR` |
| 2510.07960.md | Wearable SSL eval (2026) | Evidence: domain-matched SSL > generic FMs |
| 2405.18765.md | LaBraM (ICLR 2024) | Probe: 5.8M base, 200 Hz; `935963004/LaBraM`, MIT |
| 2510.21585.md | REVE (NeurIPS 2025) | Probe: 69M base; HF `brain-bzh/reve-base` + positions |
| 2405.17766.md | SleepFM-1 (ICML 2024) | Recipe only: demo ckpt; `rthapa84/sleepfm-codebase`, MIT |

## Non-arXiv entries (docs links — no md fetch possible)

- SleepFMStager: HF `braindecode/SleepFMStager` — `from_pretrained(n_chans=4, n_outputs=5,
  n_times=3840, sfreq=128)`, 2.42M params, CC BY-NC. Upstream `zou-group/sleepfm-clinical`
  (`model_base`/`model_diagnosis`/`model_sleep_staging`).
- SleepGPT (FM): `LordXX505/SleepGPT` (+ Nat Commun s41467-025-67970-4) — second wave.
- SleepGPT (seq LM): medRxiv 2024.10.26.24316166, `yuty2009/sleepgpt` — Viterbi-like refinement.

| Model | Paper / docs | Repo / checkpoint |
|---|---|---|
| YASA | eLife 70092 | `yasa-sleep.org`, `pip install yasa`, `raphaelvallat/yasa_classifier` |
| U-Sleep | npj Digit Med 2021, doi:10.1038/s41746-021-00440-5 | `perslev/U-Time` (paper-version tags) |
| Stanford STAGES | Nat Commun 2018, s41467-018-07229-3 | `Stanford-STAGES/stanford-stages` (hypnodensity) |
| SleepFMStager | — (braindecode) | HF `braindecode/SleepFMStager` — 128 Hz, 5-s patches, 2.4M, CC BY-NC |
| SleepGPT (seq LM) | medRxiv 2024.10.26.24316166 | `yuty2009/sleepgpt` (ckpt status unverified) |
| SleepGPT (FM) | Nat Commun 2026, s41467-025-67970-4 | `LordXX505/SleepGPT` (verify) |
| TinySleepNet | EMBC 2020, doi:10.1109/EMBC44109.2020.9176741 | `akaraspt/tinysleepnet` (+pt repro `flower-kyo`) |
| DeepSleepNet | TNSRE 2017 | `akaraspt/deepsleepnet` + Zenodo 3375235 |
| AttnSleep | TNSRE 2021, doi:10.1109/TNSRE.2021.3076234 | `emadeldeen24/AttnSleep` |

## Reading order
SLEEPYLAND → AnySleep → SleepDG → SleepDIFFormer (deep-read, notes in ONBOARDING §6)
→ SleepFMStager API → ONBOARDING.md → phased queue (YASA×5 → SLEEPYLAND×4 → Stager → AnySleep → compare).

## Model-record schema (per-model fields to fill at implementation)
`did_training_include_SleepEDF?` (competition vs clean-zero-shot) and `exact_checkpoint_provenance`
first; then channels/rate/epochs, preprocessing, params/runtime, Macro-F1 + N1-F1 + SC/ST,
splits/masks. Dropped for now (wrong ROI): OSF/REVE/BIOT/LaBraM probes, RobustSleepNet (optional #10).
