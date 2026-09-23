"""06 FINAL: run-lengths, EEG compare, EOG examples, splits, tensors, baseline feats, json, report."""
import numpy as np, csv, json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pyedflib import EdfReader
from edfio import read_edf
from collections import Counter
from scipy.signal import welch

ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
FIG=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\figs"); TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
MAP={"Sleep stage W":"Wake","Sleep stage 1":"N1","Sleep stage 2":"N2","Sleep stage 3":"N3","Sleep stage 4":"N3","Sleep stage R":"REM"}
L5=["Wake","N1","N2","N3","REM"]

# --- run-length distro (all 197, 5-class excl OTHER? include OTHER separately) ---
def all_epochs5():
    seqs=[]
    for p in sorted(ROOT.rglob("*-Hypnogram.edf")):
        e=read_edf(str(p)); anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
        ep=[]
        for o,d,t in anns: ep.extend([MAP.get(t,"OTHER")]*int(round(d/30)))
        seqs.append(ep)
    return seqs
seqs=all_epochs5()
runlens={k:[] for k in L5+["OTHER"]}
singles=Counter()
for ep in seqs:
    if not ep: continue
    cur=ep[0]; n=1
    for t in ep[1:]+[None]:
        if t==cur: n+=1
        else:
            key=cur if cur in runlens else "OTHER"
            runlens[key].append(n)
            if n==1: singles[key]+=1
            cur=t; n=1
print("median run (epochs):",{k:float(np.median(v)) if v else 0 for k,v in runlens.items()})
print("single-epoch islands:",dict(singles))
fig,ax=plt.subplots(figsize=(9,4))
ax.boxplot([runlens[k] for k in L5],labels=L5,showfliers=False)
ax.set_ylabel("run length (epochs)");ax.set_title("Stage run-length distro (median shown, outliers hidden)")
for i,k in enumerate(L5,1): ax.text(i,float(np.median(runlens[k]))+0.5,f"med {np.median(runlens[k]):.0f}",ha="center",fontsize=8)
fig.tight_layout();fig.savefig(FIG/"runlength.png",dpi=120);plt.close(fig)

# --- EEG channel compare Fpz-Cz vs Pz-Oz (SC4001, all stages bandpower) ---
def load(p):
    with EdfReader(str(p)) as f:
        n=f.signals_in_file; labels=[f.getLabel(k) for k in range(n)]
        sigs={labels[k]:np.array(f.readSignal(k),dtype=np.float64) for k in range(n)}
    return sigs
psg=ROOT/"sleep-cassette/SC4001E0-PSG.edf"; hyp=ROOT/"sleep-cassette/SC4001EC-Hypnogram.edf"
sigs=load(psg)
e=read_edf(str(hyp)); anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
ep=[]
for o,d,t in anns: ep.extend([t]*int(round(d/30)))
BANDS={"delta":(0.5,4),"theta":(4,8),"alpha":(8,13),"sigma":(11,16),"beta":(13,30)}
def bp(x,sf,band):
    fr,px=welch(x,fs=sf,nperseg=1024); m=(fr>=band[0])&(fr<=band[1]); return np.trapz(px[m],fr[m])
comp=[]
for st in L5:
    idx=[i for i,t in enumerate(ep) if MAP.get(t)==st][:6]
    for ch in ["EEG Fpz-Cz","EEG Pz-Oz"]:
        vals=[]
        for ei in idx:
            vals.append(bp(sigs[ch][ei*3000:(ei+1)*3000],100,BANDS["delta" if st=="N3" else ("alpha" if st=="Wake" else ("sigma" if st=="N2" else "theta"))]))
        comp.append((st,ch,float(np.median(vals))))
print("EEG compare (stage-relevant band med power):",comp)
fig,ax=plt.subplots(figsize=(9,4))
stages=L5; fp=[c[2] for c in comp if c[1]=="EEG Fpz-Cz"]; pz=[c[2] for c in comp if c[1]=="EEG Pz-Oz"]
x=np.arange(5);ax.bar(x-0.2,fp,0.4,label="Fpz-Cz");ax.bar(x+0.2,pz,0.4,label="Pz-Oz")
ax.set_xticks(x,stages);ax.legend();ax.set_title("Fpz-Cz vs Pz-Oz (stage-relevant band: Wake-alpha,N1-theta,N2-sigma,N3-delta,REM-theta)")
fig.tight_layout();fig.savefig(FIG/"eeg_compare.png",dpi=120);plt.close(fig)

