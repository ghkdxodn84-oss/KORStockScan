#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
RUN_PHASE="${THRESHOLD_CYCLE_CALIBRATION_PHASE:-intraday}"
AI_CORRECTION_PROVIDER="${THRESHOLD_CYCLE_AI_CORRECTION_PROVIDER:-openai}"
AI_CORRECTION_RESPONSE_JSON="${THRESHOLD_CYCLE_AI_CORRECTION_RESPONSE_JSON:-}"

mkdir -p "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"

trap 'failed_at="$(TZ=Asia/Seoul date +%FT%T%z)"; echo "[FAIL] threshold-cycle calibration target_date=$TARGET_DATE phase=$RUN_PHASE failed_at=$failed_at"' ERR

started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[START] threshold-cycle calibration target_date=$TARGET_DATE phase=$RUN_PHASE ai_correction_provider=$AI_CORRECTION_PROVIDER started_at=$started_at"

AI_CORRECTION_ARGS=(--ai-correction-provider "$AI_CORRECTION_PROVIDER")
if [ -n "$AI_CORRECTION_RESPONSE_JSON" ]; then
  AI_CORRECTION_ARGS=(--ai-correction-response-json "$AI_CORRECTION_RESPONSE_JSON")
fi

PYTHONPATH=. "$VENV_PY" -m src.engine.daily_threshold_cycle_report \
  --date "$TARGET_DATE" \
  --skip-db \
  --calibration-run-phase "$RUN_PHASE" \
  --calibration-only \
  "${AI_CORRECTION_ARGS[@]}"

finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] threshold-cycle calibration target_date=$TARGET_DATE phase=$RUN_PHASE finished_at=$finished_at"
