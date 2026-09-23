"""Gen LLM-friendly MD set from tables. Device python, stdlib+pandas."""
from pathlib import Path
import pandas as pd, json
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
LLM=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\llm"); LLM.mkdir(parents=True,exist_ok=True)
def df_md(p, n=200):
    df=pd.read_csv(p)
    s=f"_source: tables/{p.name} ({len(df)} rows)_ \n\n"
    s+=df.head(n).to_markdown(index=False)
    if len(df)>n: s+=f"\n\n_... truncated {len(df)-n} rows, see CSV_"
    return s

def w(name, title, body):
    (LLM/name).write_text(f"# {title}\n\n"+body, encoding="utf-8"); print("wrote",name)

summ=json.loads((TAB/"eda_summary.json").read_text())
w("00_index.md","LLM index — start here",
"""This folder is the LLM-friendly EDA. Figs are NOT needed — every fig has a text description in 12_fig_descriptions.md.
Order: 01 dataset → 02 channels → 03 labels → 04 balance/trim → 05 quality → 06 physiology → 07 temporal → 08 subjects → 09 splits → 10 channel+SQI → 11 tensors/preproc → 12 figs → 13 handoff.
All numbers from actual files via edfio/pyedflib (device python). Parser note: pyedflib rejects 7 ST hyps (strict header), edfio+mne read 197/197 — all stats use edfio.
""")

w("01_dataset_inventory.md","01 Dataset inventory",
f"""## Files
- 399 files total, 394 EDF, 8.715 GB. sleep-cassette 306, sleep-telemetry 88, root 5 (RECORDS, RECORDS-v1, SHA256SUMS, SC/ST-subjects.xls).
- 197 PSG + 197 Hypnogram, pairing perfect by stem (first 6 chars). 0 missing, 0 multi.
- SC PSG 153 (~49.6 MB mean, ~20 h), ST PSG 44 (~25.4 MB mean, ~9 h). Hyp ~4.3 KB mean.
- 100 subject-prefixes (78 SC IDs + 22 ST), mostly 2 nights each. Lost per PhysioNet: SC36-night1, SC52-night1, SC13-night2.

## Schemas
{df_md(TAB/'schemas.csv')}

## Recordings sample (full: tables/recordings.csv, 197 rows)
{df_md(TAB/'recordings.csv',10)}
Durations: SC ~22 h e.g. SC4001 79500 s; ST ~10 h e.g. ST7011 35900 s. See 12_fig_descriptions for duration_dist.
""")

w("02_channels_signals.md","02 Channels + sampling",
f"""## Channel availability (197 recordings)
{df_md(TAB/'channels.csv')}

## Key facts (from EdfReader headers)
- 2 schemas only. Core everywhere: EEG Fpz-Cz@100 uV, EEG Pz-Oz@100 uV, EOG horizontal@100 uV.
- EMG SHIFT: SC 1 Hz envelope ±5 uV (HPF+rect+LPF rms) vs ST 100 Hz raw ±3000 uV. Never z-score jointly.
- SC-only 1 Hz: Resp oro-nasal (thermistor, unitless ±2048), Temp rectal 34–40 DegC, Event marker. ST-only: Marker 10 Hz ID+M-E.
- Scales: SC EEG ±192/197 uV 12-bit; ST EEG/EOG/EMG ±3000 uV 14-bit. Transducers Ag-AgCl.
- Absent everywhere: SpO2, airflow pressure, chest/abd effort, ECG/HR, position, actigraphy, leg EMG.
- Example headers: SC4001 start 1989-04-24 16:13 dur 79500 s; ST7011 start 1994-07-12 23:00 dur 35900 s.

## Sample signal stats (5 recs, full: tables/signal_stats_sample.csv)
{df_md(TAB/'signal_stats_sample.csv',14)}
""")

