# 03 Labels (R&K)

## Raw → 5-class
Map: W→Wake, 1→N1, 2→N2, 3+4→N3, R→REM. ? and Movement → OTHER (exclude from loss, keep for SQI/TRT).
Convention R&K (3/4 split) on Fpz-Cz/Pz-Oz. Tech ID = 8th char of hyp filename.

## Epoch counts (197 nights, edfio expansion duration/30)
_source: tables/annotations_summary.csv (8 rows)_ 

| raw_label     |   events |   epochs_30s |      hours |        pct |
|:--------------|---------:|-------------:|-----------:|-----------:|
| Sleep stage W |     4461 |       290365 | 2419.71    | 60.0649    |
| Sleep stage 2 |     8171 |        88983 |  741.525   | 18.407     |
| Sleep stage R |     1953 |        34184 |  284.867   |  7.0713    |
| Sleep stage 1 |     7292 |        25175 |  209.792   |  5.2077    |
| Sleep stage ? |      174 |        25047 |  208.725   |  5.18122   |
| Sleep stage 3 |     4820 |        12191 |  101.592   |  2.52183   |
| Sleep stage 4 |     1462 |         7263 |   60.525   |  1.50242   |
| Movement time |      196 |          211 |    1.75833 |  0.0436474 |

- ?: 25047 epochs, mean per-rec q_before 0.0 / q_mid 0.8 / q_after 126.3 → ~99% trailing unscored. Movement 211 epochs negligible.
- Long blocks are multiples of 30 (e.g. leading Wake 30630 s = 1021 epochs). No overlaps after sort.
