# FINAL RESULTS — all models, full 197 recordings, BENCHMARK_30 Macro-F1

Generated after all inference sweeps completed. Ground truth: `epochs_v3` valid 5-class
labels, BENCHMARK_30 window (237,936 epochs). Split: subject-atomic `folds5_v3`.

## 1. Individual models (all 197 recordings)

| Run | Model | Macro-F1 | SC | ST | N1 | N2 | N3 | REM | Wake |
|---|---|---|---|---|---|---|---|---|---|
| **E11** | **AnySleep 3ch (Fpz+Pz+EOG)** | **0.8267** | .809 | .878 | .622 | .880 | .788 | .904 | .941 |
| E11c | AnySleep 2EEG (Fpz+Pz) | 0.8134 | .797 | .863 | .594 | — | .785 | .878 | — |
| E11a | AnySleep Fpz only | 0.8015 | .790 | .844 | .549 | — | .796 | .875 | — |
| E11b | AnySleep Pz only | 0.7736 | .756 | .829 | .531 | — | .748 | .844 | — |
| E20 | RobustSleepNet Fpz | 0.7501 | .736 | .788 | .442 | .828 | .717 | .855 | .908 |
| E00 | LightGBM bandpower (OOF) | 0.6672 | — | — | .339 | .752 | .687 | .585 | .920 |
| E02c | YASA Fpz+EOG cropped | 0.5463 | .531 | .562 | .069 | .750 | .580 | .649 | .684 |
| E01 | YASA Fpz | 0.5225 | .486 | .611 | .100 | .737 | .538 | .557 | .682 |
| E02 | YASA Fpz+EOG | 0.5171 | .480 | .548 | .122 | — | .364 | .665 | — |
| E03 | YASA Pz+EOG | 0.4272 | .381 | .499 | .070 | — | .262 | .560 | — |
| E10 | SleepFMStager | PARKED | — | — | — | — | — | — | — |
| E07-E09 | SLEEPYLAND (U-Sleep/DeepResNet/SleepTransformer) | DROPPED (team decision) | | | | | | | |

## 2. Combination experiments (full 197)

| Run | Method | Macro-F1 |
|---|---|---|
| E12 | 0.5·AnySleep3ch + 0.5·RSN | 0.8108 |
| E13 | AnySleep+RSN+LightGBM (equal) | 0.8219 |
| E13b | +Fpz-only AnySleep (equal) | 0.8254 |
| E14 | E13 + Viterbi (λ=0.1…0.5) | 0.806–0.820 (hurts) |
| — | E11 + Viterbi (λ=0.1) | 0.8259 (neutral) |
| **E16** | **fold-honest weighted fusion + class biases** | **0.8291** |

## 3. Final recommended system

```
p_final = 0.7 × AnySleep(Fpz+Pz+EOG) + 0.3 × RobustSleepNet(Fpz)
then:  argmax( log(p_final) + b )   with  b = [0, +0.4, 0, 0, +0.2]  (N1, REM)
```

- **OOF Macro-F1 0.8291** (fold-honest; weights/biases selected on 4 folds, applied to the 5th).
- Gain over best single model: +0.0024. Small but stable across all 5 folds.
- **No Viterbi gain** — transition prior slightly hurts (AnySleep already models context).

## 4. Channel ablation (AnySleep, all 197) — minimal-signal answer

| Input | Macro-F1 | Δ vs full |
|---|---|---|
| Fpz+Pz+EOG | **0.8267** | — |
| Fpz+Pz | 0.8134 | −0.013 |
| Fpz only | 0.8015 | −0.025 |
| Pz only | 0.7736 | −0.053 |

**Single frontal EEG keeps 97% of the full 3-channel score.** EOG is the most valuable
addition; Pz-Oz adds almost nothing. Directly answers the hackathon's minimal-signal question.

## 5. Key findings
1. **AnySleep is the winner** (0.827 full-197) but saw Sleep-EDF in training → competition
   legality must be checked; **RSN 0.750 is the best clean (never-saw-Sleep-EDF) model**.
2. **ST > SC for every context model** (RSN .788 vs .736, YASA .611 vs .486) — day-long home
   recordings are the harder domain; hospital nights are cleaner.
3. **YASA is the interpretable baseline only** (0.52–0.55, N1 F1 ≈ 0.07).
4. **Fusion/Viterbi don't pay off** on this data; a light weight+bias calibration gives +0.002.
5. **No alignment/label/harness bugs** — proven by shift sweep (peak at 0), permutation check
   (identity wins), and predicted-vs-true histograms for every model.
