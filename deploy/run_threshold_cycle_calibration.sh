#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
RUN_PHASE="${THRESHOLD_CYCLE_CALIBRATION_PHASE:-intraday}"

mkdir -p "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"

echo "[threshold-cycle] calibration start target_date=$TARGET_DATE phase=$RUN_PHASE"

PYTHONPATH=. "$VENV_PY" -m src.engine.daily_threshold_cycle_report \
  --date "$TARGET_DATE" \
  --skip-db \
  --calibration-run-phase "$RUN_PHASE" \
  --calibration-only

echo "[threshold-cycle] calibration complete target_date=$TARGET_DATE phase=$RUN_PHASE"
