"""F1: authoritative onset-grid epochs + validity + 3 windows. Device python."""
import pandas as pd, numpy as np
from pathlib import Path
from datetime import timedelta
from pyedflib import EdfReader
from edfio import read_edf
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
MAP={"Sleep stage W":"Wake","Sleep stage 1":"N1","Sleep stage 2":"N2","Sleep stage 3":"N3","Sleep stage 4":"N3","Sleep stage R":"REM"}
SLEEP={"N1","N2","N3","REM"}

def load_hyp(h):
    e=read_edf(str(h)); return sorted([(a.onset,a.duration,a.text) for a in e.annotations])

# inspect the 2 gap files first
for stem in ["ST7121JE","ST7221JA"]:
    h=list(ROOT.rglob(stem+"-Hypnogram.edf"))[0]
    anns=load_hyp(h)
    print("====",h.name)
    for i in range(len(anns)-1):
        o1,d1,t1=anns[i]; o2,d2,t2=anns[i+1]
        if abs(o2-(o1+d1))>1e-6:
            print(f" break after idx {i}: ({o1},{d1},{t1}) -> ({o2},{d2},{t2}) gap={o2-(o1+d1)}s")
    print("n ann:",len(anns))

rows=[]; overlap_files=[]; gap_files=[]
for p in sorted(ROOT.rglob("*-PSG.edf")):
    stem=p.name[:6]; cohort="SC" if p.name.startswith("SC") else "ST"
    h=list(p.parent.glob(stem+"*-Hypnogram.edf"))[0]
    anns=load_hyp(h)
    # grid size from max end
    end_max=max(o+d for o,d,_ in anns); ngrid=int(round(end_max/30))
    grid=["GAP"]*ngrid; raw=["GAP"]*ngrid
    bad=False
    for o,d,t in anns:
        i0=int(round(o/30)); n=int(round(d/30))
        if abs(o-i0*30)>1e-6 or abs(d-n*30)>1e-6:
            print("NON30",p.name,o,d,t); bad=True
        for i in range(i0,min(i0+n,ngrid)):
            if grid[i]!="GAP": overlap_files.append((p.name,i,grid[i],t))
            grid[i]=MAP.get(t,"OTHER"); raw[i]=t
    # gaps
    gaps=[i for i,g in enumerate(grid) if g=="GAP"]
    if gaps: gap_files.append((p.name,len(gaps),gaps[:5]))
    with EdfReader(str(p)) as f:
        lab=[f.getLabel(k) for k in range(f.signals_in_file)]
        ns=f.samples_in_file(lab.index("EEG Fpz-Cz"))
    for i,g in enumerate(grid):
        valid_sig=(i+1)*3000<=ns
        valid_lab=g in ("Wake","N1","N2","N3","REM")
        rows.append((stem,cohort,p.name,i,raw[i],g,valid_sig,valid_lab))
print("files with overlaps:",len(overlap_files), overlap_files[:5])
print("files with gaps:",len(gap_files))
for g in gap_files: print(g)

df=pd.DataFrame(rows,columns=["stem","cohort","psg","epoch","raw","label5","valid_sig","valid_lab"])
df["valid"]=df.valid_sig&df.valid_lab
# windows per recording
df["in_bench"]=False; df["in_main"]=False
for stem,g in df.groupby("stem"):
    idx=g.index
    sl=g[g.label5.isin(SLEEP)&g.valid].index
    if len(sl)==0: continue
    f,l=sl.min(),sl.max()
    # benchmark: ±60 epochs on epoch numbers
    ep=g.loc[idx,"epoch"]
    df.loc[idx,"in_bench"]=(ep>=ep.loc[f]-60)&(ep<=ep.loc[l]+60)&g.valid
    # main: longest sleep run allowing <=40 wake/other gap epochs between valid sleep
    seq=g.loc[idx].reset_index()
    best=None; cur_s=None; cur_e=None; last_s=None; cur_len=0; best_len=-1
    # walk epochs in order, accumulate sleep count with gaps
    cur_sleep=0; cur_start=None; prev_ep=None
    runs=[]
    for _,r in seq.iterrows():
        s=1 if (r.label5 in SLEEP and r.valid) else 0
        if cur_start is None: cur_start=r.epoch; cur_sleep=s; cur_n=1; prev_ep=r.epoch; continue
        if r.epoch==prev_ep+1:
            cur_sleep+=s; cur_n+=1
        else:
            runs.append((cur_start,prev_ep,cur_sleep,cur_n)); cur_start=r.epoch; cur_sleep=s; cur_n=1
        prev_ep=r.epoch
    runs.append((cur_start,prev_ep,cur_sleep,cur_n))
    # merge runs separated by gaps? grid contiguous so one run; instead find densest sub-interval:
    # longest interval with sleep density>=0.5: use sleep indicator array over full span
    arr=seq.set_index("epoch")
    full_idx=range(seq.epoch.min(),seq.epoch.max()+1)
    s=np.array([1 if (i in arr.index and arr.loc[i,"label5"] in SLEEP and arr.loc[i,"valid"]) else 0 for i in full_idx])
    # longest subarray with mean>=0.5 <=> maximize sum(2s-1)
    b=np.where(s==1,1,-1); best_l=best_r=0; bl=0; bsum=0; bb=-10**9
    cur_l=0; cur=0
    for i,v in enumerate(b):
        if cur+v<v: cur=v; cur_l=i
        else: cur+=v
        if cur>bb: bb=cur; best_l=cur_l; best_r=i
    a_ep=list(full_idx)[best_l]; b_ep=list(full_idx)[best_r]
    df.loc[idx,"in_main"]=(ep>=a_ep-60)&(ep<=b_ep+60)&g.valid
df.to_parquet(TAB/"epochs_authoritative.parquet",index=False)
print("epochs:",len(df),"valid:",df.valid.sum(),"bench:",df.in_bench.sum(),"main:",df.in_main.sum())
print(df.groupby("cohort")[["valid","in_bench","in_main"]].sum().to_string())
