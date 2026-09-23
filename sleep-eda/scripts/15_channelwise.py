"""15_channelwise: per-channel spatial + frequency fingerprints. EDA only."""
import numpy as np
from pathlib import Path
import pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from pyedflib import EdfReader
from edfio import read_edf
from scipy.signal import welch
MAP={"Sleep stage W":"Wake","Sleep stage 1":"N1","Sleep stage 2":"N2","Sleep stage 3":"N3","Sleep stage 4":"N3","Sleep stage R":"REM"}
L5=["Wake","N1","N2","N3","REM"]
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables"); FIG=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\figs")
BANDS={"delta":(0.5,4),"theta":(4,8),"alpha":(8,13),"sigma":(11,16),"beta":(13,30)}

recs=[p for p in sorted(ROOT.rglob("*-PSG.edf")) if p.name in
 ("SC4001E0-PSG.edf","SC4051E0-PSG.edf","SC4141E0-PSG.edf","SC4181E0-PSG.edf",
  "ST7011J0-PSG.edf","ST7012J0-PSG.edf","ST7051J0-PSG.edf","ST7111J0-PSG.edf")]
# per-channel per-stage median PSD (100Hz chs) + 1Hz aux means
psd_bank={}  # (ch,stage) -> median psd
fr_ref=None
rows=[]
for psg in recs:
    hyp=list(psg.parent.glob(psg.name[:6]+"*-Hypnogram.edf"))[0]
    e=read_edf(str(hyp)); anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
    ep=[]
    for o,d,t in anns: ep.extend([t]*int(round(d/30)))
    with EdfReader(str(psg)) as f:
        lab=[f.getLabel(k) for k in range(f.signals_in_file)]
        ns=f.samples_in_file(lab.index("EEG Fpz-Cz"))
        for st in L5:
            raw={"Wake":"Sleep stage W","N1":"Sleep stage 1","N2":"Sleep stage 2","N3":"Sleep stage 3","REM":"Sleep stage R"}[st]
            idx=[i for i,t in enumerate(ep) if t==raw and (i+1)*3000<=ns][:8]
            for ch in ["EEG Fpz-Cz","EEG Pz-Oz","EOG horizontal"]:
                segs=[np.array(f.readSignal(lab.index(ch),i*3000,3000),dtype=np.float64) for i in idx]
                if not segs: continue
                psds=[]
                for s in segs:
                    fr,px=welch(s,fs=100,nperseg=1024); psds.append(px)
                m=np.median(np.array(psds),axis=0); fr_ref=fr
                psd_bank[(psg.name,ch,st)]=m
                tot=np.trapezoid(m[(fr>=0.5)&(fr<=30)],fr[(fr>=0.5)&(fr<=30)])+1e-12
                r={b:float(np.trapezoid(m[(fr>=v[0])&(fr<=v[1])],fr[(fr>=v[0])&(fr<=v[1])])/tot) for b,v in BANDS.items()}
                rows.append({"file":psg.name,"cohort":psg.name[:2],"channel":ch,"stage":st,**r})
        # 1Hz aux fingerprint: night mean vs day mean (SC only)
        if psg.name.startswith("SC"):
            for ch in ["Resp oro-nasal","Temp rectal","EMG submental"]:
                k=lab.index(ch); sf=f.getSampleFrequency(k)
                x=np.array(f.readSignal(k),dtype=np.float64)
                # split scored-sleep vs wake via hyp (approx: first/last sleep)
                rows.append({"file":psg.name,"cohort":"SC","channel":ch,"stage":"ALL-night-mean",
                    "delta":float(x.mean()),"theta":float(x.std()),"alpha":float(np.ptp(x[:3600])), "sigma":np.nan,"beta":np.nan})
    print("done",psg.name)
pd.DataFrame(rows).to_csv(TAB/"channelwise_stage_bands.csv",index=False)
# pooled median rel-power per channel×stage
df=pd.DataFrame([r for r in rows if r["stage"] in L5])
piv=df.groupby(["channel","stage"])[list(BANDS)].median().round(4)
print(piv.to_string())
piv.to_csv(TAB/"channelwise_medians.csv")
# figs: one panel per channel, 5 stage curves (pooled across recs in bank)
for ch in ["EEG Fpz-Cz","EEG Pz-Oz","EOG horizontal"]:
    fig,ax=plt.subplots(figsize=(9,5))
    for st in L5:
        arr=np.array([psd_bank[(fn,ch,st)] for fn in [p.name for p in recs] if ( [p.name for p in recs][0],ch,st) or (fn,ch,st) in psd_bank])
        m=np.median(arr,axis=0)
        ax.semilogy(fr_ref,m,label=st)
    ax.set_xlim(0.5,30); ax.set_xlabel("Hz"); ax.set_ylabel("PSD"); ax.legend()
    ax.set_title(f"{ch} stage fingerprints (median of rec-medians, n={len(recs)} recs)")
    fig.tight_layout(); fig.savefig(FIG/f"chwise_{ch[:6].replace(' ','_')}.png",dpi=120); plt.close(fig)
# spatial gradient: Fpz-Pz log-ratio per stage (pooled)
fig,ax=plt.subplots(figsize=(8,4))
xs=np.arange(len(L5))
fp=piv.loc["EEG Fpz-Cz"]; pz=piv.loc["EEG Pz-Oz"]
# use delta and alpha gradients
ax.bar(xs-0.2, np.log10((fp['delta']+1e-6)/(pz['delta']+1e-6)),0.4,label="log10(Fpz/Pz) delta")
ax.bar(xs+0.2, np.log10((fp['alpha']+1e-6)/(pz['alpha']+1e-6)),0.4,label="log10(Fpz/Pz) alpha")
ax.set_xticks(xs,L5); ax.axhline(0,color="k",lw=0.8); ax.legend(); ax.set_title("Anterior-posterior gradient (pooled medians)")
fig.tight_layout(); fig.savefig(FIG/"spatial_gradient.png",dpi=120); plt.close(fig)
print("saved channelwise")
