# SleepLens

Sleep-quality analysis pipelines built on **Sleep-EDF Expanded** (EEG/EOG/EMG PSG)
and wearable-style surrogate signals. Three independent, executable codebases:

| Directory | Pipeline | Input | Output |
|--|--|--|--|
| [`features/`](features/) | Sleep-quality parameter extraction from labeled data | PSG EDF + expert hypnogram | ~96 per-night parameters (`features/reports/sqi_features_expert_lights_off.csv`) |
| [`sdi/`](sdi/) | Sleep Depth Index (SDI) model inference + night-level sleep-quality estimate | PSG EDF (+ SDI checkpoint) | epoch-level SDI/REM (`sdi/data/sdi/*.npz`) + composite/percentile (`sdi/reports/`) |
| [`wearable/`](wearable/) | Wearable-surrogate preprocessing, training, evaluation | PSG EDF + expert labels | per-epoch features/waveforms + out-of-fold predictions + metrics (`wearable/reports/`) |

Each directory is self-contained: full pipeline in `run_pipeline.sh`, module
README, requirements, and its own `data/`/`reports/` outputs. The three share
only the dataset on disk.

## Dataset

The pipelines read **Sleep-EDF Expanded** from a data root. Resolution order:

1. CLI flags (`--edf-root`, `--clean-root`, `--preds-root`, `--out-dir`, ...)
2. Environment variables: `SLEEPLENS_DATA` (base), `SLEEPLENS_EDF` (raw EDF
   folder), `SLEEPLENS_CLEAN` (lights-off windows), `SLEEPLENS_PREDS`
   (per-epoch staging predictions)
3. Default: `~/Projects/sleep-analysis/test/data` (this project's development
   checkout; contains the extracted dataset and derived folders)

Data root layout expected by the pipelines:

```
<data-root>/
├── sleep-edf-database-expanded-1.0.0/   # raw EDFs + SC/ST-subjects.xls
│   ├── sleep-cassette/
│   └── sleep-telemetry/
├── sleepedf_clean/                      # built by <module>/prepare_windows.py
│   ├── manifest.csv
│   ├── epochs.csv.gz
│   └── stages/<sid>.npy                 # 0=W 1=N1 2=N2 3=N3 4=R 255=UNS
└── preds/<model>/<sid>.npy              # optional per-epoch staging preds
```

Sleep-EDF Expanded is downloaded from PhysioNet
(https://physionet.org/content/sleep-edfx/1.0.0/). Stage encoding used
everywhere: `0=W, 1=N1, 2=N2, 3=N3, 4=R`, unscored `255` (expert) or `-1`
(model). Sleep-EDF hypnogram `3`+`4` are merged into N3. The raw dataset is
never modified; `sleepedf_clean/` is a derived, rebuildable lights-off window
(see each module's `prepare_windows.py`).

## Quickstart

```bash
# pick a python per module (see each module's requirements.txt)
cd features  && ./run_pipeline.sh          # e.g. PYTHON=/path/to/venv/bin/python
cd sdi       && ./run_pipeline.sh          # needs a torch env (GPU recommended)
cd wearable  && ./run_pipeline.sh
```

`SMOKE=1 ./run_pipeline.sh` limits every stage to a few nights for a quick
end-to-end check. The scripts accept `PYTHON=` and pass extra flags through the
environment (`SUBSET=`, `LIMIT=`, ...); see each module README.

## Notes and disclaimers

- `sdi/` runs the published SDI transformer (Zhou et al., npj Digital Medicine
  2025) zero-shot with deliberate Sleep-EDF input substitutions (Fpz-Cz instead
  of C4, zero-filled ECG, cassette EMG is a 1-Hz envelope). The night-level
  composite is a research estimate, **not** a validated clinical score. See
  `sdi/README.md`.
- `wearable/` models are adapted re-implementations of published architectures
  (ResUNet, WatchSleepNet), not the original code.
- Subject-disjoint splits are enforced everywhere (no subject leakage).
