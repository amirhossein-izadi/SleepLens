# features — sleep-quality parameter extraction from labeled data

Extracts ~96 interpretable parameters per night from **labeled** Sleep-EDF
recordings (expert hypnogram, or any model's per-epoch predictions) plus the
raw PSG signal. This is the measurement layer that feeds sleep-quality scoring
and sanity checks.

```
sleep-edf EDF + hypnogram ──prepare_windows.py──▶ lights-off window + stages
                                                     │
                                          extract_features.py
                                                     ▼
                     reports/sqi_features_<source>_lights_off.csv   (1 row/night)
```

## Quickstart

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

./run_pipeline.sh                    # all 197 nights, expert labels
SMOKE=1 ./run_pipeline.sh            # 2 nights, ~30 s
PYTHON=.venv/bin/python ./run_pipeline.sh
```

`run_pipeline.sh` skips window preparation when `sleepedf_clean/manifest.csv`
already exists (`FORCE_PREP=1` to rebuild).

## What gets computed

| Group | Examples |
|--|--|
| Continuity | TST, sleep efficiency, SOL, WASO, REM latency, time in bed |
| Fragmentation | awakenings + index, stage shifts, sleep fragmentation index, arousal proxy |
| Architecture | stage % of TST, first/second-half N1/REM, REM episodes, bout statistics, 5x5 stage-transition matrix |
| EEG | Welch bandpower (delta/theta/alpha/sigma/beta), SWA, spectral entropy, permutation entropy, YASA spindles (N2) and slow waves (NREM) |
| EMG | per-epoch RMS, REM atonia ratio, movement index |
| Respiration | coarse apnea proxy from the 1-Hz oro-nasal envelope (cassette only) |

`REF_RANGES` in `extract_features.py` lists adult reference values used for
interpretation (AASM-style; Sleep-EDF ages 25-101 y). The arousal and apnea
detectors are **proxies**, not AASM-scored events — see the docstrings.

## Usage

```bash
# expert labels, all nights (resume-safe: re-runs only missing nights)
python extract_features.py --source expert --resume

# hypnogram-only features (fast; skips EDF signal reads)
python extract_features.py --source expert --no-signal

# parameters computed from a model's staged output
#   expects <preds-root>/<model>/<sid>.npy (0-4, -1 unscored)
python extract_features.py --source usleep --resume
```

Data roots default to `$SLEEPLENS_DATA` (or
`~/Projects/sleep-analysis/test/data`); override with `--edf-root`,
`--clean-root`, `--preds-root`, `--report-dir`.

Stage encoding: `0=W, 1=N1, 2=N2, 3=N3, 4=R`; expert `255` and model `-1` are
unscored and excluded from denominators. Sleep-EDF hypnogram stages 3+4 merge
into N3.

## Outputs

`reports/sqi_features_<source>_lights_off.csv` — one row per session:
identity (`session`, `source`), continuity/fragmentation/architecture columns,
`tr_<A>_<B>` transition counts, EEG/EMG/respiratory parameters, `elapsed_s`.

`reports/` is gitignored; regenerate anytime with the commands above.

## Notes

- Runs without GPU. Expect ~10 s/night with signal features, <1 s/night with
  `--no-signal`.
- Spindle/slow-wave detection uses YASA >= 0.7 result objects.
- `prepare_windows.py` is incremental: an existing `manifest.csv` /
  `epochs.csv.gz` is kept and only the sessions in the current run are
  replaced, so smoke runs never clobber a full build.
