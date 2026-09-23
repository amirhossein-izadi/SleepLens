# 18 Gaps closed (audit addendum)

## Fixed this round
- `tables/subjects.csv` (100 prefixes) + `subjects_SC/ST.csv` — Sec 27 complete (was missing combined).
- `tables/cohort_compare.csv` — SC 78 subj/153 rec/22.68 h/night/Wake 64.9% vs ST 22/44/8.61 h/Wake 10.35%. Class-balance domain shift is huge — stratify splits (done) and report per-cohort Macro-F1.
- `tables/minimal_channel.csv` — A–G with coverage/availability/quality/sep/hardware/usefulness (Sec 20 complete).
- `tables/epoch_mismatch.csv` — hyp longer than signal by mean 109 epochs (e.g. SC4001 sig 2650 vs hyp 2880, +230). Trailing `?`/Wake beyond recording end has no signal — mask epochs with (i+1)*3000 > nsamples. Clock aligned at 0.0, no offset; mismatch is trailing unscored, not gaps.
- `figs/persubject_stacked.png` — top-30 stacked Wake/N1/N2/N3/REM (Sec 26.5 complete).
- `figs/eeg_per_stage_SC4001.png` — Fpz-Cz 30 s × 5 stages, same ±150 scale (Sec 26.6 complete).
- `tables/tensor_memory.csv` — [1,3000]=12 KB … batch64-ctx11 ≈25 MB (Sec 23 complete).
- `tables/baseline_features.csv` — 2908 rows with subject_id/recording_id/label + 8 feats, no future-label leak (Sec 25 complete; sample file kept as baseline_features_sample).

## True remains (out of EDA scope or needs organizers)
1. Model training + test Macro-F1 (explicitly forbidden in EDA).
2. Lights-off → SOL/WASO exact per-rec (needs date-cross-midnight parsing — formula ready, not executed).
3. Full per-subject spectral table (153×44 spectra — sampled evidence sufficient for EDA; run at modeling time).
4. Organizer clarifications: ?/Mov scoring, test cohort/trim, corrupt-7 ST in test, lights-off as feature, hardware budget (REPORT §O).
