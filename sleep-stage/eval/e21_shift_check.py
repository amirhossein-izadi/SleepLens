"""Shift-sweep alignment check for E21 (and reference E11d) on the pilot recordings."""
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

for run in ["E21", "E11d"]:
    d = pd.concat([pd.read_parquet(f) for f in sorted(Path(f"sleep-stage/runs/{run}").glob("*.parquet"))],
                  ignore_index=True)
    print(f"\n=== {run} shift sweep (pixel peak at 0 = aligned) ===")
    for stem in ["SC4001", "SC4041", "ST7011"]:
        s = d[d.stem == stem].copy()
        gt = g[g.stem == stem].set_index("epoch_index").label
        out = []
        for shift in [-3, -2, -1, 0, 1, 2, 3]:
            si = s.epoch_index.values + shift
            yy = gt.reindex(si).values
            msk = ~pd.isna(yy)
            if msk.sum() == 0:
                out.append(f"{shift:+d}: n/a")
                continue
            yp = s[[f"p_{c}" for c in CL]].values[msk].argmax(1)
            out.append(f"{shift:+d}: {macro(yy[msk], yp):.3f}")
        print(f"{stem}: " + "  ".join(out))