# --- EOG examples by stage (ST7011, one 30s per stage panel) ---
psg2=ROOT/"sleep-telemetry/ST7011J0-PSG.edf"; hyp2=ROOT/"sleep-telemetry/ST7011JP-Hypnogram.edf"
s2=load(psg2); e2=read_edf(str(hyp2)); a2=sorted([(a.onset,a.duration,a.text) for a in e2.annotations])
ep2=[]
for o,d,t in a2: ep2.extend([t]*int(round(d/30)))
fig,ax=plt.subplots(5,1,figsize=(12,8),sharex=True)
for j,st in enumerate(L5):
    ii=[i for i,t in enumerate(ep2) if MAP.get(t)==st]
    ei=ii[len(ii)//2] if ii else 0
    seg=s2["EOG horizontal"][ei*3000:(ei+1)*3000]
    ax[j].plot(np.arange(3000)/100,seg,lw=0.6); ax[j].set_title(f"EOG {st} epoch {ei} (ST7011)")
ax[-1].set_xlabel("s");fig.tight_layout();fig.savefig(FIG/"eog_bystage.png",dpi=110);plt.close(fig)

# --- recordings.csv full + subjects.csv ---
hdr=pd.read_csv(TAB/"recordings_headers.csv")
sub=pd.read_csv(TAB/"subject_class_distribution.csv")
m=sub.set_index("stem")[["n_epochs","wake_ep","n1","n2","n3","rem","q","mov"]].to_dict("index")
rows=[]
for _,r in hdr.iterrows():
    stem=r.psg_file[:6]; d=m.get(stem,{})
    rows.append({"psg_file":r.psg_file,"cohort":r.cohort,"stem":stem,"duration_h":r.duration_sec/3600,
                 "n_epochs":d.get("n_epochs",""),"wake":d.get("wake_ep",""),"n1":d.get("n1",""),"n2":d.get("n2",""),
                 "n3":d.get("n3",""),"rem":d.get("rem",""),"unknown_q":d.get("q",""),"mov":d.get("mov","")})
pd.DataFrame(rows).to_csv(TAB/"recordings.csv",index=False)
# subjects from xls
sc=pd.read_excel(ROOT/"SC-subjects.xls"); sc.to_csv(TAB/"subjects_SC.csv",index=False)
print("subjects SC age mean",sc.age.mean(),"F frac",(sc["sex (F=1)"]==1).mean(),"n nights/subj",sc.groupby("subject").size().describe().to_dict())

# --- class_distribution.csv (5-class, no-trim + 30min trim) ---
tot=483419
pd.DataFrame([{"class":k,"epochs":v,"hours":v*30/3600,"pct":v/tot*100} for k,v in
 [("Wake",290365),("N2",88983),("REM",34184),("N1",25175),("?",25047),("N3",19454),("Mov",211)]]).to_csv(TAB/"class_distribution.csv",index=False)

# --- proposed subject-wise split (stratified by cohort, keep nights together) ---
# subjects: SC400..SCxxx (from stems SC400-SC4xx), ST701..; nights paired by subject prefix stem[:5]
subs=sorted(sub.stem.str[:5].unique())
print(f"unique subject-prefixes: {len(subs)}")
# stratify: ST subjects (22) vs SC (~? ) — split 70/15/15 by subject
import random
random.seed(42)
st=[s for s in subs if s.startswith("ST")]; sc=[s for s in subs if s.startswith("SC")]
print(f"ST subj {len(st)}, SC subj {len(sc)}")
random.shuffle(st); random.shuffle(sc)
def split(lst): n=len(lst); return lst[:int(n*0.7)],lst[int(n*0.7):int(n*0.85)],lst[int(n*0.85):]
trs,vas,tes=split(sc); trt,vat,tet=split(st)
train=trs+trt; val=vas+vat; test=tes+tet
def cnt(prefixes):
    sel=sub[sub.stem.str[:5].isin(prefixes)]
    return {"subjects":len(prefixes),"recordings":len(sel),"epochs":int(sel.n_epochs.sum()),
            "wake":int(sel.wake_ep.sum()),"n1":int(sel.n1.sum()),"n2":int(sel.n2.sum()),"n3":int(sel.n3.sum()),"rem":int(sel.rem.sum())}
print("train",cnt(train)); print("val",cnt(val)); print("test",cnt(test))
with open(TAB/"split_proposal.txt","w") as f:
    f.write(f"train({len(train)} subj): {sorted(train)}\nval({len(val)}): {sorted(val)}\ntest({len(test)}): {sorted(test)}\n")
    f.write(str({"train":cnt(train),"val":cnt(val),"test":cnt(test)}))

# --- baseline tabular features sample (200 epochs SC4001, cheap feats) ---
psg0=ROOT/"sleep-cassette/SC4001E0-PSG.edf"
s0=load(psg0)
feat=[]
idx_all=[i for i,t in enumerate(ep) if MAP.get(t) in L5][:200]
for ei in idx_all:
    seg=s0["EEG Fpz-Cz"][ei*3000:(ei+1)*3000]
    fr,px=welch(seg,fs=100,nperseg=1024)
    totp=np.trapz(px[(fr>=0.5)&(fr<=30)],fr[(fr>=0.5)&(fr<=30)])+1e-12
    def rel(b0,b1):
        m=(fr>=b0)&(fr<=b1); return float(np.trapz(px[m],fr[m])/totp)
    feat.append({"epoch":ei,"label":MAP[ep[ei]],"mean":float(seg.mean()),"std":float(seg.std()),
        "rms":float(np.sqrt(np.mean(seg**2))),"ptp":float(seg.max()-seg.min()),
        "zcr":float(((seg[:-1]*seg[1:])<0).mean()),"delta":rel(0.5,4),"theta":rel(4,8),"alpha":rel(8,13),"sigma":rel(11,16),"beta":rel(13,30)})
pd.DataFrame(feat).to_csv(TAB/"baseline_features_sample.csv",index=False)
print("baseline sample",len(feat))

# --- eda_summary.json ---
summ={"dataset":{"n_psg":197,"n_hyp":197,"size_gb":8.715,"cohorts":{"SC":153,"ST":44},
 "schemas":{"SC":["EEG Fpz-Cz@100","EEG Pz-Oz@100","EOG@100","Resp1Hz","EMG@1Hz envelope","Temp1Hz","Event1Hz"],
 "ST":["EEG Fpz-Cz@100","EEG Pz-Oz@100","EOG@100","EMG@100 raw","Marker@10Hz"]},
 "subjects_prefixes":len(subs),"recordings_per_subject":"mostly 2 nights paired",
 "hyp_parser":"edfio (pyedflib fails 7 ST strict-header, mne/edfio OK all 197)"},
 "labels":{"raw_RK":["W","1","2","3","4","R","?","Movement"],"map":{"W":"Wake","1":"N1","2":"N2","3+4":"N3","R":"REM"},
 "epochs":{"Wake":290365,"N2":88983,"REM":34184,"N1":25175,"?":25047,"N3":19454,"Mov":211},
 "imbalance_5class":14.9,"imbalance_30min_trim":4.6,"unknown_?_is_trailing":True,
 "transition_self":{"Wake":0.985,"N1":0.711,"N2":0.909,"N3":0.818,"REM":0.945},
 "median_run_epochs":{k:float(np.median(v)) for k,v in runlens.items()}},
 "signals":{"emg_shift":"SC 1Hz envelope +-5uV vs ST 100Hz raw +-3000uV","physio_present":"Wake-alpha,N2-spindle-ish,N3-delta,REM-EOG+EMG-atonia observed (SC4001 PSD rel: N3delta.88 REMtheta.34)",
 "no_spo2_ecg_airflow":True,"apnea_ahi_impossible":True},
 "splits":{"strategy":"subject-wise 70/15/15 stratified SC/ST, keep nights together","train":cnt(train),"val":cnt(val),"test":cnt(test)},
 "tensors":{"fs":100,"epoch_30s":3000,"configs":{"1ch":[1,3000],"2eeg":[2,3000],"eeg_eog":[3,3000],"full_sc":">=3x3000+1Hz aux","full_st":"4x3000+marker"},"context":{"x1":[1,3000],"x5":[5,3000],"x11":[11,3000]}},
 "preprocessing":["resample: already 100Hz, no need","bandpass 0.3-35 + notch 50 (EU)","per-record zscore (never global)","SC/ST separate EMG handling","label: 3+4->N3, drop ?/Mov from loss but keep for SQI","trim 30min Wake for training only, full night for SQI"]}
with open(TAB/"eda_summary.json","w") as f: json.dump(summ,f,indent=1)
print("saved final tables + figs + eda_summary.json")
