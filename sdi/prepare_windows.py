"""Trim Sleep-EDF nights to the lights-off sleep window and save clean labels.

Why: cassette PSG files span ~20-24 h with hours of pre/post-sleep Wake.
Lights-off (SC/ST subject sheets in the dataset root) marks the clinical
time-in-bed start.

Window (default --mode sleep_period):
  [lights_off, last sleep epoch after lights_off + --wake-pad-min]
  fallback: [lights_off, lights_off + --max-hours] if no sleep found.

Modes:
  sleep_period  lights_off -> last N1/N2/N3/REM (+ optional trailing wake pad)
  lights_off    lights_off -> min(lights_off + --max-hours, end of file)

Writes (into --out-dir, default <data-root>/sleepedf_clean):
  manifest.csv
  stages/<session>.npy   int8, 0-4 stages, 255 = UNS, aligned to window
  epochs.csv.gz          session, epoch_local, epoch_full, stage, stage_str
  optional --write-edf: cropped PSG EDFs under <out-dir>/edf/

Incremental: an existing manifest/epochs table is kept and only the sessions
processed in this run are replaced, so `--limit` smoke runs and per-subset runs
never clobber a full build. Stage files are written per session.

  python prepare_windows.py                          # all 197 nights
  python prepare_windows.py --subset cassette --limit 5
  python prepare_windows.py --edf-root /data/sleep-edf --out-dir /data/clean
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import warnings
from datetime import datetime, time
from pathlib import Path

import mne
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

DEFAULT_DATA_ROOT = Path(
    os.environ.get("SLEEPLENS_DATA", Path.home() / "Projects" / "sleep-analysis" / "test" / "data")
).expanduser()
DEFAULT_EDF_ROOT = Path(
    os.environ.get("SLEEPLENS_EDF", DEFAULT_DATA_ROOT / "sleep-edf-database-expanded-1.0.0")
).expanduser()
DEFAULT_CLEAN_ROOT = Path(
    os.environ.get("SLEEPLENS_CLEAN", DEFAULT_DATA_ROOT / "sleepedf_clean")
).expanduser()
EPOCH_S = 30.0

STAGES5 = ["WAKE", "N1", "N2", "N3", "REM"]
INT_FROM_STAGE = {s: i for i, s in enumerate(STAGES5)}
STAGE_STR = {i: s for i, s in enumerate(STAGES5)}
UNS = 255

ANN_TO_STAGE = {
    "Sleep stage W": "WAKE",
    "Sleep stage 1": "N1",
    "Sleep stage 2": "N2",
    "Sleep stage 3": "N3",
    "Sleep stage 4": "N3",
    "Sleep stage R": "REM",
    "Sleep stage ?": "UNS",
}

_SUBSET_FOLDER = {"cassette": "sleep-cassette", "telemetry": "sleep-telemetry"}
_SC_RE = re.compile(r"^SC4(\d{2})(\d)")
_ST_RE = re.compile(r"^ST7(\d{2})(\d)")


def _sid(path: Path) -> str:
    return path.name[:6]


def _to_seconds(t) -> float:
    if isinstance(t, datetime):
        t = t.time()
    if isinstance(t, time):
        return t.hour * 3600 + t.minute * 60 + t.second
    if isinstance(t, (int, float, np.integer, np.floating)):
        return float(t)
    if isinstance(t, str):
        parts = [int(x) for x in t.strip().split(":")]
        while len(parts) < 3:
            parts.append(0)
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise TypeError(f"Cannot convert {t!r} to seconds")


def load_lights_off_cassette(xls: Path) -> dict[tuple[int, int], float]:
    df = pd.read_excel(xls, sheet_name="Blad1")
    out = {}
    for _, row in df.iterrows():
        out[(int(row["subject"]), int(row["night"]))] = _to_seconds(row["LightsOff"])
    return out


def load_lights_off_telemetry(xls: Path) -> dict[tuple[int, int], float]:
    """ST sheet: placebo / temazepam columns each have night nr + lights off."""
    df = pd.read_excel(xls, sheet_name="Blad1", header=None)
    out = {}
    # row 0 = titles, row 1 = Nr/Age/.../night nr/lights off/...
    for _, row in df.iloc[2:].iterrows():
        try:
            subj = int(row.iloc[0])
        except (TypeError, ValueError):
            continue
        # placebo: cols 3,4  | temazepam: cols 5,6
        for night_col, off_col in ((3, 4), (5, 6)):
            try:
                night = int(row.iloc[night_col])
                off = _to_seconds(row.iloc[off_col])
            except (TypeError, ValueError):
                continue
            out[(subj, night)] = off
    return out


def pair_sessions(edf_root: Path, subset: str) -> list[tuple[Path, Path]]:
    folder = _SUBSET_FOLDER.get(subset)
    roots = (
        [edf_root / folder]
        if folder
        else [edf_root / "sleep-cassette", edf_root / "sleep-telemetry"]
    )
    pairs = []
    for root in roots:
        psg_map = {_sid(p): p for p in sorted(root.glob("*-PSG.edf"))}
        for hyp in sorted(root.glob("*-Hypnogram.edf")):
            sid = _sid(hyp)
            if sid in psg_map:
                pairs.append((psg_map[sid], hyp))
    return pairs


def parse_subject_night(sid: str) -> tuple[int, int] | None:
    m = _SC_RE.match(sid) or _ST_RE.match(sid)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def full_stage_labels(hyp_path: Path, n_epochs: int) -> np.ndarray:
    """int8 labels for the full recording: 0-4 or UNS."""
    ann = mne.read_annotations(str(hyp_path))
    labels = np.full(n_epochs, UNS, dtype=np.uint8)
    for onset, dur, desc in zip(ann.onset, ann.duration, ann.description):
        stage = ANN_TO_STAGE.get(desc)
        if stage is None:
            continue
        start = int(round(onset / EPOCH_S))
        length = max(int(round(dur / EPOCH_S)), 1)
        for i in range(start, min(start + length, n_epochs)):
            labels[i] = INT_FROM_STAGE[stage] if stage in INT_FROM_STAGE else UNS
    return labels


def lights_off_offset_s(
    psg_start: datetime | None,
    lights_off_sof: float,
    duration_s: float,
) -> float:
    """Seconds from recording start to lights-off (same calendar day, mod 24h).

    If the wrapped offset lands outside the recording (lights-off just before
    start, or a sheet/night mismatch), fall back to the start of the file.
    """
    if psg_start is None:
        raise ValueError("PSG has no meas_date; cannot align lights-off")
    start_sof = psg_start.hour * 3600 + psg_start.minute * 60 + psg_start.second
    delta = (lights_off_sof - start_sof) % 86400
    if duration_s > 0 and delta >= duration_s:
        return 0.0
    return delta


def choose_window(
    labels_full: np.ndarray,
    t_off: float,
    n_epochs_full: int,
    mode: str,
    max_hours: float,
    wake_pad_min: float,
) -> tuple[int, int]:
    """Return [epoch_start, epoch_end) on the full-recording index."""
    e_off = int(np.floor(t_off / EPOCH_S))
    e_off = max(0, min(e_off, n_epochs_full))
    e_max = min(n_epochs_full, e_off + int(max_hours * 3600 / EPOCH_S))

    if mode == "lights_off":
        return e_off, e_max

    # sleep_period: last sleep epoch at or after lights-off
    sleep_mask = np.isin(labels_full, [INT_FROM_STAGE[s] for s in ("N1", "N2", "N3", "REM")])
    sleep_idx = np.flatnonzero(sleep_mask[:e_max])
    sleep_idx = sleep_idx[sleep_idx >= e_off]
    if sleep_idx.size == 0:
        return e_off, e_max
    e_last = int(sleep_idx[-1]) + 1
    e_pad = int(round(wake_pad_min * 60 / EPOCH_S))
    return e_off, min(n_epochs_full, e_last + e_pad, e_max)


def trim_one(
    psg_path: Path,
    hyp_path: Path,
    lights_map: dict[tuple[int, int], float],
    mode: str,
    max_hours: float,
    wake_pad_min: float,
) -> tuple[dict, np.ndarray, int, int]:
    sid = _sid(psg_path)
    raw = mne.io.read_raw_edf(str(psg_path), preload=False, verbose=False)
    sfreq = float(raw.info["sfreq"])
    n_epochs_full = int(np.floor(raw.n_times / (sfreq * EPOCH_S)))
    labels_full = full_stage_labels(hyp_path, n_epochs_full)

    sn = parse_subject_night(sid)
    if sn is None or sn not in lights_map:
        raise KeyError(f"No lights-off for session {sid} (parse={sn})")
    dur_s = n_epochs_full * EPOCH_S
    t_off = lights_off_offset_s(raw.info.get("meas_date"), lights_map[sn], dur_s)

    e0, e1 = choose_window(labels_full, t_off, n_epochs_full, mode, max_hours, wake_pad_min)
    if e1 <= e0:
        # Last resort: keep the scored sleep span of the whole recording
        sleep_mask = np.isin(labels_full, [1, 2, 3, 4])
        idx = np.flatnonzero(sleep_mask)
        if idx.size == 0:
            raise ValueError(f"Empty window for {sid}: e0={e0} e1={e1}")
        e0 = max(0, int(idx[0]) - int(round(wake_pad_min * 60 / EPOCH_S)))
        e1 = min(n_epochs_full, int(idx[-1]) + 1 + int(round(wake_pad_min * 60 / EPOCH_S)))
        if e1 <= e0:
            raise ValueError(f"Empty window for {sid}: e0={e0} e1={e1}")

    stages = labels_full[e0:e1].astype(np.uint8, copy=True)
    meas = raw.info.get("meas_date")
    meta = {
        "session": sid,
        "subset": psg_path.parent.name,
        "subject": sn[0],
        "night": sn[1],
        "psg": psg_path.name,
        "hypnogram": hyp_path.name,
        "sfreq": sfreq,
        "psg_hours": n_epochs_full * EPOCH_S / 3600,
        "lights_off_sof": lights_map[sn],
        "lights_off_offset_s": t_off,
        "epoch_start": e0,
        "epoch_end": e1,
        "n_epochs_full": n_epochs_full,
        "n_epochs_window": e1 - e0,
        "window_hours": (e1 - e0) * EPOCH_S / 3600,
        "mode": mode,
        "meas_date": str(meas) if meas is not None else "",
        "n_scored_window": int(np.sum(stages != UNS)),
        "n_sleep_window": int(np.sum(np.isin(stages, [1, 2, 3, 4]))),
    }
    return meta, stages, e0, e1


def export_trimmed_edf(
    psg_path: Path,
    hyp_path: Path,
    e0: int,
    e1: int,
    stages: np.ndarray,
    out_edf: Path,
) -> None:
    raw = mne.io.read_raw_edf(str(psg_path), preload=True, verbose=False)
    tmin = e0 * EPOCH_S
    tmax = e1 * EPOCH_S
    raw.crop(tmin=tmin, tmax=min(tmax, raw.times[-1]), include_tmax=False)
    out_edf.parent.mkdir(parents=True, exist_ok=True)
    raw.export(out_edf, fmt="edf", overwrite=True, verbose=False)

    # sidecar: one stage string per 30-s line (0-4 or ?)
    lines = []
    for s in stages:
        lines.append("?" if s == UNS else str(int(s)))
    out_edf.with_name(out_edf.stem + "_stages.txt").write_text("\n".join(lines) + "\n")


def merge_table(path: Path, new_rows: pd.DataFrame, key: str) -> pd.DataFrame:
    """Keep previous rows for sessions not in this run; replace the rest."""
    new_rows = new_rows.sort_values(key).reset_index(drop=True)
    if not path.is_file():
        return new_rows
    try:
        prev = pd.read_csv(path)
    except Exception:  # noqa: BLE001
        return new_rows
    if key not in prev.columns:
        return new_rows
    prev = prev[~prev[key].astype(str).isin(set(new_rows[key].astype(str)))]
    return pd.concat([prev, new_rows], ignore_index=True).sort_values(key).reset_index(drop=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Trim Sleep-EDF to lights-off sleep window")
    ap.add_argument("--subset", choices=["cassette", "telemetry", "both"], default="both")
    ap.add_argument("--limit", type=int, default=0, help="number of sessions (0 = all)")
    ap.add_argument("--mode", choices=["sleep_period", "lights_off"], default="sleep_period")
    ap.add_argument("--max-hours", type=float, default=16.0, help="cap on window length")
    ap.add_argument("--wake-pad-min", type=float, default=30.0, help="wake after last sleep (sleep_period)")
    ap.add_argument("--edf-root", type=Path, default=DEFAULT_EDF_ROOT, help="dataset root with SC/ST sheets")
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_CLEAN_ROOT, help="clean-window output folder")
    ap.add_argument("--write-edf", action="store_true", help="also write cropped PSG EDFs (slow/large)")
    args = ap.parse_args(argv)

    if not args.edf_root.is_dir():
        print(f"Dataset not found: {args.edf_root}", file=sys.stderr)
        print("Set SLEEPLENS_EDF / SLEEPLENS_DATA or pass --edf-root.", file=sys.stderr)
        return 1

    lights: dict[tuple[int, int], float] = {}
    sc_xls = args.edf_root / "SC-subjects.xls"
    st_xls = args.edf_root / "ST-subjects.xls"
    if args.subset in ("cassette", "both") and sc_xls.exists():
        lights.update(load_lights_off_cassette(sc_xls))
    if args.subset in ("telemetry", "both") and st_xls.exists():
        lights.update(load_lights_off_telemetry(st_xls))
    if not lights:
        print("No lights-off table loaded.", file=sys.stderr)
        return 1

    pairs = pair_sessions(args.edf_root, args.subset)
    if args.limit and args.limit > 0:
        pairs = pairs[: args.limit]
    if not pairs:
        print("No PSG/hypnogram pairs found.", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    stages_dir = args.out_dir / "stages"
    stages_dir.mkdir(exist_ok=True)
    if args.write_edf:
        (args.out_dir / "edf").mkdir(exist_ok=True)

    print(f"Sessions: {len(pairs)}  mode={args.mode}  out={args.out_dir}")
    metas, epoch_rows = [], []
    n_fail = 0
    for psg, hyp in pairs:
        sid = _sid(psg)
        try:
            meta, stages, e0, e1 = trim_one(
                psg, hyp, lights, args.mode, args.max_hours, args.wake_pad_min
            )
        except Exception as e:  # noqa: BLE001
            print(f"  [fail] {sid}: {e}", file=sys.stderr)
            n_fail += 1
            continue

        np.save(stages_dir / f"{sid}.npy", stages)
        for i, s in enumerate(stages):
            epoch_rows.append(
                {
                    "session": sid,
                    "epoch_local": i,
                    "epoch_full": e0 + i,
                    "stage": int(s),
                    "stage_str": "?" if s == UNS else STAGE_STR[int(s)],
                }
            )
        if args.write_edf:
            try:
                export_trimmed_edf(psg, hyp, e0, e1, stages, args.out_dir / "edf" / f"{sid}-PSG.edf")
            except Exception as e:  # noqa: BLE001
                print(f"  [edf-fail] {sid}: {e}", file=sys.stderr)
        metas.append(meta)
        scored = meta["n_scored_window"]
        sleep_h = meta["n_sleep_window"] * EPOCH_S / 3600
        print(
            f"  {sid}: {meta['window_hours']:.2f}h "
            f"({e0}:{e1}) sleep={sleep_h:.2f}h scored={scored}",
            flush=True,
        )

    if not metas:
        print("No sessions trimmed.", file=sys.stderr)
        return 1

    man = merge_table(args.out_dir / "manifest.csv", pd.DataFrame(metas), "session")
    man.to_csv(args.out_dir / "manifest.csv", index=False)
    epochs = merge_table(args.out_dir / "epochs.csv.gz", pd.DataFrame(epoch_rows), "session")
    epochs.to_csv(args.out_dir / "epochs.csv.gz", index=False, compression="gzip")

    st = pd.DataFrame(metas)
    print(f"\nTrimmed {len(metas)} sessions (failed={n_fail}); manifest now {len(man)} sessions")
    print(f"window hours: mean={st['window_hours'].mean():.2f} "
          f"median={st['window_hours'].median():.2f}")
    print(f"\nWrote:\n  {args.out_dir / 'manifest.csv'}\n  {args.out_dir / 'epochs.csv.gz'}\n  {stages_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
