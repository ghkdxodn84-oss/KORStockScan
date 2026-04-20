#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="$PROJECT_DIR/.venv/bin/python"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
LOCK_FILE="${MONITOR_SNAPSHOT_LOCK_FILE:-$PROJECT_DIR/tmp/run_monitor_snapshot.lock}"
LOG_FILE="${MONITOR_SNAPSHOT_LOG_FILE:-$PROJECT_DIR/logs/run_monitor_snapshot.log}"
TIMEOUT_SEC="${MONITOR_SNAPSHOT_TIMEOUT_SEC:-1200}"
ALLOW_PREOPEN_WITH_BOT="${ALLOW_PREOPEN_FULL_BUILD_WITH_BOT:-0}"

mkdir -p "$PROJECT_DIR/logs" "$PROJECT_DIR/tmp"
cd "$PROJECT_DIR"

# PREOPEN(08:00~09:00 KST)에는 bot_main 동작 중 full build를 막는다.
KST_HM="$(TZ=Asia/Seoul date +%H%M)"
KST_DOW="$(TZ=Asia/Seoul date +%u)" # 1=Mon ... 7=Sun
KST_HM_INT=$((10#$KST_HM))
IN_PREOPEN=0
if [[ "$KST_DOW" -ge 1 && "$KST_DOW" -le 5 && "$KST_HM_INT" -ge 800 && "$KST_HM_INT" -lt 900 ]]; then
  IN_PREOPEN=1
fi

BOT_RUNNING=0
if pgrep -f "src/bot_main.py" >/dev/null 2>&1; then
  BOT_RUNNING=1
fi

{
  flock -n 9 || {
    echo "[SKIP] run_monitor_snapshot already running (lock: $LOCK_FILE)"
    exit 0
  }

  if [[ "$IN_PREOPEN" -eq 1 && "$BOT_RUNNING" -eq 1 && "$ALLOW_PREOPEN_WITH_BOT" != "1" ]]; then
    echo "[SKIP] PREOPEN full build blocked while bot_main is running (08:00~09:00 KST)."
    echo "[HINT] set ALLOW_PREOPEN_FULL_BUILD_WITH_BOT=1 to override for emergency."
    exit 0
  fi

  echo "[INFO] run_monitor_snapshot start date=$TARGET_DATE preopen=$IN_PREOPEN bot_running=$BOT_RUNNING"
  timeout "$TIMEOUT_SEC" env PYTHONPATH=. "$VENV_PY" -m src.engine.run_monitor_snapshot --date "$TARGET_DATE"
  echo "[INFO] run_monitor_snapshot done date=$TARGET_DATE"
} 9>"$LOCK_FILE" >> "$LOG_FILE" 2>&1
