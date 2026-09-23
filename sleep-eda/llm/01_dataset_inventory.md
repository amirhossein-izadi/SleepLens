# 01 Dataset inventory

## Files
- 399 files total, 394 EDF, 8.715 GB. sleep-cassette 306, sleep-telemetry 88, root 5 (RECORDS, RECORDS-v1, SHA256SUMS, SC/ST-subjects.xls).
- 197 PSG + 197 Hypnogram, pairing perfect by stem (first 6 chars). 0 missing, 0 multi.
- SC PSG 153 (~49.6 MB mean, ~20 h), ST PSG 44 (~25.4 MB mean, ~9 h). Hyp ~4.3 KB mean.
- 100 subject-prefixes (78 SC IDs + 22 ST), mostly 2 nights each. Lost per PhysioNet: SC36-night1, SC52-night1, SC13-night2.

## Schemas
_source: tables/schemas.csv (2 rows)_ 

|   schema_id |   count | example_file     | channels                                                                                  |
|------------:|--------:|:-----------------|:------------------------------------------------------------------------------------------|
|           0 |     153 | SC4001E0-PSG.edf | EEG Fpz-Cz|EEG Pz-Oz|EOG horizontal|Resp oro-nasal|EMG submental|Temp rectal|Event marker |
|           1 |      44 | ST7011J0-PSG.edf | EEG Fpz-Cz|EEG Pz-Oz|EOG horizontal|EMG submental|Marker                                  |

## Recordings sample (full: tables/recordings.csv, 197 rows)
_source: tables/recordings.csv (197 rows)_ 

| psg_file         | cohort   | stem   |   duration_h |   n_epochs |   wake |   n1 |   n2 |   n3 |   rem |   unknown_q |   mov |
|:-----------------|:---------|:-------|-------------:|-----------:|-------:|-----:|-----:|-----:|------:|------------:|------:|
| SC4001E0-PSG.edf | SC       | SC4001 |      22.0833 |       2880 |   1997 |   58 |  250 |  220 |   125 |         230 |     0 |
| SC4002E0-PSG.edf | SC       | SC4002 |      23.5833 |       2880 |   1885 |   59 |  373 |  297 |   215 |          50 |     1 |
| SC4011E0-PSG.edf | SC       | SC4011 |      23.35   |       2880 |   1856 |  109 |  562 |  105 |   170 |          78 |     0 |
| SC4012E0-PSG.edf | SC       | SC4012 |      23.75   |       2880 |   1824 |   92 |  660 |   96 |   176 |          32 |     0 |
| SC4021E0-PSG.edf | SC       | SC4021 |      23.3667 |       2880 |   1907 |   94 |  545 |   95 |   163 |          76 |     0 |
| SC4022E0-PSG.edf | SC       | SC4022 |      22.9667 |       2880 |   1871 |  184 |  402 |  119 |   179 |         124 |     1 |
| SC4031E0-PSG.edf | SC       | SC4031 |      23.5    |       2880 |   2008 |   61 |  485 |   57 |   209 |          60 |     0 |
| SC4032E0-PSG.edf | SC       | SC4032 |      22.7667 |       2880 |   1957 |   45 |  400 |  131 |   199 |         148 |     0 |
| SC4041E0-PSG.edf | SC       | SC4041 |      21.4167 |       2880 |   1534 |  166 |  620 |   53 |   196 |         310 |     1 |
| SC4042E0-PSG.edf | SC       | SC4042 |      23.2667 |       2880 |   1773 |  137 |  514 |   94 |   270 |          88 |     4 |

_... truncated 187 rows, see CSV_
Durations: SC ~22 h e.g. SC4001 79500 s; ST ~10 h e.g. ST7011 35900 s. See 12_fig_descriptions for duration_dist.
