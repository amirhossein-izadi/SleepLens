"""Result payload builders, split per concern.

Two per-frame chart streams (``ssc`` = staging, ``sdi`` = sleep depth) and two
night-level feature groups (``features/ssc`` from the staging stream,
``features/sqi`` from the depth model), plus the night summary and PSQI.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings

from apps.studies.models import Study, StudyEpoch
from apps.studies.services.feature_groups import split_features, split_not_assessable
from apps.studies.utils.choices import Stage

STAGE_CODES: dict[str, int] = {stage.value: index for index, stage in enumerate(Stage)}


# ─────────────────────────────────────────────────────────────────────────────
# Per-frame streams (chart data)
# ─────────────────────────────────────────────────────────────────────────────


def build_ssc_payload(study: Study) -> dict[str, Any]:
    """Sleep stage classification per frame (chart-ready).

    The per-frame chart data covers the full recording; ``stage_summary`` and
    ``review_summary`` are computed over the benchmark analysis window
    (first→last sleep ±30 min) so distributions are not diluted by the
    untrimmed day.
    """
    rows = list(study.epochs.all().order_by("epoch_index"))
    summary_rows = _analysis_window_rows(study, rows)
    return {
        "study_id": str(study.id),
        "n_epochs": len(rows),
        "epoch_seconds": 30,
        "stage_codes": STAGE_CODES,
        "stage_labels": [stage.value for stage in Stage],
        "confidence_bands": {
            "high": settings.CONFIDENCE_HIGH,
            "medium": settings.CONFIDENCE_MEDIUM,
        },
        "frames": {
            "index": [row.epoch_index for row in rows],
            "start_sec": [row.start_sec for row in rows],
            "stage": [STAGE_CODES.get(row.stage, -1) for row in rows],
            "probabilities": [
                [round(row.probabilities.get(stage.value, 0.0), 4) for stage in Stage]
                for row in rows
            ],
            "confidence": [round(row.confidence, 4) for row in rows],
            "confidence_band": [row.confidence_band for row in rows],
            "needs_review": [row.needs_review for row in rows],
        },
        "stage_summary": _stage_summary(summary_rows),
        "review_summary": _review_summary(summary_rows),
    }


def _analysis_window_rows(study: Study, rows: list[StudyEpoch]) -> list[StudyEpoch]:
    """Rows inside the stored analysis window (falls back to all rows)."""
    window = (study.summary or {}).get("analysis_window") or {}
    start = window.get("start_epoch")
    end = window.get("end_epoch")
    if start is None or end is None:
        return rows
    return [row for row in rows if start <= row.epoch_index < end]


def build_sdi_payload(study: Study) -> dict[str, Any]:
    """Sleep depth index + REM head per frame (chart-ready)."""
    rows = list(study.epochs.all().order_by("epoch_index"))
    values = [row.sdi for row in rows if row.sdi is not None]
    stats = {
        "n": len(values),
        "mean": round(sum(values) / len(values), 4) if values else None,
        "min": round(min(values), 4) if values else None,
        "max": round(max(values), 4) if values else None,
    }
    substitutions = (study.signal_quality or {}).get("substitutions", {})
    return {
        "study_id": str(study.id),
        "model": "sdi_transformer",
        "n_epochs": len(rows),
        "epoch_seconds": 30,
        "sdi_range": [0.0, 1.0],
        "sdi_note": "higher = deeper; zero-shot research index (see substitutions)",
        "frames": {
            "index": [row.epoch_index for row in rows],
            "start_sec": [row.start_sec for row in rows],
            "sdi": [round(row.sdi, 4) if row.sdi is not None else None for row in rows],
            "rem_pred": [int(row.rem_pred) if row.rem_pred is not None else None for row in rows],
        },
        "sdi_stats": stats,
        "substitutions": substitutions,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Night-level feature groups
# ─────────────────────────────────────────────────────────────────────────────


def _feature_source(study: Study) -> tuple[dict, list[dict], dict]:
    features = getattr(study, "features", None)
    if features is None:
        return {}, [], {"available": False}
    ssc, sqi = split_features(features.values or {})
    return {"ssc": ssc, "sqi": sqi}, features.not_assessable or [], {"available": True}


def build_features_payload(study: Study) -> dict[str, Any]:
    """Both feature groups in one payload (used by the report generator)."""
    grouped, not_assessable, meta = _feature_source(study)
    return {
        "study_id": str(study.id),
        "available": meta["available"],
        "values": grouped,
        "not_assessable": not_assessable,
    }


def build_ssc_features_payload(study: Study) -> dict[str, Any]:
    """Features computed from the staging stream + staged signal features."""
    grouped, not_assessable, meta = _feature_source(study)
    ssc_marks, _ = split_not_assessable(not_assessable)
    return {
        "study_id": str(study.id),
        "available": meta["available"],
        "group": "ssc",
        "source": {
            "staging_system": (study.summary or {}).get("staging_system"),
            "staging_members": (study.summary or {}).get("staging_members"),
        },
        "values": grouped.get("ssc", {}),
        "not_assessable": ssc_marks,
    }


def build_sqi_features_payload(study: Study) -> dict[str, Any]:
    """Features computed from the sleep-depth model stream."""
    grouped, not_assessable, meta = _feature_source(study)
    _, sqi_marks = split_not_assessable(not_assessable)
    substitutions = (study.signal_quality or {}).get("substitutions", {})
    return {
        "study_id": str(study.id),
        "available": meta["available"],
        "group": "sqi",
        "model": "sdi_transformer",
        "values": grouped.get("sqi", {}),
        "not_assessable": sqi_marks,
        "substitutions": substitutions,
        "caveat": (
            "SDI is a zero-shot research index (channel substitutions applied); "
            "not clinically validated."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Night summary + PSQI
# ─────────────────────────────────────────────────────────────────────────────


def build_night_payload(study: Study) -> dict[str, Any]:
    """Night summary item: status, window, stage table, review, SDI metrics."""
    summary = study.summary or {}
    return {
        "study_id": str(study.id),
        "original_filename": study.original_filename,
        "status": study.status,
        "status_message": study.status_message,
        "error_message": study.error_message,
        "created_at": study.created_at,
        "started_at": study.started_at,
        "finished_at": study.finished_at,
        "duration_minutes": study.duration_minutes,
        "n_epochs": study.n_epochs,
        "staging_system": summary.get("staging_system"),
        "staging_members": summary.get("staging_members"),
        "analysis_window": summary.get("analysis_window"),
        "stage_counts": summary.get("stage_counts"),
        "stage_pct": summary.get("stage_pct"),
        "sleep_pct": summary.get("sleep_pct"),
        "mean_confidence": summary.get("mean_confidence"),
        "needs_review_count": summary.get("needs_review_count"),
        "needs_review_pct": summary.get("needs_review_pct"),
        "sdi_metrics": summary.get("sdi_metrics"),
        "signal_quality": study.signal_quality,
    }


def build_psqi_payload(study: Study) -> dict[str, Any]:
    """PSQI questionnaire state for a study (all-or-nothing)."""
    from apps.studies.models import PSQI
    from apps.studies.models.psqi import COMPONENT_FIELDS

    # Query instead of using the reverse-relation cache: a delete earlier in
    # the same request must be reflected immediately.
    psqi = PSQI.objects.filter(study=study).first()
    if psqi is None:
        return {"taken": False, "global_score": None, "components": {}}
    return {
        "taken": True,
        "global_score": psqi.global_score,
        "components": {field: int(getattr(psqi, field)) for field in COMPONENT_FIELDS},
    }


def _stage_summary(rows: list[StudyEpoch]) -> dict[str, Any]:
    total = len(rows) or 1
    summary: dict[str, Any] = {}
    for stage in Stage:
        stage_rows = [row for row in rows if row.stage == stage.value]
        count = len(stage_rows)
        confidences = [row.confidence for row in stage_rows]
        summary[stage.value] = {
            "count": count,
            "pct": round(100.0 * count / total, 2),
            "mean_confidence": round(sum(confidences) / count, 4) if count else None,
            "review_count": sum(1 for row in stage_rows if row.needs_review),
        }
    return summary


def _review_summary(rows: list[StudyEpoch]) -> dict[str, Any]:
    total = len(rows) or 1
    needs_review = [row for row in rows if row.needs_review]
    low = [row for row in rows if row.confidence_band == "low"]
    return {
        "needs_review_count": len(needs_review),
        "needs_review_pct": round(100.0 * len(needs_review) / total, 2),
        "low_confidence_count": len(low),
        "low_confidence_pct": round(100.0 * len(low) / total, 2),
    }
