"""YASA + TreeSHAP interpretability (the published method, applied to our data).

Config: Fpz-Cz + EOG (E02c, our best YASA config), cropped to BENCHMARK_30.
Outputs: docs/interp_yasa_global.csv, docs/interp_yasa_class.csv, docs/interp_yasa_stage.csv
"""
import sys
import time
import torch  # DLL order
import numpy as np
import pandas as pd
from pathlib import Path
import mne
import yasa
import shap

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
TAB = EDGE.parent / "sleep-eda" / "tables"
sys.path.insert(0, str(EDGE / "adapters"))
from canonical import load_canonical

CL = ["Wake", "N1", "N2", "N3", "REM"]
lab = {c: i for i, c in enumerate(CL)}
EEG, EOG = "EEG Fpz-Cz", "EOG horizontal"
N_PER_COHORT = 6

ep = pd.read_parquet(TAB / "epochs_v3.parquet")
g = ep[ep.valid & ep.label5.isin(CL)][["stem", "cohort", "epoch", "label5"]]
rng = np.random.default_rng(1)
sel = []
for co in ["SC", "ST"]:
    stems = sorted(g[g.cohort == co].stem.unique())
    sel += sorted(rng.choice(stems, size=N_PER_COHORT, replace=False).tolist())
print("recordings:", sel)

allX, allY, allS, feat_names = [], [], [], None
clf = None
t0 = time.time()
for si, stem in enumerate(sel):
    data = load_canonical(stem, channels=(EEG, EOG))
    gg = ep[(ep.stem == stem) & ep.valid & ep.in_bench]
    e0, e1 = int(gg.epoch.min()), int(gg.epoch.max())
    sl = slice(e0 * 3000, (e1 + 1) * 3000)
    info = mne.create_info(ch_names=[EEG, EOG], sfreq=100.0, ch_types=["eeg", "eog"])
    raw = mne.io.RawArray(np.stack([data[EEG][sl], data[EOG][sl]]), info, verbose=False)
    sls = yasa.SleepStaging(raw, eeg_name=EEG, eog_name=EOG)
    sls.fit()
    X = sls.get_features()
    if clf is None:
        clf = sls._load_model("auto")
        feat_names = list(clf.feature_name_)
        print("model:", type(clf).__name__, "| n_features:", len(feat_names))
        print("features:", feat_names)
    Xm = X[feat_names].copy()
    # align truth
    y = g[(g.stem == stem) & (g.epoch >= e0) & (g.epoch <= e1)].sort_values("epoch")
    yv = y.label5.map(lab).values
    n = min(len(Xm), len(yv))
    allX.append(Xm.iloc[:n].values.astype(np.float64))
    allY.append(yv[:n])
    allS.append(np.full(n, stem))
    print(f"[{si+1}/{len(sel)}] {stem} epochs={n} ({time.time()-t0:.0f}s)", flush=True)

X = np.vstack(allX)
Y = np.concatenate(allY)
S = np.concatenate(allS)
print("total epochs:", X.shape, "nan:", int(np.isnan(X).sum()))

expl = shap.TreeExplainer(clf)
sv = expl.shap_values(X)
if isinstance(sv, list):
    sv = np.stack(sv, axis=2)  # (n, f, 5)
print("shap:", sv.shape)

# NOTE: clf.classes_ order = ['N1','N2','N3','R','W'] (yasa) -> map to our CL
yasa_cls = list(clf.classes_)
YASA2OURS = {"N1": "N1", "N2": "N2", "N3": "N3", "R": "REM", "W": "Wake"}
cls_order = [YASA2OURS[c] for c in yasa_cls]
print("class order:", yasa_cls, "->", cls_order)

glob = pd.DataFrame({"feature": feat_names,
                     "mean_abs_shap": np.abs(sv).mean(axis=(0, 2))}).sort_values(
    "mean_abs_shap", ascending=False)
glob.to_csv(EDGE / "docs" / "interp_yasa_global.csv", index=False)
print("\n== YASA GLOBAL top-15 (mean |SHAP|) ==")
print(glob.head(15).to_string(index=False))

rows = []
for j, c in enumerate(cls_order):
    imp = np.abs(sv[:, :, j]).mean(0)
    order = np.argsort(-imp)
    rows.append({"class": c, **{f"#{k+1}": feat_names[i] for k, i in enumerate(order[:5])},
                 **{f"val_{k+1}": round(float(imp[i]), 4) for k, i in enumerate(order[:5])}})
cls = pd.DataFrame(rows)
cls.to_csv(EDGE / "docs" / "interp_yasa_class.csv", index=False)
print("\n== YASA PER-CLASS top-5 ==")
print(cls.to_string(index=False))

# per-stage SHAP of the model's own decision (SHAP of the predicted-class logit)
pred_j = np.array([cls_order.index(YASA2OURS[c]) for c in clf.predict(X)])
print("time_hour values: min=%.3f max=%.3f nunique=%d" % (
    np.nanmin(X[:, feat_names.index("time_hour")]), np.nanmax(X[:, feat_names.index("time_hour")]),
    len(np.unique(X[:, feat_names.index("time_hour")]))))
stage_rows = []
for j, c in enumerate(CL):
    msk = Y == lab[c]
    if msk.sum() < 10:
        continue
    own = sv[np.arange(len(X)), :, pred_j]
    top = np.argsort(-np.abs(own[msk]).mean(0))[:6]
    stage_rows.append({"stage": c, "n": int(msk.sum()),
                       **{f"#{k+1}": f"{feat_names[i]} ({own[msk][:, i].mean():+.3f})" for k, i in enumerate(top)}})
st = pd.DataFrame(stage_rows)
st.to_csv(EDGE / "docs" / "interp_yasa_stage.csv", index=False)
print("\n== YASA per-TRUE-stage top-6 features driving its own prediction ==")
print(st.to_string(index=False))
