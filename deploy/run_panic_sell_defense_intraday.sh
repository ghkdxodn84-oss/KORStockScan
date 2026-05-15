#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${PROJECT_DIR}/.venv/bin/python"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"

if [[ $# -gt 0 ]]; then
  shift
fi

LOCK_FILE="${PANIC_SELL_DEFENSE_LOCK_FILE:-$PROJECT_DIR/tmp/run_panic_sell_defense.lock}"
COOLDOWN_STATE_FILE="${PANIC_SELL_DEFENSE_COOLDOWN_STATE_FILE:-$PROJECT_DIR/tmp/run_panic_sell_defense_success.state}"
COOLDOWN_SEC="${PANIC_SELL_DEFENSE_COOLDOWN_SEC:-90}"
LOG_FILE="${PANIC_SELL_DEFENSE_LOG_FILE:-$PROJECT_DIR/logs/run_panic_sell_defense.log}"
DRY_RUN="${PANIC_SELL_DEFENSE_DRY_RUN:-0}"
NOTIFY_ENABLED="${PANIC_SELL_DEFENSE_NOTIFY_TELEGRAM_ENABLED:-true}"
NOTIFY_AUDIENCE="${PANIC_SELL_DEFENSE_NOTIFY_AUDIENCE:-all}"
NOTIFY_STATE_FILE="${PANIC_SELL_DEFENSE_NOTIFY_STATE_FILE:-$PROJECT_DIR/tmp/panic_state_telegram_notify_state.json}"
MARKET_BREADTH_COLLECT_ENABLED="${PANIC_MARKET_BREADTH_COLLECT_ENABLED:-true}"
IONICE_CLASS="${PANIC_SELL_DEFENSE_IONICE_CLASS:-2}"
IONICE_LEVEL="${PANIC_SELL_DEFENSE_IONICE_LEVEL:-7}"
NICE_LEVEL="${PANIC_SELL_DEFENSE_NICE_LEVEL:-12}"
NICE_COMMAND="${PANIC_SELL_DEFENSE_NICE_COMMAND:-nice}"
CPU_AFFINITY="${PANIC_SELL_DEFENSE_CPU_AFFINITY:-1}"

mkdir -p "$PROJECT_DIR/tmp" "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"

validate_int() {
  local value="$1"
  local fallback="$2"
  if [[ "$value" =~ ^[0-9]+$ ]]; then
    echo "$value"
  else
    echo "$fallback"
  fi
}

COOLDOWN_SEC="$(validate_int "$COOLDOWN_SEC" 90)"
IONICE_CLASS="$(validate_int "$IONICE_CLASS" 2)"
IONICE_LEVEL="$(validate_int "$IONICE_LEVEL" 7)"
NICE_LEVEL="$(validate_int "$NICE_LEVEL" 12)"

if [[ -f "$COOLDOWN_STATE_FILE" && "$COOLDOWN_SEC" -gt 0 ]]; then
  last_ts="$(date -r "$COOLDOWN_STATE_FILE" +%s 2>/dev/null || echo 0)"
  now_ts="$(date +%s)"
  elapsed=$((now_ts - last_ts))
  if [[ "$last_ts" -gt 0 && "$elapsed" -lt "$COOLDOWN_SEC" ]]; then
    remaining=$((COOLDOWN_SEC - elapsed))
    echo "[SKIP] panic sell defense cooldown active remaining=${remaining}s target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
    exit 0
  fi
fi

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "[SKIP] panic sell defense already running target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
  exit 0
fi

cmd=(env PYTHONPATH=. "$VENV_PY" -m src.engine.panic_sell_defense_report --date "$TARGET_DATE" --print-json "$@")
if [[ "$DRY_RUN" == "1" ]]; then
  cmd+=(--dry-run)
fi

if command -v taskset >/dev/null 2>&1 && [[ -n "$CPU_AFFINITY" ]] && [[ "$(nproc 2>/dev/null || echo 1)" -gt 1 ]]; then
  cmd=(taskset -c "$CPU_AFFINITY" "${cmd[@]}")
fi

if command -v ionice >/dev/null 2>&1 && [[ "$IONICE_CLASS" -ge 0 ]]; then
  cmd=(ionice -c "$IONICE_CLASS" -n "$IONICE_LEVEL" -t "${cmd[@]}")
fi

if command -v "$NICE_COMMAND" >/dev/null 2>&1; then
  cmd=("$NICE_COMMAND" -n "$NICE_LEVEL" "${cmd[@]}")
fi

started_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
echo "[START] panic sell defense target_date=${TARGET_DATE} started_at=${started_at} dry_run=${DRY_RUN}" | tee -a "$LOG_FILE"

if [[ "$MARKET_BREADTH_COLLECT_ENABLED" != "0" && "$MARKET_BREADTH_COLLECT_ENABLED" != "false" && "$MARKET_BREADTH_COLLECT_ENABLED" != "no" && "$MARKET_BREADTH_COLLECT_ENABLED" != "off" ]]; then
  echo "[START] market panic breadth collect target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
  if env PYTHONPATH=. "$VENV_PY" -m src.engine.market_panic_breadth_collector --date "$TARGET_DATE" --print-json 2>&1 | tee -a "$LOG_FILE"; then
    echo "[DONE] market panic breadth collect target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
  else
    echo "[WARN] market panic breadth collect failed target_date=${TARGET_DATE}; continuing panic report with prior/missing breadth" | tee -a "$LOG_FILE"
  fi
fi

if "${cmd[@]}" 2>&1 | tee -a "$LOG_FILE"; then
  REPORT_FILE="$PROJECT_DIR/data/report/panic_sell_defense/panic_sell_defense_${TARGET_DATE}.json"
  if [[ "$NOTIFY_ENABLED" != "0" && "$NOTIFY_ENABLED" != "false" && "$NOTIFY_ENABLED" != "no" && "$NOTIFY_ENABLED" != "off" && -f "$REPORT_FILE" ]]; then
    notify_audience="$NOTIFY_AUDIENCE"
    if [[ "$DRY_RUN" == "1" ]]; then
      notify_audience="admin"
    fi
    env PYTHONPATH=. "$VENV_PY" -m src.engine.notify_panic_state_transition \
      --report-file "$REPORT_FILE" \
      --kind panic_sell \
      --audience "$notify_audience" \
      --state-file "$NOTIFY_STATE_FILE" 2>&1 | tee -a "$LOG_FILE" || true
  fi
  touch "$COOLDOWN_STATE_FILE"
  finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
  echo "[DONE] panic sell defense target_date=${TARGET_DATE} finished_at=${finished_at}" | tee -a "$LOG_FILE"
else
  exit_code=$?
  finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
  echo "[FAIL] panic sell defense target_date=${TARGET_DATE} exit_code=${exit_code} finished_at=${finished_at}" | tee -a "$LOG_FILE"
  exit "$exit_code"
fi
