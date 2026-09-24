# Priority + experiment registry

Order = information per effort. Stop each phase only on the comparison table.

## Paper-result comparison (own protocols — NOT comparable, orientation only)
| Model | Reported Macro-F1 | N1 | Note |
|---|---|---|---|
| LGFNet | 85.0 | 67.1 | own SleepEDF-78 protocol |
| AnySleep | ~0.81 SC / ~0.77 ST | — | in-train sedf splits |
| SleepEffFormer | 78.9 | ~0.39 | own split |
| SleepTransformer-78 | 78.8 | 48.5 | SHHS-init |
| SOMNUS | 68.7–87.2 (24 ds) | — | OOD range, beats individuals 94.9% |
| SleepDG→SleepEDFx | 77.44 | — | unseen-target setting |
| DIFFormer→SleepEDFx | 78.19 | — | unseen-target setting |
| U-Sleep mean | 0.79 | 0.53 | 21 datasets |
| YASA healthy | ~0.74 | weak | NSRR-trained |
| Ours pilot E01/E02 (3 recs) | 0.55/0.53 | 0.11/0.20 | YASA zero-shot, FULL-valid |

## Queue (registry: `configs/experiments.csv`)
Phase 1: E01–E05 YASA (+fusion, +Viterbi) ✅ E01/E02 pilot done
Phase 2: E06–E09 SLEEPYLAND (SOMNUS→members)
Phase 3: E10 SleepFMStager (adapter + aggregation ablation)
Phase 4: E11 AnySleep (mark SleepEDF exposure)
STOP → compare → E12–E15 fusion/Viterbi/stacker → E16–E17 tune/local → E18–E20 DG research.
Heads/adapters explicitly allowed (SleepFM head, linear probes) — inference-first, not inference-only.
