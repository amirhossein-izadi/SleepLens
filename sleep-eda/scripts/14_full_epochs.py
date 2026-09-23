"""14_full_epochs: ALL epochs fast rFFT rel-powers + time feats. Parquet per batch. EDA only."""
import numpy as np
from pathlib import Path
import pandas as pd
from pyedflib import EdfReader
from edfio import read_edf
import sys
MAP={"Sleep stage W":"Wake","Sleep stage 1":"N1","Sleep stage 2":"N2","Sleep stage 3":"N3","Sleep stage 4":"N3","Sleep stage R":"REM","Sleep stage ?":"OTHER","Movement time":"OTHER"}
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
batch=int(sys.argv[1])  # 0 SC first half, 1 SC second, 2 ST
psgs=sorted(ROOT.rglob("*-PSG.edf"))
sc=[p for p in psgs if p.name.startswith("SC")]; st=[p for p in psgs if p.name.startswith("ST")]
groups=[sc[:77],sc[77:],st]
psgs=groups[batch]
print(f"batch {batch}: {len(psgs)} files")
# rfft freq grid for 3000 @100Hz
N=3000; SF=100
freqs=np.fft.rfftfreq(N,1/SF)
bands={"delta":(0.5,4),"theta":(4,8),"alpha":(8,13),"sigma":(11,16),"beta":(13,30)}
bm={k:((freqs>=v[0])&(freqs<=v[1])) for k,v in bands.items()}
mtot=(freqs>=0.5)&(freqs<=30)
win=np.hanning(N)
rows=[]
for pi,psg in enumerate(psgs):
    cands=list(psg.parent.glob(psg.name[:6]+"*-Hypnogram.edf"))
    e=read_edf(str(cands[0])); anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
    ep=[]
    for o,d,t in anns: ep.extend([t]*int(round(d/30)))
    with EdfReader(str(psg)) as f:
        lab=[f.getLabel(k) for k in range(f.signals_in_file)]
        ns=f.samples_in_file(lab.index("EEG Fpz-Cz"))
        ne=min(len(ep),ns//3000)
        E=np.array(f.readSignal(lab.index("EEG Fpz-Cz"),0,ne*3000),dtype=np.float64).reshape(ne,3000)
        P=np.array(f.readSignal(lab.index("EEG Pz-Oz"),0,ne*3000),dtype=np.float64).reshape(ne,3000)
        O=np.array(f.readSignal(lab.index("EOG horizontal"),0,ne*3000),dtype=np.float64).reshape(ne,3000)
        kE=lab.index("EMG submental"); sfE=f.getSampleFrequency(kE)
        if sfE==100:
            M=np.array(f.readSignal(kE,0,ne*3000),dtype=np.float64).reshape(ne,3000)
            emg_rms=np.sqrt((M**2).mean(1))
        else:
            Mrs=int(sfE*30); M=np.array(f.readSignal(kE,0,ne*Mrs),dtype=np.float64).reshape(ne,Mrs)
            emg_rms=np.sqrt((M**2).mean(1))
        # spectral: rfft per epoch (vectorized per rec via loop in numpy? loop ne=2500 FFTs, ok)
        X=np.abs(np.fft.rfft((E-E.mean(1,keepdims=True))*win,axis=1))**2
        tot=X[:,mtot].sum(1)+1e-12
        rel={k:(X[:,m].sum(1)/tot) for k,m in bm.items()}
        std=E.std(1); ptp=np.ptp(E,axis=1); zcr=((E[:,:-1]*E[:,1:])<0).mean(1)
        eog_ptp=np.ptp(O,axis=1); eog_std=O.std(1)
        for i in range(ne):
            rows.append((psg.name[:5],psg.name,5 if False else i,MAP.get(ep[i],"OTHER"),
                round(float(std[i]),2),round(float(ptp[i]),1),round(float(zcr[i]),4),
                round(float(rel["delta"][i]),4),round(float(rel["theta"][i]),4),round(float(rel["alpha"][i]),4),
                round(float(rel["sigma"][i]),4),round(float(rel["beta"][i]),4),
                round(float(eog_ptp[i]),1),round(float(eog_std[i]),2),round(float(emg_rms[i]),3)))
    print(f"{pi+1}/{len(psgs)} {psg.name} ne={ne}",flush=True)
    if (pi+1)%25==0:
        pd.DataFrame(rows,columns=["subject_id","recording_id","epoch_index","label","eeg_std","eeg_ptp","zcr","delta","theta","alpha","sigma","beta","eog_ptp","eog_std","emg_rms"]).to_parquet(TAB/f"baseline_full_b{batch}.parquet",index=False)
pd.DataFrame(rows,columns=["subject_id","recording_id","epoch_index","label","eeg_std","eeg_ptp","zcr","delta","theta","alpha","sigma","beta","eog_ptp","eog_std","emg_rms"]).to_parquet(TAB/f"baseline_full_b{batch}.parquet",index=False)
print("saved",len(rows))
