# Posterior channels + spectral shape (full 459k)

Tables: `pz_full_b{0,1,2}.parquet` (recording, epoch, label, pz_delta/theta/alpha/sigma/beta, slope_2_30, alpha_peak). Method: Hann rFFT 3000 @100 Hz, rel 0.5–30; slope = log-log fit 2–30 Hz; peak = max 7–14 Hz.

## Pooled Pz-Oz medians (full; compare Fpz in 19)
Wake: low delta, alpha/beta dominant, slope shallowest (eyes-open 1/f flat), alpha_peak ~9–10 Hz present in ~60%.
N1: theta/alpha hump, peak diffuse 8–9 Hz.
N2: sigma bump + slope steepening.
N3: delta dominant, slope steepest (~−2.5 to −3), alpha_peak absent/flat.
REM: theta/alpha mixed, slope mid, peak weak.
→ Use slope as single-number depth axis (Wake > REM/N1 > N2 > N3) + alpha_peak presence as Wake/N1 marker. Pz slope separates Wake↔N3 better than any single band.

## Anterior–posterior (Fpz vs Pz, full)
Fpz owns delta-theta depth; Pz owns alpha-peak/Wake-beta. Joint [Fpz_slope, Pz_alpha] is the most compact 2-D staging map — plot at modeling time.
