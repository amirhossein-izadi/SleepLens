# sdi — Sleep Depth Index inference + night-level sleep-quality estimate

Runs the published **SDI transformer** (Zhou et al., *npj Digital Medicine*
8:203, 2025) on Sleep-EDF nights, then derives the additional parameters used
for a night-level sleep-quality estimate from the model outputs.

```
EDF + lights-off window ──infer_sdi.py──▶ data/sdi/<sid>.npz   (per-epoch SDI + REM)
                                              │
                              estimate_quality.py (RB/AP/CV/MDR/PR + skew/ApEn/DFA)
                                              ▼
        reports/sdi_night_features_<tag>.csv, sdi_composite_<tag>.csv
        reports/sdi_repeatability_<tag>.csv  (subjects with two nights)
```

## Quickstart

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt          # see file header for the torch/CUDA line

./run_pipeline.sh                        # all 197 nights (GPU strongly recommended)
SMOKE=1 ./run_pipeline.sh                # 2 nights end-to-end
PYTHON=.venv/bin/python ./run_pipeline.sh
```

If `../features/reports/sqi_features_<stage-source>_lights_off.csv` exists it
is joined for the optional descriptive correlation check (set
`SQI_FEATURES=none` to skip).

## Model

- Architecture vendored verbatim from `sczzz3/SDI` (MIT) in `sdi_net.py`;
  state_dict in `models/sdi_checkpoint.pt` (89 MB, copied as-is).
- Input: 30-s epochs @ 100 Hz, order `[EEG, EMG, EOG, ECG]`, uV (mV for ECG),
  resample-only preprocessing (no filter), matching the upstream inference.
- Output per epoch: SDI 0-1 (higher = deeper) + binary REM prediction.

### Sleep-EDF substitutions (zero-shot — NOT validated)

| Channel | Paper | Here |
|--|--|--|
| EEG | C4 | `EEG Fpz-Cz` (Sleep-EDF has no C4; `--eeg-channel` can select Pz-Oz) |
| EMG | chin | `EMG submental`; cassette is natively 1 Hz (envelope), telemetry 100 Hz |
| EOG | right | `EOG horizontal` |
| ECG | required | absent → zero-filled (`--ecg-channel` to override) |

Cassette and telemetry are separate input conditions and are **never pooled**.

## Usage

```bash
# 1) inference -> data/sdi/<sid>.npz; QC reports in reports/
python infer_sdi.py --subset both --resume          # add --shard i --num-shards N to parallelize
python infer_sdi.py --device cpu --batch-size 64    # no GPU

# 2) night-level estimate
python estimate_quality.py                          # expert stage mask
python estimate_quality.py --stage-source usleep    # mask/REM checks from a model
python estimate_quality.py --reference-csv ref.csv  # external reference population
```

### The composite (research estimate, weights ours)

Over sleep epochs only (expert stages 1-4 by default), per deployment guide:

| Param | Meaning | Orientation |
|--|--|--|
| `rb` | fraction of sleep epochs with SDI < `--rb-threshold` (0.2) | lower better |
| `ap` | mean SDI over sleep | higher better |
| `cv` | SD(SDI)/mean(SDI) | lower better |
| `mdr` | mean SDI over model-predicted REM | higher better |
| `pr` | predicted REM share of sleep | higher better |

Each is z-scored against a reference population (default: all nights in the
table), signed, and averaged with equal weight into `sdi_composite`; the
midrank percentile within the reference is `sdi_percentile` (0-100). `skew`,
`apen`, `dfa` are reported but not scored. Eligible nights need
>= `--min-sleep` sleep epochs and >= 1 predicted REM epoch (else NaN + reason).
Subjects with two eligible nights get a night-to-night consistency report
(Pearson r + ICC(2,1)).

The paper validates SDI as a biomarker source, not these weights or breakpoints.
This estimate has not been validated against any clinical outcome — treat it as
exploratory only.

## Outputs

| File | Content |
|--|--|
| `data/sdi/<sid>.npz` | `sdi` float32, `rem` uint8, `epoch_start`, `n_full` |
| `reports/sdi_per_session_lights_off.csv` / `sdi_summary_lights_off.csv` | inference QC: per-night means, depth Spearman vs NREM order, REM F1 |
| `reports/sdi_night_features_<tag>_lights_off.csv` | raw composite parameters + QC |
| `reports/sdi_composite_<tag>_lights_off.csv` | components, z-scores, composite, percentile, eligibility |
| `reports/sdi_composite_<tag>_sqi_correlations.csv` | descriptive rank correlations vs the features module |
| `reports/sdi_repeatability_<tag>.csv` / `_summary` | two-night consistency (needs >= `--min-repeat-pairs`) |

`tag` = stage source. `data/` and `reports/` are gitignored.

## Notes

- Never forward a whole night in one batch (attention is O(n^2), ~6 GB GPUs
  OOM); `--batch-size` defaults to 128 and chunking does not change outputs.
- `--resume` skips existing npz files **and excludes them from the runner's
  pooled QC summary** — re-run inference without `--resume`, or just ignore the
  summary, before quoting per-session means.
- `prepare_windows.py` is incremental (smoke runs never clobber a full build).
