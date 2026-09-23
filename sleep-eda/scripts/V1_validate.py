"""V1: validate critic claims. Device python."""
import pandas as pd, numpy as np
from pathlib import Path
from pyedflib import EdfReader
from edfio import read_edf
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")

print("=== A. ST SOL -1430 check ===")
d=pd.read_csv(TAB/"lights_off_sol.csv")
print(d[d.cohort=="ST"][["psg_file","rec_start","lights_off","SOL_min"]].sort_values("SOL_min").head(6).to_string())
print("ST SOL<-1000:",(d[d.cohort=='ST'].SOL_min<-1000).sum())

print("=== B. Marker rate: pyedflib vs edfio vs duration ===")
for fn in ["sleep-telemetry/ST7011J0-PSG.edf","sleep-telemetry/ST7112J0-PSG.edf","sleep-cassette/SC4001E0-PSG.edf"]:
    p=ROOT/fn
    with EdfReader(str(p)) as f:
        lab=[f.getLabel(k) for k in range(f.signals_in_file)]
        for k in range(f.signals_in_file):
            if "ark" in lab[k]:
                print(fn, repr(lab[k]), "sf=",f.getSampleFrequency(k), "nsamp=",f.samples_in_file(k), "dur=",f.getFileDuration(), "nsamp/dur=",f.samples_in_file(k)/f.getFileDuration())

print("=== C. contiguity: onset/duration grid audit all 197 ===")
bad=[]
for p in sorted(ROOT.rglob("*-Hypnogram.edf")):
    e=read_edf(str(p)); anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
    for i,(o,dd,t) in enumerate(anns):
        if abs(o/30-round(o/30))>1e-6 or abs(dd/30-round(dd/30))>1e-6:
            bad.append((p.name,i,o,dd,t,"non30")); break
    for (o1,d1,_),(o2,_,_) in zip(anns,anns[1:]):
        if abs(o2-(o1+d1))>1e-6:
            bad.append((p.name,o1,d1,o2,"gap/overlap")); break
print("files violating grid/contiguity:",len(bad))
for b in bad[:10]: print(b)

print("=== E. SC4762 mid ? ===")
for stem in ["SC4762","ST7122"]:
    cands=list(ROOT.rglob(stem+"*-Hypnogram.edf"))
    for h in cands:
        e=read_edf(str(h)); anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
        ep=[]
        for o,dd,t in anns: ep.extend([t]*int(round(dd/30)))
        idx=[i for i,t in enumerate(ep) if t in ("Sleep stage 1","Sleep stage 2","Sleep stage 3","Sleep stage 4","Sleep stage R")]
        f,l=idx[0],idx[-1]
        mid=ep[f:l+1]
        from collections import Counter
        print(h.name, "mid ? epochs:",sum(1 for t in mid if t=="Sleep stage ?"), "mid Mov:",sum(1 for t in mid if t=="Movement time"), "total ep:",len(ep))

print("=== G. wake_after includes ? check (03b def) ===")
s=pd.read_csv(TAB/"subject_class_distribution.csv")
r=s[s.stem=="SC4001"].iloc[0]
print("SC4001:",r[["n_epochs","wake_ep","q","mov","wake_before_ep","wake_after_ep"]].to_dict())
print("trailing ?=q_after dominates -> wake_after_ep counts pure Wake? NO - it counts all trailing incl ?. CONFIRM critic: wake_after_ep = n-1-last_sleep includes ?/Mov.")
