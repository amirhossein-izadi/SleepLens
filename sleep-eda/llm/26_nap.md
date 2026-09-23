# Evening/afternoon naps before lights-off (48/153 SC)

Table: `tables/nap_character.csv` (file, rec_start, nap_start_clock, nap_sleep_min, nap_stages, gap_napEnd_to_LO_min, SOL, main_sleep_clock).

- **Yes, naps:** start clocks 14:00–23:00, peak 17–21. Median sleep 15.3 min (mean 24.5, max 123.5). Gap nap-end→lights-off median 69 min (awake between nap and main sleep) — classic nap pattern.
- **Light:** 242 N1 + 181 N2 blocks vs 100 N3, only 4 REM → dozing/light naps, rarely deep.
- **Main sleep later** (~23:00–01:00), separate episode.
- 2 cases nap runs into lights-off (gap −15/−5 min: SC4121, SC4332 — fell asleep early, stayed asleep).
- Implication: TST/SOL/SE must decide nap inclusion explicitly (report with + without naps); Macro-F1 training unaffected (epochs are epochs), SQI is affected.
