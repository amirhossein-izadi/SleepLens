"""27_suspicious: sustained SOL, singleton audit, rollover check, sensitivity, rule-based 48-way split."""
import pandas as pd, numpy as np
from pathlib import Path
from datetime import timedelta
from edfio import read_edf
from collections import Counter
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
MAP={"Sleep stage W":"Wake","Sleep stage 1":"N1","Sleep stage 2":"N2","Sleep stage 3":"N3","Sleep stage 4":"N3","Sleep stage R":"REM","Sleep stage ?":"OTHER","Movement time":"OTHER"}
v=pd.read_csv(TAB/"lights_off_verify.csv",parse_dates=["start","lights_off","first_sleep"])
nap=pd.read_csv(TAB/"nap_character.csv")
rows=[]
for _,r in v.iterrows():
    hyp=list((ROOT/"sleep-cassette").glob(r.file[:6]+"*-Hypnogram.edf"))[0]
    a=read_edf(str(hyp)); anns=sorted([(x.onset,x.duration,x.text) for x in a.annotations])
    ep=[]
    for o,d,t in anns: ep.extend([MAP.get(t,"OTHER")]*int(round(d/30)))
    lo_sec=(pd.Timestamp(r.lights_off)-pd.Timestamp(r.start)).total_seconds()
    # first-epoch sleep idx (old def)
    idx=[i for i,t in enumerate(ep) if t in ("N1","N2","N3","REM")]
    f1=idx[0] if idx else None
    # sustained: first idx starting 20 consecutive sleep epochs (10 min) with >=16 sleep
    sust=None
    for i in idx:
        win=ep[i:i+20]
        if len(win)<20: break
        if sum(1 for t in win if t in ("N1","N2","N3","REM"))>=16:
            sust=i; break
    # first-sleep run length (how long until first Wake, in epochs)
    runlen=0
    if f1 is not None:
        for t in ep[f1:]:
            if t in ("N1","N2","N3","REM"): runlen+=1
            else: break
    rows.append((r.file,r.SOL,f1,sust,runlen,
                 round((f1*30)/60,1) if f1 is not None else None,
                 round((sust*30)/60,1) if sust is not None else None,
                 round((lo_sec)/60,1)))
d=pd.DataFrame(rows,columns=["file","SOL_first","first_ep","sust_ep","first_run_ep","first_min","sust_min","lo_min"])
print("first-run length (epochs) describe:"); print(d.first_run_ep.describe().to_string())
print("singletons (run==1):",(d.first_run_ep==1).sum(),"/153")
print("sust-first gap (min) describe:"); print(((d.sust_ep-d.first_ep)*0.5).describe().to_string())
# rollover audit: SOL absurd (>12h or <-12h)?
print("SOL range:",v.SOL.min(),v.SOL.max())
print("sust SOL recompute:")
d["SOL_sust"]=(d.sust_ep*0.5)-(d.lo_min)
print(d.SOL_sust.describe().to_string())
print("neg under first-def:",(d.SOL_first<0).sum(),"neg under sust-def:",(d.SOL_sust<0).sum())
# rule-based split of the 48 (use first-def set)
neg=d[d.SOL_first<0].copy()
m=nap.set_index("file")
def classify(fn):
    n=m.loc[fn]
    gap=n.gap_napEnd_to_LO_min; dur=n.nap_sleep_min
    if gap>=30 and dur>=5: return "genuine-nap"
    if gap>=30 and dur<5: return "doze-blip"
    if gap<30 and dur>=10: return "early-onset?"
    return "lights-off-noise"
neg["class"]=neg.file.apply(classify)
print(neg["class"].value_counts().to_string())
print(neg.groupby("class").SOL_first.median().to_string())
# sensitivity: TST/SE/SOL under defs (medians across SC)
sub=pd.read_csv(TAB/"subject_class_distribution.csv"); sub=sub[sub.cohort=="SC"]
arch=pd.read_csv(TAB/"sleep_architecture.csv")
print("sensitivity (SC medians): TST_min",arch[arch.cohort=="SC"].TST_min.median().round(1),
      "SE_untrimmed",arch[arch.cohort=="SC"].SE_pct.median().round(1))
print("SOL_first median",round(d.SOL_first.median(),1),"SOL_sust median",round(d.SOL_sust.median(),1))
d.to_csv(TAB/"sol_sustained.csv",index=False)
neg[["file","SOL_first","SOL_sust","first_run_ep","class"]].to_csv(TAB/"neg48_classified.csv",index=False)
print("saved sol_sustained, neg48_classified")
