#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${PROJECT_DIR}/.venv/bin/python"
MODE="${1:-full}"

LOCK_FILE="${PROJECT_DIR}/tmp/run_error_detection.lock"
LOG_FILE="${PROJECT_DIR}/logs/run_error_detection.log"
REPORT_FILE="${PROJECT_DIR}/data/report/error_detection/error_detection_$(TZ=Asia/Seoul date +%F).json"

mkdir -p "$PROJECT_DIR/tmp" "$PROJECT_DIR/logs"
touch "$LOG_FILE"
cd "$PROJECT_DIR"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S') [SKIP] error detection already running mode=${MODE}" | tee -a "$LOG_FILE"
    exit 0
fi

started_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
echo "[START] error detection mode=${MODE} started_at=${started_at}" | tee -a "$LOG_FILE"

if PYTHONPATH=. "$VENV_PY" -m src.engine.error_detector --mode "$MODE" 2>&1 | tee -a "$LOG_FILE"; then
    if [ -f "$REPORT_FILE" ]; then
        PYTHONPATH=. "$VENV_PY" -m src.engine.notify_error_detection_admin \
            --report-file "$REPORT_FILE" \
            --mode "$MODE" \
            --log-file "$LOG_FILE" 2>&1 | tee -a "$LOG_FILE" || true
    else
        echo "[WARN] error detection report missing, Telegram notify skipped report_file=${REPORT_FILE}" | tee -a "$LOG_FILE"
    fi
    finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
    echo "[DONE] error detection mode=${MODE} finished_at=${finished_at}" | tee -a "$LOG_FILE"
else
    exit_code=$?
    finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
    echo "[FAIL] error detection mode=${MODE} exit_code=${exit_code} finished_at=${finished_at}" | tee -a "$LOG_FILE"
    exit "$exit_code"
fi
