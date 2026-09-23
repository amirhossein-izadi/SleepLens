# 06 Stage physiology (in-data, not textbook)

## SC4001 Fpz-Cz relative PSD (median ≤8 epochs/stage, welch 1024)
Wake d.82/t.12/a.03/s.01/b.03; N1 d.64/t.25; N2 d.80/s.02; N3 d.88; REM d.58/t.34. N3-delta, REM-theta, N1-theta separations hold.
## Fpz-Cz vs Pz-Oz (stage-relevant band median power)
Wake-alpha Fp 11.3 vs Pz 16.8 (Pz alpha slightly stronger here); N1-theta 35.1 vs 13.1; N2-sigma 4.14 vs 1.83; N3-delta 522 vs 158; REM-theta 42.7 vs 23.7. Fpz-Cz empirically stronger except Wake-alpha.
## EOG/EMG RMS (median ≤10 epochs/stage)
_source: tables/eog_emg_by_stage.csv (10 rows)_ 

| file             | stage   |   eog_rms_med |   emg_rms_med |   emg_sf |
|:-----------------|:--------|--------------:|--------------:|---------:|
| SC4001E0-PSG.edf | Wake    |       95.0624 |      3.41037  |        1 |
| SC4001E0-PSG.edf | N1      |       25.4825 |      3.04991  |        1 |
| SC4001E0-PSG.edf | N2      |       15.6047 |      2.74051  |        1 |
| SC4001E0-PSG.edf | N3      |       18.5119 |      2.84447  |        1 |
| SC4001E0-PSG.edf | REM     |       15.3685 |      0.384931 |        1 |
| ST7011J0-PSG.edf | Wake    |       46.7863 |     51.5072   |      100 |
| ST7011J0-PSG.edf | N1      |       75.9257 |     22.1797   |      100 |
| ST7011J0-PSG.edf | N2      |       95.2443 |     18.9552   |      100 |
| ST7011J0-PSG.edf | N3      |       70.7354 |      7.65123  |      100 |
| ST7011J0-PSG.edf | REM     |       93.2457 |      4.70331  |      100 |
- SC4001 (EMG 1 Hz): EOG Wake 95 → N2 15; EMG REM 0.385 (atonia) vs Wake 3.41/N1 3.05 — envelope still useful.
- ST7011 (EMG 100 Hz): EOG N2 95/REM 93 vs Wake 47 (sample variance, n=10 — don't overclaim); EMG Wake 51.5 → REM 4.7 gradient strong.
Takeaway: EOG helps Wake/REM/N1 transitions; EMG helps Wake vs REM in both cohorts despite fs mismatch (use RMS/envelope features, cohort-specific norm).
Figs in words: psd_* = N3 top at <4 Hz, REM/Wake higher 4–13; spec_* = N3 bright low band; eog_bystage = sharp saccades Wake/REM vs flat N2/N3. See 12.
