# sleep-quality-index — paper sub-bank

Charter: everything needed to run, cite, and explain the **SDI** (Sleep Depth Index) indexer that
feeds our SQI branch. Staging (60%) lives in `../../sleep-stage/`; this sub-bank is the 30% SQI side.

## Papers

| File | Version | Notes |
|---|---|---|
| `2407.04753.md` | arXiv v2, 2024-12-08, 24 pp | full text incl. appendices (Tables A1–A4, Figs A1–B5) |
| `npj-2025-01607-published.md` | npj Digital Medicine 8:203, 2025-04-11 | **published version — outcome numbers differ from the preprint** (see below) |

- DOI: https://doi.org/10.1038/s41746-025-01607-0 · cited ≥15 times, open access
- Code: `https://github.com/sczzz3/SDI` (official, per the paper's Code availability); `PKUDigitalHealth/SDI` is the group mirror. Our vendored checkpoint (`sleep-quality-index/sdi/models/sdi_checkpoint.pt`, 88.5 MB) matches this release and **strict-loads**.
- Model: ViT-style transformer, 23.2M params; input 30-s epochs @100 Hz, 4 channels `[EEG C4, EMG chin, EOG right, ECG]`; two heads: **depth** (continuous, sigmoid→0–1) + **REM** (binary).

## What it is (one paragraph)

Sleep staging labels are ordinal-ish but coarse. The paper converts clinician staging into a
**pairwise-ranking target** and trains a transformer to emit a continuous **sleep depth index** per
30-s epoch, jointly with a REM head. Validate `[RECONSTRUCT]-free`: no code needed from us to cite.
> "We propose a first-of-its-kind deep learning method to annotate the sleep depth index using the PSG data and existing sleep staging labels in an end-to-end way." [p.2](https://www.alphaxiv.org/abs/2407.04753v2?page=2)

## Method details (verified against the text)

- Input: `C×L = 4×3000`, 100 Hz; patch size 100, embed dim **D=512**, encoder depth **6**, heads **8**, MLP **2048**; CLS token + positional + channel embeddings. [p.11–12](https://www.alphaxiv.org/abs/2407.04753v2?page=11)
- Ranking margins `M_ij`: **(W,N1)=1 · (N1,N2)=0.5 · (N2,N3)=1.5 · (W,REM)=1.2**;
  REM-vs-N1/N2/N3 pairs `(1,4),(2,4),(3,4)` are marked **uncertain and masked out** of the rank loss; REM gets cross-entropy, joint loss `L = L_rank + α·L_clas`, α=1; depth head is **unbounded during training**, sigmoid only at inference. [p.12–13](https://www.alphaxiv.org/abs/2407.04753v2?page=12)
- Cohorts: MESA+MROS+CFS train (3,984 participants), 1,708 internal val, **SHHS external**; 11,485 recordings total. [p.3](https://www.alphaxiv.org/abs/2407.04753v2?page=3)

## Headline numbers

| Metric | Preprint (arXiv v2) | Published (npj 2025) |
|---|---|---|
| Depth concordance (Spearman vs W/N1/N2/N3, REM excl.) | all cohorts **>0.85** [p.3](https://www.alphaxiv.org/abs/2407.04753v2?page=3) | same |
| REM AUROC (micro / MESA / MROS / CFS / external SHHS) | **0.978 / 0.990 / 0.984 / 0.985 / 0.975** [p.3](https://www.alphaxiv.org/abs/2407.04753v2?page=3) | same |
| SDI drop vs arousal duration (Pearson, deciles) | **0.9913 / 0.9968 / 0.9955 / 0.9977** (SHHS/CFS/MESA/MROS) [p.6](https://www.alphaxiv.org/abs/2407.04753v2?page=6) | same |
| Disturbed-subtype associations | apnea OR 1.22–1.58; poor subjective quality OR 1.60–4.4; insomnia OR 1.51–4.39; hypertension 1.34/1.26; CVD OR 1.29 (SHHS) | apnea OR **1.15–1.55**; poor quality **2.35 (CFS) / 2.23 (MROS)**; insomnia **2.01/1.58**; hypertension **1.21**; CVD **1.25** (SHHS) |
| Survival (SHHS, Cox adj.) | mortality HR **1.42** (1.24–1.62, p<0.001); fatal CVD HR 1.29 (1.00–1.67, p=0.053) | mortality HR **1.33** (1.16–1.53, p<0.001); fatal CHD HR **1.38** (1.01–1.90, p=0.046) |

⚠️ **Version discipline:** the published analysis re-adjusted the outcome models (age, BMI, sex, SE, SL)
and its numbers differ from the preprint. Cite the published values; keep the preprint only for method
+ appendices. (This is exactly the kind of trap to avoid when quoting the paper.)

Night-feature effect sizes (preprint Table A3, normal→disturbed, SHHS):
RB 0.32→0.51 · CV 0.78→1.04 · AP 0.41→0.27 · SK 0.28→0.91 · MDR 0.42→0.25 · PR 0.20→0.14 ·
APPe 0.99→0.93 · DETRf 1.17→1.13 — all p<0.001. [p.22](https://www.alphaxiv.org/abs/2407.04753v2?page=22)

## Added value beyond classification (why we ship it)

1. **Depth inside a stage.** Same-labeled N2/REM epochs get different SDI by their slow-wave / EMG /
   EOG content — "the same sleep stage could be better distinguished by sleep depth index instead of
   sleep staging" (Fig. 2 cases). Staging cannot express this.
2. **Automatic fragmentation marker.** SDI-drop ↔ arousal-duration correlation ≈0.99 across four
   cohorts — an arousal proxy that needs no manual arousal scoring.
3. **A new night-level feature space**: RB, AP, CV, SK, MDR, PR, APPe, DETRf — beyond TST/SE/stage%.
4. **Prognostic signal** (their cohorts, not ours): GMM subtypes → mortality/CHD differences.
5. **AP beats SE for "quality"**: cases show two nights with SE 94% vs 93% but AP 0.253 vs 0.46 —
   depth-based quality exposes shallow second halves that SE hides (Fig. 6a).
6. **Automatic + scalable + consistent** vs manual ORP (which needs a proprietary reference table).

## Metrics we can compute from it (for our two-SQI design)

Per night (their definitions → `estimate_quality.py` implements RB/AP/CV/MDR/PR + skew/APEn/DFA):
`RB` = share of sleep epochs with SDI<0.2 · `AP` = mean SDI over sleep (≡ area/total-sleep) ·
`CV` = SD/SDI mean · `SK` = skewness · `MDR` = mean SDI over predicted REM · `PR` = predicted REM
share · `APPe` approximate entropy · `DETRf` DFA of the SDI series. [p.11](https://www.alphaxiv.org/abs/2407.04753v2?page=11)

Ours to add (paper-inspired, [RECONSTRUCT]): within-stage SDI dispersion (depth heterogeneity within
N2/N3), SDI-drop rate around our arousal proxy (reactivity), first/second-half AP asymmetry,
time-below-threshold, AUC of the SDI curve.

## Our deployment on Sleep-EDF (already running)

- Runner: `sleep-quality-index/sdi/infer_canonical.py` — our canonical 100-Hz loader (no
  `sleepedf_clean/` dependency), writes `sleep-quality-index/runs/<stem>.parquet` (`sdi`, `rem_pred`).
- **Channel substitutions** (the paper's own limitation is 4-channel dependence): Fpz-Cz ≠ C4;
  cassette EMG is a 1-Hz envelope; **ECG absent → zero-filled**; report cassette vs telemetry
  **never pooled**.
- Pilot (3 nights): depth ρ 0.70–0.90 (paper >0.85); REM AUC 0.84 (paper 0.975–0.99) → depth
  transfers, REM discrimination degrades under the substitutions.
- Full 197-night sweep: `sleep-quality-index/runs/` + `summary_sdi.csv`; night-level via
  `estimate_quality.py`.

## Standing caveats

- Sleep-EDF has **no health outcomes / no morning questionnaires** → we can reproduce the
  depth/arousal/biomarker parts, **not** the mortality/CHD claims.
- Their GMM subtype model is population-specific; our `estimate_quality.py` composite weights are
  **ours**, z-scored within our reference — a research estimate, not the paper's model.
- PSQI (Pittsburgh) is a **questionnaire** index — not derivable from PSG; can only be compared
  against, never computed from, our data.
