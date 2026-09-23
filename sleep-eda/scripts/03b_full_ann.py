"""03b: full annotations via edfio (fixes 7 pyedflib fails), epochs, trim, transitions, architecture."""
from pathlib import Path
from collections import Counter, defaultdict
import csv, json
from edfio import read_edf

ROOT = Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
OUT = Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
hyps = sorted(ROOT.rglob("*-Hypnogram.edf"))
print(f"hyp files: {len(hyps)}")

epoch_counter = Counter(); event_counter = Counter(); dur_counter = Counter()
per_rec = []  # stem, cohort, n_events, n_epochs, wake_epochs, ...
trans_raw = Counter()  # (prev_raw, cur_raw) at 30s epoch level
arch_rows = []
failed = []

MAP = {"Sleep stage W":"Wake","Sleep stage 1":"N1","Sleep stage 2":"N2",
       "Sleep stage 3":"N3","Sleep stage 4":"N3","Sleep stage R":"REM"}

for p in hyps:
    stem = p.name[:6]
    cohort = "SC" if p.name.startswith("SC") else "ST"
    try:
        e = read_edf(str(p))
        anns = [(a.onset, a.duration, a.text) for a in e.annotations]
    except Exception as ex:
        failed.append((p.name, str(ex)[:150])); continue
    # expand to 30s epochs in onset order
    anns.sort(key=lambda x: x[0])
    epochs = []  # list of raw labels per 30s
    for o,d,t in anns:
        event_counter[t]+=1; dur_counter[t]+=d
        n = int(round(d/30.0))
        if abs(n*30-d) > 1e-6:
            pass
        epochs.extend([t]*n)
    for t in epochs:
        epoch_counter[t]+=1
    # transitions at epoch level
    for a,b in zip(epochs, epochs[1:]):
        trans_raw[(a,b)]+=1
    # arch: sleep onset = first N1/N2/N3/R; final sleep = last N1/N2/N3/R
    idx_sleep = [i for i,t in enumerate(epochs) if t in ("Sleep stage 1","Sleep stage 2","Sleep stage 3","Sleep stage 4","Sleep stage R")]
    if idx_sleep:
        first, last = idx_sleep[0], idx_sleep[-1]
        wake_before = first  # epochs
        wake_after = len(epochs)-1-last
    else:
        first,last,wake_before,wake_after = -1,-1,len(epochs),0
    # ? position
    q_idx = [i for i,t in enumerate(epochs) if t=="Sleep stage ?"]
    q_before = sum(1 for i in q_idx if idx_sleep and i<first) if idx_sleep else len(q_idx)
    q_after = sum(1 for i in q_idx if idx_sleep and i>last) if idx_sleep else 0
    q_mid = len(q_idx)-q_before-q_after
    per_rec.append({"stem":stem,"cohort":cohort,"file":p.name,"n_events":len(anns),
        "n_epochs":len(epochs),"wake_ep":sum(1 for t in epochs if t=="Sleep stage W"),
        "n1":sum(1 for t in epochs if t=="Sleep stage 1"),"n2":sum(1 for t in epochs if t=="Sleep stage 2"),
        "n3":sum(1 for t in epochs if t in ("Sleep stage 3","Sleep stage 4")),
        "rem":sum(1 for t in epochs if t=="Sleep stage R"),"q":len(q_idx),
        "mov":sum(1 for t in epochs if t=="Movement time"),
        "first_sleep_idx":first,"last_sleep_idx":last,"wake_before_ep":wake_before,"wake_after_ep":wake_after,
        "q_before":q_before,"q_mid":q_mid,"q_after":q_after})

print(f"OK {len(per_rec)}/197 failed {len(failed)} {failed}")
tot_ep = sum(epoch_counter.values())
print("RAW epoch distro:")
for k,v in epoch_counter.most_common():
    print(f"  {k}: {v} ({v/tot_ep*100:.2f}%)")
five = Counter()
for k,v in epoch_counter.items():
    five[MAP.get(k,f"OTHER:{k}")] += v
print("5-class:")
for k,v in five.most_common():
    print(f"  {k}: {v} ({v/tot_ep*100:.2f}%)")
print(f"imbalance max/min (5-class excl OTHER): {max(five[k] for k in ['Wake','N1','N2','N3','REM'])}/{min(five[k] for k in ['Wake','N1','N2','N3','REM'])} = {max(five[k] for k in ['Wake','N1','N2','N3','REM'])/min(five[k] for k in ['Wake','N1','N2','N3','REM']):.1f}")

