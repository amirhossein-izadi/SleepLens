# SleepLens Sleep Quality Score — Selected Formula

**Decision: adopt `SQI-D` (the shipped SQI structure + an SDI depth term), computed in the backend, 0–100, higher = better.**

---

## 1. Selected formula

```text
# CREDITS (max 75) — every ratio clamped to [0,1]
efficiency = min(SE / 90,  1) × 35      SE  = 100 × TST / scored epochs
depth      = min(AP / 0.60, 1) × 20      AP  = mean SDI over sleep epochs
n3         = min(N3% / 20,  1) × 12      N3% = N3 epochs / TST epochs
rem        = min(REM% / 22,  1) × 10     REM% = REM epochs / TST epochs

# BASE 25, consumed by penalties (each capped; max total = 25 = base)
sfi_pen    = clamp((SFI  − 10) × 0.80, 0, 12)    SFI  = (awakenings + stage shifts) / TST hours
waso_pen   = clamp((WASO − 20) × 0.40, 0,  8)    WASO = minutes awake after sleep onset
sol_pen    = clamp((SOL  − 15) × 0.25, 0,  5)    SOL  = minutes from lights-off to first sleep epoch

score  = clamp(credits + 25 − (sfi_pen + waso_pen + sol_pen), 0, 100)
label  = ≥85 optimal · ≥75 good · ≥60 fair · else poor
```

**Missing SDI:** drop `depth` and rescale the remaining credits `× 75/55`, then apply base
and penalties. A missing model output must never silently zero part of the score.

**Provisional constants** (disclose in code/UI, replace when possible):
`AP_ref = 0.60` (no published normative AP — use the cohort median after all nights are
scored, or fit against PSQI) · `SFI knee = 10/h` (published guidance is only qualitative:
<24/h stable, >40/h fragmented).

---

## 2. Why this formula

1. **It is the published family's shape.** Credits for good values + capped penalties for bad
   ones, summing to 0–100 with category bands — the same construction as the published
   PSG-based SQI (De Fazio 2026) and the ZQ/SQ_obj indices it surveys. The alternative
   in-repo score (frontend `score.ts`) is a plain weighted sum of clamped values, i.e. the
   Sleep-Deficiency-Severity family, but with product-chosen constants.
2. **Correct denominators.** `SE` over scored epochs, `N3%`/`REM%` over **TST** — so every
   input is directly comparable to NSF/AASM reference ranges. The frontend score instead
   uses `sleep_pct` and `stage_pct`, which are percentages of the *whole recording*, and
   therefore reads ~0 for efficiency and architecture on a normal night.
3. **Every threshold is sourced.** SOL 15 min, WASO 20 min, SE ≥85 %, N3 16–20 %, REM 21–30 %
   are National Sleep Foundation consensus values (Ohayon 2017); SFI and its definition come
   from Haba-Rubio 2004. Only the SFI knee is a heuristic (flagged above).
4. **SDI has a natural slot.** The published SQI already carries a "sleep intensity" term
   built from N3; SDI `AP` replaces/extends it with a continuous depth measure — the one
   thing the SleepLens pipeline has that the published formula does not.
5. **Bounded downside.** Penalties are capped at the base, so a bad or missing metric costs
   points but can never zero the night (the clamped-weight alternative can).
6. **Single source of truth.** It already runs server-side, is stored, and is rendered
   identically in dashboard, workstation, report and assistant — a prerequisite for validating
   it against PSQI. The alternative is computed in the browser per frontend version.
7. **Same scale as what ships.** On the one documented night it scores 74 vs 72 for the
   unmodified SQI (vs 8–25 for the frontend score), so existing numbers stay continuous.

---

## 3. Metrics used — what each one is and why it is in the score

| Metric | What it is | Why it earns its place | Threshold source |
|---|---|---|---|
| **SE** (efficiency, ×35) | % of time in bed actually asleep | The single best objective predictor of perceived sleep quality; the strongest NSF consensus indicator | NSF: ≥85 % good, ≤74 % bad; target 90 % |
| **AP** (depth, ×20) | Mean Sleep Depth Index (0–1, higher = deeper) over sleep epochs | Continuous restorative-depth measure; ρ > 0.85 vs stages in Zhou 2025; unique to this pipeline | **Provisional 0.60** — no published normative value |
| **N3%** (×12) | Deep/slow-wave sleep share of TST | Physical restoration stage; standard architecture reporting | NSF adults: 16–20 % good, ≤5 % bad |
| **REM%** (×10) | REM share of TST | Memory/mood consolidation; standard architecture reporting | NSF adults: 21–30 % good, ≥41 % bad |
| **SFI** (penalty) | (awakenings + stage shifts) per hour of sleep | Overall brokenness of the night in one number | Definition: Haba-Rubio 2004; knee **heuristic** |
| **WASO** (penalty) | Minutes awake after sleep onset | Core consensus indicator of sleep maintenance | NSF: ≤20 min good, ≥51 min bad |
| **SOL** (penalty) | Minutes to fall asleep | Core consensus indicator of sleep initiation | NSF: ≤15 min good, 16–30 acceptable |

**SDI metrics shown but not scored:** `RB` (share of sleep with SDI < 0.2 — the threshold
defines the biomarker, not a quality cut-off), `CV` (stability), `MDR` (depth in REM), `PR`
(SDI-predicted REM share). They are reported for transparency and later calibration, matching
the rule `sdi_composite.py` already applies to skew/ApEn/DFA. `N3%` and `AP` both index depth
and are deliberately given 12 + 20 rather than stacking full weight on either.

**Excluded:** apnea index, arousal index and REM-atonia ratio are not used — the current
implementation hard-codes them (`4.5`, `sfi × 0.45`, `1.72`). They are unmeasured and must be
reported as not-assessable, never as constants.

---

## 4. References

1. **Selected structure:** De Fazio R, Paiano M, Del-Valle-Soto C, Velázquez R, Al-Naami B,
   Visconti P. *Hypnogram-Driven Automatic Sleep Staging and a Quality-Index Assessment…*
   Sensors 2026;26(13):4091. (credit + saturation terms for TST, N3-intensity, WASO, SFI;
   weights fitted by maximising correlation with PSQI)
2. **Thresholds:** Ohayon MM, Wickwire EM, Hirshkowitz M, et al. *National Sleep Foundation's
   sleep quality recommendations: first report.* Sleep Health 2017;3(1):59–65.
3. **SFI definition:** Haba-Rubio J, Ibanez V, Sforza E. 2004 — SFI = (awakenings + stage
   shifts) / TST.
4. **Depth (SDI):** Zhou S, Song G, Sun H, Zhang D, Leng Y, Westover MB, Hong S. *Continuous
   Sleep Depth Index Annotation with Deep Learning Yields Novel Digital Biomarkers for Sleep
   Health.* arXiv:2407.04753 / npj Digital Medicine 8:203 (2025). — local copy:
   `../sleep-analysis/test/`.
5. **Scoring rules / metric definitions:** Berry RB et al. *AASM Manual for the Scoring of
   Sleep and Associated Events*, v2.2, AASM.
6. **SDI night-level composite precedent (which biomarkers are scored):**
   `../sleep-analysis/test/sdi_composite.py`.
7. **Comparison baseline for the rejected alternative:** Buysse DJ et al. *Pittsburgh Sleep
   Quality Index.* Psychiatry Research 1989;28(2):193–213 (PSQI >5 = poor sleeper — the
   validation target when weights are refitted).
