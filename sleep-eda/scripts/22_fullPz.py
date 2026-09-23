"""22_fullPz_spectral: Pz-Oz rel-bands + 1/f slope + alpha peak, all in-signal epochs. Parquet."""
import numpy as np
from pathlib import Path
import pandas as pd
from pyedflib import EdfReader
from edfio import read_edf
import sys
MAP={"Sleep stage W":"Wake","Sleep stage 1":"N1","Sleep stage 2":"N2","Sleep stage 3":"N3","Sleep stage 4":"N3","Sleep stage R":"REM","Sleep stage ?":"OTHER","Movement time":"OTHER"}
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
batch=int(sys.argv[1])
psgs=sorted(ROOT.rglob("*-PSG.edf"))
sc=[p for p in psgs if p.name.startswith("SC")]; st=[p for p in psgs if p.name.startswith("ST")]
groups=[sc[:77],sc[77:],st]; psgs=groups[batch]
N=3000; SF=100; freqs=np.fft.rfftfreq(N,1/SF)
bm={"d":(freqs>=0.5)&(freqs<=4),"t":(freqs>=4)&(freqs<=8),"a":(freqs>=8)&(freqs<=13),"s":(freqs>=11)&(freqs<=16),"b":(freqs>=13)&(freqs<=30)}
mtot=(freqs>=0.5)&(freqs<=30)
# 1/f slope fit 2-30Hz loglog; alpha peak 7-14 max
fitm=(freqs>=2)&(freqs<=30); lx=np.log10(freqs[fitm])
apm=(freqs>=7)&(freqs<=14)
win=np.hanning(N)
rows=[]
for pi,psg in enumerate(psgs):
    hyp=list(psg.parent.glob(psg.name[:6]+"*-Hypnogram.edf"))[0]
    e=read_edf(str(hyp)); anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
    ep=[]
    for o,d,t in anns: ep.extend([t]*int(round(d/30)))
    with EdfReader(str(psg)) as f:
        lab=[f.getLabel(k) for k in range(f.signals_in_file)]
        ns=f.samples_in_file(lab.index("EEG Pz-Oz"))
        ne=min(len(ep),ns//3000)
        P=np.array(f.readSignal(lab.index("EEG Pz-Oz"),0,ne*3000),dtype=np.float64).reshape(ne,3000)
        X=np.abs(np.fft.rfft((P-P.mean(1,keepdims=True))*win,axis=1))**2
        tot=X[:,mtot].sum(1)+1e-12
        rel={k:(X[:,m].sum(1)/tot) for k,m in bm.items()}
        # slope per epoch (least squares, vectorized via loop? ne~2500, loop ok)
        slopes=np.empty(ne); apeaks=np.empty(ne)
        L=np.log10(X[:,fitm]+1e-12)
        for i in range(ne):
            y=L[i]; A=np.vstack([lx,np.ones_like(lx)]).T
            slopes[i],_ = np.linalg.lstsq(A,y,rcond=None)[0]
            seg=X[i,apm]; apeaks[i]=freqs[apm][int(np.argmax(seg))]
        for i in range(ne):
            rows.append((psg.name,i,MAP.get(ep[i],"OTHER"),round(float(rel["d"][i]),4),round(float(rel["t"][i]),4),
                round(float(rel["a"][i]),4),round(float(rel["s"][i]),4),round(float(rel["b"][i]),4),
                round(float(slopes[i]),3),round(float(apeaks[i]),2)))
    print(f"{pi+1}/{len(psgs)} {psg.name}",flush=True)
pd.DataFrame(rows,columns=["recording_id","epoch_index","label","pz_delta","pz_theta","pz_alpha","pz_sigma","pz_beta","slope_2_30","alpha_peak"]).to_parquet(TAB/f"pz_full_b{batch}.parquet",index=False)
print("saved",len(rows))
