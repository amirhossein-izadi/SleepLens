"""12_gaps: close audit gaps — subjects.csv, cohort compare, minimal-channel table, mismatch, per-subject stacked fig, eeg-per-stage fig, memory, baseline ids."""
import numpy as np, pandas as pd
from pathlib import Path
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from pyedflib import EdfReader
from edfio import read_edf
MAP={"Sleep stage W":"Wake","Sleep stage 1":"N1","Sleep stage 2":"N2","Sleep stage 3":"N3","Sleep stage 4":"N3","Sleep stage R":"REM"}
ROOT=Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables"); FIG=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\figs")

# 1 subjects.csv combined
sc=pd.read_excel(ROOT/"SC-subjects.xls")
# sc subject 0..82, night 1/2; filename ss=int -> subject
sc_out=sc.rename(columns={"subject":"subject_id","night":"night","age":"age","sex (F=1)":"sex_F1","LightsOff":"lights_off"})
sc_out["cohort"]="SC"; sc_out["notes"]="healthy, home cassette"
st=pd.read_excel(ROOT/"ST-subjects.xls",header=None)
# rows 2..: Nr Age M1/F2 placeboNight placeboOff temazNight temazOff
rows=[]
for i in range(2,len(st)):
    r=st.iloc[i]
    rows.append({"subject_id":f"ST{int(r[0]):02d}","age":int(r[1]),"sex":int(r[2]),
                 "placebo_night":int(r[3]),"placebo_off":str(r[4]),"temaz_night":int(r[5]),"temaz_off":str(r[6])})
st_out=pd.DataFrame(rows); st_out["cohort"]="ST"; st_out["notes"]="mild insomnia, placebo/temazepam crossover"
sc_out.to_csv(TAB/"subjects_SC.csv",index=False)
st_out.to_csv(TAB/"subjects_ST.csv",index=False)
# combined subjects.csv per spec (one row per subject-prefix)
sub=pd.read_csv(TAB/"subject_class_distribution.csv")
agg=sub.groupby([sub.stem.str[:5],sub.cohort]).agg(recordings=("stem","count"),epochs=("n_epochs","sum")).reset_index()
agg.columns=["subject_prefix","cohort","recordings","epochs"]
# attach age/sex where SC
age_map={int(r.subject):(r.age,int(r["sex (F=1)"])) for _,r in sc.drop_duplicates("subject").iterrows()}
agg["age"]=agg.apply(lambda r: age_map.get(int(r.subject_prefix[3:5]),(None,None))[0] if r.cohort=="SC" else None,axis=1)
agg.to_csv(TAB/"subjects.csv",index=False)
print("subjects.csv",len(agg))

# 2 cohort_compare.csv
hdr=pd.read_csv(TAB/"recordings_headers.csv")
ann=sub
coh=[]
for c in ["SC","ST"]:
    h=hdr[hdr.cohort==c]; a=ann[ann.cohort==c]
    coh.append({"cohort":c,"subjects":a.stem.str[:5].nunique(),"recordings":len(h),
        "dur_h_mean":h.duration_sec.mean()/3600,"nchan":h.nchan.iloc[0] if len(h) else None,
        "wake_pct":a.wake_ep.sum()/a.n_epochs.sum()*100,"n1":a.n1.sum(),"n2":a.n2.sum(),"n3":a.n3.sum(),"rem":a.rem.sum()})
pd.DataFrame(coh).to_csv(TAB/"cohort_compare.csv",index=False)
print(pd.DataFrame(coh).to_string())

# 3 minimal_channel.csv A-G with 6 criteria
fish=pd.read_csv(TAB/"fisher_pairs.csv",index_col=0)
mc=[
 ("A Fpz-Cz only","frontal slow/K/N3 + transitions","197/197 100Hz","clean both","FisherEEG 8.30","1 EEG","strong Wake/N1/N2/N3, weaker REM"),
 ("B Pz-Oz only","posterior alpha/Wake","197/197 100Hz","clean both","weaker N1/N3 (see eeg_compare)","1 EEG","Wake good, N3/N1 weaker"),
 ("C 2×EEG","spatial gain","197/197","clean",">A (add Pz)","2 EEG","best EEG-only"),
 ("D EEG+EOG","+slow/rapid eye mov, N1/REM","197/197","clean","Fisher 9.22 (+11%)","2-3 ch","excellent info/sensor, RECOMMENDED minimal"),
 ("E EEG+EMG","atonia Wake/REM","SC1Hz env/ST100Hz raw MISMATCH","cohort-specific","REM gain","2-3 ch","helps REM, needs separate norms"),
 ("F EEG+EOG+EMG","complete reduced staging","core 197, EMG mismatch","see cleanliness","best","3-4 ch","strongest reduced, REFERENCE"),
 ("G +Resp/Temp","sleep-context only","SC153 1Hz","noisy","~0 staging","5+ ch","SQI context, no staging gain"),
]
pd.DataFrame(mc,columns=["config","physio_coverage","availability","quality","stage_sep","hardware","usefulness"]).to_csv(TAB/"minimal_channel.csv",index=False)

