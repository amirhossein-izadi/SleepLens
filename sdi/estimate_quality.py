"""Night-level SDI sleep-quality estimate (research composite, NOT a clinical scale).

Builds on run_sdi.py outputs (data/sdi/<sid>.npz) following the deployment guide
for Zhou et al. npj Digital Medicine 8:203 (2025). The paper defines epoch-level
SDI + REM prediction; the composite below is our implementation recommendation,
not a score defined or validated by the paper.

Per night, over sleep epochs only (expert stages 1-4 by default; --stage-source
switches to a staged model dir):
  RB  = fraction of sleep epochs with SDI < --rb-threshold (default 0.2)
  AP  = mean SDI over sleep epochs
  CV  = SD(sleep SDI) / mean(sleep SDI)
  MDR = mean SDI over SDI-model-predicted REM epochs
  PR  = predicted REM epochs / sleep epochs
Standardize each feature against a reference population (default: all nights in
the feature table; --reference-csv for an external one), orient so higher is
better: -z(RB), z(AP), -z(CV), z(MDR), z(PR). Composite = equal-weight mean,
converted to an empirical 0-100 percentile within the reference.

Skewness, approximate entropy and DFA(1) are reported alongside, NOT scored
(relation to quality is less consistent in the paper). Apnea index is joined
from --sqi-features for display only and never folded into the score.

Missing-data rule: eligible nights need >= --min-sleep sleep epochs and >= 1
predicted REM epoch; otherwise composite/percentile are NaN with a reason.

Results are reported per subset/input condition (cassette EMG is a 1-Hz envelope
vs telemetry 100 Hz; both substitute Fpz-Cz and zero-fill ECG), and night-to-night
consistency is reported for subjects with two eligible nights (subject_key =
subset:subject, because Sleep-EDF reuses subject numbers across cohorts).

Sleep-EDF inference is zero-shot with substitutions - see infer_sdi.py. The
composite weights are ours; the paper's health-outcome links do not transfer to
this estimate. Validate against a stated target (e.g. PROMIS/Pittsburgh) before
treating the number as meaningful.

  python estimate_quality.py
  python estimate_quality.py --stage-source usleep
  python estimate_quality.py --sqi-features ../features/reports/sqi_features_expert_lights_off.csv

Outputs (tag = stage source): reports/sdi_night_features_<tag>_lights_off.csv
(raw features + QC), reports/sdi_composite_<tag>_lights_off.csv (components,
z-scores, composite, percentile), reports/sdi_composite_<tag>_sqi_correlations.csv
(descriptive sanity check, with --sqi-features), reports/sdi_repeatability_<tag>.csv
+ _summary (subjects with two eligible nights, when >= --min-repeat-pairs).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr

from common import (
    CLEAN_ROOT,
    INPUT_CONDITION,
    PREDS_ROOT,
    REPORT_DIR,
    SDI_OUT_ROOT,
    load_manifest,
    load_stages_int16,
)

COMPONENTS = [("rb", -1), ("ap", 1), ("cv", -1), ("mdr", 1), ("pr", 1)]
SQI_COLS = [
    "tst_min",
    "se_pct",
    "sol_min",
    "waso_min",
    "rem_lat_min",
    "sfi",
    "arousal_index",
    "apnea_index",
    "n3_pct_tst",
    "rem_pct_tst",
]


def approx_entropy(x: np.ndarray, m: int = 2, r: float | None = None) -> float:
    """Pincus approximate entropy (Chebyshev distance, matches within r)."""
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    if n <= m + 1:
        return float("nan")
    if r is None:
        r = 0.2 * x.std()
    if r <= 0:
        r = 1e-6

    def phi(mm: int) -> float:
        windows = np.lib.stride_tricks.sliding_window_view(x, mm)
        dist = np.abs(windows[:, None, :] - windows[None, :, :]).max(axis=-1)
        counts = (dist <= r).sum(axis=1) / len(windows)
        return float(np.log(np.maximum(counts, 1e-12)).mean())

    return phi(m) - phi(m + 1)


def dfa_alpha(x: np.ndarray, order: int = 1, n_scales: int = 16) -> float:
    """Detrended fluctuation analysis exponent (order 1 = standard DFA)."""
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    if n < 4 * (order + 2):
        return float("nan")
    y = np.cumsum(x - x.mean())
    scales = np.unique(
        np.logspace(np.log10(4), np.log10(max(4, n // 4)), n_scales).astype(int)
    )
    flux = []
    for s in scales:
        n_seg = n // s
        if n_seg < 1:
            continue
        t = np.arange(s)
        rms = []
        for i in range(n_seg):
            seg = y[i * s : (i + 1) * s]
            coef = np.polyfit(t, seg, order)
            rms.append(np.mean((seg - np.polyval(coef, t)) ** 2))
        flux.append(np.sqrt(np.mean(rms)))
    flux = np.asarray(flux)
    ok = flux > 0
    if ok.sum() < 2:
        return float("nan")
    return float(np.polyfit(np.log(scales[ok]), np.log(flux[ok]), 1)[0])


def night_features(sid: str, sdi: np.ndarray, rem: np.ndarray, st: np.ndarray, rb_thr: float) -> dict:
    scored = (st >= 0) & (st < 5)
    sleep = np.isin(st, [1, 2, 3, 4])
    vals = sdi[sleep].astype(np.float64)
    rem_sleep = (rem[sleep] == 1) if sleep.sum() else np.zeros(0, dtype=bool)
    n_sleep = int(sleep.sum())
    n_pred_rem = int(rem_sleep.sum())

    out = {
        "session": sid,
        "n_epochs_window": int(len(sdi)),
        "n_epochs_scored": int(scored.sum()),
        "n_sleep": n_sleep,
        "n_pred_rem": n_pred_rem,
        "sdi_mean_sleep": float(vals.mean()) if n_sleep else float("nan"),
        "rb": float((vals < rb_thr).mean()) if n_sleep else float("nan"),
        "ap": float(vals.mean()) if n_sleep else float("nan"),
        "cv": float(vals.std(ddof=1) / vals.mean()) if n_sleep > 1 and abs(vals.mean()) > 1e-8 else float("nan"),
        "skew": float(pd.Series(vals).skew()) if n_sleep > 2 else float("nan"),
        "mdr": float(sdi[sleep][rem_sleep].mean()) if n_pred_rem else float("nan"),
        "pr": float(n_pred_rem / n_sleep) if n_sleep else float("nan"),
        "apen": approx_entropy(vals) if n_sleep >= 50 else float("nan"),
        "dfa": dfa_alpha(vals) if n_sleep >= 50 else float("nan"),
    }
    if n_sleep and (st[sleep] == 4).sum():
        exp_rem = st[sleep] == 4
        out["mdr_expert"] = float(sdi[sleep][exp_rem].mean())
        out["pr_expert"] = float(exp_rem.mean())
        pred_bin = rem_sleep.astype(int)
        exp_bin = exp_rem.astype(int)
        tp = int(((pred_bin == 1) & (exp_bin == 1)).sum())
        fp = int(((pred_bin == 1) & (exp_bin == 0)).sum())
        fn = int(((pred_bin == 0) & (exp_bin == 1)).sum())
        out["rem_f1_window"] = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else float("nan")
    return out


def zscore(x: pd.Series, ref: pd.Series) -> pd.Series:
    mu, sd = ref.mean(), ref.std(ddof=0)
    return (x - mu) / sd if sd and np.isfinite(sd) and sd > 0 else x * np.nan


def repeatability_report(
    df: pd.DataFrame, tag: str, report_dir: Path, min_pairs: int = 5
) -> dict | None:
    """Night-to-night consistency for subjects with two eligible nights.

    Sleep-EDF reuses subject numbers across cohorts, so pair on subject_key.
    Reports Pearson r between the two nights and ICC(2,1); needs enough pairs
    to mean anything (--min-repeat-pairs).
    """
    el = df[df["eligible"] & df["sdi_composite"].notna()].sort_values(["subject_key", "night"])
    pairs = el.groupby("subject_key")["sdi_composite"].apply(list)
    pairs = pairs[pairs.apply(len) == 2]
    if len(pairs) < min_pairs:
        print(f"repeat-night consistency: only {len(pairs)} complete pairs (need >= {min_pairs}); skipped")
        return None

    a = np.array([p[0] for p in pairs], dtype=float)
    b = np.array([p[1] for p in pairs], dtype=float)
    x = np.column_stack([a, b])
    n, k = x.shape
    grand = x.mean()
    msr = k * ((x.mean(axis=1) - grand) ** 2).sum() / (n - 1)
    msc = n * ((x.mean(axis=0) - grand) ** 2).sum() / (k - 1)
    mse = ((x - x.mean(axis=1, keepdims=True) - x.mean(axis=0, keepdims=True) + grand) ** 2).sum() / ((n - 1) * (k - 1))
    denom = msr + (k - 1) * mse + k * (msc - mse) / n
    icc = (msr - mse) / denom if denom > 0 else float("nan")
    r = float(np.corrcoef(a, b)[0, 1]) if n > 1 else float("nan")

    pd.DataFrame(
        {
            "subject_key": list(pairs.index),
            "composite_night1": a,
            "composite_night2": b,
            "abs_diff": np.abs(a - b),
        }
    ).to_csv(report_dir / f"sdi_repeatability_{tag}.csv", index=False)
    summary = {
        "n_pairs": n,
        "pearson_r_night1_night2": r,
        "icc_2_1": icc,
        "mean_abs_diff": float(np.abs(a - b).mean()),
    }
    pd.Series(summary).to_csv(report_dir / f"sdi_repeatability_summary_{tag}.csv")
    return summary


def midrank_percentile(x: pd.Series, ref: pd.Series) -> pd.Series:
    r = np.sort(ref.dropna().to_numpy())
    if len(r) == 0:
        return x * np.nan
    pct = 100.0 * (np.searchsorted(r, x.to_numpy(), side="right") - 0.5) / len(r)
    return pd.Series(np.clip(pct, 0.0, 100.0), index=x.index)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Night-level SDI composite (research estimate)")
    ap.add_argument("--sdi-dir", type=Path, default=SDI_OUT_ROOT)
    ap.add_argument("--stage-source", default="expert", help="expert or a model name under --preds-root")
    ap.add_argument("--clean-root", type=Path, default=CLEAN_ROOT, help="expert stages/manifest")
    ap.add_argument("--preds-root", type=Path, default=PREDS_ROOT, help="model prediction folders")
    ap.add_argument("--rb-threshold", type=float, default=0.2)
    ap.add_argument("--min-sleep", type=int, default=30, help="min sleep epochs for eligibility")
    ap.add_argument("--reference-csv", type=Path, default=None, help="external reference feature table")
    ap.add_argument("--sqi-features", type=Path, default=None, help="join apnea_index + corr check")
    ap.add_argument("--min-repeat-pairs", type=int, default=5, help="min 2-night pairs for repeatability")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    args = ap.parse_args(argv)

    if not args.sdi_dir.is_dir():
        print(f"No SDI outputs in {args.sdi_dir}; run infer_sdi.py first.", file=sys.stderr)
        return 1

    man = load_manifest(args.clean_root).set_index("session")
    files = sorted(args.sdi_dir.glob("*.npz"))
    if args.limit and args.limit > 0:
        files = files[: args.limit]

    rows = []
    for f in files:
        sid = f.stem
        try:
            npz = np.load(f)
            st = load_stages_int16(sid, args.stage_source, args.clean_root, args.preds_root)
        except FileNotFoundError as e:
            print(f"  [skip] {sid}: {e}", file=sys.stderr)
            continue
        if len(st) != len(npz["sdi"]):
            print(f"  [skip] {sid}: stage length {len(st)} != sdi {len(npz['sdi'])}", file=sys.stderr)
            continue
        r = night_features(sid, npz["sdi"], npz["rem"], st, args.rb_threshold)
        r["stage_source"] = args.stage_source
        if sid in man.index:
            row = man.loc[sid]
            r.update(subset=row.subset, subject=int(row.subject), night=int(row.night))
            r["subject_key"] = f"{row.subset}:{int(row.subject)}"
            r["input_condition"] = INPUT_CONDITION.get(row.subset, "unknown")
        rows.append(r)

    if not rows:
        print("No nights scored.", file=sys.stderr)
        return 1

    df = pd.DataFrame(rows)
    comp_cols = [c for c, _ in COMPONENTS]
    ref = df
    ref_label = "self"
    if args.reference_csv is not None:
        ref = pd.read_csv(args.reference_csv)
        missing = [c for c in comp_cols if c not in ref.columns]
        if missing:
            print(f"Reference CSV lacks columns: {missing}", file=sys.stderr)
            return 1
        ref_label = str(args.reference_csv)

    z_name = lambda col, sign: f"z_{col}" + ("_neg" if sign < 0 else "")  # noqa: E731
    for col, sign in COMPONENTS:
        df[z_name(col, sign)] = sign * zscore(df[col], ref[col])
    z_cols = [z_name(c, s) for c, s in COMPONENTS]
    df["sdi_composite"] = df[z_cols].mean(axis=1, skipna=False)
    ref_z = pd.concat(
        [(sign * zscore(ref[c], ref[c])).rename(z_name(c, sign)) for c, sign in COMPONENTS], axis=1
    )
    ref_composite = ref_z[z_cols].mean(axis=1, skipna=False)
    df["sdi_percentile"] = midrank_percentile(df["sdi_composite"], ref_composite)

    reasons = []
    for r in df.itertuples():
        if r.n_sleep < args.min_sleep:
            reasons.append("too_few_sleep_epochs")
        elif r.n_pred_rem < 1:
            reasons.append("no_pred_rem")
        elif not np.isfinite(r.sdi_composite):
            reasons.append("nan_component")
        else:
            reasons.append("ok")
    df["eligible_reason"] = reasons
    df["eligible"] = df["eligible_reason"] == "ok"
    df.loc[~df["eligible"], ["sdi_composite", "sdi_percentile"]] = np.nan

    if args.sqi_features is not None and Path(args.sqi_features).is_file():
        sqi = pd.read_csv(args.sqi_features)
        keep = ["session"] + [c for c in SQI_COLS if c in sqi.columns]
        df = df.merge(sqi[keep], on="session", how="left")

    base_cols = [
        "session", "subset", "subject", "night", "subject_key", "input_condition", "stage_source",
        "n_epochs_window", "n_epochs_scored", "n_sleep", "n_pred_rem",
        "rb", "ap", "cv", "mdr", "pr", "mdr_expert", "pr_expert", "rem_f1_window",
        "skew", "apen", "dfa",
    ]
    feat_cols = [c for c in base_cols if c in df.columns]
    args.report_dir.mkdir(parents=True, exist_ok=True)
    tag = f"{args.stage_source}_lights_off"
    df[feat_cols].to_csv(args.report_dir / f"sdi_night_features_{tag}.csv", index=False)

    out_cols = feat_cols[:10] + z_cols + ["sdi_composite", "sdi_percentile", "eligible", "eligible_reason"]
    out_cols += [c for c in ("apnea_index", "has_flow") if c in df.columns]
    df[out_cols].to_csv(args.report_dir / f"sdi_composite_{tag}.csv", index=False)

    print(f"=== SDI night composite ({args.stage_source} stages, ref={ref_label}) ===")
    print(f"nights={len(df)} eligible={int(df['eligible'].sum())}")
    for subset, g in df.groupby("subset", sort=True):
        print(
            f"  {subset:15s} n={len(g):3d} eligible={int(g['eligible'].sum()):3d} "
            f"composite={g['sdi_composite'].mean():+.3f} "
            f"[{g['input_condition'].iloc[0] if 'input_condition' in g else 'unknown'}]"
        )
    print(f"components: RB={df['rb'].mean():.3f} AP={df['ap'].mean():.3f} CV={df['cv'].mean():.3f} "
          f"MDR={df['mdr'].mean():.3f} PR={df['pr'].mean():.3f}")
    print(f"composite: mean={df['sdi_composite'].mean():.3f} sd={df['sdi_composite'].std(ddof=0):.3f} "
          f"percentile {df['sdi_percentile'].min():.0f}-{df['sdi_percentile'].max():.0f}")
    if "apnea_index" in df.columns:
        print(f"apnea_index (separate, not scored): mean={df['apnea_index'].mean():.2f}")
    rep = repeatability_report(df, tag, args.report_dir, args.min_repeat_pairs)
    if rep:
        print(
            f"repeat-night: pairs={rep['n_pairs']} r={rep['pearson_r_night1_night2']:.2f} "
            f"ICC(2,1)={rep['icc_2_1']:.2f} mean|diff|={rep['mean_abs_diff']:.3f}"
        )
    print("NOTE: research estimate - weights not validated by the paper; zero-shot Sleep-EDF inference")
    print("      with deliberate input mismatches (Fpz-Cz, zero ECG; cassette EMG 1 Hz).")

    if args.sqi_features is not None and "sdi_composite" in df.columns:
        corr_rows = []
        for col in SQI_COLS:
            if col not in df.columns:
                continue
            sub = df[["sdi_composite", col]].dropna()
            if len(sub) < 5:
                continue
            rho, p = spearmanr(sub["sdi_composite"], sub[col])
            corr_rows.append({"sqi_feature": col, "spearman_rho": rho, "p_value": p, "n": len(sub)})
        if corr_rows:
            pd.DataFrame(corr_rows).to_csv(
                args.report_dir / f"sdi_composite_{tag}_sqi_correlations.csv", index=False
            )
    print(f"Reports -> {args.report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
