# Suspicious audit: naps vs lights-off (precise, skeptical)

Tables: `sol_sustained.csv` (153: first vs sustained SOL, run lengths), `neg48_classified.csv`, `nap_character.csv`, `lights_off_verify.csv`.

## Why first-epoch SOL is fragile
- First-sleep run length: median 8 epochs, 25% ≤2, **30/153 singletons** (30 s sleep → Wake). A single N1 blip moves SOL by hours.
- Sustained SOL (first 10-min window with ≥16/20 sleep epochs): median 9.0 min vs first-epoch 5.0; negatives **48 → 28**. 20/48 were blips/dozes, not sleep onset by any clinical sense.

## Rollover audit (my date logic)
- SOL range −621…+113 (sustained −560…+186). No ±1440 h errors → midnight-rollover correct. Negatives are physiological/reporting, not date bugs.

## Rule-based split of the 48 (gap + duration; labels provisional)
- genuine-nap 15 (gap≥30 min, ≥5 min sleep; median SOL −291): evening naps, awake gap, main sleep later.
- early-onset? 15 (gap<30, ≥10 min; median −103): fell asleep before lights-off and stayed — either unreported early lights-off or sleep-pressure onset; treat as main-sleep start, not nap.
- doze-blip 14 (gap≥30, <5 min; median −195): isolated N1 0.5–4 min in the evening — drowsiness, vanishes under sustained def.
- lights-off-noise 4 (gap<30, <10 min; median −10.5): within reporting/scorer noise.

## Sensitivity (SC medians)
TST 428 min; SE untrimmed 29.7% (meaningless — daytime included); SOL_first 5.0 vs SOL_sust 9.0.
**Prescription:** primary SOL = sustained; analysis window = lights-off → last sustained sleep +30 min; TST/SE/WASO reported with + without pre-window naps; the 28 sustained-negatives get per-night notes (nap vs early-onset), never silent pooling.
