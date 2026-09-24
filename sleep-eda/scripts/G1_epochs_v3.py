"""G1: v3 epochs — onset grid, independent masks, LO-anchored MAIN, epoch quality. Device python."""
import pandas as pd, numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from pyedflib import EdfReader
from edfio import read_edf
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\SleepLens\sleep-eda\tables")
MAP={"Sleep stage W":"Wake","Sleep stage 1":"N1","Sleep stage 2":"N2","Sleep stage 3":"N3","Sleep stage 4":"N3","Sleep stage R":"REM"}
SLEEP={"N1","N2","N3","REM"}
TOL=timedelta(hours=3)
def plo(s): return datetime.strptime(str(s).strip(),"%H:%M:%S")
sc=pd.read_excel(ROOT/"SC-subjects.xls")
st=pd.read_excel(ROOT/"ST-subjects.xls",header=None)
off={}; 
for i in range(2,len(st)):
    r=st.iloc[i]
    off[f"ST7{int(r[0]):02d}{int(r[3])}"]=plo(r[4]); off[f"ST7{int(r[0]):02d}{int(r[5])}"]=plo(r[6])
def resolve_lo(start, lot):
    cand=start.replace(hour=lot.hour,minute=lot.minute,second=lot.second,microsecond=0)
    if cand<start and (start-cand)<TOL: return cand
    if cand<start: return cand+timedelta(days=1)
    return cand

def episodes(df):
    """sleep episodes over grid order; bridge non-sleep <20 epochs. Returns list of (start_ep,end_ep,sleep_count)."""
    eps=[]; cs=None; ce=None; csl=0; gap=0
    for _,r in df.iterrows():
        s=1 if (r.label5 in SLEEP and r.valid_stage and r.valid_signal) else 0
        if cs is None:
            if s: cs=ce=r.epoch; csl=1; gap=0
            continue
        if r.epoch==ce+1:
            if s: ce=r.epoch; csl+=1; gap=0
            else:
                gap+=1
                if gap>=20:
                    if csl>0: eps.append((cs,ce,csl))
                    cs=None; csl=0; gap=0
                else: ce=r.epoch
        else:  # grid jump (shouldn't happen; close)
            if csl>0: eps.append((cs,ce,csl))
            cs=r.epoch if s else None; ce=r.epoch if s else None; csl=1 if s else 0; gap=0
    if cs is not None and csl>0: eps.append((cs,ce,csl))
    return eps

