"""F4: EMG harmonize ST->1Hz envelope + separation check; norm/filter evidence; robust 5-fold."""
import pandas as pd, numpy as np
from pathlib import Path
from pyedflib import EdfReader
from scipy.signal import welch
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
ep=pd.read_parquet(TAB/"epochs_authoritative.parquet")

print("=== EMG harmonize: ST raw -> 1Hz RMS envelope vs SC envelope, Wake/REM ===")
rows=[]
for p in sorted(ROOT.rglob("*-PSG.edf")):
    stem=p.name[:6]; co="SC" if p.name.startswith("SC") else "ST"
    g=ep[(ep.stem==stem)&(ep.valid)&(ep.label5.isin(["Wake","REM"]))]
    if len(g)==0: continue
    with EdfReader(str(p)) as f:
        lab=[f.getLabel(k) for k in range(f.signals_in_file)]
        k=lab.index("EMG submental"); sf=f.getSampleFrequency(k)
        if sf==100:
            nsamp=f.samples_in_file(k)
            nsec=nsamp//100
            x=np.array(f.readSignal(k,0,nsec*100),dtype=np.float64).reshape(nsec,100)
            env1=np.sqrt((x**2).mean(1))  # 1Hz RMS envelope (per-second)
        else:
            env1=np.array(f.readSignal(k),dtype=np.float64)
    # map epochs to env1 seconds
    for lab5 in ["Wake","REM"]:
        e=g[g.label5==lab5].epoch.values
        vals=[env1[int(s*30):int((s+1)*30)].mean() for s in e if int((s+1)*30)<=len(env1)]
        if vals: rows.append((stem,co,lab5,float(np.median(vals)),len(vals)))
h=pd.DataFrame(rows,columns=["stem","cohort","label","emg_env_med","n"])
print(h.groupby(["cohort","label"]).emg_env_med.median().to_string())
def fisher(a,b): return float((a.mean()-b.mean())**2/(a.var()+b.var()+1e-12))
for co in ["SC","ST"]:
    w=h[(h.cohort==co)&(h.label=="Wake")].emg_env_med; r=h[(h.cohort==co)&(h.label=="REM")].emg_env_med
    print(co,"harmonized EMG Fisher Wake/REM:",round(fisher(w,r),3))
h.to_csv(TAB/"emg_harmonized.csv",index=False)

print("=== norm evidence: full-record z vs robust on SC4001 Fpz (daytime-contaminated) ===")
with EdfReader(str(ROOT/"sleep-cassette/SC4001E0-PSG.edf")) as f:
    x=np.array(f.readSignal(0),dtype=np.float64)
mu,sig=x.mean(),x.std(); med=np.median(x); q75,q25=np.percentile(x,75),np.percentile(x,25)
print(f"mean {mu:.2f} std {sig:.2f} median {med:.2f} IQR {q75-q25:.2f} max|x| {np.abs(x).max():.1f}")
print("z of a 150uV slow wave:",150/sig,"vs robust:",(150-med)/(q75-q25))
print("fraction |z|>8:",(np.abs((x-mu)/sig)>8).mean(), "fraction robust>8:",(np.abs((x-med)/(q75-q25))>8).mean())

print("=== filter evidence: 50Hz line + high-freq content (SC4001/ST7011 Fpz, N2 epoch) ===")
from edfio import read_edf
for fn in ["sleep-cassette/SC4001E0-PSG.edf","sleep-telemetry/ST7011J0-PSG.edf"]:
    with EdfReader(str(ROOT/fn)) as f:
        x=np.array(f.readSignal(0,1500000,3000),dtype=np.float64)
    fr,px=welch(x,fs=100,nperseg=1024)
    p50=px[(fr>=49)&(fr<=51)].max(); p40=px[(fr>=38)&(fr<=42)].mean(); p70=0
    print(fn,"50Hz peak / 40Hz base:",round(float(p50/max(p40,1e-12)),2), "35-50Hz share:",round(float(px[(fr>35)&(fr<50)].sum()/px[(fr>0.5)&(fr<50)].sum()),4))

print("=== robust 5-fold (subject-atomic, balance cohort+age+N1/N3) ===")
np.random.seed(7)
subs=sorted(ep.stem.str[:5].unique())
sc=pd.read_excel(ROOT/"SC-subjects.xls")
age_map={int(r.subject):r.age for _,r in sc.drop_duplicates("subject").iterrows()}
st=pd.read_excel(ROOT/"ST-subjects.xls",header=None)
sage={f"ST7{int(st.iloc[i,0]):02d}":int(st.iloc[i,1]) for i in range(2,len(st))}
prof=ep[ep.valid&ep.label5.isin(["Wake","N1","N2","N3","REM"])].groupby(ep[ep.valid&ep.label5.isin(["Wake","N1","N2","N3","REM"])].stem.str[:5]).label5.value_counts(normalize=True).unstack(fill_value=0)
import random
folds=[[] for _ in range(5)]
# greedy: sort subjects by (cohort, age) then snake into folds by N1+N3 rarity
keys=[]
for s in subs:
    co="ST" if s.startswith("ST") else "SC"
    ag=sage.get(s,age_map.get(int(s[3:5]),60))
    rare=float(prof.loc[s][["N1","N3"]].sum()) if s in prof.index else 0
    keys.append((co,ag,s,rare))
random.shuffle(keys)
for co in ["SC","ST"]:
    g=[k for k in keys if k[0]==co]
    g.sort(key=lambda x:(x[1],x[3]))
    for i,k in enumerate(g):
        folds[i%5].append(k[2]) if i%2==0 else folds[4-(i%5)].append(k[2])
for i,f in enumerate(folds):
    d=ep[ep.stem.str[:5].isin(f)&ep.valid]
    print(f"fold{i}: nsubj={len(f)} SC={sum(1 for s in f if s.startswith('SC'))} ST={sum(1 for s in f if not s.startswith('SC'))} epochs={len(d)} Wake%={100*(d.label5=='Wake').mean():.1f} N1%={100*(d.label5=='N1').mean():.1f} N3%={100*(d.label5=='N3').mean():.1f}")
pd.DataFrame([(i,s) for i,f in enumerate(folds) for s in f],columns=["fold","subject"]).to_csv(TAB/"folds5.csv",index=False)
print("saved emg_harmonized, folds5")
