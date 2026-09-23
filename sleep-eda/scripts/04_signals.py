"""04: signal deep dive — representative SC+ST, per-stage stats, PSD, figs. Device python."""
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pyedflib import EdfReader
from edfio import read_edf
from collections import Counter

ROOT = Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
FIG = Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\figs"); FIG.mkdir(parents=True, exist_ok=True)
TAB = Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")

MAP = {"Sleep stage W":"Wake","Sleep stage 1":"N1","Sleep stage 2":"N2",
       "Sleep stage 3":"N3","Sleep stage 4":"N3","Sleep stage R":"REM"}

def load_psg(p):
    with EdfReader(str(p)) as f:
        n=f.signals_in_file
        labels=[f.getLabel(k) for k in range(n)]
        sfs=[f.getSampleFrequency(k) for k in range(n)]
        sigs={labels[k]: np.array(f.readSignal(k), dtype=np.float64) for k in range(n)}
    return sigs, labels, sfs

def hyp_epochs(hyp_path):
    e=read_edf(str(hyp_path))
    anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
    epochs=[]
    for o,d,t in anns:
        epochs.extend([t]*int(round(d/30)))
    return epochs

# pick 3 SC + 2 ST with good hyps
recs=[("sleep-cassette/SC4001E0-PSG.edf","sleep-cassette/SC4001EC-Hypnogram.edf"),
      ("sleep-cassette/SC4041E0-PSG.edf","sleep-cassette/SC4041EC-Hypnogram.edf"),
      ("sleep-cassette/SC4101E0-PSG.edf","sleep-cassette/SC4101EC-Hypnogram.edf"),
      ("sleep-telemetry/ST7011J0-PSG.edf","sleep-telemetry/ST7011JP-Hypnogram.edf"),
      ("sleep-telemetry/ST7052J0-PSG.edf","sleep-telemetry/ST7052JA-Hypnogram.edf")]

from scipy.signal import welch, spectrogram

BANDS={"delta":(0.5,4),"theta":(4,8),"alpha":(8,13),"sigma":(11,16),"beta":(13,30)}
def bandpower(freqs, psd, band):
    m=(freqs>=band[0])&(freqs<=band[1])
    return np.trapz(psd[m], freqs[m])

