"""F2: tolerance lights-off + MAIN architecture + per-window stats + N3/TST + paired drug."""
import pandas as pd, numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from pyedflib import EdfReader
from edfio import read_edf
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
ep=pd.read_parquet(TAB/"epochs_authoritative.parquet")
SLEEP={"N1","N2","N3","REM"}

def plo(s):
    return datetime.strptime(str(s).strip(),"%H:%M:%S")
sc=pd.read_excel(ROOT/"SC-subjects.xls")
st=pd.read_excel(ROOT/"ST-subjects.xls",header=None)
cond={}; off={}
for i in range(2,len(st)):
    r=st.iloc[i]; nr=int(r[0])
    for night,oc in [(int(r[3]),4),(int(r[5]),6)]:
        key=f"ST7{nr:02d}{night}"
        cond[key]="placebo" if (night==int(r[3])) else "temazepam"
        off[key]=plo(r[oc])

def resolve_lo(start, lotime):
    """candidates same-day / +1d; pick plausible: prefer SOL in [-60, 720] using first-sleep estimate passed later.
    Here: if lo is within TOL after start-30min, keep same-day; roll only if lo much earlier (>TOL=3h)."""
    TOL=timedelta(hours=3)
    cand=start.replace(hour=lotime.hour,minute=lotime.minute,second=lotime.second,microsecond=0)
    if cand<start and (start-cand)<TOL:
        return cand  # seconds/minutes earlier -> same evening (fixes -1430 bug)
    if cand<start:
        return cand+timedelta(days=1)
    return cand

# per-rec start times
starts={}
for p in sorted(ROOT.rglob("*-PSG.edf")):
    with EdfReader(str(p)) as f: starts[p.name[:6]]=f.getStartdatetime()
rows=[]
for stem,g in ep.groupby("stem"):
    cohort=g.cohort.iloc[0]; start=starts[stem]
    if cohort=="SC":
        ss=int(stem[3:5]); ng=int(stem[5])
        lo=resolve_lo(start, plo(sc[(sc.subject==ss)&(sc.night==ng)].iloc[0]["LightsOff"]))
    else:
        lo=resolve_lo(start, off[stem])
    m=g[g.in_main]
    # TIB: lo -> main end (last main epoch end), clipped to signal
    mend=m[m.in_main].epoch.max() if m.in_main.any() else np.nan
    tib=(start+timedelta(seconds=float((mend+1)*30))-lo).total_seconds()/60 if pd.notna(mend) else np.nan
    sl=m[m.label5.isin(SLEEP)]
    tst=len(sl)*0.5
    sol=None; reml=None
    mepochs=sorted(m[m.label5.isin(SLEEP)].epoch)
    if mepochs:
        sol=(start+timedelta(seconds=float(mepochs[0]*30))-lo).total_seconds()/60
        rems=[e for e in mepochs if m.set_index("epoch").loc[e,"label5"]=="REM"]
        if rems: reml=(rems[0]-mepochs[0])*0.5
    waso=sum((m.label5=="Wake"))*0.5
    se=tst/tib*100 if tib and tib>0 else np.nan
    cov=1-m[m.label5=="OTHER"].__len__()/max(1,len(m))
    rows.append((stem,cohort,lo.strftime("%Y-%m-%d %H:%M"),round(tib,1) if pd.notna(tib) else None,
        round(tst,1),round(se,1) if pd.notna(se) else None,round(sol,1) if sol is not None else None,
        round(waso,1),round(reml,1) if reml is not None else None,
        *[round((m.label5==s).sum()/max(1,len(sl))*100,2) for s in ["N1","N2","N3","REM"]],
        (m.label5!=m.label5.shift()).sum(), round((1-cov)*100,2)))
arch=pd.DataFrame(rows,columns=["stem","cohort","lights_off","TIB_min","TST_min","SE_pct","SOL_min","WASO_min","REMlat_min","N1_TST","N2_TST","N3_TST","REM_TST","transitions","unscored_pct"])
arch.to_csv(TAB/"sleep_architecture_main.csv",index=False)
print("MAIN arch medians:"); print(arch[["TIB_min","TST_min","SE_pct","SOL_min","WASO_min","REMlat_min"]].median().to_string())
print("by cohort:"); print(arch.groupby("cohort")[["TIB_min","TST_min","SE_pct","SOL_min","WASO_min"]].median().round(1).to_string())
print("ST SOL<-1000 now:",(arch[arch.cohort=="ST"].SOL_min<-1000).sum())
print("neg SOL now:",(arch.SOL_min<0).sum())

# per-window x cohort class + transitions
for w in ["valid","in_bench","in_main"]:
    d=ep[ep[w]&ep.label5.isin(["Wake","N1","N2","N3","REM"])]
    print(f"--- {w} ---")
    print(d.groupby("cohort").label5.value_counts(normalize=True).unstack().round(3).to_string())
# sleep-only composition
for w in ["valid","in_bench","in_main"]:
    d=ep[ep[w]&ep.label5.isin(SLEEP)]
    print(f"--- {w} sleep-only ---")
    print(d.groupby("cohort").label5.value_counts(normalize=True).unstack().round(3).to_string())

# N3/TST by age deciles (SC, MAIN window)
sub=pd.read_csv(TAB/"subject_class_distribution.csv")
age_map={int(r.subject):r.age for _,r in sc.drop_duplicates("subject").iterrows()}
m2=ep[ep.in_main&(ep.cohort=="SC")].copy()
m2["age"]=m2.stem.str[3:5].astype(int).map(age_map)
m2["dec"]=pd.cut(m2.age,bins=[20,40,60,80,110])
t=m2[m2.label5.isin(SLEEP)].groupby("dec",observed=True).label5.value_counts(normalize=True).unstack()
print("MAIN-window sleep composition by age:"); print(t.round(3).to_string())

# paired drug, TST-normalized (MAIN window) — explicit merge, no pivot
piv=ep[ep.in_main].groupby(["stem"]).label5.value_counts().unstack(fill_value=0)
for c in ["Wake","N1","N2","N3","REM"]:
    piv[c+"_pct"]=piv[c]/piv[["N1","N2","N3","REM"]].sum(axis=1)*100
piv["tst"]=piv[["N1","N2","N3","REM"]].sum(axis=1)
base=piv.reset_index()
base["subj"]=base.stem.str[:5]; base["condx"]=base.stem.map(cond)
for c in ["Wake","N1","N2","N3","REM","tst","N1_pct","N2_pct","N3_pct","REM_pct","Wake_pct"]:
    a=base[base.condx=="temazepam"].set_index("subj")[c]
    b=base[base.condx=="placebo"].set_index("subj")[c]
    common=a.index.intersection(b.index)
    print(f" {c}: n={len(common)} delta={float((a.loc[common]-b.loc[common]).mean()):+.2f} (tem {float(a.loc[common].mean()):.2f} vs pbo {float(b.loc[common].mean()):.2f})")
print("saved sleep_architecture_main.csv")
