"""G2: v3 architecture, per-window stats, folds-from-bench, fixed lights_off table."""
import pandas as pd, numpy as np
from pathlib import Path
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\SleepLens\sleep-eda\tables")
ep=pd.read_parquet(TAB/"epochs_v3.parquet")
W=pd.read_csv(TAB/"sleep_windows_v3.csv",parse_dates=["lights_off"])
SLEEP=["N1","N2","N3","REM"]; L5=["Wake","N1","N2","N3","REM"]

def sust_onset(g, lo_ep):
    """first 20-ep window at/after lo_ep-60 with >=16 valid sleep; returns epoch or None."""
    cand=g[(g.epoch>=lo_ep-60)&(g.valid)&(g.label5.isin(SLEEP))].epoch
    arr=g.set_index("epoch")
    for s in sorted(cand):
        win=range(int(s),int(s)+20)
        if all(i in arr.index and arr.loc[i,"valid"] and arr.loc[i,"label5"] in SLEEP for i in win if i in arr.index):
            # require >=16 of 20 present as sleep (allow missing idx)
            have=sum(1 for i in win if i in arr.index and arr.loc[i,"valid"] and arr.loc[i,"label5"] in SLEEP)
            if have>=16: return int(s)
    return None

starts={}
import re
# recover rec start: lights_off - lo_ep? store instead: recompute lo_ep per rec from windows
rows=[]; flags=[]
for stem,g in ep.groupby("stem"):
    co=g.cohort.iloc[0]
    w=W[W.stem==stem].iloc[0]
    m=g[g.in_main_window]
    tot_ep=len(m)
    unscored=m[~m.valid].__len__()
    sl=m[m.valid&m.label5.isin(SLEEP)]
    tst=len(sl)*0.5
    tib=tot_ep*0.5
    se=tst/tib*100 if tib>0 else np.nan
    # sustained onset: first 20-ep run inside window
    arr=g.set_index("epoch")
    onset=None
    for s in sorted(sl.epoch):
        win=range(int(s),int(s)+20)
        have=sum(1 for i in win if i in arr.index and arr.loc[i,"in_main_window"] and arr.loc[i,"valid"] and arr.loc[i,"label5"] in SLEEP)
        if have>=16: onset=int(s); break
    if onset is None and len(sl): onset=int(sl.epoch.min())
    lo_ep=w.main_start_ep  # window start == LO
    sol=(onset-lo_ep)*0.5 if onset is not None else None
    last=int(sl.epoch.max()) if len(sl) else None
    waso=g[(g.in_main_window)&(g.valid)&(g.label5=="Wake")&(g.epoch>onset)&(g.epoch<last)].__len__()*0.5 if onset is not None and last else 0
    rems=sorted(sl[sl.label5=="REM"].epoch) if len(sl) else []
    reml=(rems[0]-onset)*0.5 if rems and onset is not None else None
    tr=0
    mm=m[m.valid].sort_values("epoch")
    for a,b in zip(mm.iloc[:-1].itertuples(),mm.iloc[1:].itertuples()):
        if b.epoch==a.epoch+1 and b.label5!=a.label5: tr+=1
    comp={s:round((sl.label5==s).sum()/max(1,len(sl))*100,2) for s in SLEEP}
    if not (0<=se<=100): flags.append((stem,"SE",round(se,1)))
    if tst>tib+1e-9: flags.append((stem,"TST>TIB",None))
    rows.append((stem,co,round(tib,1),round(tst,1),round(se,2) if pd.notna(se) else None,
        round(sol,1) if sol is not None else None,round(waso,1),round(reml,1) if reml is not None else None,
        comp["N1"],comp["N2"],comp["N3"],comp["REM"],tr,round(unscored/tot_ep*100,2),tot_ep))
