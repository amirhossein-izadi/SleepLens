# Continuous Sleep Depth (SDI) — data, training, score

Reference: Zhou et al., *npj Digital Medicine* 8:203 (2025), "Continuous sleep depth index annotation with deep learning yields novel digital biomarkers for sleep health" (code: `sczzz3/SDI`, MIT, commit `9b1a9d7`). Our zero-shot run and the Sleep-EDF fine-tune follow the paper's model, not its data.

**Naming rule:** the fine-tuned model is *Sleep-EDF SDI-like depth*, not the paper's SDI (different dataset, EEG lead, no ECG); the paper's health-outcome links do not transfer to it.

## 1. Input data: what the model expects vs what Sleep-EDF has

The paper's model takes one **30-s PSG epoch at 100 Hz**, shape `(4, 3000)`, channel order `[EEG, EMG, EOG, ECG]`, amplitudes in **µV** (ECG in **mV**), with **no filtering and no normalization** (upstream code only resamples to 100 Hz).

Sleep-EDF does not contain the paper's exact channels or rates, so substitutions are unavoidable:

| model expects (paper) | Sleep-EDF has | what we do |
|---|---|---|
| EEG **C4** | `EEG Fpz-Cz` (or `Pz-Oz`) | substitute **Fpz-Cz**, the closest available derivation; `Pz-Oz` scored worse in the smoke test |
| right **EOG** | `EOG horizontal` | substitute horizontal EOG (same modality) |
| chin **EMG** @ 100 Hz | `EMG submental`: cassette is a native **1-Hz envelope**, telemetry is 100 Hz | keep submental; resample the envelope to 100 Hz — cassette keeps amplitude only, no high frequencies |
| **ECG** @ 100 Hz | **absent** | zero-fill the channel (zero-shot, keeps the 4-channel model untouched) or drop it (fine-tune, 3 channels) |
| uniform 100 Hz | mixed rates (e.g. cassette 100 Hz, EMG 1 Hz) | resample every channel to 100 Hz with mne; no band-pass, no scaling |
| 30-s epochs = 3000 samples | same 30-s scoring grid as the hypnogram | cut into non-overlapping 3000-sample epochs; drop the leftover tail |
| µV (ECG mV) | mne returns volts | multiply by 1e6 → µV (1e3 if an ECG channel is named) |

How the input is prepared (same steps for zero-shot and fine-tune):

1. Read the EDF channels `[EEG Fpz-Cz, EMG submental, EOG horizontal]` (+ ECG if one is named) with mne.
2. Resample everything to 100 Hz; nothing else is applied.
3. Convert amplitudes to µV (mV for ECG).
4. Cut into 30-s epochs (3000 samples) and stack as `(n_epochs, 4, 3000)` — the ECG row is all zeros when the channel is missing.
5. Score in batches (128 epochs) through the network.

The mismatch is real and deliberate: cassette (`cassette_emg_1hz_no_ecg`) is more degraded than telemetry (`telemetry_emg_100hz_no_ecg`), so the two subsets are **never pooled**, and SDI numbers are quoted as a degraded-input baseline, not the paper's SDI. After inference we check quality per night (SDI order W < N1 < N2 < N3, depth Spearman vs stages, REM F1) and flag nights that fail.

To fit the data better, the **fine-tune** adapts the released model to 3 channels: the ECG row of the channel embedding is sliced off, the 6-layer backbone stays **frozen**, and only the channel embedding + both heads are trained on Sleep-EDF stage labels. Cache: `(n_window, 3, 3000)` float16 in `[EEG, EMG, EOG]` order, labels = expert stages `0=W..4=R`, `-1` unscored (`sdi_epochs.py`). This gives *Sleep-EDF SDI-like depth*, not the paper's SDI.

## 2. Learning curve and accuracy

Architecture: per-channel patch embedding (100-sample patches → 120 tokens/epoch), 6-layer transformer (dim 512), two heads: depth scalar + 2-class REM. Fine-tune: backbone **frozen**, trainable channel embedding + FF/heads = **4.21M params**; AdamW, batch 128, 300-step warmup + cosine LR, 5-fold **GroupKFold by subject** (80 train / 20 val subjects for fold 0).

