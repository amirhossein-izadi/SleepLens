# TinySleepNet — verified notes (paper not on arXiv)

- Paper: Supratak & Guo, "TinySleepNet: An Efficient Deep Learning Model for Sleep Stage
  Scoring based on Raw Single-Channel EEG", EMBC 2020, pp. 641–644.
  DOI: 10.1109/EMBC44109.2020.9176741
- Architecture: multi-resolution 1D-CNN front-end + single unidirectional LSTM + residuals;
  raw 100 Hz single-channel EEG (Fpz-Cz in Sleep-EDF setups).
- Reported SleepEDF-78-ish range (own protocol): acc ~82.5–83.5%, Macro-F1 ~77–78.5%,
  N1-F1 ~42–47% (histories' numbers — verify on our folds, never cite as ours).
- Code: `akaraspt/tinysleepnet` (TF); PyTorch repro: `flower-kyo/Tinysleepnet-pytorch`.
  No official general-purpose pretrained checkpoint — train from scratch on our folds.
- For us: low-compute supervised baseline / pipeline sanity floor. If an advanced model
  can't beat TinySleepNet on identical folds, the architecture isn't helping.
