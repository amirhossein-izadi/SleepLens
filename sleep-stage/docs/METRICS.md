# Metrics standard (frozen — every run reports this)

Primary selection: **validation Macro-F1**. Everything else is diagnostic.

## Per-run table (from `eval/run_eval.py` → `metrics.csv`)

| Metric | Definition | Use |
|---|---|---|
| Macro-F1 | mean of 5 class F1 | PRIMARY |
| Micro-F1 (=accuracy) | overall correct rate | secondary only |
| F1-W/N1/N2/N3/REM | 2PR/(P+R) per class | N1 critical, REM/N3 diagnostic |
| SC / ST Macro-F1 | same, per cohort | robustness |
| WorstDomain = min(SC,ST) | worst cohort | robustness gate |
| DomainGap = \|SC−ST\| | cohort spread | robustness gate |
| Confusion matrix | 5×5 counts | failure modes (W↔N1, N1↔N2, W↔REM, N2↔N3) |
| Cohen κ | chance-corrected agreement | clinical reporting |
| ECE + mean confidence | calibration | uncertainty story |
| Params / ms-epoch / VRAM | efficiency | Pareto table |

## Micro vs macro (why both, why macro rules)
Micro-F1 rewards the majority class (Wake/N2). Macro-F1 weights N1 = N2.
Report both; select on macro; never select on accuracy or Top-k.

## Ground-truth discipline
Labels from `epochs_v3.parquet`, `valid_stage` only, matched on (stem, epoch_index).
Match rate is printed (pilot: 6311/6416 — unmatched = GAP/?/Mov/no-signal, by design).
Splits: `folds5_v3.csv`, subject-atomic. No test tuning (biases, λ, thresholds → validation only).
