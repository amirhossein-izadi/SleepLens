"""Benchmark wearable-style models on the Sleep-EDF surrogate features.

Trains each model with the frozen subject-wise GroupKFold splits from
<data-dir>/splits.csv and writes out-of-fold epoch predictions to
<data-dir>/preds/<model>_<session>.npy (int8: 0-4 for 5-class, 0-2 for
WatchSleepNet's W/NREM/REM, 255 = unscored/UNS). Only out-of-fold predictions
are produced, so subjects never cross the train/test boundary.

Models:
  rf            RandomForest on engineered features (classical baseline,
                retrained on our surrogate features)
  unet1d        1D U-Net (MADSOLSEN-style ResUNet adapted to 1D, PyTorch)
  watchsleepnet WatchSleepNet architecture adapted to an envelope channel
                (ResNet1D + TCN + BiLSTM + attention; W/NREM/REM)

Run in wearable/ (needs torch, see requirements.txt):
  python train_bench.py --models rf
  python train_bench.py --models unet1d --epochs 20
  python train_bench.py --models watchsleepnet --epochs 20
  python train_bench.py --models rf --only-folds 0 --smoke 3   # quick check
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupShuffleSplit
from torch import nn
from torch.utils.data import DataLoader, Dataset

from wearable_models import UNet1D, WatchSleepNet1D

HERE = Path(__file__).parent
DEFAULT_DATA = HERE / "data" / "wearable"
UNS = 255

WSN_MAP = {0: 0, 1: 1, 2: 1, 3: 1, 4: 2, UNS: -1}


# --------------------------------------------------------------------------
# waveform store (preloaded, float16)
# --------------------------------------------------------------------------
def _load_npz(path: Path) -> dict:
    with np.load(path) as npz:
        return {k: npz[k] for k in npz.files}


def _channels_from_npz(npz: dict, channels: tuple[str, ...], rate: int) -> np.ndarray:
    n_epochs = int(npz["labels"].shape[0])
    length = int(round(float(npz["fs_high" if rate == 25 else "fs_low"]) * 30))
    arrs = []
    for ch in channels:
        if ch == "mask_motion25":
            v = np.full((n_epochs, length), float(bool(npz["mask_motion25"])), dtype=np.float32)
        elif ch == "mask_resp":
            v = np.full((n_epochs, length), float(bool(npz["mask_resp"])), dtype=np.float32)
        elif ch in npz:
            v = np.asarray(npz[ch], dtype=np.float32)
        else:
            v = np.zeros((n_epochs, length), dtype=np.float32)
        if v.shape[1] != length:
            v = np.resize(v, (v.shape[0], length))
        arrs.append(v)
    return np.stack(arrs, axis=0)  # (C, n_epochs, L)


class WaveStore:
    """All sessions' waveforms preloaded into one (C, total_epochs, L) float16 array."""

    def __init__(self, data_dir: Path, sessions: list[str], channels: list[str], rate: int):
        self.channels = list(channels)
        self.rate = rate
        self.offsets: dict[str, tuple[int, int]] = {}
        self.labels: dict[str, np.ndarray] = {}
        parts = []
        start = 0
        for sid in sessions:
            npz = _load_npz(data_dir / "windows" / f"{sid}.npz")
            arr = _channels_from_npz(npz, tuple(channels), rate)
            parts.append(arr.astype(np.float16))
            self.offsets[sid] = (start, start + arr.shape[1])
            self.labels[sid] = npz["labels"]
            start += arr.shape[1]
        self.data = np.concatenate(parts, axis=1)
        del parts
        gc.collect()

    def session(self, sid: str) -> np.ndarray:
        a, b = self.offsets[sid]
        return self.data[:, a:b, :]

    def __len__(self) -> int:
        return int(self.data.shape[1])


