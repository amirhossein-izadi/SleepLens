"""nap or not? characterize 48 pre-lights-off sleep blocks: clock, duration, stages, gap to main sleep."""
import pandas as pd
from pathlib import Path
from datetime import timedelta
from edfio import read_edf
from collections import Counter
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
v=pd.read_csv(TAB/"lights_off_verify.csv",parse_dates=["start","lights_off","first_sleep"])
neg=v[v.SOL<0].copy()
print("neg:",len(neg))
rows=[]
for _,r in neg.iterrows():
    hyp=list((ROOT/"sleep-cassette").glob(r.file[:6]+"*-Hypnogram.edf"))[0]
    a=read_edf(str(hyp)); anns=sorted([(x.onset,x.duration,x.text) for x in a.annotations])
    lo_sec=(pd.Timestamp(r.lights_off)-pd.Timestamp(r.start)).total_seconds()
    # pre-LO sleep epochs: annotations with onset < lo_sec and label sleep
    pre=[(o,d,t) for o,d,t in anns if o<lo_sec and t in ("Sleep stage 1","Sleep stage 2","Sleep stage 3","Sleep stage 4","Sleep stage R")]
    pre_min=sum(d for _,d,_ in pre)/60
    stages=Counter(t for _,_,t in pre)
    # nap block: from first pre sleep onset to last pre sleep end (includes brief wake inside?)
    nap_start=min(o for o,_,_ in pre)/60 if pre else None
    nap_end=max(o+d for o,d,_ in pre)/60 if pre else None
    # gap: nap_end -> lo
    gap=(lo_sec/60-nap_end) if nap_end else None
    # main sleep: first sleep at/after lo
    post=[(o,d,t) for o,d,t in anns if o>=lo_sec and t in ("Sleep stage 1","Sleep stage 2","Sleep stage 3","Sleep stage 4","Sleep stage R")]
    main_start=post[0][0]/60 if post else None
    # clock of nap start
    nap_clock=(pd.Timestamp(r.start)+timedelta(seconds=min(o for o,_,_ in pre))).strftime("%H:%M") if pre else None
    rows.append((r.file,r.start.strftime("%H:%M"),nap_clock,round(pre_min,1),dict(stages),
                 round(gap,1) if gap else None, r.SOL,
                 (pd.Timestamp(r.start)+timedelta(seconds=main_start*60)).strftime("%H:%M") if main_start else None))
d=pd.DataFrame(rows,columns=["file","rec_start","nap_start_clock","nap_sleep_min","nap_stages","gap_napEnd_to_LO_min","SOL","main_sleep_clock"])
d.to_csv(TAB/"nap_character.csv",index=False)
print(d[["file","rec_start","nap_start_clock","nap_sleep_min","gap_napEnd_to_LO_min","main_sleep_clock"]].head(15).to_string())
print()
print("nap start clock distribution:"); print(pd.Series([x.split(':')[0] for x in d.nap_start_clock]).value_counts().sort_index().to_string())
print("nap_sleep_min describe:"); print(d.nap_sleep_min.describe().to_string())
print("gap describe:"); print(d.gap_napEnd_to_LO_min.describe().to_string())
# stage totals in naps
tot=Counter()
for _,r in d.iterrows():
    for k,vv in r.nap_stages.items(): tot[k]+=vv
print("nap stage counts (blocks):",dict(tot))
