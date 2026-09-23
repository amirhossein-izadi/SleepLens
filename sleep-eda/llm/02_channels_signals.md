# 02 Channels + sampling

## Channel availability (197 recordings)
_source: tables/channels.csv (8 rows)_ 

| channel_original   |   present_in_n_recordings |   missing_in_n | sfreqs_seen   |
|:-------------------|--------------------------:|---------------:|:--------------|
| EEG Fpz-Cz         |                       197 |              0 | 100.0         |
| EEG Pz-Oz          |                       197 |              0 | 100.0         |
| EOG horizontal     |                       197 |              0 | 100.0         |
| EMG submental      |                       197 |              0 | 1.0;100.0     |
| Resp oro-nasal     |                       153 |             44 | 1.0           |
| Temp rectal        |                       153 |             44 | 1.0           |
| Event marker       |                       153 |             44 | 1.0           |
| Marker             |                        44 |            153 | 10.0          |

## Key facts (from EdfReader headers)
- 2 schemas only. Core everywhere: EEG Fpz-Cz@100 uV, EEG Pz-Oz@100 uV, EOG horizontal@100 uV.
- EMG SHIFT: SC 1 Hz envelope ±5 uV (HPF+rect+LPF rms) vs ST 100 Hz raw ±3000 uV. Never z-score jointly.
- SC-only 1 Hz: Resp oro-nasal (thermistor, unitless ±2048), Temp rectal 34–40 DegC, Event marker. ST-only: Marker 10 Hz ID+M-E.
- Scales: SC EEG ±192/197 uV 12-bit; ST EEG/EOG/EMG ±3000 uV 14-bit. Transducers Ag-AgCl.
- Absent everywhere: SpO2, airflow pressure, chest/abd effort, ECG/HR, position, actigraphy, leg EMG.
- Example headers: SC4001 start 1989-04-24 16:13 dur 79500 s; ST7011 start 1994-07-12 23:00 dur 35900 s.

## Sample signal stats (5 recs, full: tables/signal_stats_sample.csv)
_source: tables/signal_stats_sample.csv (31 rows)_ 

| file             | channel        |   sf |        mean |        std |       rms |        p1 |      p99 |        min |       max |   flat_frac |
|:-----------------|:---------------|-----:|------------:|-----------:|----------:|----------:|---------:|-----------:|----------:|------------:|
| SC4001E0-PSG.edf | EEG Fpz-Cz     |  100 |   0.165506  |  25.9094   |  25.9099  |  -71.3143 |  71.4081 |  -192      |  170.62   |  0.00675635 |
| SC4001E0-PSG.edf | EEG Pz-Oz      |  100 |  -0.350854  |  11.426    |  11.4314  |  -31.3546 |  31.0264 |  -171.088  |  196      |  0.00989472 |
| SC4001E0-PSG.edf | EOG horizontal |  100 |   0.860522  |  73.3307   |  73.3357  | -207.221  | 230.382  |  -511.769  |  517.189  |  0.0196887  |
| SC4001E0-PSG.edf | Resp oro-nasal |    1 | 126.965     | 171.596    | 213.461   | -346      | 647      | -1748      | 1806      |  0.0104026  |
| SC4001E0-PSG.edf | EMG submental  |    1 |   2.95001   |   0.956947 |   3.10134 |    0.118  |   3.63   |    -0.108  |    3.81   |  0.00929571 |
| SC4001E0-PSG.edf | Temp rectal    |    1 |  36.9822    |   0.367227 |  36.984   |   36.0537 |  37.4355 |    34.7086 |   37.4968 |  0.0162644  |
| SC4001E0-PSG.edf | Event marker   |    1 | 858.378     |  36.0717   | 859.135   |  781      | 936      |   136      |  980      |  0.0155474  |
| SC4041E0-PSG.edf | EEG Fpz-Cz     |  100 |  -0.0602399 |  27.446    |  27.4461  |  -80.9233 |  81.8659 |  -193      |  193      |  0.00735149 |
| SC4041E0-PSG.edf | EEG Pz-Oz      |  100 |   0.430398  |  10.7149   |  10.7236  |  -28.5824 |  29.1001 |  -193.527  |  183.628  |  0.010466   |
| SC4041E0-PSG.edf | EOG horizontal |  100 |  -0.343374  |  71.6614   |  71.6622  | -215.778  | 245.556  |  -654      |  601.111  |  0.0253061  |
| SC4041E0-PSG.edf | Resp oro-nasal |    1 |  83.6632    | 276.291    | 288.68    | -758.01   | 889      | -1463      | 1633      |  0.0136318  |
| SC4041E0-PSG.edf | EMG submental  |    1 |   2.29665   |   0.92297  |   2.47517 |    0.228  |   3.144  |    -0.742  |    3.29   |  0.0119587  |
| SC4041E0-PSG.edf | Temp rectal    |    1 |  36.9903    |   0.320319 |  36.9917  |   36.0803 |  37.6407 |    35.9538 |   38.176  |  0.0256034  |
| SC4041E0-PSG.edf | Event marker   |    1 | 902.906     |  29.2774   | 903.381   |  845      | 959      |    90      | 1013      |  0.0510902  |

_... truncated 17 rows, see CSV_