# wake trim policies
def trim_stats(keep_min):
    keep_ep = int(keep_min*60/30)
    tot=Counter(); nrec=0
    for r in per_rec:
        # reconstruct? use counts: keep keep_ep wake before/after, all sleep+?+mov mid
        # wake_before/after capped
        wb = min(r["wake_before_ep"], keep_ep); wa = min(r["wake_after_ep"], keep_ep)
        # mid portion = total - wake_before - wake_after (includes all mid wake too)
        mid = r["n_epochs"]-r["wake_before_ep"]-r["wake_after_ep"]
        tot["epochs"] += wb+wa+mid
        # approx class: can't split mid wake exactly without epochs list, so approximate via totals minus trimmed wake
        # store wake trimmed
        tot["wake_kept"] += wb+wa
        nrec+=1
    return tot

print("trim approx (wake epochs kept before/after):")
for keep in [1e9, 30, 15]:
    # full recount exact using epochs would be better; do exact below with edfio re-read for precision
    pass

# exact trim: re-expand with trimming
for keep_min, tag in [(1e9,"A_no_trim"),(30,"B_30min"),(15,"C_15min")]:
    keep_ep = int(keep_min*60/30) if keep_min<1e8 else 10**9
    c = Counter()
    for p in hyps:
        try:
            e = read_edf(str(p)); anns = sorted([(a.onset,a.duration,a.text) for a in e.annotations])
        except Exception: continue
        epochs=[]
        for o,d,t in anns:
            epochs.extend([t]*int(round(d/30)))
        idx=[i for i,t in enumerate(epochs) if t in ("Sleep stage 1","Sleep stage 2","Sleep stage 3","Sleep stage 4","Sleep stage R")]
        if not idx:
            kept=epochs
        else:
            f,l=idx[0],idx[-1]
            lo=max(0,f-keep_ep); hi=min(len(epochs),l+keep_ep+1)
            kept=epochs[lo:hi]
        for t in kept:
            c[MAP.get(t,f"OTHER:{t}")] += 1
    tot=sum(c.values())
    imb = max(c[k] for k in ['Wake','N1','N2','N3','REM'])/min(c[k] for k in ['Wake','N1','N2','N3','REM'])
    print(f" {tag}: total={tot} " + ", ".join(f"{k}={v}({v/tot*100:.1f}%)" for k,v in c.most_common()) + f" imb={imb:.1f}")

# save per-recording + class distro
with open(OUT/"annotations_summary.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["raw_label","events","epochs_30s","hours","pct"])
    for k in epoch_counter.most_common():
        pass
    for k,v in epoch_counter.most_common():
        w.writerow([k,event_counter[k],v,v*30/3600,v/tot_ep*100])

with open(OUT/"subject_class_distribution.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(per_rec[0].keys())); w.writeheader(); w.writerows(per_rec)

# transition matrix raw->5class at epoch level
labels5=["Wake","N1","N2","N3","REM"]
# rebuild 5-class transitions from trans_raw
t5=Counter()
for (a,b),v in trans_raw.items():
    ma=MAP.get(a); mb=MAP.get(b)
    if ma in labels5 and mb in labels5:
        t5[(ma,mb)]+=v
# normalize rows
import json as js
mat={a:{b:0 for b in labels5} for a in labels5}
for a in labels5:
    row=sum(t5[(a,b)] for b in labels5)
    for b in labels5:
        mat[a][b]=t5[(a,b)]/row if row else 0
print("transition matrix (rows sum 1):")
for a in labels5:
    print(a, [f"{mat[a][b]:.3f}" for b in labels5])
with open(OUT/"transition_matrix.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["from/to"]+labels5)
    for a in labels5:
        w.writerow([a]+[f"{mat[a][b]:.4f}" for b in labels5])

# ? analysis
import statistics
print(f"? total epochs {epoch_counter['Sleep stage ?']}, per-rec q_before/mid/after mean: "
      f"{statistics.mean(r['q_before'] for r in per_rec):.1f}/{statistics.mean(r['q_mid'] for r in per_rec):.1f}/{statistics.mean(r['q_after'] for r in per_rec):.1f}")
print(f"wake_before mean {statistics.mean(r['wake_before_ep'] for r in per_rec):.0f} ep ({statistics.mean(r['wake_before_ep'] for r in per_rec)*30/60:.0f} min), wake_after mean {statistics.mean(r['wake_after_ep'] for r in per_rec):.0f} ep")
print("saved annotations_summary.csv subject_class_distribution.csv transition_matrix.csv")
