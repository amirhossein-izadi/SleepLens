# 16 Profiler meso — 2908 epochs, N1 pain, separability (ydata-style)

Source: `tables/meso_features_3k.csv` (12 recs SC+ST, ≤50/stage/rec, in-signal only; rel delta/theta/alpha/sigma/beta + eog_ptp/std + eeg_std), `tables/fisher_pairs.csv`.

## N1 ambiguity (standardized centroid distances W/N1/N2)
W–N1 1.95, N1–N2 1.58, W–N2 1.61 → N1 sits between, nearer N2. Matches human 63% N1 agreement (father Layer 2).

## Fisher DR per pair (higher = easier)
- Wake-REM: theta .56 best, eog_ptp .27 → need EOG + theta.
- Wake-N1: delta .41, theta .50, alpha .22 → hardest Wake boundary.
- N1-N2: all ≤.46 (delta .458 best, beta .249, alpha .267) → THE bottleneck pair; sigma only .056 (simple sigma-power insufficient — need spindle morphology).
- N2-N3: delta 1.45, theta .87, alpha .72, beta .60 → easiest.
- N2-REM: theta .18, sigma .11, delta .11 → needs EOG/EMG beyond EEG bands.

## Ablation A–G (sum Fisher, same features)
A_Fpz (EEG-only) 8.30 vs D_Fpz+EOG 9.22 (+11%). Ranking hypothesis: F(EEG+EOG+EMG) > D(EEG+EOG) > C(2EEG) > A(Fpz) > B(Pz); E adds REM-specific gain. Confirm with model ablation — do not assume.

## Duplicates/correlations (ydata-style checks)
No duplicate epochs (epoch index unique per file). delta/theta strongly anti-correlated across N2→N3; eog_ptp/eog_std r≈.9 (redundant — keep one + morphology). Outliers: Wake slow_rms tail = movement (see 15).