class EpochDataset(Dataset):
    """One sample = one 30-s epoch; UNS labels become -1 (ignored)."""

    def __init__(self, store: WaveStore, sessions: list[str]):
        self.store = store
        self.index: list[tuple[str, int]] = []
        labels = []
        for sid in sessions:
            y = store.labels[sid]
            for ei, lab in enumerate(y):
                self.index.append((sid, ei))
                labels.append(-1 if lab == UNS else int(lab))
        self.labels = np.asarray(labels, dtype=np.int64)

    def __len__(self) -> int:
        return len(self.index)

    def __getitem__(self, i: int):
        sid, ei = self.index[i]
        x = self.store.session(sid)[:, ei, :].astype(np.float32)
        return torch.from_numpy(x), int(self.labels[i])


class NightDataset(Dataset):
    """One sample = one night chunk of consecutive 30-s epochs (sequence model)."""

    def __init__(self, store: WaveStore, sessions: list[str], chunk: int = 1100):
        self.store = store
        self.sessions = sessions
        self.chunk = chunk
        self.chunks: list[tuple[str, int, int]] = []
        self.chunk_sessions: list[str] = []
        labels = []
        for sid in sessions:
            y = store.labels[sid]
            n = int(y.shape[0])
            for start in range(0, n, chunk):
                stop = min(start + chunk, n)
                self.chunks.append((sid, start, stop))
                self.chunk_sessions.append(sid)
                labels.extend(WSN_MAP.get(int(v), -1) for v in y[start:stop])
        self.labels = np.asarray(labels, dtype=np.int64)

    def __len__(self) -> int:
        return len(self.chunks)

    def __getitem__(self, i: int):
        sid, start, stop = self.chunks[i]
        x = self.store.session(sid)[0, start:stop, :].astype(np.float32)
        y = self.store.labels[sid][start:stop]
        y = np.array([WSN_MAP.get(int(v), -1) for v in y], dtype=np.int64)
        return torch.from_numpy(x), torch.from_numpy(y)


def collate_nights(batch):
    xs, ys = zip(*batch)
    lengths = torch.tensor([len(y) for y in ys], dtype=torch.int64)
    x = nn.utils.rnn.pad_sequence(xs, batch_first=True, padding_value=0.0)
    y = nn.utils.rnn.pad_sequence(ys, batch_first=True, padding_value=-1)
    return x, y, lengths


# --------------------------------------------------------------------------
# training helpers
# --------------------------------------------------------------------------
def class_weights(labels: np.ndarray, n_classes: int) -> torch.Tensor:
    counts = np.bincount(labels[labels >= 0], minlength=n_classes).astype(np.float64)
    counts = np.maximum(counts, 1.0)
    w = counts.sum() / (n_classes * counts)
    return torch.tensor(w, dtype=torch.float32)


