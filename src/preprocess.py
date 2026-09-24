"""
SleepLens Multi-Regime Data Preprocessing Pipeline
=================================================
Transforms raw Sleep-EDF Polysomnography (PSG) and Hypnogram EDF files into
standardized, filtered, trimmed, and robustly scaled 30-second epoch arrays (.npz).

Supports Three Specialized Regimes:
1. 'telemetry' (Regime 1): 4 channels @ 100 Hz (EEG Fpz-Cz, EEG Pz-Oz, EOG horizontal, raw 100Hz EMG).
2. 'cassette'  (Regime 2): Dual-rate multi-modal (100 Hz EEG/EOG + 1 Hz Resp, Temp, EMG envelope).
3. 'unified'   (Regime 3): 3 universal channels @ 100 Hz across all 197 files.
4. 'all': Executes all missing regimes sequentially.
"""

import os
import glob
import argparse
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd
import pyedflib
from scipy.signal import butter, filtfilt, iirnotch

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SleepLensPreprocess")

STAGE_MAP = {
    'Sleep stage W': 0,
    'Sleep stage 1': 1,
    'Sleep stage 2': 2,
    'Sleep stage 3': 3,
    'Sleep stage 4': 3,  # Merge Stage 3 & 4 into N3
    'Sleep stage R': 4,
}

def load_demographics(base_dir):
    """
    Parses SC-subjects.xls and ST-subjects.xls to build subject-level metadata.
    Standardizes Sex to: 1 = Female, 2 = Male.
    """
    demographics = {}
    
    # 1. Parse Sleep-Cassette demographics
    sc_path = os.path.join(base_dir, "SC-subjects.xls")
    if os.path.exists(sc_path):
        try:
            sc_df = pd.read_excel(sc_path)
            for _, row in sc_df.iterrows():
                subj = int(row['subject'])
                night = int(row['night'])
                age = int(row['age']) if not pd.isna(row['age']) else -1
                sex = int(row['sex (F=1)']) if not pd.isna(row['sex (F=1)']) else -1
                demographics[('cassette', subj, night)] = {
                    'age': age,
                    'sex': sex,
                    'lights_off': str(row.get('LightsOff', ''))
                }
        except Exception as e:
            logger.warning(f"Could not parse SC-subjects.xls: {e}")

    # 2. Parse Sleep-Telemetry demographics
    st_path = os.path.join(base_dir, "ST-subjects.xls")
    if os.path.exists(st_path):
        try:
            st_df = pd.read_excel(st_path, header=None)
            for i in range(2, len(st_df)):
                row = st_df.iloc[i]
                if pd.isna(row[0]):
                    continue
                subj = int(row[0])
                age = int(row[1]) if not pd.isna(row[1]) else -1
                raw_sex = int(row[2]) if not pd.isna(row[2]) else -1
                sex = 2 if raw_sex == 1 else (1 if raw_sex == 2 else -1)
                
                placebo_night = int(row[3]) if not pd.isna(row[3]) else 1
                temazepam_night = int(row[5]) if not pd.isna(row[5]) else 2
                
                demographics[('telemetry', subj, placebo_night)] = {
                    'age': age,
                    'sex': sex,
                    'condition': 'placebo',
                    'lights_off': str(row[4])
                }
                demographics[('telemetry', subj, temazepam_night)] = {
                    'age': age,
                    'sex': sex,
                    'condition': 'temazepam',
                    'lights_off': str(row[6])
                }
        except Exception as e:
            logger.warning(f"Could not parse ST-subjects.xls: {e}")

    return demographics

def create_filters(fs=100.0, lowcut=0.5, highcut=35.0, notch_freq=50.0, notch_q=30.0):
    nyq = 0.5 * fs
    b_band, a_band = butter(4, [lowcut / nyq, highcut / nyq], btype='band')
    b_notch, a_notch = iirnotch(notch_freq / nyq, notch_q)
    return (b_band, a_band), (b_notch, a_notch)

def create_emg_filter(fs=100.0, lowcut=10.0, highcut=45.0, notch_freq=50.0, notch_q=30.0):
    nyq = 0.5 * fs
    b_band, a_band = butter(4, [lowcut / nyq, highcut / nyq], btype='band')
    b_notch, a_notch = iirnotch(notch_freq / nyq, notch_q)
    return (b_band, a_band), (b_notch, a_notch)

