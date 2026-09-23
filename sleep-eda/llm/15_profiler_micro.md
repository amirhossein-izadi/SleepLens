# 15 Profiler micro — events inside epochs (ydata-style)

Source: `tables/micro_events.csv` (240 epochs: 4 recs × 5 stages × 12). Bands via Butterworth RMS; K-like = min < −3σ and <−40 uV; sw_occ = |0.5–4 Hz| >2.5σ fraction; EOG ptp/zc; EMG RMS (SC 1 Hz env, ST 100 Hz raw — compare within-cohort only).

## Medians by stage (pooled)
- sigma_rms: N3 2.80 > N2 2.06 ≈ Wake 2.06 > N1 1.57 > REM 1.45 → N2 spindle bump holds, but Wake movement inflates sigma (artifact caveat).
- slow_rms: N3 20.2 ≈ Wake 19.8 (movement!) > N2 12.0 > N1 7.3 > REM 6.7 → Wake slow-power is artifact, not physiology; use Wake-alpha/EOG to disambiguate.
- alpha_rms (Pz-Oz): Wake 2.15 > N3 1.93 > N1 1.58 ≈ REM 1.56 > N2 1.47.
- beta: N2 2.91 ≈ N1 2.86 ≈ Wake 2.85 > N3 2.19 > REM 1.88.
- sw_occ: N2 .0315 > Wake .0275 > N3 .027 (occ metric saturates — prefer slow_rms).
- eog_ptp: Wake 586 >> N1 337 > N2 279 > REM 259 > N3 157 → EOG separates Wake, then N1.
- emg_rms pooled meaningless across fs; within-rec: SC REM 0.385 vs Wake 3.41 (atonia holds at 1 Hz); ST REM 4.7 vs Wake 51.5.
- kcomplex_like rate: N2 .90 > N3 .75 > N1 .58 ≈ REM .56 > Wake .46 → N2 morphology signal real.

## Implication (father Layers 5/8/10)
N2 needs morphology (spindle/K), not just bandpower. Wake-REM EEG-alike → resolve with EOG+EMG. Arousal proxy (beta burst + EMG rise) could be built from beta_rms + emg_rms columns — not scored here (no arousal labels), but columns ready.
