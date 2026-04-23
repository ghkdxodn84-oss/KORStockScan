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
PROFILE="${MONITOR_SNAPSHOT_PROFILE:-full}"
IO_DELAY_SEC="${MONITOR_SNAPSHOT_IO_DELAY_SEC:-0}"
START_JITTER_SEC="${MONITOR_SNAPSHOT_START_JITTER_SEC:-0}"
SKIP_SERVER_COMPARISON="${MONITOR_SNAPSHOT_SKIP_SERVER_COMPARISON:-0}"
NOTIFY_ADMIN="${MONITOR_SNAPSHOT_NOTIFY_ADMIN:-0}"
LOCK_WAIT_SEC="${MONITOR_SNAPSHOT_LOCK_WAIT_SEC:-0}"
ALLOW_EXISTING_FULL_BUILD_WITH_BOT="${ALLOW_EXISTING_FULL_BUILD_WITH_BOT:-0}"

if [[ -z "${MONITOR_SNAPSHOT_LOCK_WAIT_SEC:-}" ]]; then
  if [[ "$PROFILE" == "full" ]]; then
    LOCK_WAIT_SEC=180
  else
    LOCK_WAIT_SEC=0
  fi
fi

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
if pgrep -f "[b]ot_main[.]py" >/dev/null 2>&1; then
  BOT_RUNNING=1
fi

SAFE_PROFILE="${PROFILE//-/_}"
MANIFEST_PATH="$PROJECT_DIR/data/report/monitor_snapshots/manifests/monitor_snapshot_manifest_${TARGET_DATE}_${SAFE_PROFILE}.json"

{
  flock -w "$LOCK_WAIT_SEC" 9 || {
    echo "[SKIP] run_monitor_snapshot already running after wait=${LOCK_WAIT_SEC}s (lock: $LOCK_FILE)"
    exit 0
  }

  if [[ "$IN_PREOPEN" -eq 1 && "$BOT_RUNNING" -eq 1 && "$ALLOW_PREOPEN_WITH_BOT" != "1" ]]; then
    echo "[SKIP] PREOPEN full build blocked while bot_main is running (08:00~09:00 KST)."
    echo "[HINT] set ALLOW_PREOPEN_FULL_BUILD_WITH_BOT=1 to override for emergency."
    exit 0
  fi

  if [[ "$PROFILE" == "full" && "$BOT_RUNNING" -eq 1 && -f "$MANIFEST_PATH" && "$ALLOW_EXISTING_FULL_BUILD_WITH_BOT" != "1" ]]; then
    echo "[SKIP] existing full snapshot manifest detected while bot_main is running."
    echo "[HINT] manifest=$MANIFEST_PATH"
    echo "[HINT] set ALLOW_EXISTING_FULL_BUILD_WITH_BOT=1 to force duplicate full rebuild."
    exit 0
  fi

  if [[ "$START_JITTER_SEC" =~ ^[0-9]+$ ]] && [[ "$START_JITTER_SEC" -gt 0 ]]; then
    JITTER_WAIT=$((RANDOM % (START_JITTER_SEC + 1)))
    echo "[INFO] run_monitor_snapshot jitter wait=${JITTER_WAIT}s (max=${START_JITTER_SEC}s)"
    sleep "$JITTER_WAIT"
  fi

  EXTRA_ARGS=()
  if [[ "$SKIP_SERVER_COMPARISON" == "1" ]]; then
    EXTRA_ARGS+=(--skip-server-comparison)
  fi

  echo "[INFO] run_monitor_snapshot start date=$TARGET_DATE preopen=$IN_PREOPEN bot_running=$BOT_RUNNING profile=$PROFILE io_delay_sec=$IO_DELAY_SEC skip_server_comparison=$SKIP_SERVER_COMPARISON notify_admin=$NOTIFY_ADMIN lock_wait_sec=$LOCK_WAIT_SEC"
  SNAPSHOT_OUTPUT_FILE="$(mktemp "$PROJECT_DIR/tmp/run_monitor_snapshot.XXXXXX")"
  set +e
  # outer flock already guards this wrapper; skip the inner lock to avoid self lock_busy skips
  timeout "$TIMEOUT_SEC" env PYTHONPATH=. "$VENV_PY" -m src.engine.run_monitor_snapshot --date "$TARGET_DATE" --profile "$PROFILE" --io-delay-sec "$IO_DELAY_SEC" --skip-lock "${EXTRA_ARGS[@]}" > "$SNAPSHOT_OUTPUT_FILE" 2>&1
  SNAPSHOT_STATUS=$?
  set -e
  cat "$SNAPSHOT_OUTPUT_FILE"
  if [[ "$SNAPSHOT_STATUS" -ne 0 ]]; then
    rm -f "$SNAPSHOT_OUTPUT_FILE"
    exit "$SNAPSHOT_STATUS"
  fi
  if [[ "$NOTIFY_ADMIN" == "1" ]]; then
    env PYTHONPATH=. "$VENV_PY" -m src.engine.notify_monitor_snapshot_admin \
      --target-date "$TARGET_DATE" \
      --profile "$PROFILE" \
      --result-file "$SNAPSHOT_OUTPUT_FILE" \
      --log-file "$LOG_FILE" || true
  fi
  rm -f "$SNAPSHOT_OUTPUT_FILE"
  echo "[INFO] run_monitor_snapshot done date=$TARGET_DATE"
} 9>"$LOCK_FILE" >> "$LOG_FILE" 2>&1
