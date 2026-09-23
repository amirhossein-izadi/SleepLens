# Event rates, transitions, age, drug (full 459k, EDA only)

Table: `events_full.parquet` (cohort,label,spindle_rms,slow_p99,k_zmin,eog_ptp,eog_vel,emg_rms,beta,is_trans). Detectors: sigma-RMS 11–16, slow p99 0.5–4, K z-min, EOG ptp/velocity, EMG RMS (cohort-native fs), beta RMS, arousal-proxy = beta > 2× N2-median.

## Full medians
spindle_rms: Wake 2.65 (movement!) > N3 2.56 (slow leakage) > N2 2.27 > N1 1.67 > REM 1.48. slow_p99: OTHER 66 > N3 61 > Wake 57 > N2 32 > REM/N1 ~21. eog_vel: OTHER 141 > Wake 109 > N1 41 ≈ REM 40 > N2 25 > N3 23. emg: Wake 3.31 > N1 2.96 > N3 2.61 > N2 2.50 > REM 1.46 (atonia dataset-wide; SC REM 0.98 vs Wake 3.30; ST REM 4.08 vs Wake 13.27 — scales differ, order same). beta: OTHER 7.86 > Wake 4.33 > N1 2.24 > N2 2.17 > N3 2.13 > REM 2.01.

## Rates (thresholded)
spindle_like (>{N2 60pct}): OTHER .63 > Wake .52 > N3 .49 > N2 .40 > N1 .19 > REM .12 (Wake/N3 false positives = movement/slow leakage — morphology + duration needed, not power). k_like (z<−3): N2 .86 > N1 .84 > Wake .83 (movement!) > REM .80 > OTHER .79 > N3 .54 (N3 slow swamps single-K detector — use template, not min). arousal-proxy: OTHER .61 > Wake .50 > N1 .10 > N2 .05 > N3 .04 ≈ REM .04 → N1 double N2 (fragmentation lives in N1).

## Transitions (boundary epochs)
46.5% of N1 adjacent to a label change (vs N2 16%, REM 11%, Wake 2%). Trans epochs: lower spindle/slow/eog/beta than stable (2.06/33/43/2.37 vs 2.44/49/79/3.37) — boundaries are attenuated/mixed, not bursts. Implication: context helps most for N1; never oversmooth singles (N1 2872 islands are the Macro-F1 battleground).

## Age (SC full)
N3% by decade: 20–40s 5.36% → 40–60 2.41% → 60–80 2.90% → 80+ 1.70% (`age_n3.png`). Age-norm SQI or age-stratified eval required.

## Drug paired (ST, within-subject placebo vs temazepam)
Temazepam −20 Wake epochs, −20 N1, +39 N2, N3/REM flat (means per night). Consolidation signature: less fragmentation, more N2. Always paired test, never pooled.
