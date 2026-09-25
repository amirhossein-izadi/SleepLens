# features

Extract ~96 interpretable sleep-quality parameters per night from labeled
Sleep-EDF recordings (expert hypnogram, or a model's per-epoch predictions).

## Setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
./run_pipeline.sh                          # all 197 nights, expert labels
SMOKE=1 ./run_pipeline.sh                  # 2 nights
PYTHON=.venv/bin/python ./run_pipeline.sh  # custom interpreter
```

The pipeline skips window preparation when `sleepedf_clean/manifest.csv`
exists (`FORCE_PREP=1` rebuilds it). Env overrides: `PYTHON`, `SUBSET`
(`cassette|telemetry|both`), `SOURCE` (`expert|<model>`), `LIMIT`.

Per stage:

```bash
python prepare_windows.py --subset both                 # EDF -> lights-off windows
python extract_features.py --source expert --resume     # all nights
python extract_features.py --source usleep --resume     # labels from a model dir
python extract_features.py --source expert --no-signal  # hypnogram only (fast)
```

Data defaults to `$SLEEPLENS_DATA` / `~/Projects/sleep-analysis/test/data`;
override with `--edf-root`, `--clean-root`, `--preds-root`, `--report-dir`.

## Output

`reports/sqi_features_<source>_lights_off.csv` — one row per night: continuity
(TST/SE/SOL/WASO/REM latency), fragmentation (awakenings, SFI, arousal proxy),
architecture (stage %, transitions, bouts), EEG (bandpower, entropy, spindles,
slow waves), EMG, and a coarse apnea proxy. Reference ranges live in
`REF_RANGES` in `extract_features.py`.

## Notes

- Stage encoding `0=W 1=N1 2=N2 3=N3 4=R`; unscored (255 / -1) excluded.
- Arousal and apnea are proxies, not AASM-scored events.
- `prepare_windows.py` is incremental: smoke runs never clobber a full build.
