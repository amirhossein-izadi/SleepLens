# 19 Full-EDA (beyond sample, still EDA — no models)

## Coverage
- `tables/signal_stats_full.csv` (1291 rows = 197 recs × all chs, full-length time-domain: mean/std/rms/min/max/p1/p99/nan/flat).
- `tables/baseline_full_b{0,1,2}.parquet` → 459201 in-signal epochs (trailing beyond-signal ? excluded by nsamples clamp). Wake 289859 / N2 88983 / REM 34184 / N1 25175 / N3 19454 / OTHER 1546.
- `tables/stage_band_medians_full.csv` — pooled medians below. Method: per-epoch Hann rFFT (3000 @100 Hz), rel powers 0.5–30.

## Pooled stage medians (FULL, not sample)
- delta: N3 .924 > Wake .811 (movement!) > N2 .795 > OTHER .768 > REM .711 > N1 .697
- theta: REM .147 > N1 .119 > N2 .103 > OTHER .089 > Wake .085 > N3 .047
- alpha: N1 .076 > REM .059 > N2 .051 > OTHER .038 > Wake .033 > N3 .017 (Wake-alpha diluted by daytime eyes-open; Pz-specific analysis in 06)
- sigma: N1 .045 > N2 .0375 > REM .033 > OTHER .031 > Wake .023 > N3 .011 (N1-sigma = vertex/spindle edge; N2>REM holds)
- beta: OTHER .100 > N1 .082 > Wake .063 > REM .058 > N2 .039 > N3 .008
- eog_ptp: Wake 548 > OTHER 566 (wake!) > REM 242 > N3 145 > N1 142 > N2 102 → EOG ladder: Wake >> REM > N1/N3 > N2
- emg_rms pooled (mixed fs, interpret with cohort split in 06): Wake 3.31 > OTHER 3.31 > N1 2.96 > N3 2.62 > N2 2.50 > REM 1.46 → REM atonia holds dataset-wide
- eeg_std: OTHER 36.7 > N3 28.6 > Wake 25.6 > N2 15.4 > REM 12.5 > N1 11.8 (N3 slow-wave amplitude; OTHER = wake activity)

## Full signal medians (std)
SC: Fpz 25.2, Pz 11.1, EOG 68.8, EMG-env 1.10, Resp 264, Temp 0.22, Event 35.3. ST: Fpz 64.4, Pz 86.6, EMG-raw 81.6, EOG 124.8. ST amplitudes ~2–3× SC (gain/range shift) — per-record norm mandatory.

## Standardized centroids (W/N1/N2, full 8-feat)
Wake (−.01,−.16,−.11,−.13,+.15,+.44,+.36,+.19), N1 (−.55,+.55,+.76,+.42,+.21,−.69,−.53,−.53), N2 (+.12,+.18,+.13,+.39,−.36,−.96,−.80,−.41) → N1 distinct (+theta/alpha, −EOG), N2 (+sigma, −EOG/beta). Confirms sampled 16 with tighter numbers.

## Files
Full stats + 3 parquets + medians CSV. Scripts 13_full_stats.py, 14_full_epochs.py. No training, no labels leaked (features from signals only, labels copied for grouping).
