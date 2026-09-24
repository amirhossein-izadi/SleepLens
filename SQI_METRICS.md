# SQI Nightly Metrics

Every metric below is implemented and extracted for each night (one row per night).
Stage codes: `0` = Wake, `1` = N1, `2` = N2, `3` = N3, `4` = REM. Epoch length is 30 s.

## Continuity — "did the patient sleep through the night?"

| Metric | Type | Explanation |
|---|---|---|
| `tib_min` | float, minutes | Time in bed: number of epochs in the lights-off window × 0.5. This is the window length itself — the denominator against which efficiency is judged. |
| `uns_frac` | float, 0–1 | Fraction of window epochs that are unscored. It says how much of the night to trust, not how good the sleep was — a high value means the other numbers rest on thin data. |
| `tst_min` | float, minutes | Total sleep time: epochs spent in N1+N2+N3+REM × 0.5. The single most basic quantity of sleep — everything else refines this number. |
| `se_pct` | float, percent | Sleep efficiency: 100 × sleep epochs ÷ scored epochs (unscored epochs excluded from the denominator). The #1 overall quality number — low efficiency means a restless night spent mostly tossing in bed. |
| `sol_min` | float, minutes | Sleep-onset latency: index of the first sleep epoch × 0.5. Long values mean trouble falling asleep, the classic insomnia complaint. NaN if the patient never slept. |
| `waso_min` | float, minutes | Wake after sleep onset: Wake epochs counted at/after the first sleep epoch × 0.5. High values mean a fragmented, shallow night — the patient kept surfacing out of sleep. |
| `rem_lat_min` | float, minutes | REM latency: (first REM epoch at/after onset − onset epoch) × 0.5. The delay before the first dream period; unusually short values can signal depression or sleep deprivation, unusually long ones delayed dreaming. NaN if there is no REM. |

## Fragmentation — "how broken was the night?"

| Metric | Type | Explanation |
|---|---|---|
| `n_awakenings` | int, count | Number of sleep→Wake transitions at/after sleep onset. Each awakening breaks the sleep cycles apart — even ones the patient won't remember in the morning. |
| `awakening_index` | float, events/hour of sleep | `n_awakenings` ÷ total-sleep-time hours. Normalizes the count so short and long nights can be compared fairly. |
| `n_stage_shifts` | int, count | Number of label changes between consecutive scored epochs over the whole window. Restless brains flip stages constantly; calm brains glide through them. |
| `shift_index` | float, events/hour of sleep | `n_stage_shifts` ÷ total-sleep-time hours. Same normalization idea as the awakening index. |
| `sfi` | float, events/hour of sleep | Sleep fragmentation index: (`n_awakenings` + `n_stage_shifts`) ÷ total-sleep-time hours. One clinically flavored number for overall brokenness. |
| `longest_sleep_bout_min` | float, minutes | Longest uninterrupted run of sleep epochs × 0.5. Long unbroken stretches are where the restorative work happens. |
| `mean_sleep_bout_min` | float, minutes | Mean length of all sleep runs × 0.5. Higher means steadier sleep that doesn't keep collapsing into wakefulness. |
| `longest_wake_post_onset_min` | float, minutes | Longest single Wake run at/after onset × 0.5 — the 2 a.m. stare-at-the-ceiling episode. 0.0 when there is none. |

## Architecture — "did the patient get the right mix?"

