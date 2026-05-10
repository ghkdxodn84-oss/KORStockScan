#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$SCRIPT_DIR}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
AUTO_PROMOTE="${KORSTOCKSCAN_SWING_RETRAIN_AUTO_PROMOTE:-true}"
FORCE_RETRAIN="${KORSTOCKSCAN_SWING_RETRAIN_FORCE:-false}"

LOG_DIR="$PROJECT_DIR/logs/swing_model_retrain"
STATUS_DIR="$PROJECT_DIR/data/report/swing_model_retrain/status"
LOCK_ROOT="$PROJECT_DIR/tmp"
LOG_PATH="$LOG_DIR/swing_model_retrain_${TARGET_DATE}.log"
STATUS_PATH="$STATUS_DIR/swing_model_retrain_${TARGET_DATE}.status.json"
LOCK_DIR="$LOCK_ROOT/swing_model_retrain_${TARGET_DATE}.lock"
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
  printf '  "report_type": "swing_model_retrain_status",\n' >> "$STATUS_PATH"
  printf '  "target_date": "%s",\n' "$TARGET_DATE" >> "$STATUS_PATH"
  printf '  "status": "%s",\n' "$status" >> "$STATUS_PATH"
  printf '  "reason": "%s",\n' "$reason" >> "$STATUS_PATH"
  printf '  "started_at": "%s",\n' "$STARTED_AT" >> "$STATUS_PATH"
  printf '  "finished_at": "%s",\n' "$finished_at" >> "$STATUS_PATH"
  printf '  "exit_code": %s,\n' "$exit_code" >> "$STATUS_PATH"
  printf '  "log_path": "%s",\n' "$LOG_PATH" >> "$STATUS_PATH"
  printf '  "json_artifact": "%s",\n' "$PROJECT_DIR/data/report/swing_model_retrain/swing_model_retrain_${TARGET_DATE}.json" >> "$STATUS_PATH"
  printf '  "runtime_change": "model_artifact_promote_only_if_guard_passed"\n' >> "$STATUS_PATH"
  printf '}\n' >> "$STATUS_PATH"
}

if [[ ! -x "$VENV_PY" ]]; then
  write_status "failed" 127 "venv_python_missing"
  echo "venv python missing: $VENV_PY"
  exit 127
fi

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  write_status "skipped" 75 "lock_exists"
  echo "swing model retrain already running for ${TARGET_DATE}: ${LOCK_DIR}"
  exit 75
fi
trap 'rm -rf "$LOCK_DIR"' EXIT

cd "$PROJECT_DIR"

args=(--date "$TARGET_DATE")
if [[ "$AUTO_PROMOTE" = "true" || "$AUTO_PROMOTE" = "1" ]]; then
  args+=(--auto-promote)
fi
if [[ "$FORCE_RETRAIN" = "true" || "$FORCE_RETRAIN" = "1" ]]; then
  args+=(--force)
fi

set +e
PYTHONPATH=. "$VENV_PY" -m src.model.swing_retrain_pipeline "${args[@]}"
rc=$?
set -e

if [[ "$rc" -eq 0 ]]; then
  write_status "succeeded" 0 "completed"
else
  write_status "failed" "$rc" "pipeline_failed"
fi
exit "$rc"
