"""05: EOG/EMG by stage, quality, subject variability, cohort, architecture, SQI feasibility, figs."""
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import csv
from pyedflib import EdfReader
from edfio import read_edf
from collections import Counter, defaultdict
import pandas as pd

ROOT = Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
FIG = Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\figs")
TAB = Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
MAP = {"Sleep stage W":"Wake","Sleep stage 1":"N1","Sleep stage 2":"N2","Sleep stage 3":"N3","Sleep stage 4":"N3","Sleep stage R":"REM"}

# --- EOG/EMG by stage on 2 recs (1 SC, 1 ST) ---
def load(p):
    with EdfReader(str(p)) as f:
        n=f.signals_in_file; labels=[f.getLabel(k) for k in range(n)]
        sfs=[f.getSampleFrequency(k) for k in range(n)]
        sigs={labels[k]:np.array(f.readSignal(k),dtype=np.float64) for k in range(n)}
    return sigs,labels,sfs

def epochs_of(h):
    e=read_edf(str(h)); anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
    ep=[]
    for o,d,t in anns: ep.extend([t]*int(round(d/30)))
    return ep

pairs=[(ROOT/"sleep-cassette/SC4001E0-PSG.edf",ROOT/"sleep-cassette/SC4001EC-Hypnogram.edf"),
       (ROOT/"sleep-telemetry/ST7011J0-PSG.edf",ROOT/"sleep-telemetry/ST7011JP-Hypnogram.edf")]
rows=[]
for psg,hyp in pairs:
    sigs,labels,sfs=load(psg); ep=epochs_of(hyp)
    is_st="ST" in psg.name
    for stage in ["Wake","N1","N2","N3","REM"]:
        idx=[i for i,t in enumerate(ep) if MAP.get(t)==stage][:10]
        eog_rms=[]; emg_rms=[]
        for ei in idx:
            # EOG 100Hz always
            seg=sigs["EOG horizontal"][ei*3000:(ei+1)*3000]
            eog_rms.append(float(np.sqrt(np.mean(seg**2))))
            em=sigs["EMG submental"]
            sfem=sfs[labels.index("EMG submental")]
            a=int(ei*30*sfem); b=int((ei+1)*30*sfem)
            emg_rms.append(float(np.sqrt(np.mean(em[a:b]**2))))
        rows.append({"file":psg.name,"stage":stage,"eog_rms_med":float(np.median(eog_rms)),
                     "emg_rms_med":float(np.median(emg_rms)),"emg_sf":sfs[labels.index("EMG submental")]})
        print(psg.name, stage, f"EOGrms={np.median(eog_rms):.1f} EMGrms={np.median(emg_rms):.3f} (sf {sfs[labels.index('EMG submental')]})")

