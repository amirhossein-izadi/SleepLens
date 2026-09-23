# 07 Temporal structure

## Transition P(t|t-1) epoch-level (5-class, ?/Mov excluded)
_source: tables/transition_matrix.csv (5 rows)_ 

| from/to   |   Wake |     N1 |     N2 |     N3 |    REM |
|:----------|-------:|-------:|-------:|-------:|-------:|
| Wake      | 0.9853 | 0.0137 | 0.0006 | 0      | 0.0003 |
| N1        | 0.0892 | 0.7109 | 0.1697 | 0.0004 | 0.0299 |
| N2        | 0.0142 | 0.0251 | 0.9091 | 0.0399 | 0.0117 |
| N3        | 0.009  | 0.0054 | 0.1667 | 0.8178 | 0.0012 |
| REM       | 0.0164 | 0.0263 | 0.0122 | 0      | 0.945  |

Self: Wake .985 N1 .711 N2 .909 N3 .818 REM .945. Cross: N1→N2 .17, N3→N2 .167, N1→Wake .089, REM→N1 .026. Sequence model strongly justified; N1 most transient.
## Runs
Median epochs: REM 11, N2 4, Wake 2, N1 2, N3 1, OTHER 1. Singles: N1 2872, N2 1957, N3 1882, Wake 1757, REM 190. N3 fragmented (3↔4 alternation) — consider smoothing/CRF. Context 5–11 epochs covers N2/REM runs.
