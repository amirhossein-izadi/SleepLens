# Sleep-EDF Expanded — Full EDA Report (device python, reproducible)

## A. Executive Summary (20 bullets)
1. 197 PSG + 197 hypnograms, 8.715 GB; SC 153 (~20 h, home, cassette) + ST 44 (~9 h, hospital telemetry, temazepam/placebo crossover).
2. Exactly 2 channel schemas; core ML signals in ALL 197: EEG Fpz-Cz@100 Hz, EEG Pz-Oz@100 Hz, EOG horizontal@100 Hz.
3. EMG domain shift: SC 1 Hz envelope (±5 uV) vs ST 100 Hz raw (±3000 uV) — never naively mix.
4. SC-only aux @1 Hz: Resp oro-nasal (thermistor), Temp rectal, Event marker. ST-only: Marker@10 Hz. No SpO2/ECG/airflow-pressure/effort/position/leg-EMG anywhere.
5. Labels are R&K: W,1,2,3,4,R,?,Movement. Map: W→Wake,1→N1,2→N2,3+4→N3,R→REM; ?+Mov = OTHER (5.22% combined, must exclude from loss, keep for SQI).
6. Global epochs (197 nights, edfio): Wake 60.06%, N2 18.41%, REM 7.07%, N1 5.21%, ? 5.18%, N3 4.02%, Mov 0.04%. Imbalance 14.9.
7. 30-min Wake trim → Wake 29.4%, N2 37.3%, imbalance 4.6; ?→0.2% because ? is 99% trailing unscored (q_after mean 126 ep, q_before 0).
8. Wake_before mean 326 min, wake_after 346 min (SC daytime) — valid SE/SOL require trim + lights-off from xls.
9. 7 ST hyps fail pyedflib strict header but read fine in mne/edfio — R&D fixed; use edfio for all hyps (197/197 OK).
10. Self-transitions dominate: Wake .985, N2 .909, REM .945, N3 .818, N1 .711 — sequence model strongly justified.
11. Median runs: REM 11, N2 4, Wake/N1 2, N3 1 (fragmented 3↔4); singles: N1 2872, N2 1957, N3 1882 — label smoothing/CRF worth testing.
12. Physiology confirmed in-data: N3 delta rel .88, REM theta .34, Wake alpha present, N2 sigma present; Fpz-Cz > Pz-Oz for N3 delta (522 vs 158) and N1 theta — Fpz-Cz empirically stronger.
13. EOG RMS separates Wake/REM vs N2/N3 (SC4001: Wake 95, REM 15 vs N2 15 — cohort-dependent; ST7011: N2 95, REM 93 vs Wake 46 — use both cohorts, don't overclaim).
14. EMG atonia visible even at 1 Hz: SC REM 0.385 vs Wake 3.41; ST REM 4.7 vs Wake 51.5 — EMG helps Wake/REM.
15. Quality: 0 NaN/Inf sampled; flat-frac <0.02 SC; ST flat ~0.10 likely quantization, not dropout; clipping to check per-record via p99.
16. Subjects: 78 SC IDs + 22 ST = 100 prefixes; mostly 2 nights/subject (SC mean 1.96; lost: 36-1, 52-1, 13-2); split MUST be subject-wise, nights kept together.
17. SC age mean 59 y, 53.6% F, 25–101 y; ST mild insomnia + drug — age/drug domain shift real.
18. Apnea/AHI/ODI/arousal/PLMI/HR/position = IMPOSSIBLE — SQI only from hypnogram architecture (TST/SE/WASO/SOL/stage%, REM-lat, transitions, awakenings).
19. Tensors: 1 epoch = 3000 @100 Hz; configs [1,3000]→[4,3000]; context ×5/×11 = [5,C,3000]/[11,C,3000]; ~KBs per sample, batches trivial.
20. Split proposal 70/15/15 subject-stratified SC/ST: train 69 subj/135 rec/331k ep, val 15/30/74k, test 16/32/77k — no subject overlap.

## B. What Dataset Do We Actually Have?
- PhysioNet sleep-edfx 1.0.0 (Kemp et al. 2000; Mourtazaev 1995; R&K 1968; van Sweden 1990). 197 whole-night PSGs + expert hyps (tech ID = 8th letter of hyp filename).
- sleep-cassette/SC4ssNE0: 1987–91, healthy Caucasians 25–101 y, no sleep meds, home Walkman-cassette, 2×~20 h day-night, EOG/EEG 100 Hz, EMG envelope 1 Hz (HPF+rect+LPF, uVrms), Resp/Temp/Event 1 Hz.
- sleep-telemetry/ST7ssNJ0: 1994, 22 subjects mild difficulty falling asleep, hospital, 2 nights (placebo vs temazepam), telemetry, ~9 h, EEG/EOG/EMG 100 Hz, marker 1 Hz (ID+M-E coding).
- Files: RECORDS (153+44 list), RECORDS-v1, SHA256SUMS, SC/ST-subjects.xls. No train/test folders. 100 subject-prefixes, 197 recordings (153 SC + 44 ST).
- 7 ST hyps need lenient parser (edfio/mne), else identical semantics.

## C. Signal Inventory
| channel | SC153 | ST44 | fs | units | notes |
| EEG Fpz-Cz | yes | yes | 100 | uV | SC ±192, ST ±3000; primary |
| EEG Pz-Oz | yes | yes | 100 | uV | SC ±197, ST ±3000 |
| EOG horizontal | yes | yes | 100 | uV | SC ±1009, ST ±3000 |
| EMG submental | envelope 1 Hz ±5 | raw 100 Hz ±3000 | — | uV | incompatible scales |
| Resp oro-nasal | 1 Hz | — | 1 | — | thermistor, AHI-insufficient |
| Temp rectal | 1 Hz 34–40 DegC | — | 1 | DegC | drift only |
| Event marker | 1 Hz | — | 1 | — | button |
| Marker | — | 10 Hz ID+M-E | 10 | — | telemetry ID/error coding |
- Sample stats in tables/signal_stats_sample.csv; figs: channel_avail, duration_dist, eeg30s/2min, hist, psd_*, spec_*.

## D. Annotation and Label Semantics
- EDF+ TALs, 0-signal hyp files. Raw: W,1,2,3,4,R,?,Movement. R&K (3/4 split) on Fpz-Cz/Pz-Oz (not C4-A1/C3-A2).
- Epoch = 30 s; long blocks = multiples of 30 (e.g. leading Wake 30630 s = 1021 epochs). No overlaps/gaps after expansion; onset-sorted.
- Map 3+4→N3 explicitly; ? (5.18%, trailing) + Mov (0.04%) excluded from Macro-F1, retained for architecture/TRT.
- ST example ST7011JP: 1092 epochs W26/1-52/2-82/3-51/4-10/R10 events.

## E. Class Balance
- Global + trim table in 03b output; class_distribution.csv; per-rec subject_class_distribution.csv; figs class_dist, persubject_wake, trim_impact.
- N1 rare (5.21%), N3 rare (4.02%), Wake dominates untrimmed. 30-min trim strongly recommended for training.

## F. Signal Quality
- signal_quality.csv; no NaN/Inf in samples; flat fractions low SC; ST ~0.10 needs per-record p99/clip audit before training; worst/best via p99_abs/std in CSV.

## G. Stage Physiology Observed
- SC4001 Fpz-Cz rel powers: Wake d.82/t.12/a.03, N1 d.64/t.25, N2 d.80/s.02, N3 d.88, REM d.58/t.34 — matches textbook.
- Fpz-Cz > Pz-Oz for N3/N1/REM relevant bands; EOG/EMG atonia gradients above; figs psd_*, eeg_compare, eog_bystage, emg_eog_by_stage.

## H. Temporal Structure
- transition_matrix.csv + png; median runs + singles above; runlength.png. Use 5–11 epoch context + sequence head.

## I. Subject and Cohort Variability
- SC old (mean 59), ST drug/insomnia; SC 20 h vs ST 9 h; EMG/scale shifts; age/sex/drug in xls; model must generalize across both — validate SC→ST and placebo→temazepam.

## J. Leakage Risks
- Critical: same subject 2 nights — never split nights. High: global normalization, full-data preprocessing, epoch shuffle. Medium: filename tech ID, lights-off/SOL leakage into features, ?/Mov handling mismatch train vs test. Low: duplicate stems (none found; 0 missing pairs).

## K. Minimal-Signal Findings
- A Fpz-Cz only: viable baseline (strongest single). B Pz-Oz only: weaker N3/N1. C 2×EEG: best EEG-only. D +EOG: big Wake/REM/N1 gain (eye movements). E +EMG: Wake/REM atonia gain but SC 1 Hz limits — use envelope features, or ST-only raw. F EEG+EOG+EMG: recommended full. G +Resp/Temp: negligible for staging, useful for SQI context only. Hypothesis: D≈F > C > A > B; E helps REM specifically; hardware: 2EEG+EOG minimal, +chin-EMG if cheap.

## L. Sleep Quality / Clinical Metric Feasibility
- sqi_feature_feasibility.csv + sleep_architecture.csv. Computable: TST/SE(approx)/WASO/SOL/N%/REM-lat/transitions/awakenings. Impossible: arousal-index/AHI/ODI/SpO2/PLMI/HR/position (signals absent).

## M. Recommended Preprocessing
- Keep 100 Hz; bandpass 0.3–35, notch 50; per-record zscore (per-channel); SC/ST separate EMG pipelines (SC envelope stats, ST raw RMS + envelope to match); epoch 30 s aligned to hyp onsets; map 3+4→N3; mask ?/Mov in loss; train with 30-min Wake trim, evaluate/infer full night for SQI; no global stats.

## N. Recommended Evaluation Split
- Subject-wise 70/15/15 stratified SC/ST, nights paired (tables/split_proposal.txt): train 69/135/331k, val 15/30/74k, test 16/32/77k. Alt: grouped 5-fold. Never epoch/record shuffle.

## O. Open Questions
1. Test scoring of ?/Mov? 2. Test cohort mix (SC/ST?) and trim policy? 3. Are corrupt-7 ST in test? 4. Lights-off allowed as feature? 5. Hardware channel budget for bonus?

## P. Files Generated
- tables/: dataset_inventory, recordings_skeleton/headers/recordings, schemas, channels, annotations_summary, subject_class_distribution, class_distribution, signal_stats_sample, eog_emg_by_stage, signal_quality, transition_matrix, sleep_architecture, sqi_feature_feasibility, baseline_features_sample, subjects_SC, split_proposal, eda_summary.json
- figs/: channel_avail, duration_dist, class_dist, persubject_wake, trim_impact, transition_matrix, runlength, eeg_compare, emg_eog_by_stage, eog_bystage, hist_*, psd_*, spec_*, eeg30s_*, eeg2min_*
- scripts/: 01_inventory, 02b_headers_fast, 03a_annotations (pyedflib demo of fails), 03b_full_ann (edfio fix), 04_signals, 05_stage_quality, 06_final

# FINAL HANDOFF TO CHATGPT
Sleep-EDF Expanded 197 nights (SC153 20h home + ST44 9h hospital drug crossover). Channels: Fpz-Cz/Pz-Oz/EOG@100 Hz all; EMG SC@1Hz envelope vs ST@100Hz raw; Resp/Temp/Event SC@1Hz; Marker ST@10Hz; no SpO2/ECG/effort. Labels R&K W/1/2/3/4/R/?/Mov → Wake/N1/N2/N3(3+4)/REM; epochs 483419: Wake60.06 N218.41 REM7.07 N15.21 ?5.18 N34.02 Mov0.04; imb14.9→4.6 with 30-min trim; ? trailing. Transitions self .71–.99; runs REM11 N24 W/N1 2 N31. Fpz-Cz best single; +EOG big, +EMG REM help. Split subject-wise 70/15/15 (69/15/16 subj). SQI only architecture-based; AHI/SpO2/arousal impossible. Tensors [C,3000] per 30 s. Preprocess per-record, SC/ST EMG separate. Parse hyps with edfio (pyedflib rejects 7 ST). See eda/tables/eda_summary.json + CSVs + figs.
