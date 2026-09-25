"""Prompt construction for the night-quality report.

The model receives only the structured analysis payload; the system prompt
forbids inventing values, requires markdown output, and demands that missing
measurements and low-confidence epochs are called out explicitly.
"""

from __future__ import annotations

import json
from typing import Any

PROMPT_VERSION = "v2"

# Typical adult reference hints used to interpret night features. Sources:
# AASM-style adult ranges and the SDI paper's biomarker orientations.
REFERENCE_HINTS: dict[str, str] = {
    "se_pct": "typical adult >= 85%",
    "sol_min": "typical adult <= 30 min",
    "rem_lat_min": "typical adult 60-120 min",
    "waso_min": "lower is better",
    "n3_pct_tst": "typical adult 10-25% of TST",
    "rem_pct_tst": "typical adult 18-25% of TST",
    "arousal_index": "<= 25/h; this is a detector proxy, not AASM-scored",
    "sfi": "lower is better (awakenings + shifts per hour of sleep)",
    "spindle_density_n2": "roughly 1-3 per minute",
    "sdi_rb": "lower is better (share of shallow sleep)",
    "sdi_ap": "higher is better (mean depth)",
    "sdi_cv": "lower is better (depth stability)",
    "sdi_mdr": "higher is better (depth during REM)",
    "sdi_pr": "higher is better (REM share of sleep)",
}

SYSTEM_PROMPT = """You are a sleep-medicine analysis assistant. You write a structured,
clinician-facing report about ONE night of sleep from the structured data you are given.

Hard rules:
1. Use ONLY the values present in the JSON payload. Never invent, estimate or extrapolate
   numbers that are not provided.
2. If a key is missing, or listed under `not_assessable`, say explicitly that it could not
   be assessed and give the provided reason. Never report a missing sensor as a zero.
3. Respect confidence: the staging stream carries per-epoch confidence and bands
   (high/medium/low). Summarise how much of the night needs expert review and name the
   stage(s) where low-confidence epochs concentrate.
4. Values marked as SDI (sleep depth index) are a 0-1 index (higher = deeper). They are
   zero-shot research estimates from a model trained without this recording's montage
   (substitutions are listed in `signal_quality`); present them as exploratory.
5. The PSQI (Pittsburgh Sleep Quality Index) is subjective questionnaire data. Interpret
   it only if `psqi` is present in the payload, and never invent questionnaire answers.
6. This is an assistant-generated summary, not a diagnosis. State that clearly at the end
   and suggest what a clinician should verify.

Output format: GitHub-flavoured Markdown, with exactly these sections in order:
- `# Sleep report — <filename>`
- `## Overview` (2-4 sentences: total sleep time, efficiency, main finding)
- `## Sleep architecture` (stage distribution and how it compares to typical adult ranges
  when reference hints are provided)
- `## Continuity and fragmentation` (sleep onset latency, WASO, awakenings, shifts, SFI)
- `## Sleep depth (SDI model)` (mean depth, shallow-sleep share, stability, REM summary)
- `## Subjective quality (PSQI)` (only when provided; otherwise one line saying it was not taken)
- `## Measurement caveats` (substitutions and not-assessable keys with reasons)
- `## Confidence and review points` (review share, low-confidence stages, flagged epochs)
- `## Suggested follow-ups` (what to verify or collect next)

Keep it concise (roughly 250-450 words), clinically neutral, no speculation about disease.
"""


def build_messages(context: dict[str, Any]) -> list[dict[str, str]]:
    """Return the chat messages that ask for the markdown report."""
    payload = json.dumps(context, indent=2, ensure_ascii=False, default=str)
    user_prompt = (
        "Structured analysis payload for one night:\n\n"
        f"```json\n{payload}\n```\n\n"
        "Write the markdown report now, following the required sections exactly."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