stats_rows=[]
# 1) per-recording channel stats (first 2 recs full, rest sampled) + plots
for ri,(psg_rel, hyp_rel) in enumerate(recs):
    psg=ROOT/psg_rel; hyp=ROOT/hyp_rel
    sigs, labels, sfs = load_psg(psg)
    epochs = hyp_epochs(hyp)
    print(f"[{ri}] {psg.name}: labels={labels} sfs={sfs} nepochs={len(epochs)}")
    for ch in labels:
        x=sigs[ch]
        sf=sfs[labels.index(ch)]
        stats_rows.append({"file":psg.name,"channel":ch,"sf":sf,"mean":float(np.mean(x)),
            "std":float(np.std(x)),"rms":float(np.sqrt(np.mean(x**2))),
            "p1":float(np.percentile(x,1)),"p99":float(np.percentile(x,99)),
            "min":float(np.min(x)),"max":float(np.max(x)),
            "flat_frac":float(np.mean(np.abs(np.diff(x))<1e-9)) if len(x)>1 else 0})
    # 30s + 2min raw EEG for a mid-sleep N2 epoch if available
    try:
        # find first N2 epoch index in middle third
        idx=[i for i,t in enumerate(epochs) if t=="Sleep stage 2"]
        pick=idx[len(idx)//2]
        sf=100
        s0=pick*30*sf
        seg30={ch:sigs[ch][s0:s0+30*sf] for ch in ["EEG Fpz-Cz","EEG Pz-Oz","EOG horizontal"]}
        fig,ax=plt.subplots(3,1,figsize=(12,6),sharex=True)
        for j,ch in enumerate(["EEG Fpz-Cz","EEG Pz-Oz","EOG horizontal"]):
            ax[j].plot(np.arange(len(seg30[ch]))/sf, seg30[ch], lw=0.5)
            ax[j].set_title(f"{psg.name} N2 epoch {pick} — {ch}")
            ax[j].set_ylabel("uV")
        ax[-1].set_xlabel("s"); fig.tight_layout()
        fig.savefig(FIG/f"eeg30s_{psg.stem}.png",dpi=100); plt.close(fig)
        # 2-min
        s1=max(0,s0-45*sf); seg120={ch:sigs[ch][s1:s1+120*sf] for ch in ["EEG Fpz-Cz","EEG Pz-Oz"]}
        fig,ax=plt.subplots(2,1,figsize=(12,5),sharex=True)
        for j,ch in enumerate(["EEG Fpz-Cz","EEG Pz-Oz"]):
            ax[j].plot(np.arange(len(seg120[ch]))/sf, seg120[ch], lw=0.4)
            ax[j].set_title(f"{psg.name} 2-min around N2 — {ch}")
        ax[-1].set_xlabel("s"); fig.tight_layout()
        fig.savefig(FIG/f"eeg2min_{psg.stem}.png",dpi=100); plt.close(fig)
        # PSD per stage (sample up to 8 epochs per stage, Fpz-Cz)
        fig,ax=plt.subplots(figsize=(9,5))
        for stage_raw,stage in [("Sleep stage W","Wake"),("Sleep stage 1","N1"),("Sleep stage 2","N2"),("Sleep stage 3","N3"),("Sleep stage R","REM")]:
            ii=[i for i,t in enumerate(epochs) if (MAP.get(t)==stage)]
            if len(ii)==0: continue
            sel=ii[:8]
            psds=[]
            for ei in sel:
                seg=sigs["EEG Fpz-Cz"][ei*30*sf:(ei+1)*30*sf]
                fr,px=welch(seg,fs=sf,nperseg=min(1024,len(seg)))
                psds.append(px)
            mpsd=np.median(np.array(psds),axis=0)
            ax.semilogy(fr,mpsd,label=stage)
            # band powers print for first rec
            if ri==0:
                bps={b:bandpower(fr,mpsd,BANDS[b]) for b in BANDS}
                tot=bandpower(fr,mpsd,(0.5,30))+1e-12
                print(f"  {stage}: "+" ".join(f"{b}={bps[b]/tot:.2f}" for b in BANDS))
        ax.set_xlim(0.5,30); ax.set_xlabel("Hz"); ax.set_ylabel("PSD uV^2/Hz"); ax.legend(); ax.set_title(f"{psg.name} stage-wise PSD Fpz-Cz (median of ≤8 epochs)")
        fig.tight_layout(); fig.savefig(FIG/f"psd_{psg.stem}.png",dpi=110); plt.close(fig)
        # spectrogram of 10 min around pick
        seg=sigs["EEG Fpz-Cz"][s0-150*sf:s0+450*sf]
        ff,tt,ss=spectrogram(seg,fs=sf,nperseg=512,noverlap=384)
        fig,ax=plt.subplots(figsize=(10,4))
        ax.pcolormesh(tt,ff,10*np.log10(ss+1e-12),shading="auto",vmin=-20,vmax=30)
        ax.set_ylim(0,30); ax.set_xlabel("s"); ax.set_ylabel("Hz"); ax.set_title(f"{psg.name} spectrogram Fpz-Cz 10min around N2")
        fig.tight_layout(); fig.savefig(FIG/f"spec_{psg.stem}.png",dpi=110); plt.close(fig)
        # amplitude hist EEG
        fig,ax=plt.subplots(figsize=(8,4))
        for ch in ["EEG Fpz-Cz","EEG Pz-Oz"]:
            x=sigs[ch][::100]  # decimate for hist
            ax.hist(x,bins=200,range=(np.percentile(x,0.5),np.percentile(x,99.5)),alpha=0.5,label=ch,histtype="stepfilled")
        ax.legend(); ax.set_title(f"{psg.name} EEG amplitude hist (0.5-99.5 pct)"); fig.tight_layout()
        fig.savefig(FIG/f"hist_{psg.stem}.png",dpi=110); plt.close(fig)
        print(f"  figs saved for {psg.name}")
    except Exception as ex:
        print(f"  plot FAIL {psg.name}: {ex}")

import csv
with open(TAB/"signal_stats_sample.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(stats_rows[0].keys())); w.writeheader(); w.writerows(stats_rows)
print("saved signal_stats_sample.csv + figs")
