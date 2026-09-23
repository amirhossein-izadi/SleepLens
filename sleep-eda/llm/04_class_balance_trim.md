# 04 Balance + Wake trim

## Global 5-class (no trim, 483419 epochs)
_source: tables/class_distribution.csv (7 rows)_ 

| class   |   epochs |      hours |        pct |
|:--------|---------:|-----------:|-----------:|
| Wake    |   290365 | 2419.71    | 60.0649    |
| N2      |    88983 |  741.525   | 18.407     |
| REM     |    34184 |  284.867   |  7.0713    |
| N1      |    25175 |  209.792   |  5.2077    |
| ?       |    25047 |  208.725   |  5.18122   |
| N3      |    19454 |  162.117   |  4.02425   |
| Mov     |      211 |    1.75833 |  0.0436474 |

Imbalance max/min = 290365/19454 = 14.9. N1 5.21% rare, N3 4.02% rare, Wake 60.06% dominates (SC daytime).
## Trim policies (exact recount)
- A_no_trim: Wake 60.1% N2 18.4 REM 7.1 N1 5.2 N3 4.0 ? 5.2% imb 14.9
- B_30min (keep ≤60 Wake epochs before first + after last sleep): Wake 29.4 N2 37.3 REM 14.3 N1 10.6 N3 8.2 ? 0.2% imb 4.6
- C_15min: Wake 26.5 N2 38.8 REM 14.9 N1 11.0 N3 8.5 imb 4.6
Rule: train with B (or C), infer/SQI on full night. Trimming must not corrupt SE/WASO — compute SQI untrimmed.
Per-recording: tables/subject_class_distribution.csv (197 rows: wake_ep,n1,n2,n3,rem,q,mov,first/last sleep idx, wake_before/after). wake_before mean 651 ep (326 min), wake_after 693 ep.
Figs in words: class_dist = Wake bar 3× N2; persubject_wake = wide 0–90% Wake; trim_impact = Wake bar halves under trim. See 12.
