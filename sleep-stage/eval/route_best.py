"""E22: best domain router — SC epochs -> E19, ST epochs -> E11 (AnySleep 3ch)."""
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
TAB = EDGE.parent / "sleep-eda" / "tables"
RUNS = EDGE / "runs"
CL = ["Wake", "N1", "N2", "N3", "REM"]

ep = pd.read_parquet(TAB / "epochs_v3.parquet")
cohort = ep[["stem", "cohort"]].drop_duplicates().set_index("stem").cohort.to_dict()

def load(run):
    fs = sorted((RUNS / run).glob("*.parquet"))
    d = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    return d[["stem", "epoch_index"] + [f"p_{c}" for c in CL]]

a = load("E19"); b = load("E11")
out = []
for df, use_cohort in [(a, "SC"), (b, "ST")]:
    df = df.copy()
    df["cohort"] = df.stem.map(cohort)
    out.append(df[df.cohort == use_cohort].drop(columns=["cohort"]))
r = pd.concat(out, ignore_index=True)
d = RUNS / "E22"
d.mkdir(exist_ok=True)
for stem, sub in r.groupby("stem", sort=True):
    sub.to_parquet(d / f"{stem}.parquet", index=False)
print(f"E22: saved {r.stem.nunique()} recordings, {len(r)} epochs")
