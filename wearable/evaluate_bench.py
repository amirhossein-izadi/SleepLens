"""Evaluate wearable-benchmark predictions against expert PSG labels.

Reads out-of-fold predictions from <data-dir>/preds/<model>_<sid>.npy (and
optional <data-dir>/yasa_pred/<sid>.npy) and reports:

  * epoch-level: accuracy, Macro-F1, Cohen's kappa, per-class F1, confusion
    matrix (5-class, 4-class W/Light/Deep/REM, and 3-class W/NREM/REM)
  * per-session and per-fold breakdowns
  * macro sleep metrics (TST, SE, SOL, WASO, REM latency) via YASA sleep
    statistics, reference vs predicted
  * majority-class baseline for comparison

Run in wearable/ (needs yasa + scikit-learn):
  python evaluate_bench.py
  python evaluate_bench.py --models rf,unet1d,watchsleepnet
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from yasa import Hypnogram

HERE = Path(__file__).resolve().parent
DEFAULT_DATA_ROOT = Path(
    os.environ.get("SLEEPLENS_DATA", Path.home() / "Projects" / "sleep-analysis" / "test" / "data")
).expanduser()
DEFAULT_CLEAN_ROOT = Path(
    os.environ.get("SLEEPLENS_CLEAN", DEFAULT_DATA_ROOT / "sleepedf_clean")
).expanduser()
DATA = HERE / "data" / "wearable"
DEFAULT_REPORTS = HERE / "reports"

STAGES5 = ["WAKE", "N1", "N2", "N3", "REM"]
STAGES4 = ["WAKE", "LIGHT", "DEEP", "REM"]
STAGES3 = ["WAKE", "NREM", "REM"]
INT_MAP5 = {0: "W", 1: "N1", 2: "N2", 3: "N3", 4: "R"}
MAP_5TO4 = np.array([0, 1, 1, 2, 3])
REF_TO_3 = np.array([0, 1, 1, 1, 2])
WSN_TO_5 = np.array([0, 2, 4], dtype=np.int64)
UNS = 255
MACRO_KEYS = {"TST": "TST", "SE": "SE", "SOL": "SOL", "WASO": "WASO", "REM_latency": "Lat_REM"}


def discover_models(pred_dir: Path, yasa_dir: Path) -> dict[str, dict[str, Path]]:
    models: dict[str, dict[str, Path]] = {}
    for p in sorted(pred_dir.glob("*_*.npy")):
        model = p.name.split("_")[0]
        sid = p.name[len(model) + 1: -4]
        models.setdefault(model, {})[sid] = p
    if yasa_dir.is_dir():
        y = {p.stem: p for p in sorted(yasa_dir.glob("*.npy"))}
        if y:
            models["yasa"] = y
    return models


def model_n_classes(model: str, preds: dict[str, Path]) -> int:
    meta = preds and next(iter(preds.values())).parent / f"{model}_meta.json"
    if meta and meta.is_file():
        name = json.loads(meta.read_text()).get("model", model)
        if name == "watchsleepnet":
            return 3
    if model == "watchsleepnet":
        return 3
    return 5


def hypno_from_ints(ints: np.ndarray) -> Hypnogram:
    v = ints.copy()
    v[v > 4] = 0  # treat unscored as Wake for macro statistics
    return Hypnogram.from_integers(v, mapping=INT_MAP5, n_stages=5, scorer="pred")


def sleep_stats(ints: np.ndarray) -> dict:
    try:
        st = hypno_from_ints(ints).sleep_statistics()
        return {k: float(st.get(src, np.nan)) for k, src in MACRO_KEYS.items()}
    except Exception:
        return {k: np.nan for k in MACRO_KEYS}


def evaluate_model(
    model: str,
    files: dict[str, Path],
    report_dir: Path,
    splits: pd.DataFrame,
    n_classes: int,
    stages_dir: Path,
) -> dict:
    fold_of = dict(zip(splits["session"].astype(str), splits["fold"].astype(int)))
    rows, macro_rows = [], []
    pooled_true, pooled_pred, pooled_fold, pooled_sid = [], [], [], []
    for sid, path in sorted(files.items()):
        stage_path = Path(stages_dir) / f"{sid}.npy"
        if not stage_path.is_file():
            print(f"  [skip] {sid}: no reference stages")
            continue
        ref = np.load(stage_path).astype(np.int64)
        pred = np.load(path).astype(np.int64)
        n = min(len(ref), len(pred))
        ref, pred = ref[:n], pred[:n]
        mask = (ref < 5) & (pred < n_classes)
        if n_classes == 3:
            yt, yp = REF_TO_3[ref[mask]], pred[mask]
        else:
            yt, yp = ref[mask], pred[mask]
        if yt.size == 0:
            continue
        pooled_true.append(yt)
        pooled_pred.append(yp)
        pooled_fold.append(np.full(yt.size, fold_of.get(sid, -1)))
        pooled_sid.append(np.full(yt.size, sid, dtype=object))
        rows.append({
            "session": sid, "fold": fold_of.get(sid, -1), "n_epochs": int(yt.size),
            "accuracy": accuracy_score(yt, yp),
            "f1_macro": f1_score(yt, yp, average="macro", labels=list(range(n_classes)), zero_division=0),
            "kappa": cohen_kappa_score(yt, yp),
        })
        rs, ps = sleep_stats(ref), sleep_stats(WSN_TO_5[pred] if n_classes == 3 else pred)
        macro_rows.append({
            "session": sid, "fold": fold_of.get(sid, -1),
            **{f"ref_{k}": v for k, v in rs.items()},
            **{f"pred_{k}": v for k, v in ps.items()},
        })

    yt = np.concatenate(pooled_true)
    yp = np.concatenate(pooled_pred)
    folds = np.concatenate(pooled_fold)
    labels = list(range(n_classes))
    prec, rec, f1, sup = precision_recall_fscore_support(yt, yp, labels=labels, zero_division=0)
    cm = confusion_matrix(yt, yp, labels=labels)
    names = STAGES3 if n_classes == 3 else STAGES5
    summary = {
        "model": model, "window": "lights_off", "n_classes": n_classes,
        "n_sessions": len(rows), "n_epochs": int(yt.size),
        "accuracy": accuracy_score(yt, yp),
        "f1_macro": f1_score(yt, yp, average="macro", labels=labels, zero_division=0),
        "kappa": cohen_kappa_score(yt, yp),
        "mean_session_f1_macro": float(np.mean([r["f1_macro"] for r in rows])) if rows else np.nan,
        "std_session_f1_macro": float(np.std([r["f1_macro"] for r in rows])) if rows else np.nan,
    }
    if n_classes == 5:
        yt4, yp4 = MAP_5TO4[yt], MAP_5TO4[yp]
        summary["f1_macro_4class"] = f1_score(yt4, yp4, average="macro", labels=list(range(4)), zero_division=0)
        summary["accuracy_4class"] = accuracy_score(yt4, yp4)
        summary["kappa_4class"] = cohen_kappa_score(yt4, yp4)
    else:
        yt5, yp5 = WSN_TO_5[yt], WSN_TO_5[yp]
        summary["f1_macro_5class_mapped"] = f1_score(yt5, yp5, average="macro", labels=list(range(5)), zero_division=0)

    per_session = pd.DataFrame(rows)
    by_stage = pd.DataFrame({"stage": names, "precision": prec, "recall": rec, "f1": f1, "support": sup})
    fold_rows = []
    for f in sorted(set(folds)):
        m = folds == f
        fold_rows.append({
            "fold": int(f), "n_epochs": int(m.sum()),
            "accuracy": accuracy_score(yt[m], yp[m]),
            "f1_macro": f1_score(yt[m], yp[m], average="macro", labels=labels, zero_division=0),
            "kappa": cohen_kappa_score(yt[m], yp[m]),
        })
    folds_df = pd.DataFrame(fold_rows)
    macro = pd.DataFrame(macro_rows)
    for k in MACRO_KEYS:
        macro[f"err_{k}"] = macro[f"pred_{k}"] - macro[f"ref_{k}"]

    report_dir.mkdir(parents=True, exist_ok=True)
    pd.Series(summary).to_csv(report_dir / f"wearable_{model}_summary.csv")
    per_session.to_csv(report_dir / f"wearable_{model}_per_session.csv", index=False)
    by_stage.to_csv(report_dir / f"wearable_{model}_by_stage.csv", index=False)
    folds_df.to_csv(report_dir / f"wearable_{model}_folds.csv", index=False)
    pd.DataFrame(cm, index=names, columns=names).to_csv(report_dir / f"wearable_{model}_confusion_matrix.csv")
    macro.to_csv(report_dir / f"wearable_{model}_macro_metrics.csv", index=False)
    return {"summary": summary, "macro": macro}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Evaluate wearable-benchmark predictions")
    ap.add_argument("--data-dir", type=Path, default=DATA)
    ap.add_argument("--pred-dir", type=Path, default=None, help="default: <data-dir>/preds")
    ap.add_argument("--clean-root", type=Path, default=DEFAULT_CLEAN_ROOT,
                    help="lights-off windows (expert stages)")
    ap.add_argument("--report-dir", type=Path, default=DEFAULT_REPORTS)
    ap.add_argument("--models", default="", help="comma list; default all discovered")
    args = ap.parse_args(argv)

    stages_dir = args.clean_root / "stages"
    splits = pd.read_csv(args.data_dir / "splits.csv")
    pred_dir = args.pred_dir or (args.data_dir / "preds")
    models = discover_models(pred_dir, args.data_dir / "yasa_pred")
    wanted = [m.strip() for m in args.models.split(",") if m.strip()]
    if wanted:
        models = {k: v for k, v in models.items() if k in wanted}
    if not models:
        print("No predictions found in", args.data_dir / "preds")
        return 1

    summaries, macros = [], []
    for model, files in models.items():
        n_classes = model_n_classes(model, files)
        print(f"=== {model} ({n_classes}-class, {len(files)} sessions) ===")
        res = evaluate_model(model, files, args.report_dir, splits, n_classes, stages_dir)
        summaries.append(res["summary"])
        res["macro"]["model"] = model
        macros.append(res["macro"])
        s = res["summary"]
        print(f"  pooled: acc={s['accuracy']:.4f} macro-F1={s['f1_macro']:.4f} kappa={s['kappa']:.4f} "
              f"(session mean {s['mean_session_f1_macro']:.4f}±{s['std_session_f1_macro']:.4f})")

    # majority-class baseline from reference labels
    refs = []
    for sid in sorted(splits["session"].astype(str)):
        p = stages_dir / f"{sid}.npy"
        if p.is_file():
            refs.append(np.load(p).astype(np.int64))
    if refs:
        yt = np.concatenate(refs)
        yt = yt[yt < 5]
        maj = np.bincount(yt, minlength=5).argmax()
        yp = np.full_like(yt, maj)
        summaries.append({
            "model": "majority", "window": "lights_off", "n_classes": 5,
            "n_sessions": len(refs), "n_epochs": int(yt.size),
            "accuracy": accuracy_score(yt, yp),
            "f1_macro": f1_score(yt, yp, average="macro", labels=list(range(5)), zero_division=0),
            "kappa": cohen_kappa_score(yt, yp), "mean_session_f1_macro": np.nan,
            "std_session_f1_macro": np.nan,
            "f1_macro_4class": f1_score(MAP_5TO4[yt], MAP_5TO4[yp], average="macro", labels=list(range(4)), zero_division=0),
            "accuracy_4class": accuracy_score(MAP_5TO4[yt], MAP_5TO4[yp]),
            "kappa_4class": cohen_kappa_score(MAP_5TO4[yt], MAP_5TO4[yp]),
        })

    comp = pd.DataFrame(summaries)
    comp.to_csv(args.report_dir / "wearable_model_comparison.csv", index=False)
    if macros:
        all_macro = pd.concat(macros, ignore_index=True)
        all_macro.to_csv(args.report_dir / "wearable_macro_metrics_all.csv", index=False)
        agg = all_macro.groupby("model").agg(
            **{f"{k}_bias": (f"err_{k}", "mean") for k in MACRO_KEYS},
            **{f"{k}_mae": (f"err_{k}", lambda s: float(np.nanmean(np.abs(s)))) for k in MACRO_KEYS},
            **{f"{k}_ref": (f"ref_{k}", "mean") for k in MACRO_KEYS},
        )
        agg.to_csv(args.report_dir / "wearable_macro_comparison.csv")
        print("\nMacro metrics (mean ref / bias / MAE):")
        for k in MACRO_KEYS:
            print(f"  {k:12s} ref={agg[f'{k}_ref'].mean():7.1f}  "
                  f"bias={agg[f'{k}_bias'].mean():+6.2f}  mae={agg[f'{k}_mae'].mean():5.2f}")

    print("\nComparison:")
    cols = ["model", "n_classes", "n_sessions", "n_epochs", "accuracy", "f1_macro", "kappa", "f1_macro_4class"]
    print(comp[[c for c in cols if c in comp.columns]].round(4).to_string(index=False))
    print(f"\nReports -> {args.report_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
