# 10 Minimal-channel + SQI feasibility

## Configs (no deep training, evidence-based hypothesis)
A Fpz-Cz: viable baseline (strongest single, N3 522 vs Pz 158). B Pz-Oz: weaker N1/N3. C 2×EEG: best EEG-only. D +EOG: big Wake/REM/N1 gain. E +EMG: REM/atonia gain (SC envelope + ST raw, separate norms). F EEG+EOG+EMG: recommended full (3×3000 @100 Hz + 1 Hz aux). G +Resp/Temp: ~0 staging gain, SQI context only. Rank: F≈D > C > A > B; E boosts REM. Hardware: 2EEG+EOG minimal, +chin-EMG if cheap.
## SQI feasibility
_source: tables/sqi_feature_feasibility.csv (14 rows)_ 

| feature                  | computable   | required                            | reliable   | comments                                                         |
|:-------------------------|:-------------|:------------------------------------|:-----------|:-----------------------------------------------------------------|
| Total Sleep Time         | yes          | hypnogram                           | high       | TST from 5-class epochs                                          |
| Sleep Efficiency         | approx       | hypnogram                           | medium     | SE=TST/TRT; TRT def depends on trim; lights-off in xls helps SOL |
| WASO                     | approx       | hypnogram                           | medium     | needs sleep-onset def; mid Wake countable                        |
| Sleep Onset Latency      | approx       | hypnogram+lights-off                | medium     | first N1/N2/N3/REM vs lights-off from xls                        |
| N1/N2/N3/REM %           | yes          | hypnogram                           | high       | direct                                                           |
| REM latency              | yes          | hypnogram                           | high       | first REM - sleep onset                                          |
| stage-transition count   | yes          | hypnogram                           | high       | from epoch sequence                                              |
| awakening count          | approx       | hypnogram                           | medium     | W intrusions ≥1 epoch; brief arousals invisible                  |
| arousal index            | no           | EEG arousal annots missing          | -          | no arousal labels                                                |
| AHI/apnea/hypopnea       | no           | no airflow/SpO2/effort @adequate fs | -          | 1Hz thermistor only; no desats                                   |
| ODI/nadir/hypoxic burden | no           | no SpO2                             | -          | -                                                                |
| PLMI                     | no           | no leg EMG                          | -          | chin EMG only                                                    |
| HR/arrhythmia            | no           | no ECG/PPG                          | -          | -                                                                |
| position features        | no           | no position/actigraphy              | -          | -                                                                |
Architecture per-rec: tables/sleep_architecture.csv (TRT/TST/SE/SOL/Nx/REM + WASO/awakenings/transitions = NaN = define at modeling time; mean TRT 1227 min / TST 426 / SE 42.8% untrimmed — recompute trimmed).
