# Wake–REM ambiguity: EEG alone is not enough (dedicated EDA)

> **Wake and REM can look surprisingly similar in EEG alone.**
> **Both can show low-amplitude mixed-frequency EEG.**
> **EOG and chin EMG help resolve the ambiguity:**
> **REM ≈ wake-like EEG + rapid eye movements + low chin EMG.**
> **That is one reason multimodal sleep staging is valuable.**

Tables: `baseline_full_b*.parquet` (459k), `subject_fingerprints.csv`. Figs: `wake_rem_overlap.png`, `wake_rem_emg.png`.

## EEG-only overlap (full-dataset numbers)
- Fpz rel-power medians — Wake vs REM: delta .811 vs .711, theta .085 vs .147. Theta helps (Fisher .54 pooled) but distributions overlap heavily (see `wake_rem_overlap.png` left: Wake/REM theta histograms almost on top of each other).
- Fisher Wake–REM (pooled): theta .536 > pz_delta .407 > eog_ptp .329 > alpha .107 > delta .063 > beta .044. **Delta .06 ≈ useless.** Pz_alpha .06 alone weak — posterior alpha is Wake-specific only in eyes-closed quiet Wake, not daytime active Wake (SC day!).
- SC split: theta .539, delta .073. ST split: theta .499, delta .002. **Delta never separates Wake–REM.** Do not build EEG-delta Wake/REM logic.

## EOG resolves it (SC strongly, ST noisily)
- Medians eog_ptp: Wake 548 vs REM 242 (pooled); SC 548 vs 214; ST 526 vs 375.
- Fisher: SC eog_ptp .752 / eog_std .773 (best features in SC) vs ST .075/.014 (high variance — ST Wake includes hospital pre-sleep restlessness + telemetry quant flats; still median 1.4×, and rapid-vs-slow morphology, not ptp alone, carries ST).
- `wake_rem_overlap.png` right: log-EOG separates the modes that theta merges. N1 slow-rolling vs REM rapid bursts need velocity/morphology (eog_vel: Wake 109 > REM 40 > N1 41 > N2 25 — REM+N1 above N2).

## Chin EMG resolves it — ONLY within-cohort (critical trap)
- Medians: pooled Wake 3.3 vs REM 1.5; SC 3.3 vs 1.0 (3.3×); ST 13.3 vs 4.1 (3.2×). Order identical, scales 4× apart.
- Fisher: SC .959 (top-1 in SC) vs pooled .001 (dead last!) vs ST .065 (variance-heavy).
- **Lesson in bold: never pool raw EMG across SC/ST. Normalize per-record (or per-cohort) first — otherwise you destroy the best REM feature and conclude EMG is useless.**

## Rule for the model (and hardware)
**EEG → candidate (Wake-or-REM) → EOG (rapid?) + EMG (atonia?) → REM.** Single-EEG models must pay for this with context + N1/REM priors; frontal-EEG+EOG is the minimal fix; +chin-EMG (per-record normed) is the reference. Evaluate Wake/REM F1 separately per cohort — pooled REM-F1 hides the ST story.
