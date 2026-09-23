"""F3: per-window transitions, ST marker decode->quality mask, quality in windows, clipping audit."""
import pandas as pd, numpy as np
from pathlib import Path
from pyedflib import EdfReader
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
ep=pd.read_parquet(TAB/"epochs_authoritative.parquet")
L5=["Wake","N1","N2","N3","REM"]

print("=== transitions per window x cohort (valid labels only) ===")
for w in ["valid","in_bench","in_main"]:
    for co in ["SC","ST"]:
        d=ep[(ep[w])&(ep.cohort==co)&(ep.label5.isin(L5))].sort_values(["stem","epoch"])
        # transitions within same stem consecutive valid epochs
        prev=d.label5.shift(); same_stem=d.stem.shift()==d.stem
        consec=(d.epoch-d.epoch.shift()==1)&same_stem
        t=d[consec].groupby([prev[consec],"label5"]).size().unstack(fill_value=0)
        t=t.reindex(index=L5,columns=L5,fill_value=0)
        rowsum=t.sum(1).replace(0,np.nan)
        print(f"-- {w}/{co} self:",{a:round(float(t.loc[a,a]/rowsum[a]),3) for a in L5})
        t.to_csv(TAB/f"trans_{w}_{co}.csv")

print("=== ST marker decode ===")
# read Marker values distribution + error code hypothesis (negative = telemetry error per doc)
rows=[]
for p in sorted((ROOT/"sleep-telemetry").glob("ST*-PSG.edf"))[:6]:
    with EdfReader(str(p)) as f:
        lab=[f.getLabel(k) for k in range(f.signals_in_file)]
        k=lab.index("Marker")
        x=np.array(f.readSignal(k),dtype=np.float64)
        u,c=np.unique(x,return_counts=True)
        print(p.name,"nuniq",len(u),"top:",sorted(zip(c,u),reverse=True)[:6])
        rows.append((p.name,len(u)))
# full: fraction negative (error) per rec + correlate with flat rate from cleanliness
clean=pd.read_csv(TAB/"cleanliness_all.csv")
negfrac={}
for p in sorted((ROOT/"sleep-telemetry").glob("ST*-PSG.edf")):
    with EdfReader(str(p)) as f:
        lab=[f.getLabel(k) for k in range(f.signals_in_file)]
        x=np.array(f.readSignal(lab.index("Marker")),dtype=np.float64)
        negfrac[p.name]=(x<0).mean()
nf=pd.DataFrame(list(negfrac.items()),columns=["file","marker_neg_frac"])
m=clean[clean.cohort=="ST"].groupby("file").flat1s_rate.mean().reset_index()
mm=nf.merge(m,on="file")
print("corr(marker_neg_frac, flat1s):",mm[["marker_neg_frac","flat1s_rate"]].corr().to_string())
print(mm.sort_values("marker_neg_frac",ascending=False).head(8).to_string())
mm.to_csv(TAB/"marker_quality.csv",index=False)

print("=== quality in windows (ST, EEG Fpz-Cz jump/flat sampled 20x1min within labelled span) ===")
# labelled span per rec from authoritative epochs
res=[]
for p in sorted((ROOT/"sleep-telemetry").glob("ST*-PSG.edf")):
    stem=p.name[:6]
    g=ep[(ep.stem==stem)&(ep.valid)]
    lo,hi=g.epoch.min(),g.epoch.max()
    with EdfReader(str(p)) as f:
        lab=[f.getLabel(k) for k in range(f.signals_in_file)]
        k=lab.index("EEG Fpz-Cz")
        x=np.array(f.readSignal(k,lo*3000,(hi-lo+1)*3000),dtype=np.float64)
        d=np.abs(np.diff(x[::10]))
        flat=np.mean([np.ptp(x[i*100:(i+1)*100])<1.0 for i in range(0,len(x)//100,10)])
        res.append((p.name,float(np.mean(d>1500)),float(flat)))
q=pd.DataFrame(res,columns=["file","jump_labelled","flat_labelled"])
print(q.describe().to_string())
print("vs full-record flats median:",clean[clean.cohort=="ST"].flat1s_rate.median())
q.to_csv(TAB/"quality_labelled_ST.csv",index=False)

print("=== clipping audit vs digital limits (all 197, 100Hz chs) ===")
out=[]
for p in sorted(ROOT.rglob("*-PSG.edf")):
    with EdfReader(str(p)) as f:
        lab=[f.getLabel(k) for k in range(f.signals_in_file)]
        for k in range(f.signals_in_file):
            if f.getSampleFrequency(k)!=100: continue
            dmin=f.getDigitalMinimum(k); dmax=f.getDigitalMaximum(k)
            x=np.array(f.readSignal(k),dtype=np.float64)
            # digital values: use readSignal digital? approximate via phys range saturation at pmin/pmax
            pmin=f.getPhysicalMinimum(k); pmax=f.getPhysicalMaximum(k)
            sat=float(np.mean((x<=pmin+1e-9)|(x>=pmax-1e-9)))
            out.append((p.name,lab[k],sat))
c=pd.DataFrame(out,columns=["file","ch","sat_frac"])
print("max sat_frac:",c.sat_frac.max())
print(c.sort_values("sat_frac",ascending=False).head(8).to_string())
c.to_csv(TAB/"clipping_audit.csv",index=False)
print("saved trans_*, marker_quality, quality_labelled_ST, clipping_audit")
