"""SLEEPYLAND full-197: usleep, deepresnet, transformer sequentially, then ensemble (SOMNUS)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pandas as pd
from sleepyland_adapter import predict, ensemble, read_probs, MODEL_RUN, ENSEMBLE_RUN
from base import save_probs

TAB = HERE.parents[1] / "sleep-eda" / "tables"
stems = sorted(pd.read_parquet(TAB / "epochs_v3.parquet").stem.unique())

for model in ["usleep", "deepresnet", "transformer"]:
    run_id = MODEL_RUN[model]
    outdir = HERE.parent / "runs" / run_id
    done = {p.stem for p in outdir.glob("*.parquet")} if outdir.exists() else set()
    for i, s in enumerate(stems):
        if s in done:
            continue
        try:
            fn = predict(s, model=model)
            df = read_probs(fn, model, s)
            if df is not None:
                save_probs(df, run_id, s)
        except Exception as e:
            print(run_id, s, "FAIL", str(e)[:120], flush=True)
        if (i + 1) % 10 == 0:
            print(run_id, f"{i+1}/{len(stems)}", flush=True)

# SOMNUS ensemble over the three models
outdir = HERE.parent / "runs" / ENSEMBLE_RUN
done = {p.stem for p in outdir.glob("*.parquet")} if outdir.exists() else set()
for i, s in enumerate(stems):
    if s in done:
        continue
    try:
        fn = f"{s}_sl"
        ensemble(fn)
        df = read_probs(fn, "ensemble", s)
        if df is not None:
            save_probs(df, ENSEMBLE_RUN, s)
    except Exception as e:
        print("E06", s, "FAIL", str(e)[:120], flush=True)
    if (i + 1) % 10 == 0:
        print("E06", f"{i+1}/{len(stems)}", flush=True)
print("SLEEPYLAND sweep done")
