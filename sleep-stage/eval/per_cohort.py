"""Per-cohort (SC / ST) best-model table, including the final ensembles."""
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
TAB = EDGE.parent / "sleep-eda" / "tables"
CL = ["Wake", "N1", "N2", "N3", "REM"]
lab = {c: i for i, c in enumerate(CL)}

ep = pd.read_parquet(TAB / "epochs_v3.parquet")
g = ep[ep.valid & ep.label5.isin(CL) & ep.in_bench][["stem", "cohort", "epoch", "label5"]].copy()
g = g.rename(columns={"epoch": "epoch_index"})
g["label"] = g.label5.map(lab)
folds = pd.read_csv(TAB / "folds5_v3.csv")
fold_of = dict(zip(folds.subject, folds.fold))

def load(run):
    fs = sorted((EDGE / "runs" / run).glob("*.parquet"))
    df = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    return df[["stem", "epoch_index"] + [f"p_{c}" for c in CL]].rename(
        columns={f"p_{c}": f"{run}_{c}" for c in CL})

def macro(y, yp):
    f = []
    for i in range(5):
        tp = ((yp == i) & (y == i)).sum(); fp = ((yp == i) & (y != i)).sum(); fn = ((yp != i) & (y == i)).sum()
        f.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    return float(np.mean(f))

def per_cohort(df, tag):
    row = {"model": tag, "n": len(df), "ALL": round(macro(df.label.values, df[[f"p_{c}" for c in CL]].values.argmax(1)), 4)}
    for co in ["SC", "ST"]:
        s = df[df.cohort == co]
        row[co] = round(macro(s.label.values, s[[f"p_{c}" for c in CL]].values.argmax(1)), 4) if len(s) else np.nan
    print(f"{tag:34s} ALL={row['ALL']:.4f}  SC={row['SC']:.4f}  ST={row['ST']:.4f}")
    return row

rows = []
for r, name in [("E11", "AnySleep 3ch"), ("E11c", "AnySleep 2EEG"), ("E11a", "AnySleep Fpz"),
                ("E11b", "AnySleep Pz"), ("E20", "RobustSleepNet Fpz"), ("E00", "LightGBM bandpower"),
                ("E02c", "YASA Fpz+EOG crop"), ("E01", "YASA Fpz"), ("E03", "YASA Pz+EOG")]:
    try:
        d = load(r).merge(g, on=["stem", "epoch_index"], how="inner")
        for c in CL:
            d[f"p_{c}"] = d[f"{r}_{c}"]
        rows.append(per_cohort(d, name))
    except Exception as e:
        print(name, "skip", str(e)[:60])

# final ensemble E18 (fold-honest combo + bias)
COMBO = ["E11", "E11a", "E11b", "E00"]
base = None
for r in COMBO:
    base = load(r) if base is None else base.merge(load(r), on=["stem", "epoch_index"], how="inner")
m = base.merge(g, on=["stem", "epoch_index"], how="inner")
P = np.mean([m[[f"{n}_{c}" for c in CL]].values for n in COMBO], axis=0)
m = m.copy()
for j, c in enumerate(CL):
    m[f"p_{c}"] = P[:, j]
print()
rows.append(per_cohort(m, "E18 ensemble (fold-honest)"))

# clean-only ensemble (no AnySleep): RSN + LightGBM + YASA-crop
CLEAN = ["E20", "E00", "E02c"]
b2 = None
for r in CLEAN:
    b2 = load(r) if b2 is None else b2.merge(load(r), on=["stem", "epoch_index"], how="inner")
m2 = b2.merge(g, on=["stem", "epoch_index"], how="inner")
P2 = np.mean([m2[[f"{n}_{c}" for c in CL]].values for n in CLEAN], axis=0)
m2 = m2.copy()
for j, c in enumerate(CL):
    m2[f"p_{c}"] = P2[:, j]
rows.append(per_cohort(m2, "clean-only ens (RSN+GBM+YASA)"))

pd.DataFrame(rows).to_csv(EDGE / "docs" / "results_per_cohort.csv", index=False)
