"""verify negative SOL SC, independent recount with details."""
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from pyedflib import EdfReader
from edfio import read_edf
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
sc=pd.read_excel(ROOT/"SC-subjects.xls")
def plo(s):
    return datetime.strptime(str(s).strip(),"%H:%M:%S")
rows=[]
for p in sorted((ROOT/"sleep-cassette").glob("SC*-PSG.edf")):
    ss=int(p.name[3:5]); ng=int(p.name[5])
    lo=plo(sc[(sc.subject==ss)&(sc.night==ng)].iloc[0]["LightsOff"])
    with EdfReader(str(p)) as f: start=f.getStartdatetime()
    hyp=list((ROOT/"sleep-cassette").glob(p.name[:6]+"*-Hypnogram.edf"))[0]
    a=read_edf(str(hyp)); anns=sorted([(x.onset,x.duration,x.text) for x in a.annotations])
    # first sleep onset seconds (annotation onset, exact clock, no 30s-expansion bias)
    fs=None
    for o,d,t in anns:
        if t in ("Sleep stage 1","Sleep stage 2","Sleep stage 3","Sleep stage 4","Sleep stage R"):
            fs=o; break
    lo_dt=start.replace(hour=lo.hour,minute=lo.minute,second=lo.second,microsecond=0)
    if lo_dt<start: lo_dt+=timedelta(days=1)
    sleep_dt=start+timedelta(seconds=fs) if fs is not None else None
    sol=(sleep_dt-lo_dt).total_seconds()/60 if sleep_dt else None
    rows.append((p.name,start,lo_dt,sleep_dt,sol,fs))
d=pd.DataFrame(rows,columns=["file","start","lights_off","first_sleep","SOL","first_sleep_sec"])
neg=d[d.SOL<0]
print("SC total",len(d),"neg SOL",len(neg))
print("neg SOL distribution (min):"); print(neg.SOL.describe().to_string())
print("mild (<60min before LO):",(neg.SOL>-60).sum(),"| deep naps (>60min):",(neg.SOL<=-60).sum())
print("examples mild:"); print(neg[neg.SOL>-60][["file","start","lights_off","first_sleep","SOL"]].head(8).to_string())
print("examples deep:"); print(neg[neg.SOL<=-60][["file","SOL"]].head(10).to_string())
# sanity: what stage is that pre-lights-off sleep? check first sleep label for 3 deep cases
for fn in neg[neg.SOL<=-60].file.head(3):
    hyp=list((ROOT/"sleep-cassette").glob(fn[:6]+"*-Hypnogram.edf"))[0]
    a=read_edf(str(hyp)); anns=sorted([(x.onset,x.duration,x.text) for x in a.annotations])
    seq=[(o,d,t) for o,d,t in anns if t!="Sleep stage W"][:4]
    print(fn,"first non-W:",[(round(o/60,1),round(dd/60,1),t) for o,dd,t in seq])
d.to_csv(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables\lights_off_verify.csv",index=False)
print("saved lights_off_verify.csv")
