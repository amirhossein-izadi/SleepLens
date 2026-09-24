# E10 SleepFMStager — PARKED with evidence (not a harness bug)

## Verified
- Mirror vs upstream parity: final_layer bit-identical; all 56 tokenizer keys bit-identical.
- Vendored code == upstream math for our mask=None path (attention pooling, PE, transformer, LSTM).
- Model RESPONDS to input: spike trains -> class 3 (0.895), sines -> class 0. Not dead.
- On our standardized 128Hz sleep EEG (3ch/4ch, scale 0.01x-10x): constant class 0 (Wake).
- Short same-stage segments: N3 -> class 2 (0.89), N2/N1/REM/Wake -> class 0.
- Hypothesis B (staging head on base-encoder embeddings) tested: constant class 2 - rejected.
- Units verified correct (Fpz std 25.9 uV, realistic).

## Remaining unknown (why parked)
- Upstream HDF5 creation not reproducible here (stale config paths, tokenized-embedding
  pipeline ambiguity). Cannot rule out an upstream-specific input convention.
- Need upstream demo data or their exact HDF5 to close.

## License: CC BY-NC 4.0 (competition terms to check).
