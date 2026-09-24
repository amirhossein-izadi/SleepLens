"""Universal evaluator: macro/micro + per-class + SC/ST + confusion + kappa + ECE.
Usage: run_eval.py <probs_parquet_or_runs_dir>  (probs have epoch_index + p_* columns)
Ground truth: sleep-eda/tables/epochs_v3.parquet (valid_stage only)."""
import numpy as np
import pandas as pd
import sys
from pathlib import Path

CLASSES = ["Wake", "N1", "N2", "N3", "REM"]
EDGE = Path(__file__).resolve().parents[1]

def f1_per_class(y_true, y_pred):
    out = {}
    for i, c in enumerate(CLASSES):
        tp = int(((y_pred == i) & (y_true == i)).sum())
        fp = int(((y_pred == i) & (y_true != i)).sum())
        fn = int(((y_pred != i) & (y_true == i)).sum())
        out[c] = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    return out

def cohen_kappa(y_true, y_pred, k=5):
    n = len(y_true)
    po = (y_true == y_pred).mean()
    pe = sum([(y_true == i).mean() * (y_pred == i).mean() for i in range(k)])
    return (po - pe) / (1 - pe) if pe < 1 else 0.0

def ece(conf, correct, bins=10):
    e = 0.0
    for b in range(bins):
        m = (conf > b / bins) & (conf <= (b + 1) / bins)
        if m.sum():
            e += m.mean() * abs(conf[m].mean() - correct[m].mean())
    return float(e)

def evaluate(df, cohort=None):
    y_true = df["label"].values
    P = df[[f"p_{c}" for c in CLASSES]].values
    y_pred = P.argmax(1)
    conf = P.max(1)
    f1 = f1_per_class(y_true, y_pred)
    return {
        "n": len(df),
        "macro_f1": float(np.mean(list(f1.values()))),
        "micro_f1": float((y_true == y_pred).mean()),
        **{f"f1_{c}": v for c, v in f1.items()},
        "kappa": float(cohen_kappa(y_true, y_pred)),
        "ece": float(ece(conf, (y_true == y_pred).astype(float))),
        "mean_conf": float(conf.mean()),
    }

def load_probs(path):
    path = Path(path)
    files = sorted(path.glob("*.parquet")) if path.is_dir() else [path]
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("probs")
    ap.add_argument("--window", default="valid", choices=["valid", "in_bench", "in_main_window"])
    a = ap.parse_args()
    probs = load_probs(a.probs)
    ep = pd.read_parquet(Path(EDGE, "..", "sleep-eda", "tables", "epochs_v3.parquet"))
    labmap = {c: i for i, c in enumerate(CLASSES)}
    g = ep[ep.valid & ep.label5.isin(CLASSES)].copy()
    if a.window != "valid":
        g = g[g[a.window]]
    g["label"] = g.label5.map(labmap)
    m = probs.merge(g[["stem", "cohort", "epoch", "label"]].rename(columns={"epoch": "epoch_index"}),
                    on=["stem", "epoch_index"], how="inner")
    print(f"window={a.window} matched {len(m)}/{len(probs)} prob epochs to ground truth")
    for name, sub in [("ALL", m), ("SC", m[m.cohort == "SC"]), ("ST", m[m.cohort == "ST"])]:
        if len(sub) == 0:
            continue
        r = evaluate(sub)
        print(f"{name}: n={r['n']} macro={r['macro_f1']:.4f} micro={r['micro_f1']:.4f} " +
              " ".join(f"{c}={r[f'f1_{c}']:.3f}" for c in CLASSES) +
              f" kappa={r['kappa']:.3f} ece={r['ece']:.3f}")
    inv = dict(enumerate(CLASSES))
    cm = pd.crosstab(m["label"].map(inv),
                     pd.Series(m[[f"p_{c}" for c in CLASSES]].values.argmax(1)).map(inv),
                     rownames=["true"], colnames=["pred"])
    print(cm.to_string())
    out = Path(a.probs) if Path(a.probs).is_dir() else Path(a.probs).parent
    slices = [("ALL", m)]
    if len(m[m.cohort == "SC"]):
        slices.append(("SC", m[m.cohort == "SC"]))
    if len(m[m.cohort == "ST"]):
        slices.append(("ST", m[m.cohort == "ST"]))
    sc = slices[1][1] if len(slices) > 1 else m
    st = slices[2][1] if len(slices) > 2 else m
    pd.DataFrame([{"slice": k, **evaluate(v)} for k, v in slices]).to_csv(out / f"metrics_{a.window}.csv", index=False)
    if len(slices) == 3:
        rsc, rst = evaluate(sc), evaluate(st)
        print(f"WorstDomain={min(rsc['macro_f1'], rst['macro_f1']):.4f} "
              f"DomainGap={abs(rsc['macro_f1'] - rst['macro_f1']):.4f}")
    print("wrote metrics.csv")

if __name__ == "__main__":
    main()
