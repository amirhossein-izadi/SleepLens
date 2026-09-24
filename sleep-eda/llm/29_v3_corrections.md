# v3 corrections (supersedes stale claims)

- Preprocessing: fixed `0.3–35 + notch 50 + z-score` RETIRED → ablations: raw+robust vs 0.3–35+robust; per-record z vs median/IQR+clip (ST7011: 150 µV at z=0.2 vs robust 3.5). Never global stats.
- Channels: `Fpz best` + `+EOG +11%` RETIRED as established → hypotheses for model ablation (Fpz/Pz/2EEG/+EOG/+harmonized-EMG). Pz Wake-alpha unique.
- EMG: ST 1 s-RMS is an APPROXIMATION of SC hardware (HPF→rect→LPF→1 Hz); prefer modality-specific encoders or per-epoch features.
- Splits: use `folds5_v3.csv` (BENCHMARK profiles) + tracks A/B/C; old 70/15/15 + folds5 = compat only.
- Windows: BENCHMARK_30 (literature/training) ≠ MAIN_SLEEP opportunity window (SQI). Masks independent (`in_main_window` ≠ `valid`). Old `in_main` deprecated.
- Architecture: use `sleep_architecture_v3.csv` (`SE_proxy`, WASO onset→final, coverage incl OTHER/GAP). Old tables in `DEPRECATED.md`.