w("03_annotations_labels.md","03 Labels (R&K)",
f"""## Raw → 5-class
Map: W→Wake, 1→N1, 2→N2, 3+4→N3, R→REM. ? and Movement → OTHER (exclude from loss, keep for SQI/TRT).
Convention R&K (3/4 split) on Fpz-Cz/Pz-Oz. Tech ID = 8th char of hyp filename.

## Epoch counts (197 nights, edfio expansion duration/30)
{df_md(TAB/'annotations_summary.csv')}

- ?: 25047 epochs, mean per-rec q_before 0.0 / q_mid 0.8 / q_after 126.3 → ~99% trailing unscored. Movement 211 epochs negligible.
- Long blocks are multiples of 30 (e.g. leading Wake 30630 s = 1021 epochs). No overlaps after sort.
""")

w("04_class_balance_trim.md","04 Balance + Wake trim",
f"""## Global 5-class (no trim, 483419 epochs)
{df_md(TAB/'class_distribution.csv')}

Imbalance max/min = 290365/19454 = 14.9. N1 5.21% rare, N3 4.02% rare, Wake 60.06% dominates (SC daytime).
## Trim policies (exact recount)
- A_no_trim: Wake 60.1% N2 18.4 REM 7.1 N1 5.2 N3 4.0 ? 5.2% imb 14.9
- B_30min (keep ≤60 Wake epochs before first + after last sleep): Wake 29.4 N2 37.3 REM 14.3 N1 10.6 N3 8.2 ? 0.2% imb 4.6
- C_15min: Wake 26.5 N2 38.8 REM 14.9 N1 11.0 N3 8.5 imb 4.6
Rule: train with B (or C), infer/SQI on full night. Trimming must not corrupt SE/WASO — compute SQI untrimmed.
Per-recording: tables/subject_class_distribution.csv (197 rows: wake_ep,n1,n2,n3,rem,q,mov,first/last sleep idx, wake_before/after). wake_before mean 651 ep (326 min), wake_after 693 ep.
Figs in words: class_dist = Wake bar 3× N2; persubject_wake = wide 0–90% Wake; trim_impact = Wake bar halves under trim. See 12.
""")

w("05_signal_quality.md","05 Quality",
f"""{df_md(TAB/'signal_quality.csv')}

- 0 NaN/Inf in sampled SC4001 + ST7011 all channels.
- Flat-frac (diff<1e-12, decimated): SC 0.002–0.017, ST ~0.10 (likely telemetry quantization, not dropout — verify per-record p99/std before training).
- p99_abs + std in CSV = clip audit. Worst/best: rank by p99_abs/std outlier per channel.
- 7 ST hyps: pyedflib OSError EDF+ Recordingfield, mne/edfio OK — parser risk closed, no data loss.
""")

w("06_stage_physiology.md","06 Stage physiology (in-data, not textbook)",
f"""## SC4001 Fpz-Cz relative PSD (median ≤8 epochs/stage, welch 1024)
Wake d.82/t.12/a.03/s.01/b.03; N1 d.64/t.25; N2 d.80/s.02; N3 d.88; REM d.58/t.34. N3-delta, REM-theta, N1-theta separations hold.
## Fpz-Cz vs Pz-Oz (stage-relevant band median power)
Wake-alpha Fp 11.3 vs Pz 16.8 (Pz alpha slightly stronger here); N1-theta 35.1 vs 13.1; N2-sigma 4.14 vs 1.83; N3-delta 522 vs 158; REM-theta 42.7 vs 23.7. Fpz-Cz empirically stronger except Wake-alpha.
## EOG/EMG RMS (median ≤10 epochs/stage)
{df_md(TAB/'eog_emg_by_stage.csv')}
- SC4001 (EMG 1 Hz): EOG Wake 95 → N2 15; EMG REM 0.385 (atonia) vs Wake 3.41/N1 3.05 — envelope still useful.
- ST7011 (EMG 100 Hz): EOG N2 95/REM 93 vs Wake 47 (sample variance, n=10 — don't overclaim); EMG Wake 51.5 → REM 4.7 gradient strong.
Takeaway: EOG helps Wake/REM/N1 transitions; EMG helps Wake vs REM in both cohorts despite fs mismatch (use RMS/envelope features, cohort-specific norm).
Figs in words: psd_* = N3 top at <4 Hz, REM/Wake higher 4–13; spec_* = N3 bright low band; eog_bystage = sharp saccades Wake/REM vs flat N2/N3. See 12.
""")