| Metric | Type | Explanation |
|---|---|---|
| `n1_pct_tst` | float, percent | 100 × N1 epochs ÷ total-sleep-time epochs. N1 is doorway light sleep — a little is normal, a lot means the night never got going. |
| `n2_pct_tst` | float, percent | 100 × N2 epochs ÷ total-sleep-time epochs. N2 is the stable backbone of the night and usually its largest share. |
| `n3_pct_tst` | float, percent | 100 × N3 epochs ÷ total-sleep-time epochs. N3 is deep sleep, the physically restorative part — too little leaves sleep unrefreshing. |
| `rem_pct_tst` | float, percent | 100 × REM epochs ÷ total-sleep-time epochs. REM is dream sleep, tied to mood regulation and memory — too little flattens the night. |
| `wake_pct_tib` | float, percent | 100 × Wake epochs ÷ scored epochs. The mirror image of sleep efficiency. |
| `tr_A_B` (25 columns, e.g. `tr_N2_N3`, `tr_REM_WAKE`) | int, counts | Counts of consecutive scored→scored epoch pairs from stage A to stage B, including self-pairs (e.g. N2→N2). They encode the night's path: healthy sleep cycles N1→N2→N3→N2→REM, while odd jumps (N3→Wake, REM→N1) flag instability. |
| `n_rem_episodes` | int, count | Number of contiguous REM runs lasting ≥ 6 epochs (3 min). This is the "how many sleep cycles did the patient get" answer — each full cycle runs about 90 minutes. |
| `mean_rem_bout_min` | float, minutes | Mean length of those ≥ 3-min REM runs × 0.5. Dream periods should grow longer toward morning. NaN when there are none. |
| `n1_pct_first_half` | float, percent | 100 × N1 epochs ÷ sleep epochs in the first half of the post-onset window (split at its midpoint). Healthy nights front-load deep sleep, so early N1 should be low. NaN if that half has no sleep. |
| `rem_pct_first_half` | float, percent | Same as above for REM in the first half — normally the smaller dream share. |
| `n1_pct_second_half` | float, percent | Same as above for N1 in the second half — light sleep legitimately grows toward morning. |
| `rem_pct_second_half` | float, percent | Same as above for REM in the second half — normally the larger dream share. |
| `move_annot_frac` | float, 0–1 | Fraction of window seconds covered by technician annotations that are not sleep stages (e.g. "Movement time"). A human cross-check of restlessness, independent of the stage labels. |

## EEG band power — "what was the brain doing?" (from `EEG Fpz-Cz` at 100 Hz)

Each 30-s epoch is split into wave-speed bands with a Welch power spectrum, like bass → treble. Bands in Hz: delta 0.5–4, theta 4–8, alpha 8–12, sigma 12–16, beta 16–30; total 0.5–30. `abs_*` = summed power in the band; `rel_*` = band power ÷ total power. Nightly value = mean over all window epochs.

| Metric | Type | Explanation |
|---|---|---|
| `abs_delta_mean` | float, power | Mean absolute delta (0.5–4 Hz) power — the slow, tall "bass" waves of deep sleep and the signature of restorative N3. |
| `rel_delta_mean` | float, 0–1 | Mean relative delta power — delta's share of total power, so nights with different overall signal strength stay comparable. |
| `abs_theta_mean` | float, power | Mean absolute theta (4–8 Hz) power — drowsy, drifting waves that dominate N1 and the slide into sleep. |
| `rel_theta_mean` | float, 0–1 | Mean relative theta power. |
| `abs_alpha_mean` | float, power | Mean absolute alpha (8–12 Hz) power — relaxed-but-awake waves that should appear in wakefulness and vanish in deep sleep. |
| `rel_alpha_mean` | float, 0–1 | Mean relative alpha power. |
| `abs_sigma_mean` | float, power | Mean absolute sigma (12–16 Hz) power — the spindle-speed band that carries sleep spindles and their memory-consolidation work. |
| `rel_sigma_mean` | float, 0–1 | Mean relative sigma power. |
| `abs_beta_mean` | float, power | Mean absolute beta (16–30 Hz) power — fast "treble" waves of a busy brain; high beta during sleep means an aroused, non-restful night. |
| `rel_beta_mean` | float, 0–1 | Mean relative beta power. |
| `swa_nrem_mean` | float, power | Mean delta power over NREM (N1+N2+N3) epochs only — slow-wave activity, the measure of sleep-pressure release, which is the core job of the night. |
| `swa_sum` | float, power | Sum of delta power over NREM epochs — the whole night's accumulated deep-sleep work in one number. |
| `rel_delta_nrem` | float, 0–1 | Mean relative delta power over NREM epochs only — reaching roughly 20% delta is the classic N3 criterion. |
| `epochs_psd` | int, count | Number of epochs that entered the spectrum computation — bookkeeping for how much signal the power numbers rest on. |

## EEG complexity — "how predictable was the brain?" (from `EEG Fpz-Cz` at 100 Hz)

