"""24_rest: lights-off SOL/SE exact + per-subject fingerprints + WakeREM numbers. EDA only."""
import numpy as np, pandas as pd, re
from pathlib import Path
from datetime import datetime, timedelta
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from pyedflib import EdfReader
from edfio import read_edf
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables"); FIG=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\figs"); LLM=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\llm")
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
MAP={"Sleep stage W":"Wake","Sleep stage 1":"N1","Sleep stage 2":"N2","Sleep stage 3":"N3","Sleep stage 4":"N3","Sleep stage R":"REM","Sleep stage ?":"OTHER","Movement time":"OTHER"}

# --- 1 lights-off exact ---
sc=pd.read_excel(ROOT/"SC-subjects.xls")  # subject, night, age, sex, LightsOff(str HH:MM:SS)
def parse_lo(s):
    for f in ("%H:%M:%S","%H:%M"):
        try: return datetime.strptime(str(s).strip(),f)
        except: pass
    return None
rows=[]
for p in sorted(ROOT.rglob("*-PSG.edf")):
    stem=p.name[:6]; cohort="SC" if p.name.startswith("SC") else "ST"
    with EdfReader(str(p)) as f: start=f.getStartdatetime(); dur=f.getFileDuration()
    # lights-off
    lo=None
    if cohort=="SC":
        ss=int(p.name[3:5]); ng=int(p.name[5])
        m=sc[(sc.subject==ss)&(sc.night==ng)]
        if len(m): lo=parse_lo(m.iloc[0]["LightsOff"])
    else:
        st=pd.read_excel(ROOT/"ST-subjects.xls",header=None)
        # build once outside ideally; quick here
        pass
    rows.append((p.name,cohort,start,dur,lo))
# ST mapping
st=pd.read_excel(ROOT/"ST-subjects.xls",header=None)
cond_off={}
for i in range(2,len(st)):
    r=st.iloc[i]; nr=int(r[0])
    for night,col in [(int(r[3]),4),(int(r[5]),6)]:
        key=f"ST7{nr:02d}{night}"
        cond_off[key]=parse_lo(r[col])
# second pass attach ST lo + compute SOL (first sleep - max(start,lo))
e2=[]
for (fn,cohort,start,dur,lo) in rows:
    if cohort=="ST":
        lo=cond_off.get(fn[:6])
    # first sleep from hyp
    hyp=list((ROOT/("sleep-cassette" if cohort=="SC" else "sleep-telemetry")).glob(fn[:6]+"*-Hypnogram.edf"))[0]
    a=read_edf(str(hyp)); anns=sorted([(x.onset,x.duration,x.text) for x in a.annotations])
    ep=[]
    for o,d,t in anns: ep.extend([MAP.get(t,"OTHER")]*int(round(d/30)))
    idx=[i for i,t in enumerate(ep) if t in ("N1","N2","N3","REM")]
    first=idx[0] if idx else None
    sleep_dt=start+timedelta(seconds=first*30) if first is not None else None
    # lo datetime: same date as start, roll +1d if lo < start-time (cross midnight)
    lo_dt=None; sol=None; se_win=None
    if lo is not None:
        lo_dt=start.replace(hour=lo.hour,minute=lo.minute,second=lo.second,microsecond=0)
        if lo_dt<start: lo_dt+=timedelta(days=1)
        if sleep_dt is not None:
            sol=(sleep_dt-lo_dt).total_seconds()/60
        # SE window: lights-off -> last sleep epoch end (or recording end if earlier)
        last=idx[-1] if idx else 0
        end=min(start+timedelta(seconds=dur), start+timedelta(seconds=(last+1)*30))
        tib=(end-lo_dt).total_seconds()/60 if end>lo_dt else np.nan
        # TST from arch
        e2.append((fn,cohort,str(start),lo_dt.strftime("%Y-%m-%d %H:%M") if lo_dt else None,
                   round(sol,1) if sol is not None else None, round(tib,1) if isinstance(tib,float) else None))
