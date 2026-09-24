# yasa 0.7.0 (device python, pip 2026-09-24)

- scikit-learn 1.7.2 installed; bundled LightGBM pickled under 0.24.2 ->
  InconsistentVersionWarning on load. Outputs validated sane on pilot
  (Wake F1 0.89 E01) but PIN THESE VERSIONS before final numbers.
- proba columns are WAKE,N1,N2,N3,REM (NOT W/R) - handled in yasa_adapter.py.
- rem_detect needs 2 EOG - unusable on our single horizontal EOG.
- predict_proba deprecated -> use hyp.proba.
