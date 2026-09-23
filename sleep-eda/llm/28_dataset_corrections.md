# Audit verdicts: validated against raw EDFs (accept / reject each, with numbers)

Critic had ZIP-only; I re-ran everything on the 8.7 GB signals. Verdicts below. Fixed artifacts listed at the end.

## ACCEPTED (bug/confirmed, fixed)
1. **ST −1430 SOL bug — ACCEPT.** 3 recs (ST7162/7022/7021) hit −1429/−1432 from date-roll on seconds-level differences. Fixed with 3 h tolerance (`resolve_lo`): ST<−1000 now 0. `sleep_architecture_main.csv`.
2. **Annotation≠signal intersection — ACCEPT.** SC hyps exceed signal (median +124 epochs); ST signal exceeds hyp (leading GAPs in 28/44 recs, up to 226 slots; 2 mid gaps incl. ST7221 65 slots). Authoritative onset-grid table: `epochs_authoritative.parquet` (484,111 slots; 457,652 valid; GAP=692 all-ST; 509 labelled-but-no-signal Wake dropped; 2,238 signal-but-unlabelled flagged).
3. **Concatenation assumption — ACCEPT with scope.** SC fully contiguous (0 gaps). ST has 692 GAP slots (28 recs) + 2 contiguity breaks (ST7121 1 slot, ST7221 65 slots). Old code silently misaligned ST epochs after gaps. Fixed by onset grid.
4. **Architecture table wrong — ACCEPT.** Old SE≈29% (TRT=1440), SOL from recording start. Recomputed on MAIN window: SE 85.9% (SC 84.7/ST 91.8), TST 426, SOL 10.5, WASO 78 (SC 86.5/ST 37.0), REM-lat 80. `sleep_architecture_main.csv`.
5. **wake_after includes ? — ACCEPT.** SC4001 wake_after 1138 incl. 230 ?. Old column kept for compat; MAIN architecture uses real Wake-only WASO.
6. **N3% denominator — ACCEPT.** Old N3/(all epochs). Corrected N3/TST by decade (MAIN): 20–40 ≈16.8%, 40–60 ≈8.0%, 60–80 ≈9.7%, 80+ ≈5.7% (critic: 17.4/7.8/9.6/5.3 — reproduced).
7. **Drug needs pairing+normalization — ACCEPT.** Reproduced: Wake −18.7, N1 −18.5, N2 +40.4, TST +32.9 epochs; N1% −2.8, N2% +3.3, N3/REM ≈0 (critic: −20/−20/+39/+29, −3/+3.4 — match).
8. **ST quality was mismeasured — ACCEPT, strongly.** Marker decode: values {ID 1/2, error −30/−31, press 33/34}; corr(marker-neg, flat)=**0.92** — flats ARE telemetry errors (ST7151 neg 23.8%). Labelled-span flats median 0.0008 vs full-record 0.068 (ST7151 25.8%→0.97%). `marker_quality.csv`, `quality_labelled_ST.csv`. Worst labelled: ST7221 6.4% (also has mid GAP).
9. **Clipping — checked, minor.** Max saturation 1.5% (ST7041 Pz-Oz); rest ≤0.35%. `clipping_audit.csv`.
10. **EMG harmonization — ACCEPT, works.** ST raw→1 Hz RMS envelope: Wake/REM Fisher SC 0.93, ST 0.72 (was 0.001 pooled-raw — scale trap). `emg_harmonized.csv`.
11. **Robust norm — ACCEPT, decisive.** ST7011: 150 µV wave at z=0.2 (invisible) vs robust 3.5 (visible); means −116…−206 corrupted by errors. Compare z vs median/IQR (+clip) as ablation; never global stats.
12. **Fpz-best + Fisher-sum + filter/notch — ACCEPT as overclaims.** Fpz-best → hypothesis (Pz Wake-alpha unique). Fisher sums retired (kept as exploratory). 50 Hz peak/base 1.8/1.4, 35–50 Hz share ≤3.4% → notch redundant; filter = ablation (raw+robust vs 0.3–35+robust).
13. **Arousal proxy ≠ index — ACCEPT.** Kept exploratory-only; no arousal labels exist.
14. **Three windows — ACCEPT, built.** FULL_VALID 457,652 / BENCHMARK_30 237,936 / MAIN 196,959. Per-window×cohort class + transition tables (`trans_{valid,bench,main}_{SC,ST}.csv`); Wake self SC .988→.896 valid→main (daytime inflation removed).
15. **Splits/folds — ACCEPT.** Old 70/15/15 kept as compat; added `folds5.csv` (20 subj/fold, Wake 61–65/N1 5–6/N3 3.5–5.3) + SC→ST / placebo-temazepam / age-strata protocol in REPORT addendum (training itself out of EDA).

## REJECTED / qualified
16. **Marker 10 Hz vs doc 1 Hz — raw wins: 10 Hz.** nsamp/duration = 10.0 exactly (2 files + pattern). Doc describes original telemetry rate; stored file is 10 Hz constant-valued (3 unique values). Use as mask, never as input (leakage).
17. **"Train on lab" — REJECT as default** (agrees with critic): ST=22 subj, younger, insomnia+drug, EMG/format/age shifts. Test SC→ST, don't assume.
18. **Mid-window ? catastrophism — qualified.** SC4762 (133 ? + 15 Mov mid) real; but only 4 SC recs have mid-? at all. Mask + coverage flag (`unscored_pct` in architecture), not a blocker.

## New files (this pass)
`epochs_authoritative.parquet`, `sleep_architecture_main.csv`, `trans_*_*.csv` (6), `marker_quality.csv`, `quality_labelled_ST.csv`, `clipping_audit.csv`, `emg_harmonized.csv`, `folds5.csv`, `lights_off_sol.csv` (fixed), `subject_fingerprints.csv`. Scripts V1, F1–F4.
