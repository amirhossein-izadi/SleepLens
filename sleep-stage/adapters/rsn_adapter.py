"""RobustSleepNet adapter: repo inference path (EDF->H5->memmap->ModuloNet, ctx 21) -> T×5.
Weights: weights/rsn-sleepedf/pretrained_model_best_model.gz = LODO sleep_edf-target
model = trained on 7 other datasets, NEVER saw Sleep-EDF -> clean zero-shot.
Repo: weights/repos/RobustSleepNet (py3.7-era code, runs on 3.10/torch2.13 for inference)."""
import sys
import torch  # FIRST - before pandas (WinError 1114 otherwise)
import numpy as np
import pandas as pd
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "weights" / "repos" / "RobustSleepNet"))
from robust_sleep_net.utils.inference.edf_to_h5 import edf_to_h5
from robust_sleep_net.utils.inference.inference import inference_on_h5
from robust_sleep_net.models.modulo_net.net import ModuloNet
from base import save_probs
from canonical import load_canonical

WEIGHTS = Path(HERE.parent / "weights" / "rsn-sleepedf" / "pretrained_model_best_model.gz").resolve()
DATA = Path(r"C:\SBU\Extra\Hachaton-Aiif\sleep-edf-dataset\sleep-edf-database-expanded-1.0.0")
_net = None

def get_net():
    global _net
    if _net is None:
        _net = ModuloNet.load(str(WEIGHTS))
        _net.eval()
    return _net

def predict_record(stem, electrodes=("EEG Fpz-Cz",)):
    psg = next((DATA / ("sleep-cassette" if stem.startswith("SC") else "sleep-telemetry")).glob(stem + "*-PSG.edf"))
    tmp = tempfile.mkdtemp()
    get_net()  # ensure load works before heavy IO
    path_to_record, _, _, _ = edf_to_h5(
        str(psg), h5_filename=f"{tmp}/record.h5",
        electrodes=list(electrodes), force=True,
        lights_on=None, lights_off=None, start_minute=False, start_30s=False)
    import shutil
    import robust_sleep_net.utils.inference.inference as inf
    # inference_on_h5 builds its own temp memmap and loads model internally; patch path via env is messy,
    # so replicate its body with our cached net:
    from robust_sleep_net.utils.inference.inference import generate_memmap_description
    from robust_sleep_net.preprocessings.h5_to_memmap import h5_to_memmaps
    from robust_sleep_net.datasets.dataset import DreemDataset
    memmap_description = generate_memmap_description(path_to_record)
    memmap_directory = tempfile.mkdtemp()
    memmap_folder, groups_description, features_description = h5_to_memmaps(
        records=[path_to_record], memmap_description=memmap_description,
        memmap_directory=memmap_directory, num_workers=1, error_tolerant=False)
    inference_dataset = DreemDataset(groups_description, features_description={},
                                     temporal_context=21,
                                     records=[f"{memmap_folder}/{x}/" for x in __import__("os").listdir(memmap_folder) if ".json" not in x])
    hypnodensity = get_net().predict_on_dataset(inference_dataset, return_prob=True, mode="arithmetic")[inference_dataset.records[0]]
    # replicate inference_on_h5 padding trim: 900 s pad -> pad_epochs trimmed each side
    pad_epochs = 900 // 30
    if pad_epochs > 0:
        hypnodensity = hypnodensity[pad_epochs:-pad_epochs]
    shutil.rmtree(memmap_directory, ignore_errors=True)
    shutil.rmtree(tmp, ignore_errors=True)
    n_ep = hypnodensity.shape[0]
    out = pd.DataFrame({"stem": stem, "epoch_index": np.arange(n_ep)})
    for j, c in enumerate(["Wake", "N1", "N2", "N3", "REM"]):
        out[f"p_{c}"] = hypnodensity[:, j]
    return out

def run(run_id, stems, **kw):
    for s in stems:
        save_probs(predict_record(s, **kw), run_id, s)
        print(run_id, s, flush=True)

if __name__ == "__main__":
    run("E20", ["SC4001", "SC4041", "ST7011"])
