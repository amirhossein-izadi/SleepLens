# 17 Profiler macro — cycles, age, drug, SQI dims (ydata-style)

## Cycles
REM episodes separated by ≥60 min non-REM → cycles/night mean 3.53, median 4.0 (`figs/cycles.png`). 70–120 min macro scale holds (father Layer 7).

## Age (SC, n=153)
Age mean 59 y (25–101), 53.6% F. Age vs N3% r = −0.40 → older = less deep sleep. Always age-stratify validation; SQI must be age-normed (more N3 is not unconditionally better).

## Drug (ST, 22 subj × placebo/temazepam)
ST-subjects.xls maps night→condition per subject (e.g. subj1: night1 placebo 23:01, night2 temazepam 23:48). Temazepam expected: ↓SOL, ↑TST, N3/REM shifts — test paired within-subject (placebo vs drug same person), do not pool naively.

## Architecture (ground truth, full night)
Per-rec `tables/sleep_architecture.csv`. Untrimmed means misleading (TRT 1227 min, SE 42.8%) — recompute on analysis window (lights-off → last sleep + 30 min). SQI dims: Duration TST; Continuity SE/WASO/awakenings; Architecture N3%/REM%/transitions; Fragmentation arousal-proxy (no true arousal labels); Respiratory/O2/HR/legs IMPOSSIBLE (no sensors).

## Temporal value
Self-transitions .71–.99; median runs REM11/N24; context 5–11 epochs covers runs without oversmoothing single-epoch islands (N1 2872 singles). Offline bidirectional OK; wearable causal only — note deployment gap.
