# 12 What each fig shows (text代替)

- channel_avail.png: bars EEG/EOG 197, EMG 197 (fs differs), Resp/Temp/Event 153, Marker 44.
- duration_dist.png: SC peak ~20–22 h, ST ~9–10 h, bimodal.
- class_dist.png: Wake 290k >> N2 89k > REM 34k > N1/Q 25k > N3 19k > Mov 211.
- persubject_wake.png: Wake% spread 5–95%, SC heavy right tail (daytime).
- trim_impact.png: Wake 60→29% under 30-min trim; N2 18→37%.
- transition_matrix.png: bright diagonal (.71–.99), N1 row most diffuse.
- runlength.png: REM long box, N3 near 1, N1 many singles.
- eeg_compare.png: Fpz bars taller except Wake-alpha.
- emg_eog_by_stage.png: U-shape EMG (Wake high, REM low) both cohorts; EOG cohort-variable.
- eog_bystage.png (ST7011): Wake/REM spiky saccades, N2/N3 flat.
- psd_<rec>.png ×5: N3 top <4 Hz; REM/N1 mid hump 4–8; Wake flatter + alpha.
- spec_<rec>.png ×5: N3 bright 0.5–4 band; Wake/REM brighter 8–30.
- eeg30s_<rec>.png ×5: N2 30 s slow waves + fast riding; EOG quiet.
- eeg2min_<rec>.png ×5: continuity, no dropout.
- hist_<rec>.png ×5: zero-mean bell, Fpz slightly wider than Pz.
Paths: eda/figs/*.png (35 total).
