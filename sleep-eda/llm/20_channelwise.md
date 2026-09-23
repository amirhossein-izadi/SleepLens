# 20 Channel-by-channel: spatiality + frequency (pooled 8 recs SC+ST)

Tables: `tables/channelwise_stage_bands.csv`, `channelwise_medians.csv`. Figs: `figs/chwise_*.png` (3), `spatial_gradient.png`.

## Spatial (what each derivation sees)
- **EEG Fpz-Cz = V(Fpz)−V(Cz):** frontopolar→central midline. Frontal slow waves/K-complexes/frontocentral spindles/vertex; near eyes → ocular contamination (artifact + useful REM/N1 eye info). Best single for N3/N1 transitions.
- **EEG Pz-Oz = V(Pz)−V(Oz):** parietal→occipital. Posterior alpha (eyes-closed Wake), visual-morning Wake, posterior theta/sigma. Complements Fpz (anterior-posterior axis).
- **EOG horizontal:** outer-canthi bipolar. Slow rolling (N1), rapid saccades (Wake/REM), quiet N2/N3. Time-domain (ptp/zc), not bandpower.
- **EMG submental:** chin tone/atonia. SC = 1 Hz envelope (HPF+rect+LPF rms, ±5) — atonia level only; ST = 100 Hz raw — bursts + atonia.
- **Resp oro-nasal (SC 1 Hz):** thermistor, uncalibrated, day-noise >> night-rhythm. **Temp rectal:** 37.2±drift. **Event/Marker:** button/telemetry flags.

## Frequency fingerprints (pooled median rel-power, 8 recs)
- **Fpz-Cz:** N3 d.871/t.076/a.028/s.022/b.023; N2 d.723/t.160/a.041/s.032/b.053; N1 d.613/t.178/a.084/s.036/b.088; REM d.640/t.179/a.056/s.021/b.025; Wake d.842(!)/t.095/a.022/s.011/b.030 → Wake-delta is movement artifact; фронтальный N3 + N1/REM-theta real.
- **Pz-Oz:** Wake d.437/t.117/**a.170/s.104/b.249** (posterior eyes-open Wake = high-freq rich, NOTHING like Fpz Wake) ; N1 a.138/t.216; REM a.103/t.174; N2 s.058; N3 d.822 → **Pz owns Wake-alpha/beta**, Fpz owns N3-delta/N1-theta.
- **EOG:** all delta .78–.90 (slow eye signal); staging via ptp (Wake 548 > REM 242 > N2 102), not bands.

## Gradient (log10 Fpz/Pz, pooled)
Delta: N3≈0, Wake>0 (frontal movement), others small. Alpha: Wake<0 (posterior alpha!), N1/N2≈0. → Use BOTH: Fpz for deep/transition, Pz for Wake/N1 boundary. Expect D(EEG+EOG) gain concentrated in Wake/N1/REM (matches +11% Fisher).

## Hardware read
2 EEG = anterior + posterior views (not redundant). +EOG = orthogonal eye axis. +chin EMG = atonia axis. Minimal product: frontal EEG + EOG (N1/REM), add posterior EEG if Wake errors dominate.
