"""Convert our staging runs (sleep-stage/runs/<run>/<stem>.parquet) into the SQI-side
preds layout expected by features/extract_features.py:

    <preds-root>/<model>/<sid>.npy   int16, window-aligned, 0=W..4=REM, -1 = unscored

Window comes from <clean-root>/manifest.csv (prepare_windows.py output).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CL = ["Wake", "N1", "N2", "N3", "REM"]
lab = {c: i for i, c in enumerate(CL)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, help="e.g. sleep-stage/runs/E22")
    ap.add_argument("--model-name", required=True, help="folder name under preds-root")
    ap.add_argument("--clean-root", required=True)
    ap.add_argument("--preds-root", required=True)
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = (ROOT.parent / run_dir).resolve()
    clean_root = Path(args.clean_root)
    man = pd.read_csv(clean_root / "manifest.csv")
    out_dir = Path(args.preds_root) / args.model_name
    out_dir.mkdir(parents=True, exist_ok=True)

    n_ok = 0
    for r in man.itertuples():
        sid = str(r.session)
        pf = run_dir / f"{sid}.parquet"
        if not pf.is_file():
            print(f"  [missing preds] {sid}")
            continue
        d = pd.read_parquet(pf).set_index("epoch_index")
        e0, e1 = int(r.epoch_start), int(r.epoch_end)
        out = np.full(e1 - e0, -1, dtype=np.int16)
        idx = d.index.intersection(np.arange(e0, e1))
        if len(idx):
            pos = idx.values - e0
            out[pos] = d.loc[idx, [f"p_{c}" for c in CL]].to_numpy().argmax(1).astype(np.int16)
        np.save(out_dir / f"{sid}.npy", out)
        n_ok += 1
        cov = float((out >= 0).mean())
        print(f"  {sid}: window {e0}:{e1} n={len(out)} covered={cov:.2%}")
    print(f"{args.model_name}: wrote {n_ok}/{len(man)} sessions -> {out_dir}")


if __name__ == "__main__":
    main()