Per-epoch validation (fold 0, 197 nights cached; the first run hung at 8/10, resumed 4 epochs at lr 1e-4):

| epoch | train loss | val loss | depth Spearman | REM F1 |
|---|---|---|---|---|
| 1 | 0.3081 | 0.2214 | 0.853 | 0.712 |
| 2 | 0.2648 | 0.2175 | 0.855 | 0.738 |
| 3 | 0.2560 | 0.2111 | 0.857 | 0.739 |
| 4 | 0.2481 | 0.2103 | 0.858 | 0.720 |
| 5 | 0.2425 | 0.2090 | 0.858 | 0.736 |
| 6 | 0.2390 | 0.2083 | 0.856 | 0.746 |
| 7 | 0.2350 | 0.2062 | 0.857 | 0.742 |
| 8 | 0.2324 | 0.2049 | 0.857 | 0.750 |
| 9 | 0.2312 | 0.2048 | 0.858 | 0.741 |
| 10 | 0.2295 | **0.2045** | 0.858 | 0.745 |
| 11 | 0.2284 | 0.2052 | 0.858 | 0.743 |
| 12 | 0.2265 | 0.2049 | 0.858 | 0.744 |

Curve flattens by epoch 8 (val 0.2045–0.2052 over the last five epochs); best = epoch 10 → `models/sdi_sleepedf_adapted_fold0.pt` (+ `.json` meta with full history).

Held-out fold-0 evaluation (40 nights, same val subjects), zero-shot vs fine-tuned:

| metric | zero-shot (4ch, zero ECG) | fine-tuned (3ch) | delta |
|---|---|---|---|
| depth Spearman (vs W<N1<N2<N3) | 0.796 ± 0.102 | **0.858 ± 0.045** | +0.062 |
| REM AUROC | 0.946 ± 0.057 | **0.963 ± 0.035** | +0.017 |
| REM F1 | 0.670 ± 0.165 | **0.745 ± 0.128** | +0.074 |
| mean SDI: wake / N3 / REM | 0.070 / 0.859 / 0.304 | 0.023 / 0.878 / 0.202 | sharper W↔N3 contrast |

Paper reference (different cohorts/input, not directly comparable): Spearman > 0.85 across cohorts; REM AUROC micro-average 0.978 (0.990/0.984/0.985 on MESA/MROS/CFS, 0.975 external SHHS).

## 3. Night sleep score (SDI composite) — exact formula

Per night (`estimate_quality.py`), over **sleep epochs only** (expert stages 1–4 by default, `--stage-source <model>` to use a staging model; SDI is produced for every epoch including unscored), with `s = SDI` values, `rem_pred` = the model's REM output:

```
RB  = mean(s < 0.2)                      shallow-sleep fraction (threshold 0.2 per paper)
AP  = mean(s)                            average depth (= paper's area under curve / TST)
CV  = SD(s, ddof=1) / mean(s)            night-time dispersion of depth
MDR = mean(s[rem_pred == 1])             depth of model-predicted REM
PR  = count(rem_pred == 1) / count(s)    predicted REM share of sleep

z(x) = (x - mean_ref) / SD_ref           reference = all nights by default, or --reference-csv
score = mean( -z(RB), z(AP), -z(CV), z(MDR), z(PR) )     equal weights, NaN if any missing
percentile = midrank of score within reference, 0–100
```

Eligibility: ≥ 30 sleep epochs **and** ≥ 1 predicted REM; otherwise NaN + reason. `skew`, `ApEn`, `DFA` are reported but not scored; `apnea_index` is joined for display only.

Why this way:

