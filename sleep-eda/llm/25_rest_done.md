# Rest done (was pending)

## Lights-off → SOL exact (`lights_off_sol.csv`, 197 rows)
Method: rec_start (EDF header) + lights_off (xls; SC subject/night, ST night→placebo/temazepam map; date rolled +1d if earlier than start). SOL = first N1/N2/N3/REM − lights_off.
- Median SOL: SC 5.0 min, ST 8.25 min, overall p50 6.5, p10 −273, p90 26.2.
- **61 negative SOL** (sleep before reported lights-off, e.g. −136…−369 min): SC daytime naps + unreliable lights-off. Do NOT define TST/SOL from lights-off blindly. Recommended analysis window: recording start → last sleep +30 min for SE; report SOL both ways (from lights-off and from first Wake→sleep transition) and flag negatives.
- TIB_lightsOff_to_end included per rec for SE recomputation.

## Per-subject fingerprints (`subject_fingerprints.csv`, 1033 rows = rec×stage)
Median Fpz bands + eog/emg + Pz bands per recording×stage (from 459k parquets). Use for outlier subjects, age/drug stratification, and nearest-subject generalization tests.

## Wake–REM
Separate bold file: `llm/24_wake_rem_ambiguity.md` + `wake_rem_overlap.png` + `wake_rem_emg.png`. Pooled-EMG trap documented (Fisher .001 pooled vs .959 SC) — per-record norm mandatory.
