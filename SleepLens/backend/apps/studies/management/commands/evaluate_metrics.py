"""Evaluate SleepLens metrics against the expert hypnogram (ground truth).

For studies ingested from Sleep-EDF (``ground_truth_labels`` present), compares
the deployed two-pass pipeline output against the expert annotation over the
SAME trimmed window (first→last predicted sleep ±30 min):

  - sleep % / stage distribution deltas (predicted vs expert)
  - SOL / WASO / REM latency / stage-shift deltas
  - staging agreement over scored epochs: accuracy, macro-F1, Cohen's kappa,
    per-stage recall
  - SDI composite percentile vs the reference row for this session

Usage:
    python manage.py evaluate_metrics <study_id>
    python manage.py evaluate_metrics <study_id> --json
"""

from __future__ import annotations

import json

import numpy as np
from django.core.management.base import BaseCommand, CommandError

from apps.analysis.pipeline.constants import EPOCH_SECONDS, STAGES
from apps.analysis.pipeline.sqi_composite import reference_row_for_session
from apps.studies.models import Study

_LABELS = list(STAGES)


def _sleep_stats(labels: np.ndarray) -> dict:
    total = len(labels) or 1
    sleep_mask = np.isin(labels, [1, 2, 3, 4])
    sleep_idx = np.flatnonzero(sleep_mask)

    counts = {stage: int((labels == index).sum()) for index, stage in enumerate(_LABELS)}

    sol_min = None
    waso_min = None
    rem_lat_min = None
    if sleep_idx.size:
        first_sleep = int(sleep_idx[0])
        last_sleep = int(sleep_idx[-1])
        sol_min = round(first_sleep * EPOCH_SECONDS / 60.0, 2)
        awake_between = int((~sleep_mask[first_sleep : last_sleep + 1]).sum())
        waso_min = round(awake_between * EPOCH_SECONDS / 60.0, 2)
        rem_positions = np.flatnonzero(labels == 4)
        if rem_positions.size and int(rem_positions[0]) > first_sleep:
            rem_lat_min = round((int(rem_positions[0]) - first_sleep) * EPOCH_SECONDS / 60.0, 2)

    return {
        "n_epochs": int(total),
        "n_sleep": int(sleep_mask.sum()),
        "sleep_pct": round(100.0 * float(sleep_mask.mean()), 2),
        "tst_min": round(int(sleep_mask.sum()) * EPOCH_SECONDS / 60.0, 1),
        "sol_min": sol_min,
        "waso_min": waso_min,
        "rem_lat_min": rem_lat_min,
        "stage_pct_window": {stage: round(100.0 * counts[stage] / total, 2) for stage in _LABELS},
        "stage_pct_tst": _pct_of_tst(labels, counts),
        "stage_shifts": int((labels[1:] != labels[:-1]).sum()) if len(labels) > 1 else 0,
    }


def _pct_of_tst(labels: np.ndarray, counts: dict[str, int]) -> dict[str, float | None]:
    sleep = int(np.isin(labels, [1, 2, 3, 4]).sum())
    if not sleep:
        return {stage: None for stage in _LABELS}
    return {stage: round(100.0 * counts[stage] / sleep, 2) for stage in _LABELS}


