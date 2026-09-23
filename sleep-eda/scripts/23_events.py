"""23_events_transitions: full spindle/K/slow/eye/atonia/arousal-proxy + transition ambiguity + age/drug. EDA only."""
import numpy as np, pandas as pd
from pathlib import Path
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from pyedflib import EdfReader
from edfio import read_edf
from scipy.signal import butter, filtfilt
MAP={"Sleep stage W":"Wake","Sleep stage 1":"N1","Sleep stage 2":"N2","Sleep stage 3":"N3","Sleep stage 4":"N3","Sleep stage R":"REM","Sleep stage ?":"OTHER","Movement time":"OTHER"}
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables"); FIG=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\figs")
def bp(x,sf,lo,hi,o=4):
    b,a=butter(o,[lo/(sf/2),hi/(sf/2)],btype="band"); return filtfilt(b,a,x)

psgs=sorted(ROOT.rglob("*-PSG.edf"))
ev=[]; trans_rows=[]
for pi,psg in enumerate(psgs):
    hyp=list(psg.parent.glob(psg.name[:6]+"*-Hypnogram.edf"))[0]
    e=read_edf(str(hyp)); anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
    ep=[]
    for o,d,t in anns: ep.extend([MAP.get(t,"OTHER")]*int(round(d/30)))
    with EdfReader(str(psg)) as f:
        lab=[f.getLabel(k) for k in range(f.signals_in_file)]
        ns=f.samples_in_file(lab.index("EEG Fpz-Cz"))
        ne=min(len(ep),ns//3000)
        E=np.array(f.readSignal(lab.index("EEG Fpz-Cz"),0,ne*3000),dtype=np.float64).reshape(ne,3000)
        O=np.array(f.readSignal(lab.index("EOG horizontal"),0,ne*3000),dtype=np.float64).reshape(ne,3000)
        kE=lab.index("EMG submental"); sfE=f.getSampleFrequency(kE)
        Mrs=int(sfE*30)
        M=np.array(f.readSignal(kE,0,ne*Mrs),dtype=np.float64).reshape(ne,Mrs)
        # per-epoch detectors (vectorized where possible)
        sig_rms=np.sqrt(np.mean(bp(E.ravel(),100,11,16).reshape(ne,3000)**2,1))  # slow; ok
        slow=bp(E.ravel(),100,0.5,4).reshape(ne,3000)
        sw_amp=np.percentile(np.abs(slow),99,axis=1)
        kmin=E.min(1); estd=E.std(1)
        eog_ptp=np.ptp(O,axis=1)
        # eye velocity proxy: max |diff| (rapid vs slow)
        eog_vel=np.abs(np.diff(O,axis=1)).max(1)
        emg_rms=np.sqrt((M**2).mean(1))
        beta_rms=np.sqrt(np.mean(bp(E.ravel(),100,13,30).reshape(ne,3000)**2,1))
        labs=np.array(ep[:ne])
        # transition-adjacent flag
        is_trans=np.zeros(ne,bool); is_trans[1:]=labs[1:]!=labs[:-1]; is_trans[:-1]|=labs[:-1]!=labs[1:]
        for i in range(ne):
            ev.append((psg.name[:2],labs[i],float(sig_rms[i]),float(sw_amp[i]),float(kmin[i]/ (estd[i]+1e-9)),
                       float(eog_ptp[i]),float(eog_vel[i]),float(emg_rms[i]),float(beta_rms[i]),bool(is_trans[i])))
    if (pi+1)%25==0: print(f"{pi+1}/{len(psgs)}",flush=True)
ev=pd.DataFrame(ev,columns=["cohort","label","spindle_rms","slow_p99","k_zmin","eog_ptp","eog_vel","emg_rms","beta","is_trans"])
ev.to_parquet(TAB/"events_full.parquet",index=False)
print("events",len(ev))
g=ev.groupby("label")[["spindle_rms","slow_p99","eog_vel","emg_rms","beta"]].median()
print(g.round(3).to_string())
# rates: spindle-like (spindle_rms>uppercase per-cohort 75pct of N2?), K-like (k_zmin<-3), arousal-proxy (beta>2x median N2 beta & emg jump)
thr_sp=ev[ev.label=="N2"].spindle_rms.quantile(0.6)
thr_k=-3.0
med_beta_n2=ev[ev.label=="N2"].beta.median()
ev["spindle_like"]=ev.spindle_rms>thr_sp
ev["k_like"]=ev.k_zmin<-3.0
ev["arousal_proxy"]= (ev.beta>2*med_beta_n2)
print("rates by stage:"); print(ev.groupby("label")[["spindle_like","k_like","arousal_proxy"]].mean().round(3).to_string())
# transition vs stable
print("trans fraction by stage:"); print(ev.groupby("label").is_trans.mean().round(3).to_string())
print("feature median trans vs stable:")
print(ev.groupby("is_trans")[["spindle_rms","slow_p99","eog_vel","beta"]].median().round(3).to_string())
# age curves (SC): N3%, WASO, SE vs age deciles
sub=pd.read_csv(TAB/"subject_class_distribution.csv"); arch=pd.read_csv(TAB/"sleep_architecture.csv")
sc_x=pd.read_excel(ROOT/"SC-subjects.xls")
age_map={int(r.subject):r.age for _,r in sc_x.drop_duplicates("subject").iterrows()}
sub["age"]=sub.stem.apply(lambda s: age_map.get(int(s[3:5])) if s.startswith("SC") else np.nan)
sub["tot"]=sub.wake_ep+sub.n1+sub.n2+sub.n3+sub.rem
sub["n3pct"]=sub.n3/sub.tot
scsub=sub[sub.cohort=="SC"].dropna(subset=["age"])
scsub["dec"]=pd.cut(scsub.age,bins=[20,40,60,80,110])
print(scsub.groupby("dec",observed=True)[["n3pct"]].mean().round(4).to_string())
fig,ax=plt.subplots(figsize=(8,4)); ax.scatter(scsub.age,scsub.n3pct*100,alpha=0.4,s=10)
ax.set_xlabel("age"); ax.set_ylabel("N3%"); ax.set_title("N3% vs age (SC, full)"); fig.tight_layout(); fig.savefig(FIG/"age_n3.png",dpi=120); plt.close(fig)
# drug paired (ST): match subject prefix nights
stsub=sub[sub.cohort=="ST"].copy()
# need placebo vs temazepam mapping from ST-subjects: night digit vs condition
st_x=pd.read_excel(ROOT/"ST-subjects.xls",header=None)
cond={}
for i in range(2,len(st_x)):
    r=st_x.iloc[i]; nr=int(r[0])
    cond[f"ST7{nr:02d}1"]=("placebo" if int(r[3])==1 else "temazepam")
    cond[f"ST7{nr:02d}2"]=("placebo" if int(r[3])==2 else "temazepam")
stsub["cond"]=stsub.stem.str[:6].map(cond)
print(stsub.groupby("cond")[["n_epochs","wake_ep","n1","n2","n3","rem"]].mean().round(1).to_string())
print("saved events_full + age/drug")