def filter_signal(sig, b_band, a_band, b_notch, a_notch):
    filtered = filtfilt(b_band, a_band, sig)
    filtered = filtfilt(b_notch, a_notch, filtered)
    return filtered

def robust_scale(epochs_array):
    flat = epochs_array.flatten()
    median = np.median(flat)
    q75 = np.percentile(flat, 75)
    q25 = np.percentile(flat, 25)
    iqr = q75 - q25
    iqr = iqr if iqr > 1e-6 else 1.0
    scaled = (epochs_array - median) / iqr
    return scaled.astype(np.float32)

def read_annotations_fallback(hyp_path):
    """Fallback parser for non-standard EDF+ hypnogram files."""
    with open(hyp_path, 'rb') as f:
        hdr = f.read(256)
        num_bytes = int(hdr[184:192].decode('ascii').strip())
        f.seek(num_bytes)
        raw_data = f.read()
    
    onsets = []
    durations = []
    descriptions = []
    for chunk in raw_data.split(b'\x00'):
        if b'\x14' in chunk:
            parts = chunk.split(b'\x14')
            parts = [p.decode('latin1', errors='ignore').strip() for p in parts if p.strip()]
            if len(parts) >= 2:
                time_part = parts[0]
                desc_part = parts[1]
                if '\x15' in time_part:
                    onset_str, dur_str = time_part.split('\x15')
                    try:
                        onset = float(onset_str.replace('+', ''))
                        dur = float(dur_str)
                    except ValueError:
                        continue
                else:
                    try:
                        onset = float(time_part.replace('+', ''))
                        dur = 30.0
                    except ValueError:
                        continue
                onsets.append(onset)
                durations.append(dur)
                descriptions.append(desc_part)
    return onsets, durations, descriptions

def get_annotations(hyp_path, epoch_sec=30):
    try:
        hyp = pyedflib.EdfReader(hyp_path)
        onsets, durations, descriptions = hyp.readAnnotations()
        hyp.close()
    except Exception as e:
        onsets, durations, descriptions = read_annotations_fallback(hyp_path)

    epoch_labels = []
    for onset, dur, desc in zip(onsets, durations, descriptions):
        n_ep = int(round(dur / epoch_sec))
        mapped_stage = STAGE_MAP.get(desc, -1)
        epoch_labels.extend([mapped_stage] * n_ep)
    return np.array(epoch_labels, dtype=np.int64)

def parse_record_identifiers(psg_fname):
    base = os.path.basename(psg_fname)
    study = 'cassette' if base.startswith('SC') else 'telemetry'
    subj_id = int(base[2:5])
    night = int(base[5])
    return study, subj_id, night, base.replace('-PSG.edf', '')

def get_in_bed_slice(y, total_epochs, epoch_sec=30):
    sleep_indices = np.where((y >= 1) & (y <= 4))[0]
    if len(sleep_indices) == 0:
        return None, None
    first_sleep = sleep_indices[0]
    last_sleep = sleep_indices[-1]
    pad = int(30 * 60 / epoch_sec)  # 60 epochs (30 min)
    start_idx = max(0, first_sleep - pad)
    end_idx = min(total_epochs, last_sleep + pad + 1)
    return start_idx, end_idx

