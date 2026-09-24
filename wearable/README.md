# wearable

Train and evaluate EEG-free (wearable-surrogate) sleep-staging models on
Sleep-EDF: EMG -> actigraphy, EOG -> eye activity, Resp -> breathing belt,
Temp -> slow trend. Only out-of-fold predictions on frozen subject-wise
GroupKFold splits are scored.

## Setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt   # see header: install the torch build for your hardware
```

## Run

```bash
./run_pipeline.sh                          # cassette, RandomForest
SMOKE=1 ./run_pipeline.sh                  # 6 nights, fold 0
MODELS=rf,unet1d,watchsleepnet EPOCHS=20 PYTHON=.venv/bin/python ./run_pipeline.sh
```

Separate environments per stage are supported (`PYTHON_EXTRACT`,
`PYTHON_TRAIN`, `PYTHON_EVAL` default to `PYTHON`):

```bash
PYTHON_EXTRACT=.venv/bin/python \
PYTHON_TRAIN=.venv_torch/bin/python \
PYTHON_EVAL=.venv/bin/python ./run_pipeline.sh
```

Per stage:

```bash
python extract_surrogates.py --subset both --limit 0 --jobs 6  # features, waveforms, splits
python train_bench.py --models rf                              # OOF predictions
python train_bench.py --models unet1d --epochs 20
python evaluate_bench.py --models rf,unet1d
```

Data defaults to `$SLEEPLENS_DATA` / `~/Projects/sleep-analysis/test/data`;
override with `--edf-root`, `--clean-root`, `--data-dir`, `--report-dir`.

## Output

- `data/wearable/features/<sid>.csv.gz` — per-epoch raw + z-scored features
- `data/wearable/windows/<sid>.npz` — normalized 1/25 Hz waveforms + labels
- `data/wearable/splits.csv` — frozen subject-wise folds (`subject_key`)
- `data/wearable/preds/<model>_<sid>.npy` — out-of-fold predictions
- `reports/wearable_*` — summary, per-session, by-stage, confusion matrix,
  macro-metric bias/MAE (TST/SE/SOL/WASO/REM latency), model comparison

## Notes

- Models in `wearable_models.py` are adapted re-implementations, not the
  original authors' code.
- Native rates differ (cassette EMG is 1 Hz; telemetry has no Resp/Temp);
  per-file rates are recorded in `data/wearable/qc.csv`.
- Reference OOF Macro-F1: RF 0.556, UNet1D 0.542, WatchSleepNet collapsed.
