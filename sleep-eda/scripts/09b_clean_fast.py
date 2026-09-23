"""09b: fast sampled cleanliness (20x1min windows per PSG)."""
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pyedflib import EdfReader

ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables"); FIG=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\figs")
psgs=sorted(ROOT.rglob("*-PSG.edf"))
rows=[]
for pi,p in enumerate(psgs):
    cohort="SC" if p.name.startswith("SC") else "ST"
    thr=500 if cohort=="SC" else 1500
    try:
        with EdfReader(str(p)) as f:
            n=f.signals_in_file; labels=[f.getLabel(k) for k in range(n)]
            sfs=[f.getSampleFrequency(k) for k in range(n)]
            dur=f.getFileDuration()
            for k in range(n):
                if sfs[k]!=100: continue
                sf=int(sfs[k]); total=int(dur*sf)
                wins=np.linspace(0,total-sf*60,20).astype(int)
                jr=[]; fl=0; tot=0; stds=[]
                for s in wins:
                    x=np.array(f.readSignal(k,s,sf*60),dtype=np.float64)
                    d=np.abs(np.diff(x))
                    jr.append(float(np.mean(d>thr)))
                    # flat 1s within window
                    for w0 in range(0,60):
                        seg=x[w0*sf:(w0+1)*sf]
                        tot+=1
                        if np.ptp(seg)<1.0: fl+=1
                    stds.append(float(np.std(x)))
                rows.append({"file":p.name,"cohort":cohort,"ch":labels[k],
                    "jump_rate":float(np.mean(jr)),"flat1s_rate":fl/max(1,tot),
                    "std_med":float(np.median(stds))})
    except Exception as e:
        print("FAIL",p.name,str(e)[:100])
    if (pi+1)%25==0: print(f"{pi+1}/{len(psgs)}",flush=True)
q=pd.DataFrame(rows); q.to_csv(TAB/"cleanliness_all.csv",index=False)
print(q.groupby(["cohort","ch"])[["jump_rate","flat1s_rate"]].median().to_string())
print("worst jumps:"); print(q.sort_values("jump_rate",ascending=False).head(8).to_string())
print("worst flats:"); print(q.sort_values("flat1s_rate",ascending=False).head(8).to_string())
fig,ax=plt.subplots(figsize=(8,5))
for c in ["SC","ST"]:
    s=q[q.cohort==c]
    ax.scatter(s.flat1s_rate,s.jump_rate,alpha=0.4,label=c,s=12)
ax.set_xlabel("flat-1s rate (sampled)");ax.set_ylabel("jump rate (sampled)");ax.legend()
ax.set_title("Cleanliness sampled audit (20×1min/night)");fig.tight_layout()
fig.savefig(FIG/"cleanliness.png",dpi=120);plt.close(fig)
print("saved")
