#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/home/ubuntu/KORStockScan}"
VENV_PY="${PROJECT_DIR}/.venv/bin/python"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"

if [[ $# -gt 0 ]]; then
  shift
fi

cd "$PROJECT_DIR"

LOG_DIR="${PROJECT_DIR}/logs/preclose_sell_target"
STATUS_DIR="${PROJECT_DIR}/data/report/preclose_sell_target/status"
LOCK_ROOT="${PROJECT_DIR}/tmp"
LOG_PATH="${LOG_DIR}/preclose_sell_target_${TARGET_DATE}.log"
LOCK_DIR="${LOCK_ROOT}/preclose_sell_target_${TARGET_DATE}.lock"
STATUS_PATH="${STATUS_DIR}/preclose_sell_target_${TARGET_DATE}.status.json"
STARTED_AT="$(TZ=Asia/Seoul date --iso-8601=seconds)"

mkdir -p "$LOG_DIR" "$STATUS_DIR" "$LOCK_ROOT"
exec > >(tee -a "$LOG_PATH") 2>&1

write_status() {
  local status="$1"
  local exit_code="$2"
  local reason="$3"
  local finished_at
  finished_at="$(TZ=Asia/Seoul date --iso-8601=seconds)"
  printf '{\n' > "$STATUS_PATH"
  printf '  "schema_version": 1,\n' >> "$STATUS_PATH"
  printf '  "report_type": "preclose_sell_target_cron_status",\n' >> "$STATUS_PATH"
  printf '  "target_date": "%s",\n' "$TARGET_DATE" >> "$STATUS_PATH"
  printf '  "status": "%s",\n' "$status" >> "$STATUS_PATH"
  printf '  "reason": "%s",\n' "$reason" >> "$STATUS_PATH"
  printf '  "started_at": "%s",\n' "$STARTED_AT" >> "$STATUS_PATH"
  printf '  "finished_at": "%s",\n' "$finished_at" >> "$STATUS_PATH"
  printf '  "exit_code": %s,\n' "$exit_code" >> "$STATUS_PATH"
  printf '  "log_path": "%s",\n' "$LOG_PATH" >> "$STATUS_PATH"
  printf '  "json_artifact": "%s",\n' "${PROJECT_DIR}/data/report/preclose_sell_target/preclose_sell_target_${TARGET_DATE}.json" >> "$STATUS_PATH"
  printf '  "markdown_artifact": "%s",\n' "${PROJECT_DIR}/data/report/preclose_sell_target/preclose_sell_target_${TARGET_DATE}.md" >> "$STATUS_PATH"
  printf '  "runtime_change": false\n' >> "$STATUS_PATH"
  printf '}\n' >> "$STATUS_PATH"
}

if [[ ! -x "$VENV_PY" ]]; then
  write_status "failed" 127 "venv_python_missing"
  echo "venv python missing: $VENV_PY"
  exit 127
fi

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  write_status "skipped" 75 "lock_exists"
  echo "preclose sell target already running for ${TARGET_DATE}: ${LOCK_DIR}"
  exit 75
fi
trap 'rm -rf "$LOCK_DIR"' EXIT

weekday="$(date -d "$TARGET_DATE" +%u)"
if [[ "${PRE_CLOSE_ALLOW_HOLIDAY:-0}" != "1" && "$weekday" -ge 6 ]]; then
  write_status "skipped" 0 "weekend_or_holiday_guard"
  echo "skip preclose sell target report on non-trading date guard: ${TARGET_DATE}"
  exit 0
fi

set +e
PYTHONPATH=. "$VENV_PY" -m src.scanners.preclose_sell_target_report --date "$TARGET_DATE" "$@"
exit_code=$?
set -e

if [[ "$exit_code" -eq 0 ]]; then
  write_status "succeeded" 0 "completed"
else
  write_status "failed" "$exit_code" "report_command_failed"
fi
exit "$exit_code"
