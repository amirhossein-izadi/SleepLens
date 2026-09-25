# analysis_weights/ — model checkpoints for the analysis pipeline

Everything in this folder **except this file** is git-ignored. The pipeline
resolves checkpoints from ``WEIGHTS_DIR`` (backend/analysis_weights by default;
override with the ``ANALYSIS_WEIGHTS_DIR`` env var).

| Model | Expected path | Size | Provenance / license |
|---|---|---|---|
| AnySleep (staging) | `anysleep/anysleep-run1.pth` | 12.2 MB | Attention U-Sleep checkpoint (MIT repo); saw Sleep-EDF variants in training |
| SDI transformer (sleep depth) | `sdi/sdi_checkpoint.pt` | 88.5 MB | Zhou et al., *npj Digital Medicine* 8:203 (2025); official checkpoint (`sczzz3/SDI`) |
| LightGBM baseline (ensemble member) | `lightgbm/baseline_lgbm.txt` | ~10 MB | Trained in-project on all 197 Sleep-EDF nights (457,655 epochs) from the sleep-eda bandpower features |

## Ensemble staging (default)

`STAGING_SYSTEM=ensemble` routes by cohort: cassette-like recordings use
AnySleep(Fpz+Pz+EOG) + AnySleep(Fpz) + AnySleep(Pz) + LightGBM (equal weights),
telemetry-like recordings use AnySleep(Fpz+Pz+EOG) alone. Measured
macro-F1: 0.8458 (ensemble) vs 0.8267 (single AnySleep).

## How they were provided here

```powershell
# from the project's experimental folders (SleepLens/sleep-stage, SleepLens/sleep-quality-index)
Copy-Item ..\..\sleep-stage\weights\repos\AnySleep\models\anysleep-run1.pth .\anysleep\
Copy-Item ..\..\sleep-quality-index\sdi\models\sdi_checkpoint.pt .\sdi\
```

## Loader guarantees

- AnySleep: loads with the vendored architecture in
  `apps/analysis/pipeline/staging/anysleep_model.py`; checkpoint logit order is
  `[Wake, N1, N2, N3, REM]` (verified by permutation search).
- SDI: `strict=True` state-dict load into `apps/analysis/pipeline/sdi/net.py`.

Both loaders are exercised by `apps/analysis/tests/test_pipeline_smoke.py`
(skipped automatically when the files are absent).