def _f1_scores(confusion: dict[str, int]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for label in _LABELS:
        tp = confusion.get(f"{label}|{label}", 0)
        fp = sum(confusion.get(f"{other}|{label}", 0) for other in _LABELS if other != label)
        fn = sum(confusion.get(f"{label}|{other}", 0) for other in _LABELS if other != label)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        scores[label] = (
            round(2 * precision * recall / (precision + recall), 4) if (precision + recall) else 0.0
        )
    return scores


def _macro_f1(confusion: dict[str, int]) -> float:
    scores = _f1_scores(confusion)
    return round(sum(scores.values()) / len(scores), 4)


def _cohens_kappa(confusion: dict[str, int]) -> float:
    total = sum(confusion.values())
    if not total:
        return float("nan")
    observed = sum(confusion.get(f"{label}|{label}", 0) for label in _LABELS) / total
    expected = sum(
        sum(confusion.get(f"{row}|{label}", 0) for row in _LABELS)
        * sum(confusion.get(f"{label}|{column}", 0) for column in _LABELS)
        for label in _LABELS
    ) / (total * total)
    if expected >= 1.0:
        return 1.0
    return round((observed - expected) / (1 - expected), 4)


def _per_stage_recall(confusion: dict[str, int]) -> dict[str, float]:
    recall: dict[str, float] = {}
    for label in _LABELS:
        expert_count = sum(confusion.get(f"{label}|{pred}", 0) for pred in _LABELS)
        recall[label] = round(confusion.get(f"{label}|{label}", 0) / expert_count, 4) if expert_count else float("nan")
    return recall


def _deltas(predicted: dict, expert: dict) -> dict:
    out: dict = {}
    for metric in ["sleep_pct", "tst_min", "sol_min", "waso_min", "rem_lat_min", "stage_shifts"]:
        pred_value = predicted.get(metric)
        expert_value = expert.get(metric)
        if isinstance(pred_value, (int, float)) and isinstance(expert_value, (int, float)):
            out[metric] = round(pred_value - expert_value, 2)
        else:
            out[metric] = None
    for stage in _LABELS:
        pred_value = predicted["stage_pct_window"].get(stage)
        expert_value = expert["stage_pct_window"].get(stage)
        out[f"stage_pct.{stage}"] = (
            round(pred_value - expert_value, 2)
            if isinstance(pred_value, (int, float)) and isinstance(expert_value, (int, float))
            else None
        )
    return out


class Command(BaseCommand):
    help = "Compare SleepLens metrics + staging against the expert hypnogram."

    def add_arguments(self, parser):
        parser.add_argument("study_id")
        parser.add_argument("--json", action="store_true", help="Emit raw JSON instead of a table.")

    def handle(self, *args, **options):
        study = Study.objects.filter(id=options["study_id"]).first()
        if study is None:
            raise CommandError("Study not found.")
        ground_truth = study.ground_truth_labels
        if not ground_truth:
            raise CommandError(
                "This study has no ground_truth_labels (only Sleep-EDF ingests carry expert hypnograms)."
            )

        rows = list(study.epochs.order_by("epoch_index"))
        if not rows:
            raise CommandError("This study has no stored epochs — run the analysis first.")

        window_start = rows[0].epoch_index
        window_end = rows[-1].epoch_index + 1
        gt_window = np.asarray(ground_truth[window_start:window_end], dtype=int)
        pred_labels = np.asarray([_LABELS.index(row.stage) for row in rows], dtype=int)

        scored = gt_window >= 0
        if not scored.any():
            raise CommandError("No scored expert epochs inside the analysis window.")

        predicted_stats = _sleep_stats(pred_labels)
        # Expert side: unscored epochs (-1) are shown as Wake for % computation
        # but excluded from the agreement analysis.
        expert_stats = _sleep_stats(np.where(scored, gt_window, 0))

        confusion: dict[str, int] = {}
        for gt_value, pred_value in zip(gt_window[scored], pred_labels[scored]):
            key = f"{_LABELS[int(gt_value)]}|{_LABELS[int(pred_value)]}"
            confusion[key] = confusion.get(key, 0) + 1
        agreement = {
            "scored_epochs": int(scored.sum()),
            "accuracy": round(
                sum(confusion.get(f"{label}|{label}", 0) for label in _LABELS) / max(1, int(scored.sum())),
                4,
            ),
            "macro_f1": _macro_f1(confusion),
            "kappa": _cohens_kappa(confusion),
            "per_stage_recall": _per_stage_recall(confusion),
        }

        composite_compare = None
        if study.summary and study.summary.get("sdi_metrics"):
            from apps.analysis.pipeline.sqi_composite import compute_composite

            ours = compute_composite(study.summary["sdi_metrics"])
            reference = reference_row_for_session(study.original_filename)
            if ours is not None and reference:
                composite_compare = {
                    "our_percentile": ours.percentile,
                    "our_composite": ours.composite,
                    "reference_percentile": reference["percentile"],
                    "reference_composite": reference["composite"],
                    "reference_n_sleep": reference["n_sleep"],
                    "delta_percentile": round(ours.percentile - reference["percentile"], 2),
                }

        report = {
            "study_id": str(study.id),
            "session": study.original_filename,
            "window_epochs": len(rows),
            "window": {"start_epoch": window_start, "end_epoch": window_end},
            "predicted": predicted_stats,
            "expert": expert_stats,
            "deltas_predicted_minus_expert": _deltas(predicted_stats, expert_stats),
            "agreement": agreement,
            "sdi_composite_vs_reference": composite_compare,
        }

        if options["json"]:
            self.stdout.write(json.dumps(report, indent=2, default=str))
            return

        self._print_table(report)

    def _print_table(self, report: dict) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING(f"SleepLens vs expert — {report['session']}"))
        self.stdout.write(f"window: {report['window']} ({report['window_epochs']} epochs)\n")

        deltas = report["deltas_predicted_minus_expert"]
        self.stdout.write(self.style.MIGRATE_HEADING("Metrics (predicted vs expert, same window)"))
        self.stdout.write(f"{'metric':<16}{'predicted':>12}{'expert':>12}{'delta':>10}")
        for metric in ["sleep_pct", "tst_min", "sol_min", "waso_min", "rem_lat_min", "stage_shifts"]:
            predicted = report["predicted"].get(metric)
            expert = report["expert"].get(metric)
            self.stdout.write(f"{metric:<16}{str(predicted):>12}{str(expert):>12}{str(deltas.get(metric)):>10}")

        self.stdout.write(self.style.MIGRATE_HEADING("\nStage distribution (% of window)"))
        self.stdout.write(f"{'stage':<8}{'predicted':>12}{'expert':>12}{'delta':>10}")
        for stage in _LABELS:
            predicted = report["predicted"]["stage_pct_window"].get(stage)
            expert = report["expert"]["stage_pct_window"].get(stage)
            self.stdout.write(
                f"{stage:<8}{str(predicted):>12}{str(expert):>12}{str(deltas.get(f'stage_pct.{stage}')):>10}"
            )

        agreement = report["agreement"]
        self.stdout.write(self.style.MIGRATE_HEADING("\nStaging agreement (scored epochs)"))
        self.stdout.write(
            f"accuracy={agreement['accuracy']}  macro_f1={agreement['macro_f1']}  kappa={agreement['kappa']}"
        )
        self.stdout.write(f"per-stage recall: {json.dumps(agreement['per_stage_recall'])}")

        composite = report["sdi_composite_vs_reference"]
        if composite:
            self.stdout.write(self.style.MIGRATE_HEADING("\nSDI composite (SQI model output)"))
            self.stdout.write(
                f"our percentile={composite['our_percentile']}  "
                f"reference percentile={composite['reference_percentile']}  "
                f"delta={composite['delta_percentile']}"
            )
        self.stdout.write("")
