#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
DIFF_DAYS="${DIFF_DAYS:-3}"
LOCK_FILE="${TUNING_MONITORING_LOCK_FILE:-$PROJECT_DIR/tmp/run_tuning_monitoring_postclose.lock}"
LOCK_WAIT_SEC="${TUNING_MONITORING_LOCK_WAIT_SEC:-60}"
MAX_RETRIES="${TUNING_MONITORING_MAX_RETRIES:-2}"
RETRY_DELAY_SEC="${TUNING_MONITORING_RETRY_DELAY_SEC:-10}"
STATUS_DIR="${TUNING_MONITORING_STATUS_DIR:-$PROJECT_DIR/data/report/tuning_monitoring/status}"
STATUS_FILE="${TUNING_MONITORING_STATUS_FILE:-$STATUS_DIR/tuning_monitoring_postclose_${TARGET_DATE}.json}"
DRY_RUN="${TUNING_MONITORING_DRY_RUN:-0}"

mkdir -p "$PROJECT_DIR/logs" "$PROJECT_DIR/tmp" "$STATUS_DIR"
cd "$PROJECT_DIR"

START_DATE="$(TZ=Asia/Seoul date -d "$TARGET_DATE -$((DIFF_DAYS - 1)) days" +%F)"

validate_int() {
  local value="$1"
  local fallback="$2"
  if [[ "$value" =~ ^[0-9]+$ ]]; then
    echo "$value"
  else
    echo "$fallback"
  fi
}

LOCK_WAIT_SEC="$(validate_int "$LOCK_WAIT_SEC" 60)"
MAX_RETRIES="$(validate_int "$MAX_RETRIES" 2)"
RETRY_DELAY_SEC="$(validate_int "$RETRY_DELAY_SEC" 10)"

write_status() {
  local overall_status="$1"
  local failed_step="${2:-}"
  local exit_code="${3:-0}"
  local finished="${4:-0}"
  env PYTHONPATH=. "$VENV_PY" - "$STATUS_FILE" "$TARGET_DATE" "$START_DATE" "$overall_status" "$failed_step" "$exit_code" "$finished" <<'PY'
import json
import sys
from datetime import datetime
from pathlib import Path

path = Path(sys.argv[1])
target_date, start_date, overall_status, failed_step, exit_code, finished = sys.argv[2:8]
payload = {}
if overall_status != "running" and path.exists():
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
payload.setdefault("target_date", target_date)
payload.setdefault("start_date", start_date)
payload.setdefault("started_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
payload.setdefault("steps", [])
payload["status"] = overall_status
payload["failed_step"] = failed_step or None
payload["exit_code"] = int(exit_code or 0)
if finished == "1":
    payload["finished_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
PY
}

record_step() {
  local step_name="$1"
  local status="$2"
  local attempt="$3"
  local exit_code="$4"
  local command_text="$5"
  env PYTHONPATH=. "$VENV_PY" - "$STATUS_FILE" "$step_name" "$status" "$attempt" "$exit_code" "$command_text" <<'PY'
import json
import sys
from datetime import datetime
from pathlib import Path

path = Path(sys.argv[1])
step_name, status, attempt, exit_code, command_text = sys.argv[2:7]
payload = {}
if path.exists():
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
payload.setdefault("steps", [])
payload["steps"].append(
    {
        "step": step_name,
        "status": status,
        "attempt": int(attempt),
        "exit_code": int(exit_code),
        "command": command_text,
        "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
)
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
PY
}

run_step() {
  local step_name="$1"
  shift
  local attempt=1
  local status=0
  local command_text="$*"

  for attempt in $(seq 1 "$MAX_RETRIES"); do
    record_step "$step_name" "started" "$attempt" 0 "$command_text"
    if [[ "$DRY_RUN" == "1" ]]; then
      echo "[DRY_RUN] $step_name: $command_text"
      record_step "$step_name" "success" "$attempt" 0 "$command_text"
      return 0
    fi

    set +e
    "$@"
    status=$?
    set -e

    if [[ "$status" -eq 0 ]]; then
      record_step "$step_name" "success" "$attempt" 0 "$command_text"
      return 0
    fi

    record_step "$step_name" "failed" "$attempt" "$status" "$command_text"
    if [[ "$attempt" -lt "$MAX_RETRIES" ]]; then
      echo "[WARN] $step_name failed attempt=${attempt}/${MAX_RETRIES}; retrying in ${RETRY_DELAY_SEC}s"
      sleep "$RETRY_DELAY_SEC"
    fi
  done

  return "$status"
}

main() {
  write_status "running" "" 0 0

  run_step "build_parquet_pipeline_events" env PYTHONPATH=. "$VENV_PY" -m src.engine.build_tuning_monitoring_parquet \
    --dataset pipeline_events \
    --single-date "$TARGET_DATE"

  run_step "build_parquet_post_sell" env PYTHONPATH=. "$VENV_PY" -m src.engine.build_tuning_monitoring_parquet \
    --dataset post_sell \
    --single-date "$TARGET_DATE"

  run_step "build_parquet_system_metric_samples" env PYTHONPATH=. "$VENV_PY" -m src.engine.build_tuning_monitoring_parquet \
    --dataset system_metric_samples \
    --single-date "$TARGET_DATE"

  run_step "compare_tuning_shadow_diff" env PYTHONPATH=. "$VENV_PY" -m src.engine.compare_tuning_shadow_diff \
    --start "$START_DATE" \
    --end "$TARGET_DATE"

  run_step "gemini_scalping_pattern_lab" "$PROJECT_DIR/analysis/gemini_scalping_pattern_lab/run.sh"
  run_step "claude_scalping_pattern_lab" "$PROJECT_DIR/analysis/claude_scalping_pattern_lab/run_all.sh"

  write_status "success" "" 0 1
  echo "[INFO] tuning monitoring postclose completed status_file=$STATUS_FILE"
}

set +e
flock -w "$LOCK_WAIT_SEC" "$LOCK_FILE" bash -c "$(declare -f validate_int write_status record_step run_step main); set -euo pipefail; PROJECT_DIR='$PROJECT_DIR' VENV_PY='$VENV_PY' TARGET_DATE='$TARGET_DATE' START_DATE='$START_DATE' STATUS_FILE='$STATUS_FILE' MAX_RETRIES='$MAX_RETRIES' RETRY_DELAY_SEC='$RETRY_DELAY_SEC' DRY_RUN='$DRY_RUN'; main"
RUN_STATUS=$?
set -e

if [[ "$RUN_STATUS" -ne 0 ]]; then
  write_status "failed" "see_steps" "$RUN_STATUS" 1
  echo "[ERROR] tuning monitoring postclose failed status=${RUN_STATUS} status_file=$STATUS_FILE"
  exit "$RUN_STATUS"
fi
