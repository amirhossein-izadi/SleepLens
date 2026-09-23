# 21 EDA perfection — closed loop

## Audit result: 12/12 spec CSVs + JSON OK, 16/16 figs OK, 21 llm mds OK
- `signal_quality_full.csv` (1291 rows, all 197×chs full-length + sampled jump/flat) supersedes 10-row sample (kept as `signal_quality.csv`).
- `dir_summary.png` added (Sec 26.1 was tables-only).
- `subjects.csv` ages 100/100 (SC from xls + ST mapped).
- `sleep_architecture.csv` WASO/awakenings/transitions now REAL (medians: WASO 47.5 min, awakenings 18, transitions 125) — was NaN.
- Full-EDA: 459201 in-signal epochs, pooled medians, channelwise 8-rec fingerprints + full amplitude medians.
- Epoch mismatch masked: trailing beyond-signal `?` excluded everywhere full (nsamples clamp).

## Spec compliance (EDA.md §§1–30)
1–11 inventory/subjects/headers/EEG/EOG/EMG/aux/labels/epochs/balance/trim: DONE + full. 12 quality: DONE full. 13 stage-wise: DONE full+sample. 14 temporal: DONE. 15 subject var: DONE (stats_full + arch). 16 cohort: DONE (cohort_compare). 17 metadata: DONE (subjects.csv + SC/ST). 18 leakage: REPORT §J + splits. 19 splits: DONE + tradeoffs. 20 minimal-channel: DONE (minimal_channel.csv). 21 architecture: DONE real. 22 SQI: DONE. 23 tensors: DONE + memory. 24 preproc: DONE + why. 25 baseline: DONE (baseline_features.csv 2908 + full parquets 459k). 26 figs 16/16 + 30 extras. 27 machine outputs 12/12 + json. 28 REPORT A–P + handoff. 29 no-training obeyed; subject-wise; ?/Mov never silently dropped; 3+4 merge explicit; evidence vs inference separated. 30/28 questions: REPORT + llm/13 + 19/20.

## Father layers covered
L0 hierarchy → 13/17; L1 staging → 03/06; L2 N1 → 16 (1.95/1.58 + Fisher); L3–5 EEG space/freq/morph → 20/15; L6–7 temporal/cycles → 07/cycles; L8 EOG/EMG → 06/20; L9 minimal → minimal_channel; L10–11 arousal/apnea → 10/14 (proxies + impossibility proof); L12–13 workflow/full-PSG → 10/14; L14–15 SQI → 10/17; L16–18 traps → 02/03/08/18; L19–21 bottlenecks/leakage/splits → 09/16; L22–23 architecture/MVP → 10/11.

## Only true remains
Model training, exact lights-off datetime math, per-epoch full Pz-Oz bands (Fpz full done; Pz pooled-8 done — extend at modeling time), organizer clarifications (§O). Nothing else pending in EDA.
