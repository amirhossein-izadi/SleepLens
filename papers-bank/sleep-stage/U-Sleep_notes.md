# U-Sleep — verified notes (paper not on arXiv; full text: npj Digit Med 2021)

- Paper: Perslev et al., "U-Sleep: resilient high-frequency sleep staging",
  npj Digital Medicine 4:72 (2021). DOI: 10.1038/s41746-021-00440-5
- Training: 19,924 PSGs / 15,660 participants / 16 studies (13 in-dist + 8 holdout-only).
- Input: exactly 1 EEG + 1 EOG, arbitrary standard positions; internal 128 Hz resample;
  outputs stages up to 128 Hz; laptop-CPU inference in seconds.
- Channel strategy: all (EEG,EOG) pairs + majority vote (quadratic cost vs AnySleep linear).
- Reported mean F1: W .90, N1 .53, N2 .85, N3 .76, REM .90; mean .79 (SEDF-SC 0.79);
  matches best human expert on DOD-H/DOD-O consensus.
- EMG: tested, no gain — excluded (same conclusion as AnySleep).
- Use: `perslev/U-Time` repo (paper-version tags), hosted inference at sleep.ai.ku.dk.
- For us: mature zero-shot reference; rigid 1+1 channel format vs AnySleep's n-channel.