all_ep=[]; all_q=[]; winrows=[]
for p in sorted(ROOT.rglob("*-PSG.edf")):
    stem=p.name[:6]; co="SC" if p.name.startswith("SC") else "ST"
    h=list(p.parent.glob(stem+"*-Hypnogram.edf"))[0]
    e=read_edf(str(h)); anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
    end_max=max(o+d for o,d,_ in anns); ngrid=int(round(end_max/30))
    grid=["GAP"]*ngrid; raw=["GAP"]*ngrid
    for o,d,t in anns:
        i0=int(round(o/30)); n=int(round(d/30))
        for i in range(i0,min(i0+n,ngrid)):
            grid[i]=MAP.get(t,"OTHER"); raw[i]=t
    with EdfReader(str(p)) as f:
        lab=[f.getLabel(k) for k in range(f.signals_in_file)]
        sfs={lab[k]:f.getSampleFrequency(k) for k in range(f.signals_in_file)}
        ns=f.samples_in_file(lab.index("EEG Fpz-Cz"))
        start=f.getStartdatetime()
        # epoch quality: ST marker-neg frac + flat-1s frac per 100Hz ch (vectorized per rec)
        chs100=[l for l in lab if sfs[l]==100]
        sigs={l:np.array(f.readSignal(lab.index(l)),dtype=np.float64) for l in chs100}
        marker=None
        mk=[l for l in lab if "ark" in l]
        if mk: marker=np.array(f.readSignal(lab.index(mk[0])),dtype=np.float64)
        mksf=sfs[mk[0]] if mk else None
    # LO
    if co=="SC":
        ss=int(stem[3:5]); ng=int(stem[5])
        lot=plo(sc[(sc.subject==ss)&(sc.night==ng)].iloc[0]["LightsOff"])
    else: lot=off[stem]
    lo=resolve_lo(start,lot)
    lo_ep=(lo-start).total_seconds()/30
    df=pd.DataFrame({"stem":stem,"cohort":co,"epoch":np.arange(ngrid),"raw":raw,"label5":grid})
    df["valid_signal"]=df.epoch.apply(lambda i:(i+1)*3000<=ns)
    df["valid_stage"]=df.label5.isin(["Wake","N1","N2","N3","REM"])
    df["valid"]=df.valid_signal&df.valid_stage
    # episodes + classification vs LO
    eps=episodes(df)
    naps=[]; early=None; primary=None
    cands=[e for e in eps if e[1]>=lo_ep-60]
    if cands: primary=max(cands,key=lambda e:e[2])
    for (a,b,c) in eps:
        if b<lo_ep-60: naps.append((a,b,c))
        elif primary and (a,b,c)!=(primary) and False: pass
    # early-onset: primary starts before LO (sleep continuous across LO) or nap within 60ep gap merging
    early_min=None
    if primary and primary[0]<lo_ep:
        early_min=(lo_ep-primary[0])*0.5
    # MAIN window: [LO, primary_end+60] (+60 margin end only; start=LO opportunity)
    if primary:
        wstart=int(max(0,np.floor(lo_ep))); wend=int(primary[1]+60)
    else:
        wstart=int(max(0,np.floor(lo_ep))); wend=ngrid-1
    df["in_main_window"]=(df.epoch>=wstart)&(df.epoch<=wend)
    # benchmark: first/last valid sleep ±60
    sl=df[df.valid&df.label5.isin(SLEEP)]
    if len(sl):
        f0,l0=sl.epoch.min(),sl.epoch.max()
        df["in_bench"]=(df.epoch>=f0-60)&(df.epoch<=l0+60)&df.valid
    else: df["in_bench"]=False
    all_ep.append(df)
    # quality rows (only epochs with signal)
    n_ep=ns//3000
    flat={l:np.zeros(n_ep) for l in chs100}
    for l in chs100:
        x=sigs[l][:n_ep*3000].reshape(n_ep,3000)
        w1=x.reshape(n_ep*30,100)
        fl=(np.ptp(w1,axis=1)<1.0).reshape(n_ep,30).mean(1)
        flat[l]=fl
    sat={}
    for l in chs100:
        x=sigs[l][:n_ep*3000]
        sat[l]=np.zeros(n_ep)  # phys-limit sat needs header; do coarse: |x|>=pmax? use per-rec max proxy later
    if marker is not None:
        per=int(mksf*30); nm=len(marker)//per
        mn=(marker[:nm*per].reshape(nm,per)<0).mean(1)
    for i in range(min(n_ep,ngrid)):
        all_q.append((stem,i,
            float(mn[i]) if marker is not None and i<len(mn) else np.nan,
            *[float(flat[l][i]) for l in ["EEG Fpz-Cz","EEG Pz-Oz","EOG horizontal","EMG submental"] if l in flat]))
    winrows.append((stem,co,lo.strftime("%Y-%m-%d %H:%M"),wstart,wend,
                    len(naps),sum(c for _,_,c in naps)*0.5 if naps else 0,
                    round(early_min,1) if early_min else None,
                    primary[0] if primary else None,primary[1] if primary else None,primary[2]*0.5 if primary else None))
    if len(winrows)%40==0: print(len(winrows),flush=True)

ep3=pd.concat(all_ep,ignore_index=True)
ep3.to_parquet(TAB/"epochs_v3.parquet",index=False)
q=pd.DataFrame(all_q,columns=["stem","epoch","telemetry_neg_frac","flat_fpz","flat_pz","flat_eog","flat_emg"])
q.to_parquet(TAB/"epoch_quality_v3.parquet",index=False)
w=pd.DataFrame(winrows,columns=["stem","cohort","lights_off","main_start_ep","main_end_ep","n_naps","nap_sleep_min","early_min","primary_start","primary_end","primary_sleep_min"])
w.to_csv(TAB/"sleep_windows_v3.csv",index=False)
print("v3 epochs:",len(ep3),"in_main_window:",ep3.in_main_window.sum(),"bench:",ep3.in_bench.sum())
print("naps>0:",(w.n_naps>0).sum(),"/197  early non-null:",w.early_min.notna().sum())
