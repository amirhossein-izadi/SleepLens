# sdi

Run the published Sleep Depth Index (SDI) transformer (Zhou et al., npj Digital
Medicine 2025) on Sleep-EDF nights, then compute a night-level sleep-quality
estimate from the model outputs.

## Setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt   # see header: install the torch build for your hardware
```

## Run

```bash
./run_pipeline.sh                          # all nights, GPU recommended
SMOKE=1 ./run_pipeline.sh                  # 2 nights
PYTHON=.venv/bin/python ./run_pipeline.sh
```

Per stage:

```bash
python prepare_windows.py --subset both              # lights-off windows
python infer_sdi.py --subset both --resume           # -> data/sdi/<sid>.npz
python estimate_quality.py                           # -> reports/sdi_composite_*.csv
```

Useful flags: `--device cpu --batch-size 64`, `--shard i --num-shards N`
(parallel workers), `--stage-source usleep` (sleep mask from model predictions),
`--sqi-features ../features/reports/sqi_features_expert_lights_off.csv`
(optional join, used by `run_pipeline.sh` automatically when present).

## Output

- `data/sdi/<sid>.npz` — per-epoch SDI (0-1, higher = deeper) + REM (0/1)
- `reports/sdi_per_session_lights_off.csv`, `sdi_summary_lights_off.csv` — QC
- `reports/sdi_night_features_<tag>_lights_off.csv` — RB/AP/CV/MDR/PR, skew/ApEn/DFA
- `reports/sdi_composite_<tag>_lights_off.csv` — z-scores, composite, percentile
- `reports/sdi_repeatability_<tag>*` — night-to-night consistency

## Notes

- **Zero-shot with substitutions**: EEG Fpz-Cz (paper: C4), ECG zero-filled,
  cassette EMG is a 1-Hz envelope. Cassette and telemetry are never pooled.
- The composite weights are ours and unvalidated — a research estimate only.
- Never forward a whole night in one batch (O(n²) attention OOMs); default
  `--batch-size 128` is safe and chunking does not change outputs.
- `--resume` skips existing nights and excludes them from the QC summary.
