#!/usr/bin/env bash
# Full SDI pipeline: Sleep-EDF EDF -> lights-off windows -> per-epoch SDI/REM
# inference -> night-level sleep-quality composite.
#
#   ./run_pipeline.sh                 # all nights, expert stage mask
#   SMOKE=1 ./run_pipeline.sh         # 2 nights end-to-end
#   PYTHON=/path/to/venv/bin/python ./run_pipeline.sh
#
# Environment overrides: PYTHON, SUBSET (cassette|telemetry|both), LIMIT,
# STAGE_SOURCE (expert|<model>), FORCE_PREP=1, SQI_FEATURES=<csv|none>,
# plus SLEEPLENS_DATA / SLEEPLENS_EDF / SLEEPLENS_CLEAN / SLEEPLENS_PREDS.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python}"
SUBSET="${SUBSET:-both}"
STAGE_SOURCE="${STAGE_SOURCE:-expert}"
LIMIT="${LIMIT:-0}"
if [[ "${SMOKE:-0}" != "0" ]]; then
  LIMIT=2
fi

CLEAN_ROOT="${SLEEPLENS_CLEAN:-${SLEEPLENS_DATA:-$HOME/Projects/sleep-analysis/test/data}/sleepedf_clean}"
MANIFEST="$CLEAN_ROOT/manifest.csv"

echo "== [1/3] lights-off windows =="
if [[ -f "$MANIFEST" && "${FORCE_PREP:-0}" == "0" ]]; then
  echo "   $MANIFEST exists; skipping (FORCE_PREP=1 to rebuild)"
else
  "$PYTHON" prepare_windows.py --subset "$SUBSET" --limit "$LIMIT"
fi

echo
echo "== [2/3] SDI inference (device chosen automatically) =="
"$PYTHON" infer_sdi.py --subset "$SUBSET" --limit "$LIMIT" --resume

echo
echo "== [3/3] night-level sleep-quality estimate =="
SQI="${SQI_FEATURES:-../features/reports/sqi_features_${STAGE_SOURCE}_lights_off.csv}"
if [[ "$SQI" == "none" || ! -f "$SQI" ]]; then
  echo "   no SQI feature table at $SQI; running without the optional join"
  "$PYTHON" estimate_quality.py --stage-source "$STAGE_SOURCE" --limit "$LIMIT"
else
  "$PYTHON" estimate_quality.py --stage-source "$STAGE_SOURCE" --limit "$LIMIT" --sqi-features "$SQI"
fi

echo
echo "done -> reports/sdi_composite_${STAGE_SOURCE}_lights_off.csv"
