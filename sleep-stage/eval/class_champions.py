"""Class-level champions: which model best predicts each class, on ALL / SC / ST,
for BOTH evaluation windows (BENCHMARK_30 headline + full-valid).

Outputs:
  docs/class_champions.csv        long: window, subset, class, run, model, f1, recall, precision, ...
  docs/class_champions_top3.csv   top-3 per (window, subset, class) by F1
  docs/class_recall_champions.csv best-recall model per cell
  docs/CLASS_CHAMPIONS.md         readable artifact
"""
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE = HERE.parent
TAB = EDGE.parent / "sleep-eda" / "tables"
CL = ["Wake", "N1", "N2", "N3", "REM"]
lab = {c: i for i, c in enumerate(CL)}

RUNS = {
    "E11": "AnySleep 3ch", "E11d": "AnySleep Fpz+EOG", "E11c": "AnySleep 2EEG",
    "E11a": "AnySleep Fpz", "E11b": "AnySleep Pz", "E20": "RobustSleepNet",
    "E00": "LightGBM (ours)", "E02c": "YASA crop", "E01": "YASA Fpz",
    "E02": "YASA Fpz+EOG", "E03": "YASA Pz+EOG",
    "E16": "Ens 0.7ANY+0.3RSN+bias", "E17": "Ens ANYx3+LGBM", "E18": "Ens ANYx3+LGBM+bias",
    "E21": "U-Sleep CSDP (open)",
    "E19": "Ens v2 ANYx2+USleepCSDP+LGBM", "E19b": "Ens v2 +bias",
}

ep = pd.read_parquet(TAB / "epochs_v3.parquet")
g = ep[ep.valid & ep.label5.isin(CL)][["stem", "cohort", "epoch", "label5", "in_bench"]].rename(
    columns={"epoch": "epoch_index"})
g["label"] = g.label5.map(lab)
REF = {"valid": int(g.in_bench.notna().sum()), "bench": int(g.in_bench.sum())}

def load(run):
    fs = sorted((EDGE / "runs" / run).glob("*.parquet"))
    d = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    return d[["stem", "epoch_index"] + [f"p_{c}" for c in CL]]

def cls_stats(y, yp, i):
    tp = int(((yp == i) & (y == i)).sum()); fp = int(((yp == i) & (y != i)).sum()); fn = int(((yp != i) & (y == i)).sum())
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    return round(float(f1), 4), round(float(rec), 4), round(float(prec), 4), int((y == i).sum())

rows = []
for run, name in RUNS.items():
    m = load(run).merge(g, on=["stem", "epoch_index"], how="inner")
    for win in ["bench", "valid"]:
        w = m if win == "valid" else m[m.in_bench]
        for subset in ["ALL", "SC", "ST"]:
            s = w if subset == "ALL" else w[w.cohort == subset]
            if not len(s):
                continue
            y = s.label.values
            yp = s[[f"p_{c}" for c in CL]].values.argmax(1)
            for i, c in enumerate(CL):
                f1, rec, prec, sup = cls_stats(y, yp, i)
                rows.append({"window": win, "subset": subset, "class": c, "run": run, "model": name,
                             "f1": f1, "recall": rec, "precision": prec, "support": sup,
                             "n": len(s), "coverage": round(len(s) / REF[win], 3)})

df = pd.DataFrame(rows)
df.to_csv(EDGE / "docs" / "class_champions.csv", index=False)

top3 = (df.sort_values(["window", "subset", "class", "f1"], ascending=[True, True, True, False])
          .groupby(["window", "subset", "class"]).head(3).copy())
top3["rank"] = top3.groupby(["window", "subset", "class"]).cumcount() + 1
top3.to_csv(EDGE / "docs" / "class_champions_top3.csv", index=False)

best_rec = (df.sort_values(["window", "subset", "class", "recall"], ascending=[True, True, True, False])
              .groupby(["window", "subset", "class"]).head(1)[["window", "subset", "class", "run", "model", "recall"]])
best_rec.to_csv(EDGE / "docs" / "class_recall_champions.csv", index=False)

lines = ["# Class-level champions",
         "",
         "Per-class F1, champion = argmax F1 within each (window, subset, class).",
         "Best-recall model listed separately (high-recall expert option).",
         "`bench` = BENCHMARK_30 (237,936 epochs, headline); `valid` = all scored valid epochs.",
         "E17/E18 cover 237,310/237,936 bench epochs (LightGBM gaps); all other runs full.",
         ""]
for win, wname in [("bench", "BENCHMARK_30 (headline)"), ("valid", "FULL-VALID")]:
    lines += [f"# {wname}", ""]
    for subset in ["ALL", "SC", "ST"]:
        sub = df[(df.window == win) & (df.subset == subset)]
        lines += [f"## {subset}", "", "| Class | Champion | F1 | Recall | Precision | Runner-up | Best recall model |",
                  "|---|---|---|---|---|---|---|"]
        for c in CL:
            t = sub[sub["class"] == c].sort_values("f1", ascending=False)
            br = best_rec[(best_rec.window == win) & (best_rec.subset == subset) & (best_rec["class"] == c)].iloc[0]
            b = t.iloc[0]; r2 = t.iloc[1]
            lines.append(f"| {c} | **{b['model']}** ({b.run}) | {b.f1:.3f} | {b.recall:.3f} | {b.precision:.3f} | "
                         f"{r2['model']} ({r2.run}) {r2.f1:.3f} | {br.model} ({br.run}) {br.recall:.3f} |")
        lines.append("")
Path(EDGE / "docs" / "CLASS_CHAMPIONS.md").write_text("\n".join(lines), encoding="utf-8")

for win in ["bench", "valid"]:
    print(f"\n===== champions ({win}) =====")
    for subset in ["ALL", "SC", "ST"]:
        sub = df[(df.window == win) & (df.subset == subset)]
        print(f"-- {subset} --")
        for c in CL:
            t = sub[sub["class"] == c].sort_values("f1", ascending=False)
            line = " | ".join(f"{r.model} {r.f1:.3f}" for r in t.head(3).itertuples())
            print(f"{c:5s}: {line}")

print("\n===== N1 detail (bench), top 4 =====")
n1 = df[(df.window == "bench") & (df["class"] == "N1")].sort_values("f1", ascending=False).head(4)
print(n1[["subset", "model", "f1", "recall", "precision", "support"]].to_string(index=False))
print("\nartifacts: docs/class_champions.csv, class_champions_top3.csv, class_recall_champions.csv, CLASS_CHAMPIONS.md")
