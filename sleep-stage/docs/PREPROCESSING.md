# Preprocessing standard (frozen)

Rule: **canonical 100-Hz source, model-owned adapters.** Never one global tensor for all models.

## Canonical (`adapters/canonical.py`)
Raw EDF values, no filter/resample/norm. Epoch = 30 s × 100 Hz = 3000 samples.
v3 masks (`valid_signal`, `valid_stage`, `in_bench`, `in_main_window`, quality) travel with data.

## Accepted input frequencies per model
| Model | Hz in | Transform | Filter | Norm |
|---|---|---|---|---|
| YASA | 100 (native) | none (internal ↓100 Hz) | NONE manually | internal robust |
| SLEEPYLAND | toolbox-owned | container | robust scaling | container |
| AnySleep | **128** (3840/epoch) | polyphase resample | none | median/IQR per rec/ch, clip ±20 |
| SleepFMStager | **128** (6×640/epoch) | anti-aliased resample | upstream | upstream; aggregate 6→1 on validation |
| SleepDG/DIFFormer | **100** ([2,3000]×20) | none | 0.3–35 Hz | z-score |
| SleepEffFormer | **100** (Fpz) | none | 0.5–40 Hz Butterworth | per-epoch z-score |
| BIOT/LaBraM/REVE | **200** | anti-aliased resample | model default | model default + derivation tokens |

YASA env caveat: sklearn 1.7.2 vs trained 0.24.2 raises `InconsistentVersionWarning`;
outputs validated sane (Wake F1 0.89 pilot) but pin versions before final numbers.
YASA proba columns are `WAKE,N1,N2,N3,REM` (handled in adapter); `rem_detect` unusable (needs 2 EOG).

## Adapter alignment law (learned from E20 bug)
Reproduce the repo's padding/trimming exactly (RSN: 900-s pad → trim 30 epochs/side;
skipping it shifted all predictions and cost 0.37 macro). Assert output epoch count
against signal length before saving. Report FULL_VALID + BENCHMARK_30 for every run.

## Crop-before-inference (advisor test C — CONFIRMED for YASA)
Context-sensitive models (YASA rolling 7.5-min/2-min features, RSN 21-epoch GRU,
SleepFM LSTM) see daytime wake in full SC recordings and degrade. Cropping the signal
to the BENCHMARK_30 interval BEFORE inference (then offsetting epoch_index) gained:
SC4001 +0.111, SC4041 +0.057, ST7011 +0.035 macro. Run both modes; report crop as the
benchmark number and full as the deployment/robustness number.

## Debug matrix (run before trusting any adapter)
1. units: pcts/std per channel (µV sanity) 2. shift sweep s∈[-5,5] (peak must be 0)
3. class permutation 5! (identity must win) 4. pred vs true histograms
5. native-vs-custom parity where the repo ships a CLI.

## Windows
BENCHMARK_30 = staging benchmark; MAIN_SLEEP = architecture/SQI; FULL_VALID = robustness.
Crop recordings to the window before inference (pretrained stagers saw nights, not 24-h days).
Never cross GAP/?/Mov in sequences; split/pad with masks.