| Metric | Type | Explanation |
|---|---|---|
| `spec_entropy_nrem` | float, bits | Per epoch: Shannon entropy (base 2) of the power spectrum normalized over 0.5–30 Hz; nightly = mean over NREM (N1+N2+N3) epochs. It compresses the whole wave mix into one number for brain predictability — low means deeply asleep. |
| `spec_entropy_rem` | float, bits | Same, averaged over REM epochs — dreaming brains look busier than deep sleep but calmer than wake. |
| `spec_entropy_wake` | float, bits | Same, averaged over Wake epochs — the high end of the scale. |
| `perm_entropy_wake` | float, 0–1 | Per epoch: order-3, delay-1 permutation entropy of the raw signal, normalized by ln(6); nightly = mean over Wake epochs. It confirms the depth ordering without any frequency math. |
| `perm_entropy_nrem` | float, 0–1 | Same, averaged over NREM epochs — the low end of the scale. |
| `perm_entropy_rem` | float, 0–1 | Same, averaged over REM epochs — sitting between NREM and wake. |

## Microstructure — "the tiny events that protect (or ruin) sleep" (YASA detectors on `EEG Fpz-Cz` at 100 Hz, in µV)

| Metric | Type | Explanation |
|---|---|---|
| `spindle_count_n2` | int, count | Number of YASA-detected sleep spindles on N2 epochs; 0 when none found. Spindles are 0.5–2 s bursts near 13 Hz that shield sleep against disturbance and lock in memories. |
| `spindle_density_n2` | float, events/minute of N2 | Spindle count ÷ N2 minutes — the headline spindle number. NaN when there is no N2. Few spindles mean fragile sleep and weaker memory consolidation. |
| `spindle_dur_mean` | float, seconds | Mean spindle duration. Shifts in length can flag aging or medication effects. NaN when no spindles. |
| `spindle_freq_mean` | float, Hz | Mean spindle frequency (speed). NaN when no spindles. |
| `spindle_amp_mean` | float, µV | Mean spindle amplitude (size). NaN when no spindles. |
| `sw_count_nrem` | int, count | Number of YASA-detected slow waves on N2+N3 epochs; 0 when none found. Slow waves are the giant ~1-second waves of deep sleep — the visible unit of physical restoration. |
| `sw_density_nrem` | float, events/minute of NREM | Slow-wave count ÷ NREM (N1+N2+N3) minutes. NaN when there is no NREM. |
| `sw_negamp_mean` | float, µV | Mean slow-wave negative-peak amplitude (depth). Shallower waves mean lighter deep sleep. NaN when no slow waves. |
| `sw_dur_mean` | float, seconds | Mean slow-wave duration (length). NaN when no slow waves. |
| `arousal_count` | int, count | Heuristic micro-arousals: brief 3+ s brain activations the patient never notices. Detected as 8–30 Hz envelope surges above 2.5× a trailing 60-s median baseline during sleep, kept ≥ 10 s apart. This is a ranking heuristic, not clinical AASM scoring. |
| `arousal_index` | float, events/hour of sleep | Arousal count ÷ total-sleep-time hours. Micro-arousals destroy deep sleep silently, so this is the compact summary of invisible fragmentation. |

## Muscle and breathing — "was the body truly paralyzed in dreams?"

EMG: per-epoch RMS of the chin-muscle envelope in µV. REM group = REM epochs; NREM group = N1+N2+N3 epochs.

| Metric | Type | Explanation |
|---|---|---|
| `emg_median_uv` | float, µV | Nightly median of per-epoch EMG RMS — the overall muscle-tone level, and the context for the ratios below. |
| `emg_rem_mean_uv` | float, µV | Mean EMG RMS over REM epochs. NaN when there is no REM. |
| `emg_nrem_mean_uv` | float, µV | Mean EMG RMS over NREM epochs. NaN when there is no NREM. |
| `rem_atonia_ratio` | float, ratio | Mean NREM RMS ÷ mean REM RMS. In REM the body should be paralyzed, so this should sit clearly above 1 — a value near 1 means dangerous dream-enacting behavior. NaN when either group is empty. |
| `movement_index` | float, 0–1 | Fraction of epochs with RMS above 3× the nightly median. Restless legs, tossing, and teeth grinding all show up here. |
| `apnea_count` | int, count | Breathing pauses: airflow envelope below 10% of its trailing 120-s median for ≥ 10 s during sleep (gaps ≤ 5 s merged). A coarse proxy without oxygen data — it catches clear pauses but cannot score hypopneas. |
| `apnea_index` | float, events/hour of sleep | Apnea count ÷ total-sleep-time hours. This is the core of the AHI-style score doctors use, in proxy form. |
| `apnea_time_pct` | float, percent | 100 × seconds in pauses ÷ window seconds — pause severity in one number. |
| `has_flow` | int, 0 or 1 | 1 when the night has a breathing channel, else 0. When 0, the three apnea fields are missing — never zero. |
