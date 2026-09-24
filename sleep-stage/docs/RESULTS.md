# RESULTS (pilot 3 recs unless noted) — updated live

Metric: Macro-F1. Ground truth: epochs_v3 valid labels. Class order verified per model
(shift sweep peaks at 0, identity permutation wins for all — see eval/debug_checks.py).

## Master table (BENCHMARK_30 where available)

| Run | Model | Train-by-us | FULL_VALID | BENCH_30 | SC | ST | N1 | Notes |
|---|---|---|---|---|---|---|---|---|
| E11 | AnySleep (Fpz+Pz+EOG) | none | **0.861** | **0.847** | .831 | .880 | .73 | sedf-exposed (disclosed); full sweep 81/197 |
| E20 | RobustSleepNet (Fpz) | none | 0.762 | **0.750** | .736 | **.788** | .44 | **FULL 197 DONE**; clean zero-shot (LODO) |
| E07 | SLEEPYLAND U-Sleep (EEG+EOG) | none | 0.774 | 0.739 | .812 | .644 | .44 | pilot; full sweep 30/197 |
| E02c | YASA (Fpz+EOG, cropped) | none | 0.546 | 0.546 | .531 | .562 | .07 | crop-before-inference |
| E01 | YASA (Fpz, full rec) | none | 0.557 | 0.523 | .486 | .611 | .10 | full-197 |
| E03 | YASA (Pz+EOG, full rec) | none | 0.474 | 0.427 | .381 | .499 | .07 | full-197 |
| E10 | SleepFMStager | none | PARKED | — | — | — | — | constant-Wake; see runs/E10/NOTES.md |

## Key findings (evidence)
1. **No alignment/label bugs**: all models peak at shift 0, identity permutation wins,
   AnySleep pred hist ≈ true hist. Harness validated.
2. **RSN bug fixed**: missing 900-s padding trim cost 0.37 macro (0.43→0.80).
3. **Crop-before-inference confirmed** (advisor test C): YASA +0.085 macro full-197
   (0.461→0.546); per-rec +0.03..+0.11. Context-sensitive models degrade on day-long SC.
4. **YASA is genuinely weaker** on our montage: N1 F1 ~0.07-0.10 (documented weakness),
   central-derivation preference; still useful as clean external zero-shot + SHAP story.
5. **AnySleep is strongest overall** but saw Sleep-EDF in training (competition-legal?).
6. **RSN (clean) beats U-Sleep on ST** (.680 vs .644) but loses on SC (.811 vs .812 → tie).
7. **ST vs SC flip**: YASA does *better* on ST than SC (clean in-bed recording, no daytime
   wake context) — the opposite of AnySleep/RSN. Domain-robustness is model-specific.
8. SleepFMStager: mirror weights bit-identical to upstream, responds to input, but
   constant Wake on our pipeline → parked pending upstream HDF5 reproduction.
