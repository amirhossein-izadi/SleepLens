# wearable — wearable-surrogate preprocessing, training, evaluation

Explores the hardware (wearable) angle of sleep staging **without any EEG
input**: the PSG channels are reused as wearable surrogates, models are trained
subject-wise, and only out-of-fold predictions are scored.

```
EDF + expert labels ──extract_surrogates.py──▶ features/ + windows/ + splits.csv
                                                      │
                                             train_bench.py (GroupKFold OOF)
                                                      ▼
                                             data/wearable/preds/<model>_<sid>.npy
                                                      │
                                             evaluate_bench.py
                                                      ▼
                                             reports/wearable_*
```

Sensor mapping: `EMG submental` → actigraphy/motion, `EOG horizontal` → eye
activity, `Resp oro-nasal` → breathing belt (cassette only), `Temp rectal` →
slow trend (cassette only). Native rates differ per subset (cassette EMG is a
1-Hz envelope, telemetry has no Resp/Temp) — high-rate features exist only
where the channel supports them (`qc.csv` records `fs_emg/fs_eog/fs_resp`).

## Quickstart

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt          # see file header for the torch/CUDA line

./run_pipeline.sh                        # cassette, RandomForest
SMOKE=1 ./run_pipeline.sh                # 6 nights, fold 0, 2-epoch test
MODELS=rf,unet1d,watchsleepnet EPOCHS=20 PYTHON=.venv/bin/python ./run_pipeline.sh
```

The pipeline can also use separate environments per stage (e.g. a torch env for
training, a yasa env for extraction/evaluation):

```bash
PYTHON_EXTRACT=.venv/bin/python \
PYTHON_TRAIN=.venv_torch/bin/python \
PYTHON_EVAL=.venv/bin/python ./run_pipeline.sh
```

## Stages

### 1. Surrogate extraction (`extract_surrogates.py`)

Per 30-s epoch, aligned 1:1 with the expert labels:

- **features/<sid>.csv.gz** — raw + robust z-scored per-epoch features:
  motion (EMG RMS/std/range, PIM counts, band powers, Hjorth, kurtosis,
  zero-crossing rate), eye activity (variance, band power, peaks, amplitude
  p95), respiration (rate, rate CV, amplitude variance), temperature
  (mean, slope). `feature_dictionary.csv` lists every feature.
- **windows/<sid>.npz** — normalized 1-Hz and 25-Hz waveforms (`motion1`,
  `eog1`, `resp1`, `eog25`, `motion25`) + labels + availability masks.
- **counts/<sid>.csv** — per-minute activity counts (HypnosPy-style input).
- **splits.csv** — frozen subject-wise GroupKFold assignment
  (`subject_key = subset:subject`; Sleep-EDF reuses subject numbers across
  cohorts, so keys are namespaced).
- optional `--with-yasa`: YASA EEG baseline predictions as reference.

```bash
python extract_surrogates.py --subset both --limit 0 --jobs 6
python extract_surrogates.py --limit 3 --with-yasa          # smoke
```

### 2. Training (`train_bench.py`)

Adapted re-implementations in `wearable_models.py` (**not** the original
authors' code): `rf` RandomForest on engineered features, `unet1d` 1D ResUNet
(MADSOLSEN-style), `watchsleepnet` ResNet1D+TCN+BiLSTM+attention
(WillKeWang-style, W/NREM/REM 3-class). Training uses the frozen splits with a
subject-disjoint validation carve-out; predictions are written only for held-out
folds → `preds/<model>_<sid>.npy` (int8; 255 = unscored) + `<model>_meta.json`.

```bash
python train_bench.py --models rf
python train_bench.py --models unet1d --epochs 20
python train_bench.py --models rf --only-folds 0 --smoke 3   # quick check
```

### 3. Evaluation (`evaluate_bench.py`)

Epoch-level accuracy / Macro-F1 / Cohen's kappa / per-class F1 / confusion
matrix (5-class and 4-class W/Light/Deep/REM; 3-class W/NREM/REM for
WatchSleepNet), per-session and per-fold breakdowns, and macro sleep metrics
(TST, SE, SOL, WASO, REM latency) via YASA `Hypnogram.sleep_statistics()`,
reference vs predicted, plus a majority-class baseline.

```bash
python evaluate_bench.py
python evaluate_bench.py --models rf,unet1d,watchsleepnet
```

## Outputs

`data/wearable/` (features, waveforms, counts, predictions — gitignored) and
`reports/wearable_*` (summary, per-session, by-stage, folds, confusion matrix,
macro metrics, model comparison — gitignored). Data roots default to
`$SLEEPLENS_DATA` or `~/Projects/sleep-analysis/test/data`; override with
`--edf-root`, `--clean-root`, `--data-dir`, `--report-dir`.

## Reference results (197 Sleep-EDF nights, lights-off)

| Model | Classes | OOF Macro-F1 |
|--|--|--|
| RF (engineered features) | 5 | 0.556 |
| UNet1D (adapted) | 5 | 0.542 |
| WatchSleepNet1D (adapted) | 3 (W/NREM/REM) | collapsed (κ ≈ 0.01) |

EEG-free staging is far below PSG models — that gap is the point of the
hardware discussion. `evaluate_bench.py` also prints macro-metric bias/MAE so
the effect on TST/SE/SOL can be quantified, not just per-epoch agreement.

## Notes

- The splits are frozen on purpose: every model is compared on the same
  subject-wise partition, and OOF predictions are the only scored ones.
- `prepare_windows.py` is incremental (smoke runs never clobber a full build);
  `extract_surrogates.py --overwrite` forces recomputation of a session.