# 4 epoch_mismatch.csv: signal epochs vs hyp epochs per rec (sample headers + sub)
hdr["sig_epochs"]=hdr.duration_sec/30
m=sub.set_index("stem")["n_epochs"]
rows2=[]
for _,r in hdr.iterrows():
    stem=r.psg_file[:6]
    rows2.append({"psg_file":r.psg_file,"sig_epochs":r.duration_sec/30,"hyp_epochs":m.get(stem,None),
                  "diff":(m.get(stem,0)-r.duration_sec/30) if stem in m.index else None})
pd.DataFrame(rows2).to_csv(TAB/"epoch_mismatch.csv",index=False)
print("mismatch example:",pd.DataFrame(rows2).head(3).to_string())
print("mean hyp-sig diff (epochs):",pd.DataFrame(rows2)["diff"].mean())

# 5 per-subject stacked fig (top 30 recs by epochs)
top=sub.sort_values("n_epochs",ascending=False).head(30)
fig,ax=plt.subplots(figsize=(12,5))
b=ax.bar(top.stem,top.wake_ep,label="Wake"); b=ax.bar(top.stem,top.n1,bottom=top.wake_ep,label="N1")
b=ax.bar(top.stem,top.n2,bottom=top.wake_ep+top.n1,label="N2"); b=ax.bar(top.stem,top.n3,bottom=top.wake_ep+top.n1+top.n2,label="N3")
b=ax.bar(top.stem,top.rem,bottom=top.wake_ep+top.n1+top.n2+top.n3,label="REM")
ax.set_xticklabels(top.stem,rotation=90,fontsize=7); ax.legend(fontsize=8); ax.set_title("Per-recording stacked classes (top30 by epochs)")
fig.tight_layout(); fig.savefig(FIG/"persubject_stacked.png",dpi=120); plt.close(fig)

# 6 eeg per-stage examples (SC4001, Fpz-Cz 30s each stage in one fig)
psg=ROOT/"sleep-cassette/SC4001E0-PSG.edf"; hyp=ROOT/"sleep-cassette/SC4001EC-Hypnogram.edf"
e=read_edf(str(hyp)); anns=sorted([(a.onset,a.duration,a.text) for a in e.annotations])
ep=[]
for o,d,t in anns: ep.extend([t]*int(round(d/30)))
with EdfReader(str(psg)) as f:
    k=f.getLabel([f.getLabel(j) for j in range(f.signals_in_file)].index("EEG Fpz-Cz")) if False else None
    # simpler: index 0 is Fpz-Cz
    fig,ax=plt.subplots(5,1,figsize=(12,8),sharex=True,sharey=True)
    for j,st in enumerate(["Wake","N1","N2","N3","REM"]):
        raw={"Wake":"Sleep stage W","N1":"Sleep stage 1","N2":"Sleep stage 2","N3":"Sleep stage 3","REM":"Sleep stage R"}[st]
        idx=[i for i,t in enumerate(ep) if t==raw and (i+1)*3000<=f.samples_in_file(0)][5]
        seg=np.array(f.readSignal(0,idx*3000,3000),dtype=np.float64)
        ax[j].plot(np.arange(3000)/100,seg,lw=0.6); ax[j].set_title(f"Fpz-Cz {st} epoch {idx}")
        ax[j].set_ylim(-150,150)
    ax[-1].set_xlabel("s"); fig.tight_layout(); fig.savefig(FIG/"eeg_per_stage_SC4001.png",dpi=110); plt.close(fig)

# 7 memory table
mem=[{"config":"[1,3000] f32","bytes":12000},{"config":"[3,3000]","bytes":36000},{"config":"[5,3,3000] ctx5","bytes":180000},{"config":"[11,3,3000] ctx11","bytes":396000},{"config":"batch64 ctx11","bytes":25344000}]
pd.DataFrame(mem).to_csv(TAB/"tensor_memory.csv",index=False)

# 8 baseline ids: rebuild sample with subject/recording/epoch_index (reuse meso subset columns)
m3=pd.read_csv(TAB/"meso_features_3k.csv")
m3.rename(columns={"file":"recording_id","stage":"label"}).assign(subject_id=lambda d:d.recording_id.str[:5]).to_csv(TAB/"baseline_features.csv",index=False)
print("saved subjects, cohort_compare, minimal_channel, mismatch, stacked fig, per-stage eeg, memory, baseline_features")
