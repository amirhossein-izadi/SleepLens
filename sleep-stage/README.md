# sleep-stage — experiment standard

`canonical 100-Hz v3 data + model adapters + universal T×5 output + frozen evaluator.`

## Layout
- `adapters/` — `base.py` (SleepStager interface), `canonical.py` (raw EDF + v3 alignment),
  `yasa_adapter.py` (E01–E03), future: `sleepyland_adapter.py`, `anysleep_adapter.py`, ...
- `eval/run_eval.py` — metrics.csv per run (macro/micro, per-class, SC/ST, WorstDomain, κ, ECE, confusion)
- `runs/<EXP-ID>/<stem>.parquet` — epoch_index + p_Wake…p_REM (the ONLY model contract)
- `configs/experiments.csv` — E01–E20 registry (frozen order)
- `docs/` — METRICS.md, PREPROCESSING.md, PRIORITY.md (frozen standards)

## Rules
1. Same v3 ground truth + folds for every model; model-owned preprocessing only.
2. Report SC and ST separately, always. 3. No test tuning. 4. Heads/adapters allowed;
   inference-first, not inference-only.
