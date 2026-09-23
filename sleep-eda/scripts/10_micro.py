"""10_micro: event proxies per stage (spindle/slow-wave/eye-mov/atonia/arousal). Sampled, fast."""
import numpy as np
from pathlib import Path
import pandas as pd
from pyedflib import EdfReader
from edfio import read_edf
from scipy.signal import welch, butter, filtfilt
from collections import Counter
MAP={"Sleep stage W":"Wake","Sleep stage 1":"N1","Sleep stage 2":"N2","Sleep stage 3":"N3","Sleep stage 4":"N3","Sleep stage R":"REM"}

ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")

def butter_bp(lo,hi,sf,ord=4):
    b,a=butter(ord,[lo/(sf/2),hi/(sf/2)],btype="band"); return b,a
def band_rms(x,sf,lo,hi):
    b,a=butter_bp(lo,hi,sf); y=filtfilt(b,a,x); return float(np.sqrt(np.mean(y**2)))

# use 4 recs: 2 SC (young+old for age contrast) + 2 ST (placebo/temazepam pair of same subject if possible)
recs=[("sleep-cassette/SC4001E0-PSG.edf","sleep-cassette/SC4001EC-Hypnogram.edf"),  # F33
      ("sleep-cassette/SC4111E0-PSG.edf","sleep-cassette/SC4111EC-Hypnogram.edf"),  # older?
      ("sleep-telemetry/ST7011J0-PSG.edf","sleep-telemetry/ST7011JP-Hypnogram.edf"),
      ("sleep-telemetry/ST7012J0-PSG.edf","sleep-telemetry/ST7012JP-Hypnogram.edf")]
rows=[]
for psg_rel,hyp_rel in recs:
    psg=ROOT/psg_rel; hyp=ROOT/hyp_rel
    e=read_edf(str(hyp)); anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
    ep=[]
    for o,d,t in anns: ep.extend([t]*int(round(d/30)))
    with EdfReader(str(psg)) as f:
        lab=[f.getLabel(k) for k in range(f.signals_in_file)]
        sfs=[f.getSampleFrequency(k) for k in range(f.signals_in_file)]
        def get(ch):
            k=lab.index(ch); return np.array(f.readSignal(k),dtype=np.float64),sfs[k]
        eeg,_=get("EEG Fpz-Cz"); eegP,_=get("EEG Pz-Oz"); eog,_=get("EOG horizontal")
        try: emg,sfem=get("EMG submental")
        except: emg,sfem=None,None
    # sample up to 12 epochs per stage
    for st in ["Wake","N1","N2","N3","REM"]:
        idx=[i for i,t in enumerate(ep) if MAP.get(t)==st][:12]
        for ei in idx:
            s=eeg[ei*3000:(ei+1)*3000]; sp=eegP[ei*3000:(ei+1)*3000]; eo=eog[ei*3000:(ei+1)*3000]
            # proxies
            sigma=band_rms(s,100,11,16); slow=band_rms(s,100,0.5,4); alpha=band_rms(sp,100,8,13)
            beta=band_rms(s,100,13,30)
            # K-complex proxy: min peak < -75uV in SC scale (adaptive: < -3*std)
            kx=float(np.min(s)); kcx=1 if kx < -3*np.std(s) and kx < -40 else 0
            # slow-wave occupancy: frac samples |0.5-4 filtered|>75uV (SC) — use percentile-adaptive: >2.5std
            b,a=butter_bp(0.5,4,100); sfilt=filtfilt(b,a,s)
            sw_occ=float(np.mean(np.abs(sfilt)>2.5*np.std(sfilt)))
            # eye movements: EOG peak-to-peak + zero-crossing of derivative
            eog_ptp=float(np.ptp(eo)); eog_zc=float(((np.diff(eo[:-1])>0)!=(np.diff(eo[1:])>0)).mean())
            # EMG
            if emg is not None and sfem==100:
                seg=emg[ei*3000:(ei+1)*3000]; emg_rms=float(np.sqrt(np.mean(seg**2)))
            elif emg is not None:
                a0=int(ei*30*sfem); emg_rms=float(np.sqrt(np.mean(emg[a0:a0+int(30*sfem)]**2)))
            else: emg_rms=np.nan
            # arousal proxy: beta burst (>1.5x median beta of N2 in this rec? simplified: beta>30 + emg jump) — flag only
            rows.append({"file":psg.name,"stage":st,"epoch":ei,"sigma_rms":sigma,"slow_rms":slow,"alpha_rms":alpha,
                         "beta_rms":beta,"kcomplex_like":kcx,"k_min":kx,"sw_occ":sw_occ,"eog_ptp":eog_ptp,"eog_zc":eog_zc,"emg_rms":emg_rms})
    print("done",psg.name,len([r for r in rows if r["file"]==psg.name]))

df=pd.DataFrame(rows); df.to_csv(TAB/"micro_events.csv",index=False)
g=df.groupby("stage")[["sigma_rms","slow_rms","alpha_rms","beta_rms","sw_occ","eog_ptp","emg_rms"]].median()
print(g.to_string())
print("kcomplex_like rate by stage:"); print(df.groupby("stage").kcomplex_like.mean().to_string())
print("saved micro_events.csv",len(df))
