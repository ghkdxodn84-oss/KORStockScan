#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
MAX_ITERATIONS="${THRESHOLD_CYCLE_MAX_ITERATIONS:-80}"
MAX_INPUT_LINES="${THRESHOLD_CYCLE_MAX_INPUT_LINES_PER_CHUNK:-20000}"
MAX_OUTPUT_LINES="${THRESHOLD_CYCLE_MAX_OUTPUT_LINES_PER_PARTITION:-25000}"
SKIP_DB="${THRESHOLD_CYCLE_SKIP_DB:-false}"

mkdir -p "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"

echo "[threshold-cycle] postclose start target_date=$TARGET_DATE max_iterations=$MAX_ITERATIONS"

for i in $(seq 1 "$MAX_ITERATIONS"); do
  out="$(
    PYTHONPATH=. "$VENV_PY" -m src.engine.backfill_threshold_cycle_events \
      --date "$TARGET_DATE" \
      --mode incremental \
      --resume \
      --max-input-lines-per-chunk "$MAX_INPUT_LINES" \
      --max-output-lines-per-partition "$MAX_OUTPUT_LINES"
  )"
  echo "$out"
  completed="$(printf '%s' "$out" | "$VENV_PY" -c 'import json,sys; print(str(json.load(sys.stdin).get("completed", False)).lower())')"
  status="$(printf '%s' "$out" | "$VENV_PY" -c 'import json,sys; print(json.load(sys.stdin).get("status", ""))')"
  paused_reason="$(printf '%s' "$out" | "$VENV_PY" -c 'import json,sys; print(json.load(sys.stdin).get("paused_reason") or "")')"
  if [ "$completed" = "true" ]; then
    break
  fi
  if [ "$status" = "paused_by_availability_guard" ] && [ -n "$paused_reason" ]; then
    echo "[threshold-cycle] availability guard paused target_date=$TARGET_DATE reason=$paused_reason"
    break
  fi
  sleep 1
done

report_args=(--date "$TARGET_DATE")
if [ "$SKIP_DB" = "true" ]; then
  report_args+=(--skip-db)
fi

PYTHONPATH=. "$VENV_PY" -m src.engine.daily_threshold_cycle_report "${report_args[@]}"
echo "[threshold-cycle] postclose report complete target_date=$TARGET_DATE"
