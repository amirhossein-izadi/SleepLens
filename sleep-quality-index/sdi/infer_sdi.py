"""Run the npj Digital Medicine'25 Sleep Depth Index (SDI) transformer
(sczzz3/SDI, weight/checkpoint.pt) on Sleep-EDF lights-off windows.

The paper model consumes 30-s epochs at 100 Hz, 4 channels in this order:
[EEG (paper: C4), chin EMG, EOG (paper: right), ECG], and returns a 0-1 SDI
(higher = deeper) plus a binary REM prediction per epoch. Preprocessing mirrors
upstream src/infer.py: resample to 100 Hz only (no filter), fixed 30-s epochs,
uV for EEG/EMG/EOG and mV for ECG.

Sleep-EDF adaptations (zero-shot, NOT validated):
  * EEG: 'EEG Fpz-Cz' (Sleep-EDF has no C4); --eeg-channel can select Pz-Oz.
  * EMG: 'EMG submental'; cassette is natively 1 Hz (mne upsamples a smooth
    envelope -> no HF content), telemetry is native 100 Hz.
  * ECG: absent in Sleep-EDF -> zero-filled unless --ecg-channel names one.
  * Unscored epochs are kept (the model scores every epoch); estimate_quality.py
    masks them.

Output: data/sdi/<sid>.npz with window-aligned sdi (float32), rem (uint8 0/1),
epoch_start, n_full. QC vs expert stages -> reports/sdi_per_session_lights_off.csv
and reports/sdi_summary_lights_off.csv (per-session mean +/- std; --resume skips
are excluded, so re-score missing nights before quoting the summary).

  python infer_sdi.py --subset cassette --limit 3   # smoke
  python infer_sdi.py --subset both --limit 0 --resume
  python infer_sdi.py --subset both --shard 0 --num-shards 4
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import mne
import numpy as np
import pandas as pd
import torch
from scipy.stats import spearmanr
from sklearn.metrics import f1_score, precision_score, recall_score

from common import (
    CLEAN_ROOT,
    EDF_ROOT,
    EMG_CH,
    EOG_CH,
    INPUT_CONDITION,
    MODEL_CKPT,
    REPORT_DIR,
    SDI_OUT_ROOT,
    _sid,
    load_stages_int16,
    manifest_windows,
    pair_sessions,
)
from sdi_net import Net

CKPT = MODEL_CKPT
MODEL = "sdi"
FS_OUT = 100
EPOCH_SAMPLES = 30 * FS_OUT
ORDINAL = {0: 0, 1: 1, 2: 2, 3: 3}




def load_model(device: str) -> torch.nn.Module:
    state = torch.load(CKPT, map_location="cpu", weights_only=True)
    net = Net()
    net.load_state_dict(state, strict=True)
    return net.to(device).eval()


def read_sdi_input(
    psg_path: Path,
    eeg_ch: str,
    ecg_ch: str | None,
) -> tuple[np.ndarray, int]:
    """(n_epochs, 4, 3000) float32 in [EEG, EMG, EOG, ECG] order."""
    want = [eeg_ch, EMG_CH, EOG_CH] + ([ecg_ch] if ecg_ch else [])
    raw = mne.io.read_raw_edf(str(psg_path), preload=True, include=want, verbose=False)
    raw.resample(FS_OUT, verbose=False)
    x = raw.get_data(picks=[eeg_ch, EMG_CH, EOG_CH]) * 1e6
    if ecg_ch:
        ecg = raw.get_data(picks=[ecg_ch]) * 1e3
    else:
        ecg = np.zeros_like(x[:1])
    x = np.concatenate([x, ecg], axis=0)
    n = x.shape[1] // EPOCH_SAMPLES
    x = (
        x[:, : n * EPOCH_SAMPLES]
        .reshape(4, n, EPOCH_SAMPLES)
        .transpose(1, 0, 2)
        .astype(np.float32)
    )
    return x, n


def predict(x: np.ndarray, net: torch.nn.Module, device: str, batch_size: int) -> tuple:
    n = x.shape[0]
    sdi = np.zeros(n, dtype=np.float32)
    rem = np.zeros(n, dtype=np.uint8)
    with torch.no_grad():
        for s in range(0, n, batch_size):
            b = torch.from_numpy(x[s : s + batch_size]).to(device)
            depth, rem_logits = net(b)
            sdi[s : s + batch_size] = torch.sigmoid(depth).squeeze(-1).cpu().numpy()
            rem[s : s + batch_size] = rem_logits.argmax(-1).cpu().numpy().astype(np.uint8)
    return sdi, rem


def qc_metrics(st: np.ndarray, sdi: np.ndarray, rem: np.ndarray) -> dict:
    scored = (st >= 0) & (st < 5)
    sleep = np.isin(st, [1, 2, 3, 4])
    ordinal = np.full(st.shape, np.nan)
    for k, v in ORDINAL.items():
        ordinal[st == k] = v
    ok = ~np.isnan(ordinal)
    depth_rho = (
        spearmanr(ordinal[ok], sdi[ok]).statistic if ok.sum() > 10 else float("nan")
    )
    y_rem = (st[scored] == 4).astype(int)
    p_rem = rem[scored].astype(int)
    return {
        "n_epochs_scored": int(scored.sum()),
        "n_sleep": int(sleep.sum()),
        "n_pred_rem": int(rem[sleep].sum()),
        "sdi_mean": float(sdi[sleep].mean()) if sleep.sum() else float("nan"),
        "sdi_mean_wake": float(sdi[st == 0].mean()) if (st == 0).sum() else float("nan"),
        "sdi_mean_n3": float(sdi[st == 3].mean()) if (st == 3).sum() else float("nan"),
        "sdi_mean_rem": float(sdi[st == 4].mean()) if (st == 4).sum() else float("nan"),
        "depth_spearman": float(depth_rho),
        "rem_f1": float(f1_score(y_rem, p_rem, zero_division=0)),
        "rem_precision": float(precision_score(y_rem, p_rem, zero_division=0)),
        "rem_recall": float(recall_score(y_rem, p_rem, zero_division=0)),
        "rem_pred_rate": float(p_rem.mean()),
        "rem_expert_rate": float(y_rem.mean()),
    }


def run_one(
    psg_path: Path,
    window: tuple[int, int],
    net: torch.nn.Module,
    device: str,
    eeg_ch: str,
    ecg_ch: str | None,
    batch_size: int,
    clean_root: Path = CLEAN_ROOT,
) -> dict:
    sid = _sid(psg_path)
    t0 = time.time()
    x, n_full = read_sdi_input(psg_path, eeg_ch, ecg_ch)
    sdi_full, rem_full = predict(x, net, device, batch_size)

    st = load_stages_int16(sid, "expert", clean_root)
    e0, e1 = max(0, window[0]), min(n_full, window[1])
    if len(st) != e1 - e0:
        raise ValueError(f"stage window mismatch for {sid}: {len(st)} vs {e1 - e0}")

    sdi_w, rem_w = sdi_full[e0:e1], rem_full[e0:e1]
    row = {
        "session": sid,
        "subset": psg_path.parent.name,
        "input_condition": INPUT_CONDITION.get(psg_path.parent.name, "unknown"),
        "window": "lights_off",
        "eeg_channel": eeg_ch,
        "ecg_channel": ecg_ch or "zeros",
        "n_epochs_window": int(e1 - e0),
        "n_epochs_total": int(n_full),
        "pred_sec": time.time() - t0,
        "_sdi": sdi_w,
        "_rem": rem_w,
        "_e0": e0,
        "_n_full": n_full,
    }
    row.update(qc_metrics(st, sdi_w, rem_w))
    return row


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SDI transformer on Sleep-EDF (lights-off)")
    ap.add_argument("--subset", choices=["cassette", "telemetry", "both"], default="both")
    ap.add_argument("--limit", type=int, default=0, help="number of sessions (0 = all)")
    ap.add_argument("--eeg-channel", default="EEG Fpz-Cz", help="Sleep-EDF EEG derivation")
    ap.add_argument("--ecg-channel", default=None, help="EDF channel to use as ECG (mV); default zero-fill")
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--edf-root", type=Path, default=EDF_ROOT, help="raw Sleep-EDF dataset root")
    ap.add_argument("--clean-root", type=Path, default=CLEAN_ROOT, help="lights-off windows")
    ap.add_argument("--out-dir", type=Path, default=SDI_OUT_ROOT, help="SDI npz output folder")
    ap.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    ap.add_argument("--resume", action="store_true", help="skip sessions whose npz exists")
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--num-shards", type=int, default=1)
    args = ap.parse_args(argv)

    if not CKPT.is_file():
        print(f"Checkpoint not found: {CKPT}", file=sys.stderr)
        return 1
    try:
        windows = manifest_windows(args.clean_root)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1

    pairs = pair_sessions(args.edf_root, args.subset)
    if args.limit and args.limit > 0:
        pairs = pairs[: args.limit]
    pairs = [(p, h) for p, h in pairs if _sid(p) in windows]
    if args.num_shards > 1:
        pairs = [p for i, p in enumerate(pairs) if i % args.num_shards == args.shard]
    print(
        f"Sessions to score: {len(pairs)} ({args.subset}, window=lights_off, "
        f"eeg={args.eeg_channel}, ecg={args.ecg_channel or 'zeros'}, device={args.device})"
    )

    net = load_model(args.device)
    sdi_dir = args.out_dir
    sdi_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for psg, _hyp in pairs:
        sid = _sid(psg)
        if args.resume and (sdi_dir / f"{sid}.npz").is_file():
            print(f"  [resume] {sid}: sdi exists, skipping", flush=True)
            continue
        try:
            r = run_one(
                psg, windows[sid], net, args.device,
                args.eeg_channel, args.ecg_channel, args.batch_size,
                args.clean_root,
            )
        except Exception as e:  # noqa: BLE001
            print(f"  [fail] {sid}: {e}", file=sys.stderr)
            continue
        np.savez(
            sdi_dir / f"{sid}.npz",
            sdi=r.pop("_sdi"),
            rem=r.pop("_rem"),
            epoch_start=r.pop("_e0"),
            n_full=r.pop("_n_full"),
        )
        print(
            f"  {r['session']}  sleep SDI={r['sdi_mean']:.3f} "
            f"(W {r['sdi_mean_wake']:.3f} / N3 {r['sdi_mean_n3']:.3f} / R {r['sdi_mean_rem']:.3f}) "
            f"depth_rho={r['depth_spearman']:.3f} rem_F1={r['rem_f1']:.3f} "
            f"({r['pred_sec']:.1f}s)",
            flush=True,
        )
        rows.append(r)

    if not rows:
        if args.resume and pairs:
            print("All sessions already scored; nothing to do.")
            return 0
        print("No sessions succeeded.", file=sys.stderr)
        return 1

    args.report_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(args.report_dir / f"{MODEL}_per_session_lights_off.csv", index=False)

    def _summary_row(group: pd.DataFrame, label: str) -> dict:
        return {
            "subset": label,
            "input_condition": INPUT_CONDITION.get(label, "all" if label == "all" else "unknown"),
            "n_sessions": len(group),
            "n_epochs_window": int(group["n_epochs_window"].sum()),
            "mean_sdi_sleep": group["sdi_mean"].mean(),
            "mean_sdi_wake": group["sdi_mean_wake"].mean(),
            "mean_sdi_n3": group["sdi_mean_n3"].mean(),
            "mean_sdi_rem": group["sdi_mean_rem"].mean(),
            "mean_depth_spearman": group["depth_spearman"].mean(),
            "std_depth_spearman": group["depth_spearman"].std(ddof=0),
            "mean_rem_f1": group["rem_f1"].mean(),
            "std_rem_f1": group["rem_f1"].std(ddof=0),
            "mean_pred_sec": group["pred_sec"].mean(),
        }

    summary_rows = [_summary_row(g, name) for name, g in df.groupby("subset", sort=True)]
    summary_rows.append(_summary_row(df, "all"))
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(args.report_dir / f"{MODEL}_summary_lights_off.csv", index=False)

    print(f"\n=== {MODEL} (lights_off) ===")
    for r in summary.itertuples():
        print(
            f"{r.subset:15s} n={r.n_sessions:3d}  sleep SDI={r.mean_sdi_sleep:.3f}  "
            f"depth rho={r.mean_depth_spearman:.3f}±{r.std_depth_spearman:.3f}  "
            f"REM F1={r.mean_rem_f1:.3f}  [{r.input_condition}]"
        )
    print("Cassette and telemetry are separate input conditions; both are mismatched vs the paper.")
    print(f"Outputs -> {sdi_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