# ==============================================================================
# Regime 1: Hospital Telemetry Specialized (4 Channels @ 100 Hz)
# ==============================================================================
def process_record_telemetry(psg_path, hyp_path, output_dir, demographics, epoch_sec=30):
    study, subj_id, night, record_id = parse_record_identifiers(psg_path)
    if study != 'telemetry':
        return record_id, "skipped_not_telemetry", 0

    out_file = os.path.join(output_dir, f"{record_id}.npz")
    if os.path.exists(out_file):
        return record_id, "already_exists", 0

    try:
        epoch_labels = get_annotations(hyp_path, epoch_sec)
        psg = pyedflib.EdfReader(psg_path)
        labels = psg.getSignalLabels()
        
        idx_fpz = labels.index('EEG Fpz-Cz')
        idx_pz  = labels.index('EEG Pz-Oz')
        idx_eog = labels.index('EOG horizontal')
        idx_emg = labels.index('EMG submental')

        fs = psg.getSampleFrequency(idx_fpz)
        raw_fpz = psg.readSignal(idx_fpz)
        raw_pz  = psg.readSignal(idx_pz)
        raw_eog = psg.readSignal(idx_eog)
        raw_emg = psg.readSignal(idx_emg)
        psg.close()

        # Filters
        (b_eeg, a_eeg), (b_notch, a_notch) = create_filters(fs=fs)
        (b_emg, a_emg), _ = create_emg_filter(fs=fs)

        filt_fpz = filter_signal(raw_fpz, b_eeg, a_eeg, b_notch, a_notch)
        filt_pz  = filter_signal(raw_pz, b_eeg, a_eeg, b_notch, a_notch)
        filt_eog = filter_signal(raw_eog, b_eeg, a_eeg, b_notch, a_notch)
        filt_emg = filter_signal(raw_emg, b_emg, a_emg, b_notch, a_notch)

        samples_per_ep = int(epoch_sec * fs)
        total_epochs = min(len(filt_fpz) // samples_per_ep, len(epoch_labels))

        ep_fpz = filt_fpz[:total_epochs * samples_per_ep].reshape(total_epochs, samples_per_ep)
        ep_pz  = filt_pz[:total_epochs * samples_per_ep].reshape(total_epochs, samples_per_ep)
        ep_eog = filt_eog[:total_epochs * samples_per_ep].reshape(total_epochs, samples_per_ep)
        ep_emg = filt_emg[:total_epochs * samples_per_ep].reshape(total_epochs, samples_per_ep)
        y = epoch_labels[:total_epochs]

        start_idx, end_idx = get_in_bed_slice(y, total_epochs, epoch_sec)
        if start_idx is None:
            return record_id, "no_sleep_epochs", 0

        ep_fpz = ep_fpz[start_idx:end_idx]
        ep_pz  = ep_pz[start_idx:end_idx]
        ep_eog = ep_eog[start_idx:end_idx]
        ep_emg = ep_emg[start_idx:end_idx]
        y_trimmed = y[start_idx:end_idx]
        orig_indices = np.arange(start_idx, end_idx)

        valid_mask = y_trimmed != -1
        ep_fpz = ep_fpz[valid_mask]
        ep_pz  = ep_pz[valid_mask]
        ep_eog = ep_eog[valid_mask]
        ep_emg = ep_emg[valid_mask]
        y_valid = y_trimmed[valid_mask]
        orig_indices = orig_indices[valid_mask]

        if len(y_valid) == 0:
            return record_id, "no_valid_epochs", 0

        # Scale channels
        sc_fpz = robust_scale(ep_fpz)
        sc_pz  = robust_scale(ep_pz)
        sc_eog = robust_scale(ep_eog)
        sc_emg = robust_scale(ep_emg)

        # 4-channel tensor: shape (N, 4, 3000)
        x_4ch = np.stack([sc_fpz, sc_pz, sc_eog, sc_emg], axis=1)

        demo_key = ('telemetry', subj_id % 100, night)
        demo = demographics.get(demo_key, {'age': -1, 'sex': -1, 'condition': 'unknown'})

        np.savez_compressed(
            out_file,
            x_4ch=x_4ch,
            x_fpz=sc_fpz,
            x_pz=sc_pz,
            x_eog=sc_eog,
            x_emg=sc_emg,
            y=y_valid,
            subject_id=subj_id,
            night=night,
            study=study,
            record_id=record_id,
            age=demo.get('age', -1),
            sex=demo.get('sex', -1),
            condition=demo.get('condition', 'unknown'),
            epoch_indices=orig_indices,
            fs=int(fs)
        )
        return record_id, "success", len(y_valid)

    except Exception as e:
        logger.error(f"Error processing {record_id} in telemetry regime: {e}")
        return record_id, f"error: {str(e)}", 0

# ==============================================================================
# Regime 2: Home Cassette Specialized (Dual-Rate Multi-Modal)
# ==============================================================================
def process_record_cassette(psg_path, hyp_path, output_dir, demographics, epoch_sec=30):
    study, subj_id, night, record_id = parse_record_identifiers(psg_path)
    if study != 'cassette':
        return record_id, "skipped_not_cassette", 0

    out_file = os.path.join(output_dir, f"{record_id}.npz")
    if os.path.exists(out_file):
        return record_id, "already_exists", 0

    try:
        epoch_labels = get_annotations(hyp_path, epoch_sec)
        psg = pyedflib.EdfReader(psg_path)
        labels = psg.getSignalLabels()
        
        idx_fpz  = labels.index('EEG Fpz-Cz')
        idx_pz   = labels.index('EEG Pz-Oz')
        idx_eog  = labels.index('EOG horizontal')
        idx_resp = labels.index('Resp oro-nasal')
        idx_temp = labels.index('Temp rectal')
        idx_emg  = labels.index('EMG submental')

        fs_fast = psg.getSampleFrequency(idx_fpz)   # 100 Hz
        fs_slow = psg.getSampleFrequency(idx_resp)  # 1 Hz

        raw_fpz  = psg.readSignal(idx_fpz)
        raw_pz   = psg.readSignal(idx_pz)
        raw_eog  = psg.readSignal(idx_eog)
        raw_resp = psg.readSignal(idx_resp)
        raw_temp = psg.readSignal(idx_temp)
        raw_emg  = psg.readSignal(idx_emg)
        psg.close()

        # 1. Filter Fast 100 Hz Streams
        (b_band, a_band), (b_notch, a_notch) = create_filters(fs=fs_fast)
        filt_fpz = filter_signal(raw_fpz, b_band, a_band, b_notch, a_notch)
        filt_pz  = filter_signal(raw_pz, b_band, a_band, b_notch, a_notch)
        filt_eog = filter_signal(raw_eog, b_band, a_band, b_notch, a_notch)

        # 2. Transform Slow 1 Hz Streams
        # Temperature: Delta T relative to nocturnal mean
        delta_temp = raw_temp - np.mean(raw_temp)
        # Respiration: Z-Score standardized
        std_resp = np.std(raw_resp)
        std_resp = std_resp if std_resp > 1e-6 else 1.0
        z_resp = (raw_resp - np.mean(raw_resp)) / std_resp
        # EMG envelope
        filt_emg_slow = raw_emg

        # Slicing
        samp_fast = int(epoch_sec * fs_fast) # 3000
        samp_slow = int(epoch_sec * fs_slow) # 30

        total_epochs = min(
            len(filt_fpz) // samp_fast,
            len(z_resp) // samp_slow,
            len(epoch_labels)
        )

        ep_fpz  = filt_fpz[:total_epochs * samp_fast].reshape(total_epochs, samp_fast)
        ep_pz   = filt_pz[:total_epochs * samp_fast].reshape(total_epochs, samp_fast)
        ep_eog  = filt_eog[:total_epochs * samp_fast].reshape(total_epochs, samp_fast)
        ep_resp = z_resp[:total_epochs * samp_slow].reshape(total_epochs, samp_slow)
        ep_temp = delta_temp[:total_epochs * samp_slow].reshape(total_epochs, samp_slow)
        ep_emg  = filt_emg_slow[:total_epochs * samp_slow].reshape(total_epochs, samp_slow)
        y = epoch_labels[:total_epochs]

        start_idx, end_idx = get_in_bed_slice(y, total_epochs, epoch_sec)
        if start_idx is None:
            return record_id, "no_sleep_epochs", 0

        ep_fpz  = ep_fpz[start_idx:end_idx]
        ep_pz   = ep_pz[start_idx:end_idx]
        ep_eog  = ep_eog[start_idx:end_idx]
        ep_resp = ep_resp[start_idx:end_idx]
        ep_temp = ep_temp[start_idx:end_idx]
        ep_emg  = ep_emg[start_idx:end_idx]
        y_trimmed = y[start_idx:end_idx]
        orig_indices = np.arange(start_idx, end_idx)

        valid_mask = y_trimmed != -1
        ep_fpz  = ep_fpz[valid_mask]
        ep_pz   = ep_pz[valid_mask]
        ep_eog  = ep_eog[valid_mask]
        ep_resp = ep_resp[valid_mask]
        ep_temp = ep_temp[valid_mask]
        ep_emg  = ep_emg[valid_mask]
        y_valid = y_trimmed[valid_mask]
        orig_indices = orig_indices[valid_mask]

        if len(y_valid) == 0:
            return record_id, "no_valid_epochs", 0

        # Scale 100 Hz streams
        sc_fpz = robust_scale(ep_fpz)
        sc_pz  = robust_scale(ep_pz)
        sc_eog = robust_scale(ep_eog)
        # Slow streams
        sc_resp = ep_resp.astype(np.float32)
        sc_temp = ep_temp.astype(np.float32)
        sc_emg  = robust_scale(ep_emg)

        # Multi-rate tensors
        x_fast = np.stack([sc_fpz, sc_pz, sc_eog], axis=1)    # (N, 3, 3000)
        x_slow = np.stack([sc_resp, sc_temp, sc_emg], axis=1) # (N, 3, 30)

        demo_key = ('cassette', subj_id % 100, night)
        demo = demographics.get(demo_key, {'age': -1, 'sex': -1})

        np.savez_compressed(
            out_file,
            x_fast=x_fast,
            x_slow=x_slow,
            x_fpz=sc_fpz,
            x_pz=sc_pz,
            x_eog=sc_eog,
            x_resp=sc_resp,
            x_temp=sc_temp,
            x_emg_slow=sc_emg,
            y=y_valid,
            subject_id=subj_id,
            night=night,
            study=study,
            record_id=record_id,
            age=demo.get('age', -1),
            sex=demo.get('sex', -1),
            epoch_indices=orig_indices,
            fs_fast=int(fs_fast),
            fs_slow=int(fs_slow)
        )
        return record_id, "success", len(y_valid)

    except Exception as e:
        logger.error(f"Error processing {record_id} in cassette regime: {e}")
        return record_id, f"error: {str(e)}", 0

# ==============================================================================
# Regime 3: Unified Combined Pipeline
# ==============================================================================
def process_record_unified(psg_path, hyp_path, output_dir, demographics, epoch_sec=30):
    study, subj_id, night, record_id = parse_record_identifiers(psg_path)
    out_file = os.path.join(output_dir, f"{record_id}.npz")
    if os.path.exists(out_file):
        return record_id, "already_exists", 0

    try:
        epoch_labels = get_annotations(hyp_path, epoch_sec)
        psg = pyedflib.EdfReader(psg_path)
        labels = psg.getSignalLabels()
        
        idx_fpz = labels.index('EEG Fpz-Cz')
        idx_pz  = labels.index('EEG Pz-Oz') if 'EEG Pz-Oz' in labels else -1
        idx_eog = labels.index('EOG horizontal') if 'EOG horizontal' in labels else -1

        fs = psg.getSampleFrequency(idx_fpz)
        raw_fpz = psg.readSignal(idx_fpz)
        raw_pz  = psg.readSignal(idx_pz) if idx_pz != -1 else None
        raw_eog = psg.readSignal(idx_eog) if idx_eog != -1 else None
        psg.close()

        (b_band, a_band), (b_notch, a_notch) = create_filters(fs=fs)
        filt_fpz = filter_signal(raw_fpz, b_band, a_band, b_notch, a_notch)
        filt_pz  = filter_signal(raw_pz, b_band, a_band, b_notch, a_notch) if raw_pz is not None else None
        filt_eog = filter_signal(raw_eog, b_band, a_band, b_notch, a_notch) if raw_eog is not None else None

        samples_per_ep = int(epoch_sec * fs)
        total_epochs = min(len(filt_fpz) // samples_per_ep, len(epoch_labels))

        ep_fpz = filt_fpz[:total_epochs * samples_per_ep].reshape(total_epochs, samples_per_ep)
        ep_pz  = filt_pz[:total_epochs * samples_per_ep].reshape(total_epochs, samples_per_ep) if filt_pz is not None else None
        ep_eog = filt_eog[:total_epochs * samples_per_ep].reshape(total_epochs, samples_per_ep) if filt_eog is not None else None
        y = epoch_labels[:total_epochs]

        start_idx, end_idx = get_in_bed_slice(y, total_epochs, epoch_sec)
        if start_idx is None:
            return record_id, "no_sleep_epochs", 0

        ep_fpz = ep_fpz[start_idx:end_idx]
        if ep_pz is not None:
            ep_pz = ep_pz[start_idx:end_idx]
        if ep_eog is not None:
            ep_eog = ep_eog[start_idx:end_idx]
        y_trimmed = y[start_idx:end_idx]
        orig_indices = np.arange(start_idx, end_idx)

        valid_mask = y_trimmed != -1
        ep_fpz = ep_fpz[valid_mask]
        if ep_pz is not None:
            ep_pz = ep_pz[valid_mask]
        if ep_eog is not None:
            ep_eog = ep_eog[valid_mask]
        y_valid = y_trimmed[valid_mask]
        orig_indices = orig_indices[valid_mask]

        if len(y_valid) == 0:
            return record_id, "no_valid_epochs", 0

        sc_fpz = robust_scale(ep_fpz)
        sc_pz  = robust_scale(ep_pz) if ep_pz is not None else np.zeros_like(sc_fpz)
        sc_eog = robust_scale(ep_eog) if ep_eog is not None else np.zeros_like(sc_fpz)

        demo_key = (study, subj_id % 100, night)
        demo = demographics.get(demo_key, {'age': -1, 'sex': -1})

        np.savez_compressed(
            out_file,
            x_fpz=sc_fpz,
            x_pz=sc_pz,
            x_eog=sc_eog,
            y=y_valid,
            subject_id=subj_id,
            night=night,
            study=study,
            record_id=record_id,
            age=demo.get('age', -1),
            sex=demo.get('sex', -1),
            epoch_indices=orig_indices,
            fs=int(fs)
        )
        return record_id, "success", len(y_valid)

    except Exception as e:
        logger.error(f"Error processing {record_id} in unified regime: {e}")
        return record_id, f"error: {str(e)}", 0

# ==============================================================================
# Driver Function
# ==============================================================================
def find_matched_pairs(base_dir):
    psg_files = sorted(glob.glob(os.path.join(base_dir, '**/*-PSG.edf'), recursive=True))
    hyp_files = sorted(glob.glob(os.path.join(base_dir, '**/*-Hypnogram.edf'), recursive=True))

    hyp_dict = {}
    for h in hyp_files:
        fname = os.path.basename(h)
        prefix = fname[:6]
        hyp_dict[prefix] = h

    pairs = []
    for p in psg_files:
        fname = os.path.basename(p)
        prefix = fname[:6]
        if prefix in hyp_dict:
            pairs.append((p, hyp_dict[prefix]))
    return pairs

def run_regime(regime_name, data_dir, output_dir, max_workers=4, limit=None):
    os.makedirs(output_dir, exist_ok=True)
    demographics = load_demographics(data_dir)
    all_pairs = find_matched_pairs(data_dir)

    if regime_name == "telemetry":
        pairs = [p for p in all_pairs if os.path.basename(p[0]).startswith("ST")]
        proc_fn = process_record_telemetry
    elif regime_name == "cassette":
        pairs = [p for p in all_pairs if os.path.basename(p[0]).startswith("SC")]
        proc_fn = process_record_cassette
    else:  # unified
        pairs = all_pairs
        proc_fn = process_record_unified

    if limit is not None and limit > 0:
        pairs = pairs[:limit]

    logger.info(f"=== Starting Preprocessing for Regime: '{regime_name}' ===")
    logger.info(f"Target Directory: {output_dir}")
    logger.info(f"Records to Process: {len(pairs)} using {max_workers} worker processes...")

    summary = {'success': 0, 'skipped': 0, 'failed': 0, 'total_epochs': 0}

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(proc_fn, psg, hyp, output_dir, demographics): psg
            for psg, hyp in pairs
        }
        for future in as_completed(futures):
            record_id, status, n_epochs = future.result()
            if status == "success":
                summary['success'] += 1
                summary['total_epochs'] += n_epochs
                logger.info(f"[{summary['success'] + summary['skipped']}/{len(pairs)}] Processed {record_id}: {n_epochs} epochs")
            elif status == "already_exists":
                summary['skipped'] += 1
                logger.info(f"Skipped {record_id}: Already exists.")
            else:
                summary['failed'] += 1
                logger.error(f"Failed {record_id}: {status}")

    logger.info(f"=== Regime '{regime_name}' Preprocessing Completed: {summary} ===")
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SleepLens Multi-Regime Preprocessing Pipeline")
    parser.add_argument("--regime", type=str, default="all", choices=["unified", "telemetry", "cassette", "all"],
                        help="Which regime to preprocess")
    parser.add_argument("--data_dir", type=str, default="../SleepLens/sleep-edf-database-expanded-1.0.0",
                        help="Path to Sleep-EDF raw dataset directory")
    parser.add_argument("--output_base", type=str, default="../SleepLens/data",
                        help="Base output directory")
    parser.add_argument("--max_workers", type=int, default=6,
                        help="Number of parallel worker processes")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of records to process (for debugging)")
    args = parser.parse_args()

    if args.regime in ["unified", "all"]:
        run_regime("unified", args.data_dir, os.path.join(args.output_base, "processed"),
                   max_workers=args.max_workers, limit=args.limit)
        
    if args.regime in ["telemetry", "all"]:
        run_regime("telemetry", args.data_dir, os.path.join(args.output_base, "processed_telemetry"),
                   max_workers=args.max_workers, limit=args.limit)
        
    if args.regime in ["cassette", "all"]:
        run_regime("cassette", args.data_dir, os.path.join(args.output_base, "processed_cassette"),
                   max_workers=args.max_workers, limit=args.limit)
