# 05 Quality

_source: tables/signal_quality.csv (10 rows)_ 

| file             | channel        |   nan |   inf |   flat_frac |   p99_abs |        std |
|:-----------------|:---------------|------:|------:|------------:|----------:|-----------:|
| SC4001E0-PSG.edf | EEG Fpz-Cz     |     0 |     0 |  0.00236856 |   82.2857 |  25.9094   |
| SC4001E0-PSG.edf | EEG Pz-Oz      |     0 |     0 |  0.00455221 |   39.9919 |  11.426    |
| SC4001E0-PSG.edf | EOG horizontal |     0 |     0 |  0.00907423 |  256.008  |  73.3307   |
| SC4001E0-PSG.edf | Resp oro-nasal |     0 |     0 |  0.0132092  |  670      | 171.596    |
| SC4001E0-PSG.edf | EMG submental  |     0 |     0 |  0.00792553 |    3.63   |   0.956947 |
| SC4001E0-PSG.edf | Temp rectal    |     0 |     0 |  0.0166059  |   37.4355 |   0.367227 |
| ST7011J0-PSG.edf | EEG Fpz-Cz     |     0 |     0 |  0.100953   | 2353.23   | 669.649    |
| ST7011J0-PSG.edf | EEG Pz-Oz      |     0 |     0 |  0.109571   | 2353.23   | 666.383    |
| ST7011J0-PSG.edf | EOG horizontal |     0 |     0 |  0.10205    | 2353.23   | 668.668    |
| ST7011J0-PSG.edf | EMG submental  |     0 |     0 |  0.144594   | 2353.23   | 665.187    |

- 0 NaN/Inf in sampled SC4001 + ST7011 all channels.
- Flat-frac (diff<1e-12, decimated): SC 0.002–0.017, ST ~0.10 (likely telemetry quantization, not dropout — verify per-record p99/std before training).
- p99_abs + std in CSV = clip audit. Worst/best: rank by p99_abs/std outlier per channel.
- 7 ST hyps: pyedflib OSError EDF+ Recordingfield, mne/edfio OK — parser risk closed, no data loss.
