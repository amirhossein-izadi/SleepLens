#!/usr/bin/env bash
# Full features pipeline: Sleep-EDF EDF + hypnogram -> lights-off windows
# -> per-night sleep-quality parameters.
#
#   ./run_pipeline.sh                 # all nights, expert labels
#   SMOKE=1 ./run_pipeline.sh         # 2 nights end-to-end
#   PYTHON=/path/to/venv/bin/python ./run_pipeline.sh
#
# Environment overrides: PYTHON, SUBSET (cassette|telemetry|both), LIMIT,
# SOURCE (expert|<model>), FORCE_PREP=1 to rebuild windows even if they exist,
# plus SLEEPLENS_DATA / SLEEPLENS_EDF / SLEEPLENS_CLEAN / SLEEPLENS_PREDS.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python}"
SUBSET="${SUBSET:-both}"
SOURCE="${SOURCE:-expert}"
LIMIT="${LIMIT:-0}"
if [[ "${SMOKE:-0}" != "0" ]]; then
  LIMIT=2
fi

CLEAN_ROOT="${SLEEPLENS_CLEAN:-${SLEEPLENS_DATA:-$HOME/Projects/sleep-analysis/test/data}/sleepedf_clean}"
MANIFEST="$CLEAN_ROOT/manifest.csv"

echo "== [1/2] lights-off windows =="
if [[ -f "$MANIFEST" && "${FORCE_PREP:-0}" == "0" ]]; then
  echo "   $MANIFEST exists; skipping (FORCE_PREP=1 to rebuild)"
else
  "$PYTHON" prepare_windows.py --subset "$SUBSET" --limit "$LIMIT"
fi

echo
echo "== [2/2] parameter extraction (source=$SOURCE) =="
"$PYTHON" extract_features.py --source "$SOURCE" --subset "$SUBSET" --limit "$LIMIT" --resume

echo
echo "done -> reports/sqi_features_${SOURCE}_lights_off.csv"
