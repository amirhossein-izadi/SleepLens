"""Inference speed benchmark: per-model cost, per-night cost, real-time factor.

Answers: how long does one model take on CPU, and how real-time is a deployed system?
"""
import sys
import time
import torch  # FIRST (Windows DLL order)
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
TAB = EDGE.parent / "sleep-eda" / "tables"
sys.path.insert(0, str(EDGE / "adapters"))

print(f"torch {torch.__version__} | threads={torch.get_num_threads()} | device=cpu")

def timeit(fn, n=3, warmup=1):
    for _ in range(warmup):
        fn()
    ts = []
    for _ in range(n):
        t = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t)
    return min(ts), float(np.mean(ts))

# ---------- 1. AnySleep: length scaling ----------
import importlib
anysleep = importlib.import_module("anysleep_adapter")
model = anysleep.get_model()
EP = 3840  # samples per 30-s epoch @128Hz
print("\n== AnySleep forward-only (3 channels, CPU) ==")
for ne in [1, 4, 40, 120, 960]:
    X = torch.randn(1, ne * EP, 3)
    mn, av = timeit(lambda: model(X), n=3)
    per_ep = av / ne
    rtf = (ne * 30) / av  # signal seconds processed per wall second
    print(f"{ne:4d} epochs ({ne*30/60:6.1f} min): {av*1000:8.1f} ms  | {per_ep*1000:7.2f} ms/epoch | real-time x{rtf:,.0f}", flush=True)

X = torch.randn(1, 20 * 60 * 128, 3)
mn, av = timeit(lambda: model(X), n=2)
print(f"streaming window 20 min: {av*1000:.0f} ms -> {av/40*1000:.1f} ms per 30-s epoch (context-aware streaming)")

# ---------- 2. full adapter pipeline on one real recording ----------
print("\n== Full AnySleep pipeline on one real recording (SC4001) ==")
t0 = time.perf_counter()
df = anysleep.predict_record("SC4001", channels=("EEG Fpz-Cz", "EEG Pz-Oz", "EOG horizontal"))
tot = time.perf_counter() - t0
ne = len(df)
print(f"SC4001: {ne} epochs ({ne*30/3600:.1f} h) in {tot:.1f}s -> {tot/ne*1000:.1f} ms/epoch, real-time x{(ne*30)/tot:,.0f}")

# ---------- 3. preprocessing cost alone ----------
from canonical import load_canonical, resample_poly
t0 = time.perf_counter()
data = load_canonical("SC4001", channels=("EEG Fpz-Cz",))
t_load = time.perf_counter() - t0
t0 = time.perf_counter()
x = resample_poly(data["EEG Fpz-Cz"].astype(np.float64), 100, 128)
t_res = time.perf_counter() - t0
hrs = len(x) / 128 / 3600
print(f"\nEDF load (1 ch, {hrs:.1f} h): {t_load:.1f}s | polyphase 100->128Hz: {t_res:.1f}s")

# ---------- 4. RSN ----------
try:
    rsn = importlib.import_module("rsn_adapter")
    print("\n== RobustSleepNet pipeline (SC4001) ==")
    t0 = time.perf_counter()
    d = rsn.predict_record("SC4001")
    tot = time.perf_counter() - t0
    print(f"RSN SC4001: {len(d)} epochs in {tot:.1f}s -> {tot/len(d)*1000:.1f} ms/epoch, real-time x{(len(d)*30)/tot:,.0f}")
except Exception as e:
    print("RSN bench skipped:", str(e)[:120])

# ---------- 5. YASA (crop) ----------
try:
    from yasa_adapter import YasaStager
    st = YasaStager(eeg="EEG Fpz-Cz", eog="EOG horizontal", name="bench", crop_bench=True)
    print("\n== YASA pipeline (SC4001, cropped to BENCHMARK_30) ==")
    t0 = time.perf_counter()
    d = st.predict_record("SC4001")
    tot = time.perf_counter() - t0
    print(f"YASA SC4001: {len(d)} epochs in {tot:.1f}s -> {tot/len(d)*1000:.1f} ms/epoch, real-time x{(len(d)*30)/tot:,.0f}")
except Exception as e:
    print("YASA bench skipped:", str(e)[:120])

# ---------- 6. LightGBM ----------
try:
    import lightgbm as lgb
    fs = []
    for b in [0, 1, 2]:
        p = TAB / f"baseline_full_b{b}.parquet"
        if p.exists():
            fs.append(pd.read_parquet(p))
    bdf = pd.concat(fs, ignore_index=True)
    FEATS = ["eeg_std", "eeg_ptp", "zcr", "delta", "theta", "alpha", "sigma", "beta",
             "eog_ptp", "eog_std", "emg_rms"]
    clf = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=63,
                             class_weight="balanced", n_jobs=8, verbose=-1)
    t0 = time.perf_counter()
    clf.fit(bdf[FEATS], bdf.label)
    t_fit = time.perf_counter() - t0
    mn, av = timeit(lambda: clf.predict_proba(bdf[FEATS].iloc[:960]), n=3)
    print(f"\nLightGBM: fit on {len(bdf)} epochs in {t_fit:.1f}s | predict 960 epochs: {av*1000:.1f} ms -> {av/960*1000:.3f} ms/epoch")
except Exception as e:
    print("LGBM bench skipped:", str(e)[:120])
