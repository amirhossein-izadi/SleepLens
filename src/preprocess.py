"""
SleepLens Data Preprocessing Pipeline
====================================
Transforms raw Sleep-EDF Polysomnography (PSG) and Hypnogram EDF files into
standardized, trimmed, filtered, and robustly scaled 30-second epoch arrays (.npz).

Features:
- Dual-cohort matching (Sleep-Cassette and Sleep-Telemetry)
- 4th-order Butterworth bandpass (0.5–35.0 Hz) + 50 Hz IIR Notch filter
- Ground-truth remapping to 5 AASM classes (W, N1, N2, N3, REM)
- In-bed wake trimming (30 minutes buffer before first sleep & after last sleep)
- Robust per-record scaling using Interquartile Range (IQR)
- Multi-channel support (EEG Fpz-Cz, EEG Pz-Oz, EOG horizontal)
- Demographic integration (Age, Sex, Night from SC-subjects / ST-subjects spreadsheets)
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

# Standard AASM Stage Mapping
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
                # In SC: 'sex (F=1)': 1=Female, 2=Male
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
            # Row 0: Headers, Row 1: Subheaders, Data from Row 2
            for i in range(2, len(st_df)):
                row = st_df.iloc[i]
                if pd.isna(row[0]):
                    continue
                subj = int(row[0])
                age = int(row[1]) if not pd.isna(row[1]) else -1
                # In ST: M1/F2 -> standardize to: 1=Female, 2=Male
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

def filter_signal(signal, b_band, a_band, b_notch, a_notch):
    # Apply zero-phase forward-backward filtering
    filtered = filtfilt(b_band, a_band, signal)
    filtered = filtfilt(b_notch, a_notch, filtered)
    return filtered

def robust_scale(epochs_array):
    """
    Applies per-record Robust IQR scaling across epochs.
    epochs_array: shape (N, samples_per_epoch)
    """
    flat = epochs_array.flatten()
    median = np.median(flat)
    q75 = np.percentile(flat, 75)
    q25 = np.percentile(flat, 25)
    iqr = q75 - q25
    iqr = iqr if iqr > 1e-6 else 1.0
    scaled = (epochs_array - median) / iqr
    return scaled.astype(np.float32)

def find_matched_pairs(base_dir):
    """
    Identifies and matches all (PSG, Hypnogram) pairs in both sub-cohorts.
    """
    psg_files = sorted(glob.glob(os.path.join(base_dir, '**/*-PSG.edf'), recursive=True))
    hyp_files = sorted(glob.glob(os.path.join(base_dir, '**/*-Hypnogram.edf'), recursive=True))

    hyp_dict = {}
    for h in hyp_files:
        fname = os.path.basename(h)
        # Prefix matching: first 6 chars (e.g. SC4001 or ST7011)
        prefix = fname[:6]
        hyp_dict[prefix] = h

    pairs = []
    for p in psg_files:
        fname = os.path.basename(p)
        prefix = fname[:6]
        if prefix in hyp_dict:
            pairs.append((p, hyp_dict[prefix]))
        else:
            logger.warning(f"Unmatched PSG file found: {p}")

    return pairs

def parse_record_identifiers(psg_fname):
    """
    Extracts study type, subject ID, and night number from the filename.
    SC4001E0 -> ('cassette', 400, 1)
    ST7011J0 -> ('telemetry', 701, 1)
    """
    base = os.path.basename(psg_fname)
    study = 'cassette' if base.startswith('SC') else 'telemetry'
    subj_id = int(base[2:5])
    night = int(base[5])
    return study, subj_id, night, base.replace('-PSG.edf', '')

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

def process_record(psg_path, hyp_path, output_dir, demographics, epoch_sec=30, fs_target=100.0):
    study, subj_id, night, record_id = parse_record_identifiers(psg_path)
    out_file = os.path.join(output_dir, f"{record_id}.npz")
    
    if os.path.exists(out_file):
        return record_id, "already_exists", 0

    try:
        # 1. Read Hypnogram Annotations (with fallback for non-compliant EDF+ headers)
        try:
            hyp = pyedflib.EdfReader(hyp_path)
            onsets, durations, descriptions = hyp.readAnnotations()
            hyp.close()
        except Exception as e:
            logger.info(f"pyedflib failed on {os.path.basename(hyp_path)} ({e}); using TAL fallback parser.")
            onsets, durations, descriptions = read_annotations_fallback(hyp_path)

        epoch_labels = []
        for onset, dur, desc in zip(onsets, durations, descriptions):
            n_ep = int(round(dur / epoch_sec))
            mapped_stage = STAGE_MAP.get(desc, -1)  # -1 for Movement time, ?, or artifacts
            epoch_labels.extend([mapped_stage] * n_ep)
        epoch_labels = np.array(epoch_labels, dtype=np.int64)

        # 2. Read PSG Signals
        psg = pyedflib.EdfReader(psg_path)
        labels = psg.getSignalLabels()
        
        # Identify available channels
        fpz_idx = labels.index('EEG Fpz-Cz') if 'EEG Fpz-Cz' in labels else -1
        pz_idx = labels.index('EEG Pz-Oz') if 'EEG Pz-Oz' in labels else -1
        eog_idx = labels.index('EOG horizontal') if 'EOG horizontal' in labels else -1

        if fpz_idx == -1:
            psg.close()
            return record_id, "missing_eeg_fpz", 0

        fs_raw = psg.getSampleFrequency(fpz_idx)
        raw_fpz = psg.readSignal(fpz_idx)
        raw_pz = psg.readSignal(pz_idx) if pz_idx != -1 else None
        raw_eog = psg.readSignal(eog_idx) if eog_idx != -1 else None
        psg.close()

        # 3. Filtering
        (b_band, a_band), (b_notch, a_notch) = create_filters(fs=fs_raw)
        filt_fpz = filter_signal(raw_fpz, b_band, a_band, b_notch, a_notch)
        filt_pz = filter_signal(raw_pz, b_band, a_band, b_notch, a_notch) if raw_pz is not None else None
        filt_eog = filter_signal(raw_eog, b_band, a_band, b_notch, a_notch) if raw_eog is not None else None

        # 4. Epoch Segmentation
        samples_per_ep = int(epoch_sec * fs_raw)
        total_epochs = min(len(filt_fpz) // samples_per_ep, len(epoch_labels))
        
        ep_fpz = filt_fpz[:total_epochs * samples_per_ep].reshape(total_epochs, samples_per_ep)
        ep_pz = filt_pz[:total_epochs * samples_per_ep].reshape(total_epochs, samples_per_ep) if filt_pz is not None else None
        ep_eog = filt_eog[:total_epochs * samples_per_ep].reshape(total_epochs, samples_per_ep) if filt_eog is not None else None
        y = epoch_labels[:total_epochs]

        # 5. In-Bed Wake Trimming (Fix 24h recording bias)
        sleep_indices = np.where((y >= 1) & (y <= 4))[0]
        if len(sleep_indices) == 0:
            return record_id, "no_sleep_epochs", 0

        first_sleep = sleep_indices[0]
        last_sleep = sleep_indices[-1]
        pad = int(30 * 60 / epoch_sec)  # 60 epochs (30 min)

        start_idx = max(0, first_sleep - pad)
        end_idx = min(total_epochs, last_sleep + pad + 1)

        # Slice to trimmed in-bed window
        ep_fpz = ep_fpz[start_idx:end_idx]
        if ep_pz is not None:
            ep_pz = ep_pz[start_idx:end_idx]
        if ep_eog is not None:
            ep_eog = ep_eog[start_idx:end_idx]
        y_trimmed = y[start_idx:end_idx]
        orig_indices = np.arange(start_idx, end_idx)

        # Filter out unscored / artifact epochs (-1)
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

        # 6. Robust IQR Scaling
        scaled_fpz = robust_scale(ep_fpz)
        scaled_pz = robust_scale(ep_pz) if ep_pz is not None else np.zeros_like(scaled_fpz)
        scaled_eog = robust_scale(ep_eog) if ep_eog is not None else np.zeros_like(scaled_fpz)

        # 7. Attach Demographic Metadata
        demo_key = (study, subj_id % 100 if study == 'cassette' else subj_id % 100, night)
        demo = demographics.get(demo_key, {'age': -1, 'sex': -1, 'lights_off': ''})

        # Save to compressed .npz archive
        np.savez_compressed(
            out_file,
            x_fpz=scaled_fpz,
            x_pz=scaled_pz,
            x_eog=scaled_eog,
            y=y_valid,
            subject_id=subj_id,
            night=night,
            study=study,
            record_id=record_id,
            age=demo.get('age', -1),
            sex=demo.get('sex', -1),
            epoch_indices=orig_indices,
            fs=int(fs_raw)
        )
        return record_id, "success", len(y_valid)

    except Exception as e:
        logger.error(f"Error processing {record_id}: {e}")
        return record_id, f"error: {str(e)}", 0

def run_preprocessing(data_dir, output_dir, max_workers=4, limit=None):
    os.makedirs(output_dir, exist_ok=True)
    demographics = load_demographics(data_dir)
    pairs = find_matched_pairs(data_dir)

    if limit is not None and limit > 0:
        pairs = pairs[:limit]

    logger.info(f"Loaded {len(demographics)} demographic records.")
    logger.info(f"Commencing preprocessing for {len(pairs)} records using {max_workers} worker processes...")

    summary = {'success': 0, 'skipped': 0, 'failed': 0, 'total_epochs': 0}

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_record, psg, hyp, output_dir, demographics): psg
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
                logger.info(f"Skipped {record_id}: Already processed.")
            else:
                summary['failed'] += 1
                logger.error(f"Failed {record_id}: {status}")

    logger.info(f"Preprocessing completed: {summary}")
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SleepLens Preprocessing Pipeline")
    parser.add_argument("--data_dir", type=str, default="../SleepLens/sleep-edf-database-expanded-1.0.0",
                        help="Path to Sleep-EDF raw dataset directory")
    parser.add_argument("--output_dir", type=str, default="../SleepLens/data/processed",
                        help="Output directory for processed .npz files")
    parser.add_argument("--max_workers", type=int, default=4,
                        help="Number of parallel worker processes")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of records to process (for debugging)")
    args = parser.parse_args()

    run_preprocessing(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        max_workers=args.max_workers,
        limit=args.limit
    )
