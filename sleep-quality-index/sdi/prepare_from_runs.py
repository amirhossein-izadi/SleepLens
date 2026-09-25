"""Convert canonical SDI runs to the npz format `estimate_quality.py` expects.

Our inference (`sdi/infer_canonical.py`) writes full-recording parquet files
(`runs/<stem>.parquet` with epoch_index from the recording start). Erfan's
night-composite pipeline expects per-session npz files *aligned to the
lights-off window* from `sleepedf_clean/manifest.csv`:

    <out-dir>/<sid>.npz   sdi float32 · rem uint8 · epoch_start int · n_full int
    len(sdi) == epoch_end - epoch_start   (so it matches stages/<sid>.npy)

    python prepare_from_runs.py \
        --clean-root ../features/data/sleepedf_clean \
        --runs-dir ../runs \
        --out-dir data/sdi
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

MODULE_DIR = Path(__file__).resolve().parent
DEFAULT_CLEAN = MODULE_DIR.parent / "features" / "data" / "sleepedf_clean"
DEFAULT_RUNS = MODULE_DIR.parent / "runs"
DEFAULT_OUT = MODULE_DIR / "data" / "sdi"


def convert(*, clean_root: Path, runs_dir: Path, out_dir: Path) -> tuple[int, int]:
    manifest = pd.read_csv(clean_root / "manifest.csv")
    out_dir.mkdir(parents=True, exist_ok=True)
    written = skipped = 0

    for row in manifest.itertuples():
        sid = str(row.session)
        parquet = runs_dir / f"{sid}.parquet"
        if not parquet.is_file():
            print(f"  [skip] {sid}: no prediction parquet")
            skipped += 1
            continue

        frame = pd.read_parquet(parquet).set_index("epoch_index")
        start, end = int(row.epoch_start), int(row.epoch_end)
        window = frame.reindex(range(start, end))
        if window["sdi"].isna().any() or len(window) != end - start:
            print(f"  [skip] {sid}: window {start}:{end} not fully covered by predictions")
            skipped += 1
            continue

        np.savez_compressed(
            out_dir / f"{sid}.npz",
            sdi=window["sdi"].to_numpy(dtype=np.float32),
            rem=window["rem_pred"].to_numpy(dtype=np.uint8),
            epoch_start=np.int32(start),
            n_full=np.int32(len(frame)),
        )
        written += 1

    return written, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean-root", type=Path, default=DEFAULT_CLEAN)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    written, skipped = convert(
        clean_root=args.clean_root, runs_dir=args.runs_dir, out_dir=args.out_dir
    )
    print(f"npz written: {written} | skipped: {skipped} -> {args.out_dir}")


if __name__ == "__main__":
    main()
