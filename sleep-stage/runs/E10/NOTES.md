# E10 SleepFMStager — PARKED with evidence (not a harness bug)

## Verified
- Mirror vs upstream parity: final_layer bit-identical; all 56 tokenizer keys bit-identical.
- Vendored code == upstream math for our mask=None path (attention pooling, PE, transformer, LSTM).
- Model RESPONDS to input: spike trains -> class 3 (0.895), sines -> class 0. Not dead.
- On our standardized 128Hz sleep EEG (3ch/4ch, scale 0.01x-10x): constant class 0 (Wake).
- Short same-stage segments: N3 -> class 2 (0.89), N2/N1/REM/Wake -> class 0.
- Hypothesis B (staging head on base-encoder embeddings) tested: constant class 2 - rejected.
- Units verified correct (Fpz std 25.9 uV, realistic).

## Decisive diagnostic (eval/e10_diagnostic.py -> docs/e10_diagnostic.csv)
6 input regimes x 3 recordings, ALL -> 100% Wake (macro 0.063-0.064, zero N1/N2/N3/REM):
z-score | raw uV | z-score x26 (uV scale) | 4ch (dup EOG) | 4ch real EMG (ST, 100Hz) | 30-s windows.
=> input scale, channel count, and windowing are all ruled out as the cause.

## Verdict: not solvable with available artifacts (closed)
- Weights bit-identical to upstream, model alive on synthetic input, yet constant-Wake on real
  EEG in every tested convention (6/6 + earlier probe).
- Only remaining unknown is the upstream HDF5/label pipeline (start_index / tokenized-embedding
  alignment) which is not reproducible from the release (stale config paths, no demo data).
- Park permanently unless upstream demo data or author contact becomes available.

## License: CC BY-NC 4.0 (competition terms to check).
