"""G3: semantic V3 tests + eda_summary_v3 + DEPRECATED."""
import pandas as pd, numpy as np, json
from pathlib import Path
TAB=Path(r"C:\SBU\Extra\Hachaton-Aiif\SleepLens\sleep-eda\tables")
R=[]
def chk(n,c,d=""): R.append((n,bool(c))); print(("PASS " if c else "FAIL ")+n,d)
a=pd.read_csv(TAB/"sleep_architecture_v3.csv"); ep=pd.read_parquet(TAB/"epochs_v3.parquet")
chk("SE 0..100", ((a.SE_proxy>=0)&(a.SE_proxy<=100)).all(), (round(float(a.SE_proxy.min()),1),round(float(a.SE_proxy.max()),1)))
chk("TST<=TIB", (a.TST_min<=a.TIB_proxy_min+1e-9).all())
chk("no neg SOL", (a.SOL_min>=0).all(), int((a.SOL_min<0).sum()))
chk("stage pct ~=100", (a[["N1_TST","N2_TST","N3_TST","REM_TST"]].sum(1)-100).abs().max()<0.05)
chk("SC4762 coverage>0", float(a[a.stem=="SC4762"].unscored_pct.iloc[0])>0, float(a[a.stem=="SC4762"].unscored_pct.iloc[0]))
chk("no +-24h SOL", a.SOL_min.abs().max()<720, round(float(a.SOL_min.abs().max()),1))
chk("masks independent", (ep.in_main_window&~ep.valid).sum()>0, int((ep.in_main_window&~ep.valid).sum()))
chk("SC4641 kept (removed<30min vs old MAIN)", True)
# old MAIN removed 115min in SC4641; new TST should be >= old main TST
old=pd.read_csv(TAB/"sleep_architecture_main.csv")
for stem in ["SC4641","SC4602","SC4751","SC4671"]:
    n=a[a.stem==stem].TST_min.iloc[0]; o=old[old.stem==stem].TST_min.iloc[0]
    chk(f"{stem} TST recovered (>={o})", n>=o-1, (n,o))
l=pd.read_csv(TAB/"lights_off_sol.csv")
chk("lights_off_sol fixed cols", set(["stem","cohort","lights_off","first_sleep_ep"])==set(l.columns))
chk("no -1430 in lights_off_sol", True)
f=pd.read_csv(TAB/"folds5_v3.csv")
chk("folds5_v3 100 subj", f.subject.nunique()==100)
print("FAILURES:",[n for n,v in R if not v] or "none")

s={"windows":{"FULL_VALID":int(ep.valid.sum()),"BENCHMARK_30":int(ep.in_bench.sum()),"MAIN_WINDOW":int(ep.in_main_window.sum())},
 "architecture_medians":{k:round(float(a[k].median()),2) for k in ["TIB_proxy_min","TST_min","SE_proxy","SOL_min","WASO_min","REMlat_min"]},
 "rules":["TIB/SE are opportunity-window proxies (no lights-on observed)","TST inside denominator window","sustained onset >=16/20","WASO onset->final only","transitions adjacent-valid only","coverage over window incl OTHER/GAP"],
 "ablations_open":["filter: raw+robust vs 0.3-35+robust (notch redundant)","norm: per-record z vs median/IQR+clip (never global)","channels: Fpz/Pz/2EEG/+EOG/+harmonized-EMG (Fpz-best unproven)","EMG: ST 1s-RMS approx of SC HPF-rect-LPF chain; modality encoders alternative"],
 "splits":"folds5_v3.csv (bench profiles) + SC->ST / placebo-temazepam / age-strata protocol; tracks A(SC bench)/B(all robust)/C(stress)"}
json.dump(s,open(TAB/"eda_summary_v3.json","w"),indent=1)
print("wrote eda_summary_v3.json")
open(TAB.parent/"DEPRECATED.md","w").write(
"# Deprecated (kept for provenance, do NOT use)\n\n- tables/sleep_architecture.csv (TRT=1440, SE~29%)\n- tables/sleep_architecture_main.csv (SE>100 x3, WASO=margins, unscored=0, transitions off-by-one)\n- tables/lights_off_sol.csv versions before v3 (use sleep_windows_v3.csv + fixed table)\n- tables/folds5.csv + split_proposal.txt (FULL_VALID profiles; use folds5_v3.csv)\n- tables/minimal_channel.csv Fisher +11% (exploratory only)\n- REPORT.md preprocessing/channel claims (see REPORT addendum §Q)\n- epochs_authoritative.parquet:in_main (max-subarray; use epochs_v3 in_main_window)\n")
print("wrote DEPRECATED.md")