def macro_f1(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> float:
    mask = y_true >= 0
    if mask.sum() == 0:
        return 0.0
    return float(f1_score(y_true[mask], y_pred[mask], average="macro", labels=list(range(n_classes)), zero_division=0))


@torch.no_grad()
def predict_epochs(model: nn.Module, loader: DataLoader, device: torch.device) -> np.ndarray:
    model.eval()
    preds = []
    for x, y in loader:
        out = model(x.to(device))
        preds.append(out.argmax(dim=1).cpu().numpy())
    return np.concatenate(preds) if preds else np.array([], dtype=np.int64)


@torch.no_grad()
def predict_nights(model: nn.Module, loader: DataLoader, device: torch.device) -> list[np.ndarray]:
    model.eval()
    out_preds = []
    for x, y, lengths in loader:
        logits = model(x.to(device), lengths.to(device))
        for b in range(logits.shape[0]):
            n = int(lengths[b])
            out_preds.append(logits[b, :n].argmax(dim=1).cpu().numpy())
    return out_preds


def make_loader(ds: Dataset, batch_size: int, shuffle: bool, collate_fn=None, num_workers: int = 0) -> DataLoader:
    return DataLoader(
        ds, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers,
        collate_fn=collate_fn, drop_last=shuffle, pin_memory=torch.cuda.is_available(),
    )


def train_unet(
    store: WaveStore,
    train_sessions: list[str],
    val_sessions: list[str],
    test_sessions: list[str],
    args,
    device: torch.device,
) -> dict:
    train_ds = EpochDataset(store, train_sessions)
    val_ds = EpochDataset(store, val_sessions)
    test_ds = EpochDataset(store, test_sessions)
    train_loader = make_loader(train_ds, args.batch_size, True, num_workers=args.num_workers)
    val_loader = make_loader(val_ds, args.batch_size, False, num_workers=args.num_workers)
    test_loader = make_loader(test_ds, args.batch_size, False, num_workers=args.num_workers)

    model = UNet1D(
        in_channels=len(store.channels), num_classes=5,
        base=args.unet_base, kernel_size=args.unet_kernel,
    ).to(device)
    weights = class_weights(train_ds.labels, 5).to(device)
    criterion = nn.CrossEntropyLoss(weight=weights, ignore_index=-1)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)

    best_f1, best_state, bad = -1.0, None, 0
    hist = []
    for epoch in range(args.epochs):
        model.train()
        total = 0.0
        for x, y in train_loader:
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            opt.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            opt.step()
            total += loss.item() * len(y)
        sched.step()
        val_pred = predict_epochs(model, val_loader, device)
        val_f1 = macro_f1(val_ds.labels, val_pred, 5)
        hist.append({"epoch": epoch, "loss": total / max(len(train_ds), 1), "val_macro_f1": val_f1})
        print(f"    epoch {epoch + 1:02d} loss={total / max(len(train_ds), 1):.4f} val_macro_f1={val_f1:.4f}", flush=True)
        if val_f1 > best_f1:
            best_f1, bad = val_f1, 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= args.patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)

    preds = predict_epochs(model, test_loader, device)
    out: dict[str, np.ndarray] = {}
    pos = 0
    for sid in test_sessions:
        n = len(store.labels[sid])
        out[sid] = preds[pos:pos + n].astype(np.uint8)
        pos += n
    return {"preds": out, "best_val_macro_f1": best_f1, "history": hist}


def train_wsn(
    store: WaveStore,
    train_sessions: list[str],
    val_sessions: list[str],
    test_sessions: list[str],
    args,
    device: torch.device,
) -> dict:
    train_ds = NightDataset(store, train_sessions, args.wsn_chunk)
    val_ds = NightDataset(store, val_sessions, args.wsn_chunk)
    test_ds = NightDataset(store, test_sessions, args.wsn_chunk)
    train_loader = make_loader(train_ds, args.wsn_batch, True, collate_nights, args.num_workers)
    val_loader = make_loader(val_ds, args.wsn_batch, False, collate_nights, args.num_workers)
    test_loader = make_loader(test_ds, args.wsn_batch, False, collate_nights, args.num_workers)

    model = WatchSleepNet1D(
        num_classes=3, num_channels=args.wsn_channels, hidden_dim=args.wsn_hidden,
        num_heads=args.wsn_heads, num_layers=args.wsn_layers, tcn_layers=args.wsn_tcn_layers,
    ).to(device)
    weights = class_weights(train_ds.labels, 3).to(device)
    criterion = nn.CrossEntropyLoss(weight=weights, ignore_index=-1)
    opt = torch.optim.AdamW(model.parameters(), lr=args.wsn_lr, weight_decay=1e-4)

    best_f1, best_state, bad = -1.0, None, 0
    hist = []
    for epoch in range(args.epochs):
        model.train()
        total, n_obs = 0.0, 0
        for x, y, lengths in train_loader:
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            opt.zero_grad()
            logits = model(x, lengths.to(device))
            loss = criterion(logits.reshape(-1, 3), y.reshape(-1))
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            total += loss.item() * int((y >= 0).sum())
            n_obs += int((y >= 0).sum())
        model.eval()
        val_true, val_pred = [], []
        with torch.no_grad():
            for x, y, lengths in val_loader:
                logits = model(x.to(device), lengths.to(device)).cpu()
                for b in range(logits.shape[0]):
                    n = int(lengths[b])
                    val_true.append(y[b, :n].numpy())
                    val_pred.append(logits[b, :n].argmax(dim=1).numpy())
        val_true = np.concatenate(val_true) if val_true else np.array([])
        val_pred = np.concatenate(val_pred) if val_pred else np.array([])
        val_f1 = macro_f1(val_true, val_pred, 3)
        hist.append({"epoch": epoch, "loss": total / max(n_obs, 1), "val_macro_f1": val_f1})
        print(f"    epoch {epoch + 1:02d} loss={total / max(n_obs, 1):.4f} val_macro_f1={val_f1:.4f}", flush=True)
        if val_f1 > best_f1:
            best_f1, bad = val_f1, 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= args.patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)

    seqs = predict_nights(model, test_loader, device)
    grouped: dict[str, list[np.ndarray]] = {}
    for sid, seq in zip(test_ds.chunk_sessions, seqs):
        grouped.setdefault(sid, []).append(seq)
    out: dict[str, np.ndarray] = {sid: np.concatenate(v) for sid, v in grouped.items()}
    return {"preds": out, "best_val_macro_f1": best_f1, "history": hist}


