# Inference & modeling log — complete narrative (start → now)

## Phase 0 — Data foundation (before any model)
- Full EDA of Sleep-EDF Expanded (197 PSG, 100 subjects, SC 153 home + ST 44 hospital).
- Produced the **v3 canonical contract** in `sleep-eda/tables/`:
  `epochs_v3.parquet` (onset-grid, 457,652 valid epochs, signal∩label intersection),
  `sleep_windows_v3.csv` (FULL_VALID / BENCHMARK_30 / MAIN_SLEEP),
  `folds5_v3.csv` (5 subject-atomic folds), transition matrices, quality flags.
- These are the ONLY EDA artifacts models use (alignment + evaluation), never as features.

## Phase 1 — Research → papers bank + onboarding
- Read both researcher histories end-to-end; built `papers-bank/sleep-stage/` (26 full papers,
  README with repos/checkpoints/licenses, ONBOARDING.md with model-fit + per-model preprocessing).
- Key conclusion: no clean zero-shot SOTA exists for our exact setup (all strong checkpoints
  except YASA saw Sleep-EDF) → run YASA for the clean story, AnySleep for the strong number.

## Phase 2 — Harness built (`sleep-stage/`)
- `adapters/`: T×5 contract (`SleepStager`), canonical raw-EDF loader (no filter/resample),
  per-model adapters.
- `eval/run_eval.py`: macro/micro, 5-class F1, SC/ST, WorstDomain, DomainGap, κ, ECE, confusion.
- `eval/debug_checks.py`: epoch-shift sweep ±5, class-permutation 5!, histograms.
- `runs/E##/`: versioned predictions (parquet: stem, epoch_index, p_*).
- `docs/`: METRICS, PREPROCESSING, PRIORITY, RESULTS. `weights/`: git-ignored + MANIFEST.

## Phase 3 — Weights acquired
- **AnySleep** `anysleep-run1.pth` (MIT) · **RSN** LODO-sleep_edf model (clean zero-shot, 7 other datasets)
- **SLEEPYLAND** docker (usleepyland + wild-to-fancy + manager + notebook, all UP)
- **SleepFMStager** HF mirror + vendored py3.10 code.

## Phase 4 — Pilots + bug hunt (3 recordings)
Bugs found and fixed:
1. **RSN missing 900-s padding trim** → all predictions shifted 30 epochs → 0.43 → 0.80.
2. **YASA proba columns** are `WAKE,N1,N2,N3,REM` (not W/R) → first run zero-filled Wake/REM.
3. **torch must import before pandas** on this Windows env (DLL WinError 1114).
4. **Crop-before-inference** (advisor test C): YASA +0.085 macro full-197 (0.461→0.546).
5. Path/merge bugs in sweep scripts.
SleepFM investigation: mirror **bit-identical** to upstream (56 tokenizer + fc tensors verified),
code path equal, responds to input, but constant Wake on our data → parked with evidence.

**Debug matrix (all models):** units µV-verified · shift sweep peaks at 0 · identity
permutation wins · pred hist ≈ true hist → **no alignment/label/harness bugs**.

## Phase 5 — Full sweeps (current)
| Run | Model | Preprocessing (native) | Coverage |
|---|---|---|---|
| E01 | YASA Fpz | raw 100 Hz, no filter | **197 ✅** |
| E02 | YASA Fpz+EOG | raw 100 Hz | **197 ✅** |
| E02c | YASA Fpz+EOG, cropped | crop to BENCHMARK_30 then raw | **197 ✅** |
| E03 | YASA Pz+EOG | raw 100 Hz | **197 ✅** |
| E20 | RobustSleepNet Fpz | their EDF→H5: 0.2–30 Hz → 60 Hz → IQR norm → pad 900 s → trim | **195/197** |
| E11 | AnySleep Fpz+Pz+EOG | 128 Hz polyphase, median/IQR, clip ±20 | 51/197 |
| E11a | AnySleep Fpz only | same | 108/197 |
| E11b | AnySleep Pz only | same | 108/197 |
| E11c | AnySleep 2×EEG | same | 63/197 |
| E07 | SLEEPYLAND U-Sleep | container: RobustScaler, 128 Hz, trim | 26/197 |
| E08 | SLEEPYLAND DeepResNet | container | queued |
| E09 | SLEEPYLAND SleepTransformer | container | queued |
| E06 | SOMNUS (soft-vote ensemble) | container | queued |
| E00 | LightGBM bandpower baseline | EDA feature tables | built, not yet run |
| E10 | SleepFMStager | 128 Hz + z-score | parked |

## Results (BENCH_30 Macro-F1)
| Model | Macro-F1 | SC | ST | Notes |
|---|---|---|---|---|
| AnySleep 3ch | **0.847** (pilot) | .831 | .880 | sedf-exposed (disclosed) |
| RobustSleepNet | 0.767 (pilot) | .811 | .680 | clean zero-shot |
| SLEEPYLAND U-Sleep | 0.739 (pilot) | .812 | .644 | clean |
| YASA Fpz+EOG crop | 0.546 | .531 | .562 | clean, full-197 |
| YASA Fpz | 0.523 | .486 | .611 | clean, full-197 |
| YASA Pz+EOG | 0.427 | .381 | .499 | clean, full-197 |
| SleepFMStager | parked | — | — | constant Wake |

## Next (after sweeps)
E11/E11a/b/c full numbers → channel ablation table · E06 SOMNUS · E12–E14 fusion+Viterbi
(pilot was neutral) · E15 tiny OOF stacker · E17 SleepEffFormer (local training) · SQI design.