w("07_temporal.md","07 Temporal structure",
f"""## Transition P(t|t-1) epoch-level (5-class, ?/Mov excluded)
{df_md(TAB/'transition_matrix.csv')}

Self: Wake .985 N1 .711 N2 .909 N3 .818 REM .945. Cross: N1→N2 .17, N3→N2 .167, N1→Wake .089, REM→N1 .026. Sequence model strongly justified; N1 most transient.
## Runs
Median epochs: REM 11, N2 4, Wake 2, N1 2, N3 1, OTHER 1. Singles: N1 2872, N2 1957, N3 1882, Wake 1757, REM 190. N3 fragmented (3↔4 alternation) — consider smoothing/CRF. Context 5–11 epochs covers N2/REM runs.
""")

w("08_subjects_cohorts.md","08 Subjects + domain shifts",
"""- 100 prefixes: 78 SC + 22 ST. SC: mean 1.96 nights/subj (lost 36-1,52-1,13-2 per PhysioNet). ST: 22×2 (placebo+temazepam).
- SC: 1987–91 home cassette, healthy 25–101 y, mean 59 y, 53.6% F, no meds, 20 h day-night. ST: 1994 hospital telemetry, mild insomnia else healthy, temazepam vs placebo, 9 h.
- Shifts: age, site/home-hospital, device (cassette vs telemetry), scales (±192 vs ±3000), EMG fs, drug, duration. Validate SC→ST + placebo→temazepam. Full per-rec: tables/subject_class_distribution.csv; SC demographics: tables/subjects_SC.csv.
""")

w("09_leakage_splits.md","09 Leakage + splits",
f"""## Risks
- Critical: 2 nights/subject — never split nights across train/val/test.
- High: global z-score / full-data preprocessing / epoch shuffle.
- Medium: tech-ID in filename, lights-off/SOL as feature, ?/Mov train-test mismatch, SC/ST EMG joint norm.
- Low: duplicates (none; 0 missing pairs).
## Proposal (subject-wise 70/15/15, stratified SC/ST, nights paired)
Train 69 subj / 135 rec / 331264 ep (wake199653 n117778 n259840 n313905 rem23241); Val 15/30/74832; Test 16/32/77323. Lists: tables/split_proposal.txt. Alt: grouped 5-fold.
""")

w("10_minimal_channel_sqi.md","10 Minimal-channel + SQI feasibility",
f"""## Configs (no deep training, evidence-based hypothesis)
A Fpz-Cz: viable baseline (strongest single, N3 522 vs Pz 158). B Pz-Oz: weaker N1/N3. C 2×EEG: best EEG-only. D +EOG: big Wake/REM/N1 gain. E +EMG: REM/atonia gain (SC envelope + ST raw, separate norms). F EEG+EOG+EMG: recommended full (3×3000 @100 Hz + 1 Hz aux). G +Resp/Temp: ~0 staging gain, SQI context only. Rank: F≈D > C > A > B; E boosts REM. Hardware: 2EEG+EOG minimal, +chin-EMG if cheap.
## SQI feasibility
{df_md(TAB/'sqi_feature_feasibility.csv',20)}
Architecture per-rec: tables/sleep_architecture.csv (TRT/TST/SE/SOL/Nx/REM + WASO/awakenings/transitions = NaN = define at modeling time; mean TRT 1227 min / TST 426 / SE 42.8% untrimmed — recompute trimmed).
""")

