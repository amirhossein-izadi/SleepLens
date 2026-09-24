"""SleepFM hypothesis test: A (tokenizer->head) vs B (base-encoder-emb->head)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
SFM = HERE.parent / "weights" / "repos" / "sleepfm-clinical" / "sleepfm"
sys.path.insert(0, str(SFM))
sys.path.insert(0, str(HERE.parent / "adapters"))

import torch
import numpy as np
import pandas as pd
import models.models as M
from canonical import load_canonical, resample_poly

base = M.SetTransformer(in_channels=1, patch_size=640, embed_dim=128, num_heads=8, num_layers=6,
                        pooling_head=8, dropout=0.3, max_seq_length=128)
sd = torch.load(str(SFM / "checkpoints/model_base/best.pt"), map_location="cpu")["state_dict"]
sd = {k.replace("module.", ""): v for k, v in sd.items()}
r = base.load_state_dict(sd, strict=False)
print("base missing:", r.missing_keys[:4], "unexpected:", r.unexpected_keys[:4])

head = M.SleepEventLSTMClassifier(embed_dim=128, num_heads=4, num_layers=1, num_classes=5,
                                  pooling_head=4, dropout=0.3, max_seq_length=8196)
sd2 = torch.load(str(SFM / "checkpoints/model_sleep_staging/best.pth"), map_location="cpu")
sd2 = {k.replace("module.", ""): v for k, v in sd2.items()}
r2 = head.load_state_dict(sd2, strict=False)
print("head missing:", r2.missing_keys[:4], "unexpected:", r2.unexpected_keys[:4])
base.eval(); head.eval()

ep = pd.read_parquet(HERE.parents[1] / "sleep-eda" / "tables" / "epochs_v3.parquet")
g = ep[(ep.stem == "SC4001") & ep.valid]
data = load_canonical("SC4001", channels=("EEG Fpz-Cz", "EEG Pz-Oz", "EOG horizontal"))
proc = []
for ch in ("EEG Fpz-Cz", "EEG Pz-Oz", "EOG horizontal"):
    x = resample_poly(data[ch].astype(np.float64), 100, 128)
    proc.append((x - x.mean()) / (x.std() or 1))
X = np.stack(proc, axis=0)

with torch.no_grad():
    for stage in ["N3", "N2", "REM", "Wake"]:
        idx = g[g.label5 == stage].epoch.values[:12]
        idx = idx[(idx + 1) * 3840 <= X.shape[1]]
        if len(idx) < 6:
            continue
        seg = np.concatenate([X[:, i * 3840:(i + 1) * 3840] for i in idx], axis=1)
        xb = torch.from_numpy(seg).float().unsqueeze(0)
        mask = torch.zeros(1, X.shape[0])
        _, emb = base(xb, mask)                     # (1,S,E) contextualized
        tok = base.patch_embedding(xb)              # (1,C,S,E)
        outB, _ = head(emb.unsqueeze(1), torch.zeros(1, 1, emb.shape[1]))
        outA, _ = head(tok, torch.zeros(1, X.shape[0], tok.shape[2]))
        print(stage,
              "B(base-emb):", [round(float((outB.argmax(-1) == i).float().mean()), 2) for i in range(5)],
              "| A(tok):", [round(float((outA.argmax(-1) == i).float().mean()), 2) for i in range(5)])