with open(TAB/"eog_emg_by_stage.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

# EMG plot by stage
df=pd.DataFrame(rows)
fig,ax=plt.subplots(1,2,figsize=(12,4))
for j,col in enumerate(["eog_rms_med","emg_rms_med"]):
    for fn in df.file.unique():
        sub=df[df.file==fn]
        ax[j].plot(sub.stage, sub[col], marker="o", label=fn[:12])
    ax[j].set_title(col); ax[j].legend(fontsize=8)
fig.tight_layout(); fig.savefig(FIG/"emg_eog_by_stage.png",dpi=120); plt.close(fig)

# --- quality scan headers+sample: NaN/Inf/flat/clip on sample recs ---
qrows=[]
for psg,hyp in pairs:
    sigs,labels,sfs=load(psg)
    for ch in labels:
        if "Marker" in ch or "Event" in ch: continue
        x=sigs[ch]
        qrows.append({"file":psg.name,"channel":ch,"nan":int(np.isnan(x).sum()),"inf":int(np.isinf(x).sum()),
            "flat_frac":float(np.mean(np.abs(np.diff(x[::10]))<1e-12)),
            "p99_abs":float(np.percentile(np.abs(x),99)),"std":float(np.std(x))})
        print(psg.name,ch,"nan",np.isnan(x).sum(),"flat",f"{np.mean(np.abs(np.diff(x[::10]))<1e-12):.4f}")
with open(TAB/"signal_quality.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(qrows[0].keys())); w.writeheader(); w.writerows(qrows)

# --- durations distro + channel availability + class distro figs ---
hdr=pd.read_csv(TAB/"recordings_headers.csv")
fig,ax=plt.subplots(figsize=(9,4))
ax.hist(hdr[hdr.cohort=="SC"].duration_sec/3600,bins=20,alpha=0.6,label="SC")
ax.hist(hdr[hdr.cohort=="ST"].duration_sec/3600,bins=20,alpha=0.6,label="ST")
ax.legend();ax.set_xlabel("hours");ax.set_title("Recording duration distro");fig.tight_layout()
fig.savefig(FIG/"duration_dist.png",dpi=120);plt.close(fig)

ch=pd.read_csv(TAB/"channels.csv")
fig,ax=plt.subplots(figsize=(9,4))
ax.barh(ch.channel_original,ch.present_in_n_recordings)
ax.set_xlabel("n recordings /197");ax.set_title("Channel availability");fig.tight_layout()
fig.savefig(FIG/"channel_avail.png",dpi=120);plt.close(fig)

ann=pd.read_csv(TAB/"annotations_summary.csv")
# map to 5-class for plot
fig,ax=plt.subplots(figsize=(9,4))
labs=list(ann.raw_label); vals=list(ann.epochs_30s)
ax.bar(labs,vals);ax.set_xticklabels(labs,rotation=30,ha="right");ax.set_title("Global 30s epoch distro (raw labels, 197 nights via edfio)")
fig.tight_layout();fig.savefig(FIG/"class_dist.png",dpi=120);plt.close(fig)

# transition heatmap
tm=pd.read_csv(TAB/"transition_matrix.csv",index_col=0)
fig,ax=plt.subplots(figsize=(6,5))
im=ax.imshow(tm.values,vmin=0,vmax=1)
ax.set_xticks(range(5),tm.columns);ax.set_yticks(range(5),tm.index)
for i in range(5):
    for j in range(5):
        ax.text(j,i,f"{tm.values[i,j]:.2f}",ha="center",va="center",fontsize=9,color="white" if tm.values[i,j]>0.5 else "black")
ax.set_title("5-class transition P(t|t-1) epoch-level");fig.colorbar(im);fig.tight_layout()
fig.savefig(FIG/"transition_matrix.png",dpi=130);plt.close(fig)

# per-subject Wake% (from subject_class_distribution)
sub=pd.read_csv(TAB/"subject_class_distribution.csv")
sub["wake_pct"]=sub.wake_ep/sub.n_epochs*100
fig,ax=plt.subplots(figsize=(10,4))
ax.hist(sub.wake_pct,bins=25);ax.set_xlabel("Wake % per recording");ax.set_title("Per-recording Wake% (197 nights)")
fig.tight_layout();fig.savefig(FIG/"persubject_wake.png",dpi=120);plt.close(fig)

# trim impact bar (from 03b numbers)
cats=["Wake","N2","REM","N1","N3"]; vals_full=[60.1,18.4,7.1,5.2,4.0]; vals_30=[29.4,37.3,14.3,10.6,8.2]
x=np.arange(len(cats));fig,ax=plt.subplots(figsize=(8,4))
ax.bar(x-0.2,vals_full,0.4,label="no trim");ax.bar(x+0.2,vals_30,0.4,label="30min trim")
ax.set_xticks(x,cats);ax.set_ylabel("%");ax.legend();ax.set_title("Wake trim impact (excl ?/Mov)")
fig.tight_layout();fig.savefig(FIG/"trim_impact.png",dpi=120);plt.close(fig)

# --- sleep architecture per recording (ground truth) ---
arch=[]
for _,r in sub.iterrows():
    n=r.n_epochs; sl=r.n1+r.n2+r.n3+r.rem
    arch.append({"stem":r.stem,"cohort":r.cohort,"TRT_min":n*0.5,"TST_min":sl*0.5,
        "SE_pct":sl/n*100 if n else 0,"WASO_min":np.nan,"SOL_min":r.wake_before_ep*0.5,
        "N1_min":r.n1*0.5,"N2_min":r.n2*0.5,"N3_min":(r.n3)*0.5,"REM_min":r.rem*0.5,
        "awakenings":np.nan,"transitions":np.nan})
pd.DataFrame(arch).to_csv(TAB/"sleep_architecture.csv",index=False)
print("arch means:",pd.DataFrame(arch)[["TRT_min","TST_min","SE_pct"]].mean().to_dict())

# --- SQI feasibility ---
feas=[
 ("Total Sleep Time","yes","hypnogram","high","TST from 5-class epochs"),
 ("Sleep Efficiency","approx","hypnogram","medium","SE=TST/TRT; TRT def depends on trim; lights-off in xls helps SOL"),
 ("WASO","approx","hypnogram","medium","needs sleep-onset def; mid Wake countable"),
 ("Sleep Onset Latency","approx","hypnogram+lights-off","medium","first N1/N2/N3/REM vs lights-off from xls"),
 ("N1/N2/N3/REM %","yes","hypnogram","high","direct"),
 ("REM latency","yes","hypnogram","high","first REM - sleep onset"),
 ("stage-transition count","yes","hypnogram","high","from epoch sequence"),
 ("awakening count","approx","hypnogram","medium","W intrusions ≥1 epoch; brief arousals invisible"),
 ("arousal index","no","EEG arousal annots missing","-","no arousal labels"),
 ("AHI/apnea/hypopnea","no","no airflow/SpO2/effort @adequate fs","-","1Hz thermistor only; no desats"),
 ("ODI/nadir/hypoxic burden","no","no SpO2","-","-"),
 ("PLMI","no","no leg EMG","-","chin EMG only"),
 ("HR/arrhythmia","no","no ECG/PPG","-","-"),
 ("position features","no","no position/actigraphy","-","-"),
]
pd.DataFrame(feas,columns=["feature","computable","required","reliable","comments"]).to_csv(TAB/"sqi_feature_feasibility.csv",index=False)
print("saved eog_emg, quality, arch, sqi + 7 figs")