- The paper defines the features but **no single validated scalar** — its own whole-night analysis is a Gaussian-mixture clustering into *normal* vs *disturbed* subtypes. A transparent equal-weight z-sum is our implementation recommendation, not the paper's score; weights are not fit because there is no ground-truth quality label to fit to.
- Directions are taken from the paper's disturbed-subtype findings: larger RB, smaller AP, larger CV, smaller MDR, smaller PR. So `-z(RB)`, `z(AP)`, `-z(CV)`, `z(MDR)`, `z(PR)`.
- z-scoring makes units comparable; the percentile makes one night interpretable against a reference cohort. Raw components are kept in the report so the score can be recomputed with other weights/reference.
- `mdr_expert` / `pr_expert` (from expert stages) are stored alongside for sanity checks; the score itself uses the model's REM predictions, which is what deployment has.
- Caveat: zero-shot Sleep-EDF inference has deliberate mismatches (Fpz-Cz, no ECG, 1-Hz cassette EMG), and the paper's mortality/CVD links apply to its SDI, not to this composite. Validate against a stated target (e.g. PROMIS/Pittsburgh) before treating it as meaningful.

What each metric shows / why it exists:

| metric | what it shows | why it exists |
|---|---|---|
| RB | fraction of the night spent in shallow sleep (SDI < 0.2) | catches fragmentation below light-sleep threshold regardless of stage labels; higher in the disturbed subtype |
| AP | average depth over sleep — a label-free analog of sleep efficiency | paper: "more accurate than conventional SE" (SE ignores depth); lower in the disturbed subtype |
| CV | how dispersed/fluctuating depth is across the night | high CV = repeated disturbance/arousal-like instability; higher in the disturbed subtype |
| MDR | depth during REM epochs | REM-specific physiology (atonia, dream activity); deeper REM in the normal subtype |
| PR | REM share of sleep (model-predicted) | classic sleep-health quantity, obtained free from the model's REM head; lower in the disturbed subtype |
| skew / ApEn / DFA | asymmetry and complexity of the depth time series | reported for exploration only: directions are inconsistent in the paper (normal subtype had *larger* complexity), so they are not folded into the score |

This composite is the SDI-derived night score. It is separate from the wider 96-feature SQI; no SQI weights are fixed yet.

## 4. What the model is; what it adds; how labels enter the score

**Main point.** Staging compresses every 30 s into one of five labels. The SDI model instead outputs a **continuous depth index in [0, 1] per 30-s epoch** (higher = deeper) plus a REM/not-REM prediction, so within-stage differences (e.g. light vs deep N2, phasic REM) become visible. The paper shows SDI drops track arousal duration almost perfectly (Pearson > 0.99), and SDI-derived features cluster nights into normal vs disturbed subtypes associated with +33% all-cause mortality and +38% fatal coronary heart disease (SHHS, adjusted). It is *not* meant to replace staging — it annotates what staging flattens.

**Beyond previous staging.** (1) Arbitrary continuous resolution instead of 5 classes; (2) validated arousal/fragmentation signal; (3) a source of novel digital biomarkers (RB, AP, CV, MDR, PR, …); (4) usable on top of existing labels — no new human annotation needed.

**How the labels are used.**

- *Training:* discrete stages (W/N1/N2/N3/REM) become **ranks**. `PairMarginRankLoss` (paper, verbatim) compares epoch pairs and pushes depth to respect known order with stage-specific margins (e.g. W–N3 margin 3, N1–N2 margin 0.5); **all REM-vs-NREM pairs are excluded** because REM's ordinal position is not defined. The REM head is trained with cross-entropy. So continuous depth is *learned from discrete labels* — that is the core trick.
- *Inference:* each 30-s epoch yields `sdi` (float 0–1) and `rem` (0/1) to `data/sdi/<sid>.npz`; nights are processed in batches (never the whole night at once).
- *Score:* depth values over sleep epochs produce **RB, AP, CV**; the model's REM predictions produce **MDR, PR**; the five oriented z-scores are averaged into the composite/percentile. The sleep-epoch mask can come from expert stages or from a staging model (`--stage-source usleep`), so the full pipeline can run label-free.

**Provenance:** paper figures/metrics — Fig. 1 (acronyms), Fig. 3 (arousal), Fig. 4–5 (subtypes/outcomes); code — `infer_sdi.py`/`run_sdi.py` (input + inference), `sdi_net.py` (architecture), `sdi_loss.py` (ranking loss), `sdi_finetune.py` + `sdi_epochs.py` (fine-tune), `estimate_quality.py`/`sdi_composite.py` (score), reports in `reports/sdi_*`.
