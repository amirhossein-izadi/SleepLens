"""Chunk 1: dataset inventory (EDA Sec 1-2) - stdlib + pandas only, device python."""
import os, re, csv
from pathlib import Path
from collections import Counter

ROOT = Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
OUT = Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
OUT.mkdir(parents=True, exist_ok=True)

all_files = [p for p in ROOT.rglob("*") if p.is_file()]
print(f"TOTAL FILES: {len(all_files)}")

ext_counter = Counter(p.suffix.lower() if p.suffix else "<no-ext>" for p in all_files)
print("EXTENSIONS:", dict(ext_counter))

total_bytes = sum(p.stat().st_size for p in all_files)
print(f"TOTAL SIZE: {total_bytes/1e9:.3f} GB ({total_bytes} bytes)")

# per-dir counts
for d in [ROOT, ROOT/"sleep-cassette", ROOT/"sleep-telemetry"]:
    if d.exists():
        files = [p for p in d.glob("*") if p.is_file()]
        print(f"{d.name}: {len(files)} files")

# pattern table
psg = list(ROOT.rglob("*-PSG.edf"))
hyp = list(ROOT.rglob("*-Hypnogram.edf"))
print(f"PSG files: {len(psg)}, Hypnogram files: {len(hyp)}")

# naming conventions
# SC: SC4SSN{1,2}E0-PSG.edf ; ST: ST7SSNJ0-PSG.edf
sc_psg = [p for p in psg if p.name.startswith("SC")]
st_psg = [p for p in psg if p.name.startswith("ST")]
print(f"SC PSG: {len(sc_psg)}, ST PSG: {len(st_psg)}")
sc_hyp = [p for p in hyp if p.name.startswith("SC")]
st_hyp = [p for p in hyp if p.name.startswith("ST")]
print(f"SC Hyp: {len(sc_hyp)}, ST Hyp: {len(st_hyp)}")

# subject extraction: SC: subject = SC4SS (e.g. SC400), night = N (1/2)? Actually SC4001E0: subject 400, night 1? Check: SC4SSN
# ST: ST7SSN e.g. ST7011: subject 701? night 1?
def sc_parse(name):
    m = re.match(r"SC4(\d{2})(\d)E0-PSG\.edf", name)
    if m: return f"SC4{m.group(1)}", m.group(2)
    return None, None

def st_parse(name):
    m = re.match(r"ST7(\d{2})(\d)J0-PSG\.edf", name)
    if m: return f"ST7{m.group(1)}", m.group(2)
    return None, None

subs = set(); recs = []
for p in psg:
    if p.name.startswith("SC"):
        s,n = sc_parse(p.name)
        if s: subs.add(s)
        recs.append((s,n,"SC",p.name))
    else:
        s,n = st_parse(p.name)
        if s: subs.add(s)
        recs.append((s,n,"ST",p.name))
print(f"UNIQUE SUBJECTS (from PSG names): {len(subs)} -> {sorted(subs)[:5]} ... {sorted(subs)[-5:]}")

# pairing check: every PSG should have a Hypnogram
psg_stems = {}
for p in psg:
    # PSG: SC4001E0-PSG.edf ; Hyp: SC4001EC-Hypnogram.edf -> stem SC4001
    stem = p.name[:6]
    psg_stems.setdefault(stem, []).append(p.name)
hyp_stems = {}
for p in hyp:
    stem = p.name[:6]
    hyp_stems.setdefault(stem, []).append(p.name)

all_stems = set(list(psg_stems.keys())+list(hyp_stems.keys()))
missing_hyp = [s for s in psg_stems if s not in hyp_stems]
missing_psg = [s for s in hyp_stems if s not in psg_stems]
multi_hyp = {s:v for s,v in hyp_stems.items() if len(v)>1}
print(f"stems total: {len(all_stems)}, missing hyp: {len(missing_hyp)} {missing_hyp[:10]}, missing psg: {len(missing_psg)} {missing_psg[:10]}, multi-hyp: {len(multi_hyp)}")

# other files
others = [p for p in all_files if p.suffix.lower() not in (".edf",)]
print("NON-EDF FILES:")
for p in others:
    print(f"  {p.relative_to(ROOT)} ({p.stat().st_size} bytes)")

# size ranges per pattern
import statistics
def sizerange(files):
    ss = sorted(p.stat().st_size for p in files)
    return min(ss), max(ss), sum(ss)/len(ss) if ss else (0,0,0)

for label, files in [("PSG",psg),("HYP",hyp),("SC-PSG",sc_psg),("ST-PSG",st_psg)]:
    mn,mx,av = sizerange(files)
    print(f"{label}: n={len(files)} min={mn} max={mx} mean={av:.0f}")

# save recordings.csv skeleton (no EDF read yet)
with open(OUT/"recordings_skeleton.csv","w",newline="") as f:
    w = csv.writer(f)
    w.writerow(["stem","cohort","subject_id","night","psg_file","hyp_file","paired"])
    for stem in sorted(all_stems):
        cohort = "SC" if stem.startswith("SC") else "ST"
        if stem.startswith("SC"):
            subj = stem[:5]; night = stem[5]
        else:
            subj = stem[:5]; night = stem[5]
        pf = ";".join(psg_stems.get(stem,[])); hf=";".join(hyp_stems.get(stem,[]))
        w.writerow([stem,cohort,subj,night,pf,hf,("OK" if (stem in psg_stems and stem in hyp_stems) else "MISSING")])

# save inventory summary
with open(OUT/"dataset_inventory.csv","w",newline="") as f:
    w = csv.writer(f)
    w.writerow(["pattern","count","likely_role","size_min","size_max","notes"])
    for label, files, role, notes in [
        ("*-PSG.edf",psg,"raw signals","SC+ST PSG"),
        ("SC*-PSG.edf",sc_psg,"SC signals","sleep cassette"),
        ("ST*-PSG.edf",st_psg,"ST signals","sleep telemetry"),
        ("*-Hypnogram.edf",hyp,"annotations","hypnograms"),
        ("SC*-Hypnogram.edf",sc_hyp,"SC annotations",""),
        ("ST*-Hypnogram.edf",st_hyp,"ST annotations",""),
    ]:
        mn,mx,av = sizerange(files)
        w.writerow([label,len(files),role,mn,mx,notes])

print("saved recordings_skeleton.csv + dataset_inventory.csv to", OUT)
