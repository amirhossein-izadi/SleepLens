"""perfection fixes: signal_quality_full, dir fig, subjects age, architecture real WASO/awaken/trans, index update."""
import numpy as np, pandas as pd
from pathlib import Path
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from edfio import read_edf
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables"); FIG=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\figs"); LLM=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\llm")
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
MAP={"Sleep stage W":"Wake","Sleep stage 1":"N1","Sleep stage 2":"N2","Sleep stage 3":"N3","Sleep stage 4":"N3","Sleep stage R":"REM","Sleep stage ?":"OTHER","Movement time":"OTHER"}

# 1 signal_quality_full from signal_stats_full + cleanliness
stats=pd.read_csv(TAB/"signal_stats_full.csv")
clean=pd.read_csv(TAB/"cleanliness_all.csv")
# cleanliness covers 100Hz chs sampled; merge on file+ch/channel
q=stats.merge(clean.rename(columns={"ch":"channel"}),on=["file","cohort","channel"],how="left")
q.to_csv(TAB/"signal_quality_full.csv",index=False)
print("signal_quality_full",q.shape)

# 2 dir summary fig
fig,ax=plt.subplots(1,2,figsize=(11,4))
ax[0].bar(["cassette","telemetry","root"],[306,88,5]); ax[0].set_title("Files per folder (total 399)")
ax[1].bar(["edf-PSG","edf-Hyp","xls","txt","noext"],[197,197,2,1,2]); ax[1].set_title("By type (394 EDF = 8.715 GB)")
fig.suptitle("Dataset directory summary"); fig.tight_layout(); fig.savefig(FIG/"dir_summary.png",dpi=120); plt.close(fig)

# 3 subjects age fill ST
subs=pd.read_csv(TAB/"subjects.csv"); st=pd.read_csv(TAB/"subjects_ST.csv")
age_st={r.subject_id:r.age for _,r in st.iterrows()}
# subject_prefix ST701 -> ST701? st subject_id ST01.. need map: prefix ST7ss -> ss=int(prefix[3:5])? ST701 ss=01 -> ST01
def st_age(prefix):
    try: ss=int(prefix[3:5]); key=f"ST{ss:02d}"; return age_st.get(key)
    except: return None
subs["age"]=subs.apply(lambda r: r.age if pd.notna(r.age) else (st_age(r.subject_prefix) if r.cohort=="ST" else None),axis=1)
subs.to_csv(TAB/"subjects.csv",index=False)
print("subjects ages filled:",subs.age.notna().sum(),"/100")

# 4 architecture real WASO/awakenings/transitions from hyp sequences
arch=pd.read_csv(TAB/"sleep_architecture.csv").set_index("stem")
n_fix=0
for p in sorted(ROOT.rglob("*-Hypnogram.edf")):
    stem=p.name[:6]
    e=read_edf(str(p)); anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
    ep=[]
    for o,d,t in anns: ep.extend([MAP.get(t,"OTHER")]*int(round(d/30)))
    idx=[i for i,t in enumerate(ep) if t in ("N1","N2","N3","REM")]
    if not idx: continue
    f,l=idx[0],idx[-1]
    mid=ep[f:l+1]
    waso=sum(1 for t in mid if t=="Wake")*0.5
    awak=sum(1 for a,b in zip(mid,mid[1:]) if a in ("N1","N2","N3","REM") and b=="Wake")
    trans=sum(1 for a,b in zip(ep,ep[1:]) if a!=b)
    arch.loc[stem,["WASO_min","awakenings","transitions"]]=[waso,awak,trans]
    n_fix+=1
arch.to_csv(TAB/"sleep_architecture.csv")
print("arch fixed",n_fix,"example:",arch[["WASO_min","awakenings","transitions"]].median().to_dict())

# 5 index update
idx=LLM/"00_index.md"
t=idx.read_text(encoding="utf-8")
add="\n14 deep-story (home/lab life) → 15 micro events → 16 meso N1/Fisher → 17 macro cycles/age/drug → 18 gaps-closed → 19 full-EDA (459k) → 20 channelwise → 21 perfection (this file).\nRequired outputs: tables/*.csv (12 spec + full), figs (16/16 + extras), REPORT.md A–P.\n"
if "21 perfection" not in t:
    idx.write_text(t+add,encoding="utf-8")
print("done perfection fixes")
