"""Chunk 2b: header-only inventory with EdfReader (fast, no signal load)."""
from pathlib import Path
import csv
from collections import Counter, defaultdict
from pyedflib import EdfReader

ROOT = Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
OUT = Path(r"C:\SBU\Extra\Hachaton-Aiif\eda\tables")
psg_files = sorted(ROOT.rglob("*-PSG.edf"))

chan_counter = Counter()
schema_counter = Counter()
schema_examples = {}
sfreq_map = defaultdict(set)
unit_map = defaultdict(set)
rows = []
fails = []

for i, p in enumerate(psg_files):
    try:
        with EdfReader(str(p)) as f:
            n = f.signals_in_file
            labels = [f.getLabel(k) for k in range(n)]
            sfs = [f.getSampleFrequency(k) for k in range(n)]
            durs = [f.getFileDuration() for _ in range(1)][:1]
            dur = f.getFileDuration()
            # units / phys minmax for first file of each schema later
        schema = tuple(labels)
        schema_counter[schema] += 1
        if schema not in schema_examples:
            schema_examples[schema] = p.name
        for lab, fs in zip(labels, sfs):
            chan_counter[lab] += 1
            sfreq_map[lab].add(float(fs))
        rows.append((p.name, "SC" if p.name.startswith("SC") else "ST", n, "|".join(labels),
                     "|".join(str(x) for x in sfs), dur))
    except Exception as e:
        fails.append((p.name, str(e)))
    if (i+1) % 40 == 0:
        print(f"done {i+1}/{len(psg_files)}", flush=True)

print(f"OK: {len(rows)}/{len(psg_files)}, FAIL: {len(fails)} {fails[:5]}")
print(f"UNIQUE SCHEMAS: {len(schema_counter)}")
for sch, cnt in schema_counter.most_common():
    print(f"  n={cnt} ex={schema_examples[sch]} labels={list(sch)}")
print("\nCHANNELS:")
for ch, c in chan_counter.most_common():
    print(f"  {ch!r}: {c}/197 sfreqs={sorted(sfreq_map[ch])}")

with open(OUT/"channels.csv","w",newline="",encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["channel_original","present_in_n_recordings","missing_in_n","sfreqs_seen"])
    for ch, c in chan_counter.most_common():
        w.writerow([ch, c, 197-c, ";".join(str(x) for x in sorted(sfreq_map[ch]))])

with open(OUT/"schemas.csv","w",newline="",encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["schema_id","count","example_file","channels"])
    for i,(sch,cnt) in enumerate(schema_counter.most_common()):
        w.writerow([i, cnt, schema_examples[sch], "|".join(sch)])

with open(OUT/"recordings_headers.csv","w",newline="",encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["psg_file","cohort","nchan","labels","sfreqs","duration_sec"])
    w.writerows(rows)
print("saved channels.csv schemas.csv recordings_headers.csv")