a=pd.DataFrame(rows,columns=["stem","cohort","TIB_proxy_min","TST_min","SE_proxy","SOL_min","WASO_min","REMlat_min","N1_TST","N2_TST","N3_TST","REM_TST","transitions","unscored_pct","window_epochs"])
a.to_csv(TAB/"sleep_architecture_v3.csv",index=False)
print("SE range:",a.SE_proxy.min(),a.SE_proxy.max(),"| SE>100:",(a.SE_proxy>100).sum())
print("neg SOL:",(a.SOL_min<0).sum(),"| medians:"); print(a[["TIB_proxy_min","TST_min","SE_proxy","SOL_min","WASO_min","REMlat_min"]].median().to_string())
print("FLAGS:",flags)
print("SC4762 unscored:",a[a.stem=="SC4762"][["unscored_pct","window_epochs"]].to_string(index=False))
print("stage pct sum check max dev:",(a[["N1_TST","N2_TST","N3_TST","REM_TST"]].sum(1)-100).abs().max())

# per-window x cohort class + transitions (adjacency-only)
for w in ["valid","in_bench","in_main_window"]:
    d=ep[ep[w]&ep.label5.isin(L5)]
    print(f"--- {w} ---")
    print(d.groupby("cohort").label5.value_counts(normalize=True).unstack().round(3).to_string())
    for co in ["SC","ST"]:
        dd=d[d.cohort==co].sort_values(["stem","epoch"])
        consec=(dd.epoch.values[1:]==dd.epoch.values[:-1]+1)&(dd.stem.values[1:]==dd.stem.values[:-1])
        frm=dd.label5.values[:-1][consec]; to=dd.label5.values[1:][consec]
        t=pd.crosstab(frm,to).reindex(index=L5,columns=L5,fill_value=0)
        t.to_csv(TAB/f"transition_v3_{w}_{co}.csv")
        rs=t.sum(1).replace(0,np.nan)
        print(f"{w}/{co} Wake-self:",round(float(t.loc["Wake","Wake"]/rs["Wake"]),3))

# fixed lights_off table (overwrite stale)
lo2=[]
for stem,g in ep.groupby("stem"):
    w=W[W.stem==stem].iloc[0]
    sl=g[g.valid&g.label5.isin(SLEEP)]
    f=sl.epoch.min() if len(sl) else None
    lo2.append((stem,g.cohort.iloc[0],w.lights_off,f))
pd.DataFrame(lo2,columns=["stem","cohort","lights_off","first_sleep_ep"]).to_csv(TAB/"lights_off_sol.csv",index=False)
print("lights_off_sol.csv overwritten (fixed datetimes, first_sleep_ep grid)")

# folds from BENCHMARK profiles
subs=sorted(ep.stem.str[:5].unique())
prof=ep[ep.in_bench&ep.label5.isin(L5)].groupby(ep[ep.in_bench&ep.label5.isin(L5)].stem.str[:5]).label5.value_counts(normalize=True).unstack(fill_value=0)
import pandas as pd
sc=pd.read_excel(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0\SC-subjects.xls")
age_map={int(r.subject):r.age for _,r in sc.drop_duplicates("subject").iterrows()}
st=pd.read_excel(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0\ST-subjects.xls",header=None)
sage={f"ST7{int(st.iloc[i,0]):02d}":int(st.iloc[i,1]) for i in range(2,len(st))}
folds=[[] for _ in range(5)]
keys=[]
for s in subs:
    co="ST" if s.startswith("ST") else "SC"
    ag=sage.get(s,age_map.get(int(s[3:5]),60))
    rare=float(prof.loc[s][["N1","N3"]].sum()) if s in prof.index else 0
    keys.append((co,ag,s,rare))
import random; random.seed(7); random.shuffle(keys)
for co in ["SC","ST"]:
    g=[k for k in keys if k[0]==co]; g.sort(key=lambda x:(x[1],x[3]))
    for i,k in enumerate(g): folds[i%5 if i%2==0 else 4-(i%5)].append(k[2])
for i,f in enumerate(folds):
    d=ep[ep.stem.str[:5].isin(f)&ep.in_bench]
    print(f"fold{i}: nsubj={len(f)} epochs={len(d)} Wake%={100*(d.label5=='Wake').mean():.1f} N1%={100*(d.label5=='N1').mean():.1f} N3%={100*(d.label5=='N3').mean():.1f}")
pd.DataFrame([(i,s) for i,f in enumerate(folds) for s in f],columns=["fold","subject"]).to_csv(TAB/"folds5_v3.csv",index=False)
print("saved architecture_v3, transitions v3, folds5_v3")
