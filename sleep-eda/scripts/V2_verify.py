"""V2: independent re-verification of all headline claims. Prints PASS/FAIL."""
import pandas as pd, numpy as np
from pathlib import Path
from pyedflib import EdfReader
from edfio import read_edf
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
ok=[]; 
def chk(name, cond, detail=""):
    ok.append((name,bool(cond))); print(("PASS " if cond else "FAIL ")+name, detail)

# 1 epochs authoritative: recount valid from parquet + independent edfio expansion totals
ep=pd.read_parquet(TAB/"epochs_authoritative.parquet")
chk("valid=457652", ep.valid.sum()==457652, ep.valid.sum())
chk("bench=237936", ep.in_bench.sum()==237936, ep.in_bench.sum())
chk("main=196959", ep.in_main.sum()==196959, ep.in_main.sum())
tot=0
for p in sorted(ROOT.rglob("*-Hypnogram.edf")):
    e=read_edf(str(p))
    for a in e.annotations: tot+=int(round(a.duration/30))
chk("raw annotation total=483419", tot==483419, tot)
chk("GAP=692 all ST", (ep.label5=="GAP").sum()==692 and (ep[ep.label5=="GAP"].cohort=="ST").all(), (ep.label5=="GAP").sum())

# 2 SOL fix
arch=pd.read_csv(TAB/"sleep_architecture_main.csv")
chk("ST SOL<-1000 == 0", (arch[arch.cohort=="ST"].SOL_min<-1000).sum()==0)
chk("SE median ~85.9", abs(arch.SE_pct.median()-85.9)<0.2, round(arch.SE_pct.median(),2))
chk("TST median 426", abs(arch.TST_min.median()-426)<2, round(arch.TST_min.median(),1))
chk("WASO SC>ST", arch[arch.cohort=="SC"].WASO_min.median()>arch[arch.cohort=="ST"].WASO_min.median(),
    (round(arch[arch.cohort=="SC"].WASO_min.median(),1),round(arch[arch.cohort=="ST"].WASO_min.median(),1)))

# 3 marker
mq=pd.read_csv(TAB/"marker_quality.csv")
c=mq[["marker_neg_frac","flat1s_rate"]].corr().iloc[0,1]
chk("marker-flat corr>0.9", c>0.9, round(c,3))
chk("ST7151 neg~0.238", abs(mq[mq.file=="ST7151J0-PSG.edf"].marker_neg_frac.iloc[0]-0.238273)<1e-4)
q=pd.read_csv(TAB/"quality_labelled_ST.csv")
chk("labelled flat median<0.002", q.flat_labelled.median()<0.002, round(q.flat_labelled.median(),5))
chk("worst labelled ST7221", q.sort_values("flat_labelled",ascending=False).iloc[0].file=="ST7221J0-PSG.edf")

# 4 marker 10Hz raw
with EdfReader(str(ROOT/"sleep-telemetry/ST7011J0-PSG.edf")) as f:
    lab=[f.getLabel(k) for k in range(f.signals_in_file)]; k=lab.index("Marker")
    chk("Marker 10Hz raw", abs(f.samples_in_file(k)/f.getFileDuration()-10.0)<1e-9)

# 5 EMG
h=pd.read_csv(TAB/"emg_harmonized.csv")
def fisher(a,b): return float((a.mean()-b.mean())**2/(a.var()+b.var()+1e-12))
for co,exp in [("SC",0.927),("ST",0.719)]:
    w=h[(h.cohort==co)&(h.label=="Wake")].emg_env_med; r=h[(h.cohort==co)&(h.label=="REM")].emg_env_med
    v=fisher(w,r); chk(f"{co} EMG Fisher~{exp}", abs(v-exp)<0.01, round(v,3))

# 6 N3/TST decades from authoritative + ages
sc=pd.read_excel(ROOT/"SC-subjects.xls")
am={int(r.subject):r.age for _,r in sc.drop_duplicates("subject").iterrows()}
m=ep[ep.in_main&(ep.cohort=="SC")].copy(); m["age"]=m.stem.str[3:5].astype(int).map(am)
m["dec"]=pd.cut(m.age,bins=[20,40,60,80,110])
t=m[m.label5.isin(["N1","N2","N3","REM"])].groupby("dec",observed=True).label5.value_counts(normalize=True).unstack()["N3"]
chk("N3/TST 20-40~0.168", abs(t.iloc[0]-0.168)<0.01, round(float(t.iloc[0]),3))
chk("N3/TST 80+~0.057", abs(t.iloc[3]-0.057)<0.01, round(float(t.iloc[3]),3))

# 7 drug paired deltas
st=pd.read_excel(ROOT/"ST-subjects.xls",header=None)
cond={}
for i in range(2,len(st)):
    r=st.iloc[i]
    cond[f"ST7{int(r[0]):02d}{int(r[3])}"]="placebo"; cond[f"ST7{int(r[0]):02d}{int(r[5])}"]="temazepam"
pv=ep[ep.in_main].groupby("stem").label5.value_counts().unstack(fill_value=0)
pv["cond"]=pv.index.map(cond); pv["tst"]=pv[["N1","N2","N3","REM"]].sum(axis=1)
pv["subj"]=pv.index.str[:5]
for c,exp in [("N2",40.4),("N1",-18.5),("Wake",-18.7)]:
    a=pv[pv.cond=="temazepam"].set_index("subj")[c]; b=pv[pv.cond=="placebo"].set_index("subj")[c]
    common=a.index.intersection(b.index); v=float((a.loc[common]-b.loc[common]).mean())
    chk(f"drug {c}~{exp}", abs(v-exp)<1.0, round(v,1))

# 8 transitions
for w,co,a,exp in [("valid","SC","Wake",0.988),("in_main","SC","Wake",0.896),("in_main","ST","Wake",0.811)]:
    t=pd.read_csv(TAB/f"trans_{w}_{co}.csv",index_col=0)
    v=t.loc[a,a]/t.loc[a].sum()
    chk(f"trans {w}/{co} Wake-self~{exp}", abs(v-exp)<0.005, round(v,3))

# 9 folds
f=pd.read_csv(TAB/"folds5.csv")
chk("folds 100 subj", f.subject.nunique()==100, f.subject.nunique())
chk("folds 20 each", (f.fold.value_counts()==20).all(), f.fold.value_counts().to_dict())

# 10 SC4762 / ST7122
e=read_edf(str(list(ROOT.rglob("SC4762*-Hypnogram.edf"))[0])); anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
ep2=[]
for o,d,t in anns: ep2.extend([t]*int(round(d/30)))
idx=[i for i,t in enumerate(ep2) if t in ("Sleep stage 1","Sleep stage 2","Sleep stage 3","Sleep stage 4","Sleep stage R")]
mid=ep2[idx[0]:idx[-1]+1]
chk("SC4762 mid?=133", sum(1 for t in mid if t=="Sleep stage ?")==133, sum(1 for t in mid if t=="Sleep stage ?"))

print()
print("FAILURES:",[n for n,v in ok if not v] or "none")