pd.DataFrame(e2,columns=["psg_file","cohort","rec_start","lights_off","SOL_min","TIB_lightsOff_to_end_min"]).to_csv(TAB/"lights_off_sol.csv",index=False)
d=pd.read_csv(TAB/"lights_off_sol.csv")
print("SOL median SC/ST:"); print(d.groupby("cohort").SOL_min.median().to_string())
print("SOL pcts:",d.SOL_min.quantile([0.1,0.5,0.9]).to_string())
print("neg SOL (sleep before lights-off, clock/definition issues):",(d.SOL_min<0).sum(),d[d.SOL_min<0][["psg_file","SOL_min"]].head(5).to_string())

# --- 2 per-subject fingerprints from full parquets ---
base=pd.concat([pd.read_parquet(TAB/f"baseline_full_b{i}.parquet") for i in [0,1,2]],ignore_index=True)
pz=pd.concat([pd.read_parquet(TAB/f"pz_full_b{i}.parquet") for i in [0,1,2]],ignore_index=True)
m=base.merge(pz,on=["recording_id","epoch_index","label"],how="inner")
# per recording × stage medians
fp=m.groupby(["recording_id","label"])[["delta","theta","alpha","sigma","beta","eog_ptp","emg_rms","pz_delta","pz_alpha","pz_sigma"]].median().round(4)
fp.to_csv(TAB/"subject_fingerprints.csv")
print("fingerprints",fp.shape)

# --- 3 WakeREM numbers ---
w=m[m.label=="Wake"]; r=m[m.label=="REM"]
def fisher(a,b):
    return float((a.mean()-b.mean())**2/(a.var()+b.var()+1e-12))
feats=["delta","theta","alpha","sigma","beta","pz_delta","pz_alpha","eog_ptp","eog_std","emg_rms"]
fr={c:fisher(w[c],r[c]) for c in feats}
print("Wake-REM Fisher:",{k:round(v,3) for k,v in sorted(fr.items(),key=lambda x:-x[1])})
# overlap: Bhattacharyya-ish via histogram intersection on delta/theta
print("WakeREM medians Fpz:",w[["delta","theta"]].median().round(3).to_dict(),r[["delta","theta"]].median().round(3).to_dict())
print("WakeREM medians EOG/EMG:",w[["eog_ptp","emg_rms"]].median().round(1).to_dict(),r[["eog_ptp","emg_rms"]].median().round(1).to_dict())
# fig: overlapping hist Fpz-theta vs EOG-ptp
fig,ax=plt.subplots(1,2,figsize=(12,4))
ax[0].hist(w.theta,bins=60,range=(0,0.5),alpha=0.5,label="Wake",density=True)
ax[0].hist(r.theta,bins=60,range=(0,0.5),alpha=0.5,label="REM",density=True)
ax[0].legend(); ax[0].set_title("Fpz theta rel-power: Wake vs REM overlap (EEG-only ambiguity)")
ax[1].hist(np.log10(w.eog_ptp+1),bins=60,alpha=0.5,label="Wake",density=True)
ax[1].hist(np.log10(r.eog_ptp+1),bins=60,alpha=0.5,label="REM",density=True)
ax[1].legend(); ax[1].set_title("log EOG-ptp: Wake vs REM separates")
fig.tight_layout(); fig.savefig(FIG/"wake_rem_overlap.png",dpi=120); plt.close(fig)
# EMG hist
fig,ax=plt.subplots(figsize=(6,4))
ax.hist(np.log10(w.emg_rms+0.1),bins=60,alpha=0.5,label="Wake",density=True)
ax.hist(np.log10(r.emg_rms+0.1),bins=60,alpha=0.5,label="REM",density=True)
ax.legend(); ax.set_title("log EMG-rms: Wake vs REM (atonia axis)")
fig.tight_layout(); fig.savefig(FIG/"wake_rem_emg.png",dpi=120); plt.close(fig)
print("saved lights_off_sol, fingerprints, wake_rem figs")
