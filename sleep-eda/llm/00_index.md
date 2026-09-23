# LLM index — start here

This folder is the LLM-friendly EDA. Figs are NOT needed — every fig has a text description in 12_fig_descriptions.md.
Order: 01 dataset → 02 channels → 03 labels → 04 balance/trim → 05 quality → 06 physiology → 07 temporal → 08 subjects → 09 splits → 10 channel+SQI → 11 tensors/preproc → 12 figs → 13 handoff.
All numbers from actual files via edfio/pyedflib (device python). Parser note: pyedflib rejects 7 ST hyps (strict header), edfio+mne read 197/197 — all stats use edfio.

14 deep-story (home/lab life) → 15 micro events → 16 meso N1/Fisher → 17 macro cycles/age/drug → 18 gaps-closed → 19 full-EDA (459k) → 20 channelwise → 21 completeness checklist → 22 posterior spectral → 23 events/transitions → 24 wake-rem ambiguity → 25 rest done → 26 naps → 27 nap audit → 28 dataset corrections.
Required outputs: tables/*.csv (12 spec + full), figs (16/16 + extras), REPORT.md A–P.
