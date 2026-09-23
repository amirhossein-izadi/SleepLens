"""audit perfection."""
from pathlib import Path
import pandas as pd
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables"); FIG=Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\figs")
req=['dataset_inventory.csv','recordings.csv','subjects.csv','channels.csv','annotations_summary.csv','class_distribution.csv','subject_class_distribution.csv','signal_quality.csv','transition_matrix.csv','sleep_architecture.csv','sqi_feature_feasibility.csv','eda_summary.json']
print("=== CSV/JSON ===")
for f in req:
    p=TAB/f
    if not p.exists():
        print("MISSING",f); continue
    if p.suffix==".json":
        print(f,"OK json"); continue
    try:
        df=pd.read_csv(p)
        flag="EMPTY!" if len(df)==0 else "ok"
        print(f, "rows=",len(df), "cols=",list(df.columns)[:8], flag)
    except Exception as e:
        print(f,"ERR",str(e)[:100])
print()
checks={"channel_avail.png":1,"duration_dist.png":1,"class_dist.png":1,"persubject_wake.png":1,"persubject_stacked.png":1,
 "eeg_per_stage_SC4001.png":1,"transition_matrix.png":1,"runlength.png":1,"eeg_compare.png":1,"eog_bystage.png":1,
 "emg_eog_by_stage.png":1,"cleanliness.png":1,"trim_impact.png":1,"cycles.png":1,"spatial_gradient.png":1}
for k in checks:
    print(k, "OK" if (FIG/k).exists() else "MISSING")
print("psd_n=",len(list(FIG.glob("psd_*.png"))),"spec_n=",len(list(FIG.glob("spec_*.png"))),
      "eeg30s_n=",len(list(FIG.glob("eeg30s_*.png"))),"fullnight_n=",len(list(FIG.glob("fullnight_*.png"))))
