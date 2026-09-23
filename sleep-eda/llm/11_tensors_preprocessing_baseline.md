# 11 Tensors, preprocessing, baseline feats

## Tensors (fs 100, 30 s = 3000)
1ch [1,3000] (~12 KB f32); 2EEG [2,3000]; EEG+EOG [3,3000]; ST-full [4,3000]+marker; SC-full 3×3000 + 1 Hz aux (90). Context ×5 [5,C,3000], ×11 [11,C,3000]. Batches trivial.
## Preprocessing (justified in-data)
1) keep 100 Hz (no resample) 2) bandpass 0.3–35 + notch 50 EU 3) per-record per-channel zscore (never global) 4) SC/ST separate EMG (SC envelope stats, ST raw RMS→envelope to match) 5) map 3+4→N3, mask ?/Mov in loss 6) train 30-min trim, SQI full-night 7) 5–11 epoch context.
## Baseline tabular sample (200 epochs SC4001: mean/std/rms/ptp/zcr + rel delta/theta/alpha/sigma/beta + label)
Full: tables/baseline_features_sample.csv (200 rows). Schema: epoch,label,mean,std,rms,ptp,zcr,delta,theta,alpha,sigma,beta.