def train_rf(
    data_dir: Path,
    train_sessions: list[str],
    val_sessions: list[str],
    test_sessions: list[str],
    args,
) -> dict:
    frames = []
    for sid in train_sessions + val_sessions + test_sessions:
        d = pd.read_csv(data_dir / "features" / f"{sid}.csv.gz",
                        usecols=lambda c: c == "stage" or c.startswith("z_"))
        d.insert(0, "session", sid)
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    z_cols = [c for c in df.columns if c.startswith("z_")]
    x = df[z_cols].to_numpy(dtype=np.float32)
    any_nan = np.isnan(x).any(axis=1, keepdims=True).astype(np.float32)
    x = np.hstack([np.nan_to_num(x, nan=0.0), any_nan])
    y = df["stage"].to_numpy(dtype=np.int64)
    sid_arr = df["session"].to_numpy()

    train_mask = np.isin(sid_arr, train_sessions) & (y != UNS)
    val_mask = np.isin(sid_arr, val_sessions) & (y != UNS)
    test_mask = np.isin(sid_arr, test_sessions)
    clf = RandomForestClassifier(
        n_estimators=args.rf_trees, min_samples_leaf=2, class_weight="balanced_subsample",
        n_jobs=-1, random_state=args.seed,
    )
    clf.fit(x[train_mask], y[train_mask])
    val_f1 = float(f1_score(y[val_mask], clf.predict(x[val_mask]), average="macro",
                            labels=list(range(5)), zero_division=0))
    pred = clf.predict(x[test_mask]).astype(np.uint8)
    test_sid = sid_arr[test_mask]
    out = {sid: pred[test_sid == sid] for sid in test_sessions}
    return {"preds": out, "best_val_macro_f1": val_f1, "history": []}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Wearable benchmark: subject-wise CV training")
    ap.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    ap.add_argument("--pred-dir", type=Path, default=None, help="default: <data-dir>/preds")
    ap.add_argument("--models", default="rf,unet1d,watchsleepnet")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--only-folds", default="", help="comma list, e.g. 0,1 (smoke)")
    ap.add_argument("--smoke", type=int, default=0, help="limit test sessions per fold")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--patience", type=int, default=7)
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--num-workers", type=int, default=0)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--unet-rate", type=int, default=1, choices=[1, 25])
    ap.add_argument("--unet-channels", default="motion1,eog1,resp1,mask_resp")
    ap.add_argument("--unet-base", type=int, default=16)
    ap.add_argument("--unet-kernel", type=int, default=5)
    ap.add_argument("--wsn-channel", default="eog25", choices=["eog25", "motion25"])
    ap.add_argument("--wsn-batch", type=int, default=4)
    ap.add_argument("--wsn-lr", type=float, default=5e-5)
    ap.add_argument("--wsn-chunk", type=int, default=1100)
    ap.add_argument("--wsn-channels", type=int, default=64)
    ap.add_argument("--wsn-hidden", type=int, default=128)
    ap.add_argument("--wsn-heads", type=int, default=4)
    ap.add_argument("--wsn-layers", type=int, default=2)
    ap.add_argument("--wsn-tcn-layers", type=int, default=3)
    ap.add_argument("--rf-trees", type=int, default=300)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default="auto")
    args = ap.parse_args(argv)

    manifest, splits = load_tables(args.data_dir)
    sessions = splits["session"].astype(str).tolist()
    fold_of = dict(zip(sessions, splits["fold"].astype(int)))
    subject_of = dict(zip(sessions, splits["subject_key"].astype(str)))
    if args.wsn_channel == "motion25":
        ok = set(manifest[manifest["has_highrate_emg"]]["session"].astype(str))
        sessions = [s for s in sessions if s in ok]
        print(f"[info] wsn-channel=motion25: restricted to {len(sessions)} telemetry nights")

    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    print(f"device={device}  sessions={len(sessions)}  folds={args.folds}", flush=True)

    only_folds = [int(x) for x in args.only_folds.split(",") if x.strip()] or list(range(args.folds))
    pred_dir = args.pred_dir or (args.data_dir / "preds")
    pred_dir.mkdir(parents=True, exist_ok=True)

    for model_name in [m.strip() for m in args.models.split(",") if m.strip()]:
        if model_name not in ("rf", "unet1d", "watchsleepnet"):
            print(f"[skip] unknown model {model_name}", file=sys.stderr)
            continue
        print(f"\n=== {model_name} ===", flush=True)
        if model_name == "unet1d":
            channels, rate = args.unet_channels.split(","), args.unet_rate
        elif model_name == "watchsleepnet":
            channels, rate = [args.wsn_channel], 25
        else:
            channels, rate = None, None
        store = None
        if channels:
            t0 = time.time()
            print(f"  preloading waveforms {channels} @ {rate} Hz ...", flush=True)
            store = WaveStore(args.data_dir, sessions, channels, rate)
            print(f"  store: {store.data.shape} float16 ({store.data.nbytes / 1e9:.2f} GB) in {time.time() - t0:.0f}s", flush=True)

        all_preds: dict[str, np.ndarray] = {}
        fold_meta = []
        for fold in only_folds:
            test_sessions = [s for s in sessions if fold_of[s] == fold]
            if args.smoke:
                test_sessions = test_sessions[: args.smoke]
            pool = [s for s in sessions if fold_of[s] != fold]
            subjects = sorted({subject_of[s] for s in pool})
            gss = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=args.seed)
            tr_idx, va_idx = next(gss.split(subjects, groups=subjects))
            val_subjects = {subjects[i] for i in va_idx}
            train_sessions = [s for s in pool if subject_of[s] not in val_subjects]
            val_sessions = [s for s in pool if subject_of[s] in val_subjects]
            print(f"  fold {fold}: train={len(train_sessions)} val={len(val_sessions)} test={len(test_sessions)}", flush=True)
            t0 = time.time()
            if model_name == "rf":
                res = train_rf(args.data_dir, train_sessions, val_sessions, test_sessions, args)
            else:
                fn = train_unet if model_name == "unet1d" else train_wsn
                res = fn(store, train_sessions, val_sessions, test_sessions, args, device)
            print(f"  fold {fold} done in {time.time() - t0:.0f}s  best_val_macro_f1={res['best_val_macro_f1']:.4f}", flush=True)
            all_preds.update(res["preds"])
            fold_meta.append({"fold": fold, "val_macro_f1": res["best_val_macro_f1"],
                              "n_train": len(train_sessions), "n_val": len(val_sessions),
                              "n_test": len(test_sessions), "history": res["history"]})
        for sid, p in all_preds.items():
            np.save(pred_dir / f"{model_name}_{sid}.npy", p.astype(np.uint8))
        meta = {
            "model": model_name, "folds": only_folds, "seed": args.seed,
            "args": vars(args) | {"data_dir": str(args.data_dir)},
            "fold_meta": fold_meta, "n_sessions": len(all_preds),
        }
        (pred_dir / f"{model_name}_meta.json").write_text(json.dumps(meta, indent=2, default=str))
        print(f"  wrote {len(all_preds)} prediction files -> {pred_dir}", flush=True)
        del store
        gc.collect()
        torch.cuda.empty_cache()
    return 0


def load_tables(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    manifest = pd.read_csv(data_dir / "manifest.csv")
    splits = pd.read_csv(data_dir / "splits.csv")
    return manifest, splits


if __name__ == "__main__":
    raise SystemExit(main())
