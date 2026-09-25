"""Channel intervention: quantify each channel's contribution from existing ablation runs.
Configs: 3ch (E11) / 2EEG (E11c) / Fpz-only (E11a) / Pz-only (E11b).
Outputs: docs/interp_channel_*.csv + printed summary."""
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
TAB = EDGE.parent / "sleep-eda" / "tables"
CL = ["Wake", "N1", "N2", "N3", "REM"]
lab = {c: i for i, c in enumerate(CL)}

ep = pd.read_parquet(TAB / "epochs_v3.parquet")
g = ep[ep.valid & ep.label5.isin(CL) & ep.in_bench][["stem", "cohort", "epoch", "label5"]].copy()
g = g.rename(columns={"epoch": "epoch_index"})
g["label"] = g.label5.map(lab)

def load(run):
    fs = sorted((EDGE / "runs" / run).glob("*.parquet"))
    d = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    return d[["stem", "epoch_index"] + [f"p_{c}" for c in CL]].rename(
        columns={f"p_{c}": f"{run}_{c}" for c in CL})

CFG = {"3ch": "E11", "2EEG": "E11c", "Fpz+EOG": "E11d", "Fpz": "E11a", "Pz": "E11b"}
m = g.copy()
for name, r in CFG.items():
    d = load(r)
    m = m.merge(d, on=["stem", "epoch_index"], how="inner")
    m[f"pred_{name}"] = m[[f"{r}_{c}" for c in CL]].values.argmax(1)
    m[f"conf_{name}"] = m[[f"{r}_{c}" for c in CL]].values.max(1)

def stats(y, yp, mask=None):
    if mask is not None:
        y, yp = y[mask], yp[mask]
    out = []
    for i in range(5):
        tp = ((yp == i) & (y == i)).sum(); fp = ((yp == i) & (y != i)).sum(); fn = ((yp != i) & (y == i)).sum()
        f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        out.append({"class": CL[i], "f1": round(float(f1), 4), "recall": round(float(rec), 4),
                    "precision": round(float(prec), 4), "support": int((y == i).sum())})
    return pd.DataFrame(out)

print("=== per-class metrics per channel config (ALL) ===")
rows = []
for name in CFG:
    s = stats(m.label.values, m[f"pred_{name}"].values)
    s["config"] = name
    rows.append(s)
    print(f"\n-- {name} --")
    print(s[["class", "f1", "recall", "precision", "support"]].to_string(index=False))
percfg = pd.concat(rows)
percfg.to_csv(EDGE / "docs" / "interp_channel_perclass.csv", index=False)

print("\n=== value of adding a channel (F1 delta) ===")
piv = percfg.pivot(index="class", columns="config", values="f1").reindex(CL)
piv["EOG_added_(3ch-2EEG)"] = (piv["3ch"] - piv["2EEG"]).round(4)
piv["Pz_added_(2EEG-Fpz)"] = (piv["2EEG"] - piv["Fpz"]).round(4)
piv["Fpz_vs_Pz_(Fpz-Pz)"] = (piv["Fpz"] - piv["Pz"]).round(4)
print(piv.round(4).to_string())
piv.to_csv(EDGE / "docs" / "interp_channel_delta.csv")

print("\n=== intervention cases: epochs where EOG changes the answer ===")
cases = []
for src, dst in [("2EEG", "3ch"), ("Fpz", "3ch")]:
    msk = (m[f"pred_{src}"] != m[f"pred_{dst}"])
    sub = m[msk]
    tab = pd.crosstab(sub[f"pred_{src}"].map({i: c for i, c in enumerate(CL)}),
                      sub[f"pred_{dst}"].map({i: c for i, c in enumerate(CL)}))
    print(f"\n{src} -> {dst} changed on {msk.sum()} epochs ({100*msk.mean():.2f}%):")
    print(tab.to_string())
    # how often is the flip correct?
    ok_src = (sub[f"pred_{src}"].values == sub.label.values)
    ok_dst = (sub[f"pred_{dst}"].values == sub.label.values)
    print(f"  correct: {src}={ok_src.mean():.3f}  {dst}={ok_dst.mean():.3f}")
    cases.append({"pair": f"{src}->{dst}", "n_changed": int(msk.sum()),
                  "acc_src_on_changed": round(float(ok_src.mean()), 4),
                  "acc_dst_on_changed": round(float(ok_dst.mean()), 4)})
pd.DataFrame(cases).to_csv(EDGE / "docs" / "interp_channel_flips.csv", index=False)

print("\n=== REM without EOG (true-REM epochs, 2EEG vs 3ch) ===")
rem = m[m.label == lab["REM"]]
for name in CFG:
    rec = (rem[f"pred_{name}"].values == lab["REM"]).mean()
    print(f"REM recall {name:5s}: {rec:.4f}  (n={len(rem)})")

print("\n=== N1 without EOG / without Fpz ===")
n1 = m[m.label == lab["N1"]]
for name in CFG:
    rec = (n1[f"pred_{name}"].values == lab["N1"]).mean()
    print(f"N1  recall {name:5s}: {rec:.4f}  (n={len(n1)})")

# example epochs for the presentation
ex = m[(m.pred_3ch == lab["REM"]) & (m.pred_2EEG != lab["REM"]) & (m.label == lab["REM"])]
ex = ex.sort_values("conf_3ch", ascending=False).head(10)
ex["pred_3ch"] = ex.pred_3ch.map({i: c for i, c in enumerate(CL)})
ex["pred_2EEG"] = ex.pred_2EEG.map({i: c for i, c in enumerate(CL)})
ex["true"] = ex.label.map({i: c for i, c in enumerate(CL)})
ex[["stem", "epoch_index", "true", "pred_3ch", "pred_2EEG", "conf_3ch", "conf_2EEG"]].to_csv(
    EDGE / "docs" / "interp_channel_examples.csv", index=False)
print("\n10 example epochs where EOG rescued REM -> docs/interp_channel_examples.csv")
