"""Case-context builder for the assistant.

Reuses the exact same payloads the report generator uses, so the assistant
never sees numbers the API does not expose — and never invents values.
"""

from __future__ import annotations

import json
from typing import Any

from apps.studies.services.results import (
    build_features_payload,
    build_night_payload,
    build_psqi_payload,
)

CONTEXT_INSTRUCTIONS = (
    "You are the SleepLens clinical assistant. A sleep expert is consulting you about ONE\n"
    "night of sleep. Ground every answer in the case data below and follow these rules:\n"
    "1. Use only the provided values; never invent or extrapolate numbers.\n"
    "2. Items listed under not_assessable must be called 'not assessable' with the given\n"
    "   reason — never reported as zero or normal.\n"
    "3. Sleep depth (SDI) values are a zero-shot research index (see substitutions);\n"
    "   present them as exploratory, not diagnostic.\n"
    "4. Staging has per-epoch confidence; flag which parts need expert review.\n"
    "5. This is decision support, not a diagnosis."
)


def build_case_context(study: Any) -> str:
    """Compact, honest JSON context for one study."""
    night = build_night_payload(study)
    features = build_features_payload(study)
    patient = getattr(study, "patient", None)
    context: dict[str, Any] = {
        "patient": (
            {
                "full_name": patient.full_name,
                "birth_year": patient.birth_year,
                "sex": patient.sex,
            }
            if patient is not None
            else None
        ),
        "night": {
            "original_filename": night.get("original_filename"),
            "status": night.get("status"),
            "n_epochs": night.get("n_epochs"),
            "duration_minutes": night.get("duration_minutes"),
            "staging_system": night.get("staging_system"),
            "analysis_window": night.get("analysis_window"),
            "stage_pct": night.get("stage_pct"),
            "mean_confidence": night.get("mean_confidence"),
            "needs_review_pct": night.get("needs_review_pct"),
            "sdi_metrics": night.get("sdi_metrics"),
            "signal_quality": night.get("signal_quality"),
        },
        "psqi": build_psqi_payload(study),
        "ssc_features": features.get("values", {}).get("ssc", {}),
        "sqi_features": features.get("values", {}).get("sqi", {}),
        "not_assessable": features.get("not_assessable", []),
    }
    payload = json.dumps(context, indent=2, ensure_ascii=False, default=str)
    return f"{CONTEXT_INSTRUCTIONS}\n\nCase data (JSON):\n{payload}"
