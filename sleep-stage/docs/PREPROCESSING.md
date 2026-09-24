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

## Windows
BENCHMARK_30 = staging benchmark; MAIN_SLEEP = architecture/SQI; FULL_VALID = robustness.
Crop recordings to the window before inference (pretrained stagers saw nights, not 24-h days).
Never cross GAP/?/Mov in sequences; split/pad with masks.
