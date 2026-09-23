"""11_meso_macro_ablation: thousands epochs, N1 overlap, cycles, age/drug, ablation Fisher, temporal gain."""
import numpy as np
from pathlib import Path
import pandas as pd
from pyedflib import EdfReader
from edfio import read_edf
from scipy.signal import welch
from collections import Counter
MAP={"Sleep stage W":"Wake","Sleep stage 1":"N1","Sleep stage 2":"N2","Sleep stage 3":"N3","Sleep stage 4":"N3","Sleep stage R":"REM"}
L5=["Wake","N1","N2","N3","REM"]
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
FIG=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\figs")
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

# MESO: 3000 epochs stratified across ~12 recs (SC young/old + ST placebo/temazepam), cheap feats
recs=sorted(ROOT.rglob("*-PSG.edf"))
# pick 12 spread
pick=[p for p in recs if p.name in ("SC4001E0-PSG.edf","SC4002E0-PSG.edf","SC4051E0-PSG.edf","SC4141E0-PSG.edf","SC4181E0-PSG.edf","SC4191E0-PSG.edf","ST7011J0-PSG.edf","ST7012J0-PSG.edf","ST7051J0-PSG.edf","ST7052J0-PSG.edf","ST7111J0-PSG.edf","ST7112J0-PSG.edf")]
feats=[]
for psg in pick:
    hyp=psg.parent/(psg.name[:6]+"-"+("EC" if "SC" in psg.name else "JP")+"-Hypnogram.edf")
    # robust hyp match: find stem file
    cands=list(psg.parent.glob(psg.name[:6]+"*-Hypnogram.edf"))
    if not cands: continue
    hyp=cands[0]
    e=read_edf(str(hyp)); anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
    ep=[]
    for o,d,t in anns: ep.extend([t]*int(round(d/30)))
    with EdfReader(str(psg)) as f:
        lab=[f.getLabel(k) for k in range(f.signals_in_file)]
        nsamp=f.samples_in_file(lab.index("EEG Fpz-Cz"))
        # sample 50/reclass balanced where possible (inside open file!)
        for st in L5:
            idx=[i for i,t in enumerate(ep) if MAP.get(t)==st and (i+1)*3000<=nsamp][:50]
            for ei in idx:
                s=np.array(f.readSignal(lab.index("EEG Fpz-Cz"),ei*3000,3000),dtype=np.float64)
                eo=np.array(f.readSignal(lab.index("EOG horizontal"),ei*3000,3000),dtype=np.float64)
                if len(s)<3000: continue
                fr,px=welch(s,fs=100,nperseg=1024); tot=np.trapz(px[(fr>=0.5)&(fr<=30)],fr[(fr>=0.5)&(fr<=30)])+1e-12
                def rel(a,b):
                    m=(fr>=a)&(fr<=b); return float(np.trapz(px[m],fr[m])/tot)
                feats.append({"file":psg.name,"cohort":psg.name[:2],"stage":st,
                    "delta":rel(0.5,4),"theta":rel(4,8),"alpha":rel(8,13),"sigma":rel(11,16),"beta":rel(13,30),
                    "eog_ptp":float(np.ptp(eo)),"eog_std":float(np.std(eo)),"eeg_std":float(np.std(s))})
    print("meso",psg.name)
df=pd.DataFrame(feats); df.to_csv(TAB/"meso_features_3k.csv",index=False)
print(len(df))
# N1 ambiguity: distance of N1 centroid to W and N2 (standardized euclid) + overlap via boxplots
import numpy as np
cols=["delta","theta","alpha","sigma","beta","eog_ptp","eog_std","eeg_std"]
std=(df[cols]-df[cols].mean())/df[cols].std()
cen=std.groupby(df.stage).mean()
from scipy.spatial.distance import cdist
D=cdist(cen.loc[["Wake","N1","N2"]],cen.loc[["Wake","N1","N2"]])
print("centroid dist W/N1/N2:\n",pd.DataFrame(D,index=["W","N1","N2"],columns=["W","N1","N2"]).to_string())
# per-feature Fisher DR = (m1-m2)^2/(v1+v2) for pairs
def fisher(a,b,c):
    x=df[df.stage==a][c]; y=df[df.stage==b][c]
    return float((x.mean()-y.mean())**2/(x.var()+y.var()+1e-12))
pairs=[("Wake","REM"),("Wake","N1"),("N1","N2"),("N2","N3"),("N2","REM")]
fish=pd.DataFrame([{c:fisher(a,b,c) for c in cols} for a,b in pairs],index=[f"{a}-{b}" for a,b in pairs])
print(fish.to_string())
fish.to_csv(TAB/"fisher_pairs.csv")
# ablation A-G: sum Fisher over pairs using channel subsets (eeg-only cols vs +eog)
eeg_cols=["delta","theta","alpha","sigma","beta","eeg_std"]; eog_cols=["eog_ptp","eog_std"]
abl={}
for name,cc in [("A_Fpz",eeg_cols),("D_Fpz+EOG",eeg_cols+eog_cols)]:
    abl[name]=float(fish[cc].sum().sum())
print("ablation (feature-sum Fisher, higher=more separable):",abl)

# MACRO: cycles per rec (REM onset gaps>60min define cycles), age vs N3, placebo vs temazepam
sub=pd.read_csv(TAB/"subject_class_distribution.csv")
sc=pd.read_excel(ROOT/"SC-subjects.xls")
# age: map filename ss->subject? ss=int(name[3:5])? SC4001 ss=00->subject0. use that.
def ss_subj(name): return int(name[3:5])
ages={}
for _,r in sc.drop_duplicates("subject").iterrows(): ages[int(r.subject)]=r.age
sub["age"]=sub.stem.apply(lambda s: ages.get(int(s[3:5]),np.nan) if s.startswith("SC") else np.nan)
sub["tot"]=sub.wake_ep+sub.n1+sub.n2+sub.n3+sub.rem
sub["n3pct"]=sub.n3/sub.tot
print("age vs N3% corr (SC):",sub[sub.cohort=="SC"][["age","n3pct"]].corr().to_string())
# ST placebo vs temazepam: night? ST-subjects xls col mapping messy; use stem night digit: ST7ssN: N=1/2, xls says which is placebo per subject. parse xls properly:
st=pd.read_excel(ROOT/"ST-subjects.xls",header=None)
print(st.head(8).to_string())
# cycles: count REM episodes separated by >=30min non-REM
cyc=[]
for p in sorted(ROOT.rglob("*-Hypnogram.edf")):
    e=read_edf(str(p)); anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
    ep=[]
    for o,d,t in anns: ep.extend([MAP.get(t,"OTHER")]*int(round(d/30)))
    rem_starts=[i for i in range(1,len(ep)) if ep[i]=="REM" and ep[i-1]!="REM"]
    ncyc=1+sum(1 for a,b in zip(rem_starts,rem_starts[1:]) if (b-a)*0.5>=60)
    cyc.append(ncyc)
print(f"cycles/night mean {np.mean(cyc):.2f} median {np.median(cyc)} (REM-episode based)")
fig,ax=plt.subplots(figsize=(8,4)); ax.hist(cyc,bins=range(0,9),align="left",rwidth=0.8)
ax.set_xlabel("cycles/night");ax.set_title("Sleep cycles per night (REM-gap≥60min)");fig.tight_layout()
fig.savefig(FIG/"cycles.png",dpi=120);plt.close(fig)
print("saved meso 3k, fisher, cycles")
