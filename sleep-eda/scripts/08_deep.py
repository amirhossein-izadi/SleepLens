"""08_deep: full-night story overviews. Device python."""
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pyedflib import EdfReader
from edfio import read_edf

ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
FIG=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\figs"); TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
MAP={"Sleep stage W":0,"Sleep stage 1":1,"Sleep stage 2":2,"Sleep stage 3":3,"Sleep stage 4":4,"Sleep stage R":5,"Sleep stage ?":-1,"Movement time":-2}
STAGE_NAMES={0:"W",1:"N1",2:"N2",3:"N3a",4:"N3b",5:"REM",-1:"?",-2:"M"}

def load_full(p):
    with EdfReader(str(p)) as f:
        n=f.signals_in_file; labels=[f.getLabel(k) for k in range(n)]
        sfs=[f.getSampleFrequency(k) for k in range(n)]
        start=f.getStartdatetime()
        dur=f.getFileDuration()
        sigs={}
        for k in range(n):
            x=np.array(f.readSignal(k),dtype=np.float64)
            sigs[labels[k]]=(x,sfs[k])
    return sigs,start,dur

def hyp_seq(h):
    e=read_edf(str(h)); anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
    ep=[]
    for o,d,t in anns: ep.extend([t]*int(round(d/30)))
    return ep, anns

recs=[("sleep-cassette/SC4001E0-PSG.edf","sleep-cassette/SC4001EC-Hypnogram.edf"),
      ("sleep-cassette/SC4041E0-PSG.edf","sleep-cassette/SC4041EC-Hypnogram.edf"),
      ("sleep-telemetry/ST7011J0-PSG.edf","sleep-telemetry/ST7011JP-Hypnogram.edf")]
sc_xls=pd.read_excel(ROOT/"SC-subjects.xls")

for psg_rel,hyp_rel in recs:
    psg=ROOT/psg_rel; hyp=ROOT/hyp_rel
    sigs,start,dur=load_full(psg)
    ep,anns=hyp_seq(hyp)
    print(f"==== {psg.name} start={start} dur_h={dur/3600:.2f} nepochs={len(ep)}")
    print(f"  anns: {len(anns)} first={(anns[0][0],anns[0][1],anns[0][2])} last={(anns[-1][0],anns[-1][1],anns[-1][2])}")
    # envelope: RMS per 30s for EEG/EOG @100Hz, mean per 30s for 1Hz aux
    ne=len(ep)
    t_h=np.arange(ne)*30/3600
    # hypnogram numeric
    hyp_num=np.array([MAP.get(x,-9) for x in ep])
    # eeg rms
    fig,ax=plt.subplots(5,1,figsize=(14,10),sharex=True)
    ax[0].step(t_h,hyp_num,where="post",lw=0.7)
    ax[0].set_yticks([0,1,2,3,4,5,-1],[ "W","N1","N2","N3","N4","REM","?"]); ax[0].set_title(f"{psg.name} FULL NIGHT hypnogram (start {start})")
    ax[0].invert_yaxis()
    for j,ch in enumerate(["EEG Fpz-Cz","EEG Pz-Oz","EOG horizontal"],start=1):
        x,sf=sigs[ch]; n30=int(30*sf)
        rms=np.array([np.sqrt(np.mean(x[i*n30:(i+1)*n30]**2)) if (i+1)*n30<=len(x) else np.nan for i in range(ne)])
        ax[j].plot(t_h,rms,lw=0.7); ax[j].set_ylabel(f"{ch}rms"); ax[j].set_yscale("log")
    # aux panel
    j=4
    for ch in sigs:
        if ch in ("EEG Fpz-Cz","EEG Pz-Oz","EOG horizontal"): continue
        x,sf=sigs[ch]
        if sf==1.0:
            n30=int(30*sf); m=np.array([np.mean(x[i*n30:(i+1)*n30]) if (i+1)*n30<=len(x) else np.nan for i in range(ne)])
            ax[j].plot(t_h,m,lw=0.8,label=ch)
    ax[j].legend(fontsize=7,ncol=3); ax[j].set_ylabel("1Hz aux"); ax[j].set_xlabel("hours from recording start")
    fig.tight_layout(); fig.savefig(FIG/f"fullnight_{psg.stem}.png",dpi=110); plt.close(fig)
    # zoom: 20 min around sleep onset
    idx=[i for i,t in enumerate(ep) if t in ("Sleep stage 1","Sleep stage 2","Sleep stage 3","Sleep stage 4","Sleep stage R")]
    if idx:
        f0=idx[0]; print(f"  first sleep epoch {f0} ({f0*30/60:.0f} min in), wake_before={f0} ep")
        # raw 10-min EEG around onset
        for ch in ["EEG Fpz-Cz","EOG horizontal"]:
            x,sf=sigs[ch]; sf=int(sf)
            a=max(0,(f0-5)*30*sf); b=min(len(x),(f0+5)*30*sf)
            fig,axx=plt.subplots(figsize=(13,3))
            axx.plot(np.arange(b-a)/sf/60, x[a:b], lw=0.5)
            axx.axvline(5*30/60 if a>0 else f0*30/60, color="r", ls="--", label="first sleep")
            axx.set_xlabel("min (10-min window)"); axx.set_title(f"{psg.name} sleep-onset raw {ch}")
            axx.legend(); fig.tight_layout(); fig.savefig(FIG/f"onset_{psg.stem}_{ch[:3]}.png",dpi=110); plt.close(fig)
    # lights-off lookup for SC
    if "SC" in psg.name:
        # stem SC4001 -> subject? SC-subjects uses subject numbers 0..? map via RECORDS order? use filename parsing: SC4ssN
        import re
        m=re.match(r"SC4(\d{2})(\d)",psg.name)
        print("  SC parse ss,N:",m.groups() if m else None)
print("done overviews")