w("11_tensors_preprocessing_baseline.md","11 Tensors, preprocessing, baseline feats",
f"""## Tensors (fs 100, 30 s = 3000)
1ch [1,3000] (~12 KB f32); 2EEG [2,3000]; EEG+EOG [3,3000]; ST-full [4,3000]+marker; SC-full 3×3000 + 1 Hz aux (90). Context ×5 [5,C,3000], ×11 [11,C,3000]. Batches trivial.
## Preprocessing (justified in-data)
1) keep 100 Hz (no resample) 2) bandpass 0.3–35 + notch 50 EU 3) per-record per-channel zscore (never global) 4) SC/ST separate EMG (SC envelope stats, ST raw RMS→envelope to match) 5) map 3+4→N3, mask ?/Mov in loss 6) train 30-min trim, SQI full-night 7) 5–11 epoch context.
## Baseline tabular sample (200 epochs SC4001: mean/std/rms/ptp/zcr + rel delta/theta/alpha/sigma/beta + label)
Full: tables/baseline_features_sample.csv (200 rows). Schema: epoch,label,mean,std,rms,ptp,zcr,delta,theta,alpha,sigma,beta.
""")

w("12_fig_descriptions.md","12 What each fig shows (text代替)",
"""- channel_avail.png: bars EEG/EOG 197, EMG 197 (fs differs), Resp/Temp/Event 153, Marker 44.
- duration_dist.png: SC peak ~20–22 h, ST ~9–10 h, bimodal.
- class_dist.png: Wake 290k >> N2 89k > REM 34k > N1/Q 25k > N3 19k > Mov 211.
- persubject_wake.png: Wake% spread 5–95%, SC heavy right tail (daytime).
- trim_impact.png: Wake 60→29% under 30-min trim; N2 18→37%.
- transition_matrix.png: bright diagonal (.71–.99), N1 row most diffuse.
- runlength.png: REM long box, N3 near 1, N1 many singles.
- eeg_compare.png: Fpz bars taller except Wake-alpha.
- emg_eog_by_stage.png: U-shape EMG (Wake high, REM low) both cohorts; EOG cohort-variable.
- eog_bystage.png (ST7011): Wake/REM spiky saccades, N2/N3 flat.
- psd_<rec>.png ×5: N3 top <4 Hz; REM/N1 mid hump 4–8; Wake flatter + alpha.
- spec_<rec>.png ×5: N3 bright 0.5–4 band; Wake/REM brighter 8–30.
- eeg30s_<rec>.png ×5: N2 30 s slow waves + fast riding; EOG quiet.
- eeg2min_<rec>.png ×5: continuity, no dropout.
- hist_<rec>.png ×5: zero-mean bell, Fpz slightly wider than Pz.
Paths: eda/figs/*.png (35 total).
""")

w("13_handoff.md","13 Handoff (paste to next AI)",
"""Sleep-EDF Expanded 197 nights (SC153 20h home healthy 25–101y + ST44 9h hospital temazepam/placebo). Ch: Fpz-Cz/Pz-Oz/EOG@100 all; EMG SC@1Hz env ±5 vs ST@100Hz ±3000; Resp/Temp/Event SC@1Hz; Marker ST@10Hz; no SpO2/ECG/effort. Labels R&K→Wake/N1/N2/N3(3+4)/REM; epochs Wake290365 N288983 REM34184 N125175 ?25047 N319454 Mov211; imb14.9→4.6 (30-min trim); ? trailing. Trans self .71–.99; runs REM11 N24. Fpz best single; +EOG big; +EMG REM help. Split subject-wise 69/15/16 subj. SQI architecture-only (AHI/SpO2 impossible). Tensors [C,3000]. Preproc per-record, SC/ST EMG separate. Parse hyps edfio. Tables eda/tables/*.csv + eda_summary.json; text EDA eda/llm/00–13.
""")
print("done", len(list(LLM.glob('*.md'))))
