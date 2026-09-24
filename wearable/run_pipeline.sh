#!/usr/bin/env bash
# Full wearable pipeline: Sleep-EDF EDF -> lights-off windows -> surrogate
# features + waveforms -> subject-wise out-of-fold training -> metrics.
#
#   ./run_pipeline.sh                 # all cassette nights, rf model
#   SMOKE=1 ./run_pipeline.sh         # 2 nights + 1 fold end-to-end
#   MODELS=rf,unet1d PYTHON=/path/to/venv/bin/python ./run_pipeline.sh
#
# Environment overrides: PYTHON (all stages) or per-stage PYTHON_EXTRACT,
# PYTHON_TRAIN, PYTHON_EVAL; MODELS, SUBSET, LIMIT, JOBS, EPOCHS, FORCE_PREP=1,
# plus SLEEPLENS_DATA / SLEEPLENS_EDF / SLEEPLENS_CLEAN.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python}"
PYTHON_EXTRACT="${PYTHON_EXTRACT:-$PYTHON}"
PYTHON_TRAIN="${PYTHON_TRAIN:-$PYTHON}"
PYTHON_EVAL="${PYTHON_EVAL:-$PYTHON}"
MODELS="${MODELS:-rf}"
SUBSET="${SUBSET:-cassette}"
LIMIT="${LIMIT:-0}"
JOBS="${JOBS:-4}"
ONLY_FOLDS="${ONLY_FOLDS:-}"
SMOKE_FLAG=()
if [[ "${SMOKE:-0}" != "0" ]]; then
  LIMIT=6                      # enough nights to build the frozen folds
  ONLY_FOLDS="${ONLY_FOLDS:-0}"
  SMOKE_FLAG=(--smoke 2)
fi

CLEAN_ROOT="${SLEEPLENS_CLEAN:-${SLEEPLENS_DATA:-$HOME/Projects/sleep-analysis/test/data}/sleepedf_clean}"
MANIFEST="$CLEAN_ROOT/manifest.csv"

echo "== [1/4] lights-off windows =="
if [[ -f "$MANIFEST" && "${FORCE_PREP:-0}" == "0" ]]; then
  echo "   $MANIFEST exists; skipping (FORCE_PREP=1 to rebuild)"
else
  "$PYTHON" prepare_windows.py --subset "$SUBSET" --limit "$LIMIT"
fi

echo
echo "== [2/4] surrogate feature extraction =="
"$PYTHON_EXTRACT" extract_surrogates.py --subset "$SUBSET" --limit "$LIMIT" --jobs "$JOBS"

echo
echo "== [3/4] subject-wise out-of-fold training ($MODELS) =="
TRAIN_ARGS=(--models "$MODELS")
[[ -n "$ONLY_FOLDS" ]] && TRAIN_ARGS+=(--only-folds "$ONLY_FOLDS")
[[ ${#SMOKE_FLAG[@]} -gt 0 ]] && TRAIN_ARGS+=("${SMOKE_FLAG[@]}")
[[ -n "${EPOCHS:-}" ]] && TRAIN_ARGS+=(--epochs "$EPOCHS")
"$PYTHON_TRAIN" train_bench.py "${TRAIN_ARGS[@]}"

echo
echo "== [4/4] evaluation =="
"$PYTHON_EVAL" evaluate_bench.py --models "$MODELS"

echo
echo "done -> reports/wearable_*"
