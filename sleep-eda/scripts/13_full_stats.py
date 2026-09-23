"""13_full_stats: ALL 197 recs x all channels, one rec at a time. Fast time-domain only."""
import numpy as np
from pathlib import Path
import pandas as pd
from pyedflib import EdfReader
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
import sys
batch=int(sys.argv[1]) if len(sys.argv)>1 else 0  # 0:SC, 1:ST
psgs=sorted(ROOT.rglob("*-PSG.edf"))
psgs=[p for p in psgs if (p.name.startswith("SC") and batch==0) or (p.name.startswith("ST") and batch==1)]
print(f"batch {batch}: {len(psgs)} files")
rows=[]
for pi,p in enumerate(psgs):
    try:
        with EdfReader(str(p)) as f:
            n=f.signals_in_file
            for k in range(n):
                lab=f.getLabel(k); sf=f.getSampleFrequency(k)
                x=np.array(f.readSignal(k),dtype=np.float64)
                # decimate for percentiles on 100Hz to save time
                xd=x[::10] if len(x)>100000 else x
                rows.append({"file":p.name,"cohort":p.name[:2],"channel":lab,"sf":sf,"n":len(x),
                    "mean":float(x.mean()),"std":float(x.std()),"rms":float(np.sqrt(np.mean(x**2))),
                    "min":float(x.min()),"max":float(x.max()),
                    "p1":float(np.percentile(xd,1)),"p99":float(np.percentile(xd,99)),
                    "nan":int(np.isnan(x).sum()),"flat_frac":float(np.mean(np.abs(np.diff(xd))<1e-12))})
    except Exception as e:
        print("FAIL",p.name,str(e)[:120])
    if (pi+1)%20==0: print(f"{pi+1}/{len(psgs)}",flush=True)
    # incremental save
    if (pi+1)%40==0:
        pd.DataFrame(rows).to_csv(TAB/f"signal_stats_full_b{batch}.csv",index=False)
pd.DataFrame(rows).to_csv(TAB/f"signal_stats_full_b{batch}.csv",index=False)
print("saved",len(rows))
