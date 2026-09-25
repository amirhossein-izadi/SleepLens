"""Pilot like-for-like: macro per stem for E21 vs E11d/E11/E20."""
import numpy as np
import pandas as pd
from pathlib import Path

CL = ["Wake", "N1", "N2", "N3", "REM"]
lab = {c: i for i, c in enumerate(CL)}
TAB = Path("sleep-eda/tables")
ep = pd.read_parquet(TAB / "epochs_v3.parquet")
g = ep[ep.valid & ep.label5.isin(CL) & ep.in_bench][["stem", "epoch", "label5"]].rename(
    columns={"epoch": "epoch_index"})
g["label"] = g.label5.map(lab)

def macro(y, yp):
    f = []
    for i in range(5):
        tp = ((yp == i) & (y == i)).sum(); fp = ((yp == i) & (y != i)).sum(); fn = ((yp != i) & (y == i)).sum()
        f.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    return float(np.mean(f))

stems = ["SC4001", "SC4041", "ST7011"]
print(f"{'run':5s} " + " ".join(f"{s:>9s}" for s in stems) + "   3-rec")
for run in ["E21", "E11d", "E11", "E20"]:
    d = pd.concat([pd.read_parquet(f) for f in sorted(Path(f"sleep-stage/runs/{run}").glob("*.parquet"))],
                  ignore_index=True)
    m = d.merge(g, on=["stem", "epoch_index"], how="inner")
    P = m[[f"p_{c}" for c in CL]].values
    yp = P.argmax(1)
    row = []
    for s in stems:
        msk = (m.stem == s).values
        row.append(f"{macro(m.label.values[msk], yp[msk]):9.4f}" if msk.sum() else "     n/a")
    print(f"{run:5s} " + " ".join(row) + f"   {macro(m.label.values, yp):.4f}")
