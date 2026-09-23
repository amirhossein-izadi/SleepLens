# 14 Deep story — what the data actually is (beyond statistics)

## The two movies
- **SC (153 nights): a day + a night at home.** Recorder on ~15:00–17:00 (e.g. SC4001 16:13, SC4041 16:50). Subject goes home, lives normally 6–9 h (dinner, TV, walking — EOG RMS 50–100, EMG envelope ~3.4, Resp thermistor swinging ±900, Event marker baseline ~888 with button blips), lights-off ~22:00–00:38 (xls), first sleep 400–510 min after start (~00:30), ~7–8 h sleep in clear cycles (EEG RMS log-envelope rises/falls per cycle), morning Wake, then technician stops scoring → trailing `?` 1–2 h (e.g. SC4001 last `?` 6900 s). Full night figs: `figs/fullnight_SC4001E0-PSG.png`, `fullnight_SC4041E0-PSG.png`.
- **ST (44 nights): a hospital night.** Recorder on ~23:00 (ST7011 23:00), wake_before mean 52 epochs (26 min), ~8–9 h scored sleep, morning Wake, little/no `?`. `figs/fullnight_ST7011J0-PSG.png`. Placebo vs temazepam nights per subject (ST-subjects.xls).

## Lights-off vs sleep
- SC xls gives LightsOff per night (e.g. subject 0 night1 00:38). Recording start is afternoon, so LightsOff − start ≈ 6–8 h ≈ wake_before. First-sleep − LightsOff = SOL proxy (usually 10–40 min; compute per-rec from `subject_class_distribution.wake_before_ep` + xls time math — not precomputed to avoid clock-date ambiguity).
- ST lights-off in ST-subjects.xls per night (placebo/temazepam columns); start ≈ lights-off − 0–30 min.

## Aux channels tell the story
- Temp rectal (SC 1 Hz): flat 37.2 ± 0.02 daytime, slow ~0.3–0.5 °C dip after sleep onset, rise before wake — drift, not staging signal.
- Resp oro-nasal (SC 1 Hz): huge daytime swings (mean 308 std 398, −900…1806), quieter rhythmic at night — thermistor only, no calibration, 1 Hz useless for AHI.
- Event marker (SC): baseline ~888 ± 66 with presses; ST Marker (10 Hz): −31/1 two-level ID+M-E coding (ID = unit 1/2 if positive, telemetry error if negative) — movement/error flags, not sleep labels.
- Onset zoom figs (`onset_*_EEG.png`, `onset_*_EOG.png`): 10-min raw around first sleep shows alpha → theta + slow eye movements → spindle-ish — transition visible by eye.

## Are all data clean?
- **No gaps/dropouts in file continuity:** EDF records contiguous; annotation onset 0.0 = recording start; no clock offset; 30 s grid exact.
- **SC remarkably clean:** sampled audit 20×1 min/night, all 100 Hz chs median jump 0, flat-1s 0. Worst jump SC4491 EOG 0.0036 (movement, not failure).
- **ST systematic flat-quantization:** median flat-1s 6.8% (ptp <1 uV in 1 s). Worst ST7151 25.8%, ST7192 17%. First-10-min ST7151: uniq values only 567–2018/60000 samples, ptp1s_med 0.00 but std ~220 → intermittent flats + large steps (wake movement + telemetry quant/error). Not whole-night loss — mid-sleep windows normal. Treat as quantization + wake artifact; robust norm + movement-aware features required. Worst jumps ST7211 EOG 0.00135.
- **No NaN/Inf** in sampled SC4001/ST7011 all chs. Clipping: check `cleanliness_all.csv` p99/std per file before training; phys ranges (±192 SC vs ±3000 ST) already imply separate norms.
- **`?` is not dirt:** 99% trailing unscored after final Wake (q_after mean 126 ep, q_before 0). Technician stopped scoring, signal continues. Exclude from loss, include in TRT with note.
- Table: `tables/cleanliness_all.csv` (591 rows: file×100Hz-ch, jump_rate, flat1s_rate, std_med). Fig: `figs/cleanliness.png` (SC cluster at origin, ST cloud ~0.05–0.25 flat).

## What to do with this understanding
1. Train on 30-min-trimmed scored sleep; always report full-night SQI untrimmed.
2. Per-record z-score; SC/ST separate; EMG envelope-match (ST RMS→1 Hz env as extra feature, keep raw too for ST-only ablations).
3. Use lights-off from xls for SOL (parse carefully: dates cross midnight).
4. Flag ST7151/ST7192/ST7211 as low-quality validation probes, not auto-drop.
5. Show full-night RMS + hypnogram (`fullnight_*.png`) in final deck — judges grasp the home-day story instantly.
